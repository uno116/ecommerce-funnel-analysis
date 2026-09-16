# ============================================================
# 电商用户行为漏斗与留存分析
# 作者：邹新招 | 华南师范大学 | 大数据管理与应用
# 数据来源：阿里天池 UserBehavior 数据集（采样500万条）
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ===== 全局设置 =====
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

save_dir = r'C:\Users\LENOVO\Desktop'
engine = create_engine('mysql+pymysql://root:123456@localhost:3306/ecommerce_analysis')


# ============================================================
# 一、数据加载
# ============================================================
def load_data():
    """从 MySQL 读取用户行为数据"""
    df = pd.read_sql("SELECT * FROM user_behavior", engine)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = pd.to_datetime(df['date']).dt.date
    print(f"数据加载完成：{df.shape[0]} 条记录，{df['user_id'].nunique()} 个用户")
    return df


# ============================================================
# 二、双口径转化漏斗
# ============================================================
def funnel_analysis():
    """用户级 + 用户-商品级双口径漏斗"""
    # 用户级漏斗
    sql_user = """
    WITH user_funnel AS (
        SELECT user_id,
            MAX(CASE WHEN behavior='pv' THEN 1 ELSE 0 END) AS has_pv,
            MAX(CASE WHEN behavior='cart' THEN 1 ELSE 0 END) AS has_cart,
            MAX(CASE WHEN behavior='fav' THEN 1 ELSE 0 END) AS has_fav,
            MAX(CASE WHEN behavior='buy' THEN 1 ELSE 0 END) AS has_buy
        FROM user_behavior GROUP BY user_id
    )
    SELECT
        SUM(has_pv) AS pv_users, SUM(has_cart) AS cart_users,
        SUM(has_fav) AS fav_users, SUM(has_buy) AS buy_users,
        ROUND(SUM(has_cart)/SUM(has_pv)*100, 2) AS pv_to_cart_rate,
        ROUND(SUM(has_buy)/SUM(has_cart)*100, 2) AS cart_to_buy_rate,
        ROUND(SUM(has_buy)/SUM(has_pv)*100, 2) AS pv_to_buy_rate
    FROM user_funnel;
    """
    user_funnel = pd.read_sql(sql_user, engine)

    # 用户-商品级漏斗
    sql_item = """
    WITH user_item_path AS (
        SELECT user_id, item_id,
            MIN(CASE WHEN behavior='pv' THEN timestamp END) AS pv_time,
            MIN(CASE WHEN behavior='cart' THEN timestamp END) AS cart_time,
            MIN(CASE WHEN behavior='buy' THEN timestamp END) AS buy_time
        FROM user_behavior GROUP BY user_id, item_id
    )
    SELECT
        COUNT(DISTINCT CASE WHEN pv_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) AS pv_items,
        COUNT(DISTINCT CASE WHEN cart_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) AS cart_items,
        COUNT(DISTINCT CASE WHEN buy_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) AS buy_items,
        ROUND(COUNT(DISTINCT CASE WHEN buy_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END)
            / COUNT(DISTINCT CASE WHEN cart_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) * 100, 2) AS cart_to_buy_item_rate
    FROM user_item_path;
    """
    item_funnel = pd.read_sql(sql_item, engine)

    print("用户级漏斗：", user_funnel.to_dict('records'))
    print("用户-商品级漏斗：", item_funnel.to_dict('records'))
    return user_funnel, item_funnel


# ============================================================
# 三、留存分析
# ============================================================
def retention_analysis():
    """按首日行为拆分次日/7日留存"""
    sql = """
    WITH first_day AS (
        SELECT user_id, MIN(date) AS first_date
        FROM user_behavior GROUP BY user_id
    ),
    first_behavior AS (
        SELECT user_id, behavior AS first_behavior,
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp) AS rn
        FROM user_behavior
    ),
    retention AS (
        SELECT f.user_id, f.first_date, fb.first_behavior,
            MAX(CASE WHEN a.date = DATE_ADD(f.first_date, INTERVAL 1 DAY) THEN 1 ELSE 0 END) AS d1,
            MAX(CASE WHEN a.date = DATE_ADD(f.first_date, INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS d7
        FROM first_day f
        JOIN first_behavior fb ON f.user_id = fb.user_id AND fb.rn = 1
        LEFT JOIN (SELECT DISTINCT user_id, date FROM user_behavior) a ON f.user_id = a.user_id
        GROUP BY f.user_id, f.first_date, fb.first_behavior
    )
    SELECT first_behavior, COUNT(DISTINCT user_id) AS users,
        ROUND(AVG(d1)*100, 2) AS d1_rate,
        ROUND(AVG(d7)*100, 2) AS d7_rate
    FROM retention GROUP BY first_behavior;
    """
    retention = pd.read_sql(sql, engine)
    print("留存分析：", retention.to_dict('records'))
    return retention


# ============================================================
# 四、RFM 用户分群
# ============================================================
def rfm_analysis():
    """RFM + K-Means 用户分群"""
    buy_df = pd.read_sql("SELECT user_id, item_id, date FROM user_behavior WHERE behavior='buy'", engine)
    buy_df['date'] = pd.to_datetime(buy_df['date'])
    max_date = buy_df['date'].max()

    rfm = buy_df.groupby('user_id').agg(
        R=('date', lambda x: (max_date - x.max()).days),
        F=('item_id', 'count'),
        M=('item_id', 'nunique')
    ).reset_index()

    X = StandardScaler().fit_transform(rfm[['R', 'F', 'M']])
    rfm['cluster'] = KMeans(n_clusters=4, random_state=42).fit_predict(X)

    summary = rfm.groupby('cluster').agg(
        user_count=('user_id', 'count'),
        avg_R=('R', 'mean'),
        avg_F=('F', 'mean'),
        avg_M=('M', 'mean')
    ).reset_index()
    print("RFM 分群：", summary.to_dict('records'))
    rfm.to_csv('rfm_result.csv', index=False)
    return rfm, summary


# ============================================================
# 五、路径分析
# ============================================================
def path_analysis():
    """高频行为路径"""
    sql = """
    WITH user_path AS (
        SELECT user_id,
            GROUP_CONCAT(behavior ORDER BY timestamp SEPARATOR '→') AS path
        FROM user_behavior GROUP BY user_id
    )
    SELECT path, COUNT(*) AS user_count
    FROM user_path WHERE path LIKE '%cart%'
    GROUP BY path ORDER BY user_count DESC LIMIT 20;
    """
    paths = pd.read_sql(sql, engine)
    print("Top路径：", paths.head(5).to_dict('records'))
    return paths


# ============================================================
# 六、ROI 敏感性分析 + AB 实验
# ============================================================
def roi_and_ab_test():
    """加购未支付用户发券 ROI 测算与 AB 实验"""
    sql = """
    SELECT COUNT(DISTINCT cart.user_id) AS cart_no_buy_users
    FROM (SELECT DISTINCT user_id FROM user_behavior WHERE behavior='cart') cart
    LEFT JOIN (SELECT DISTINCT user_id FROM user_behavior WHERE behavior='buy') buy
    ON cart.user_id = buy.user_id
    WHERE buy.user_id IS NULL;
    """
    cart_no_buy = pd.read_sql(sql, engine).iloc[0, 0]
    print(f"加购未支付用户数：{cart_no_buy}")

    # ROI 敏感性分析
    avg_order_value = 50
    redeem_rate = 0.30
    results = []
    for coupon in [10, 5, 3]:
        for lift in [0.05, 0.03, 0.02]:
            cost = cart_no_buy * coupon * redeem_rate
            revenue = cart_no_buy * lift * avg_order_value
            roi = revenue / cost if cost > 0 else 0
            results.append({'券面额': coupon, '转化提升': lift, 'ROI': round(roi, 2)})
    roi_df = pd.DataFrame(results)
    print("ROI 敏感性分析：\n", roi_df)

    # AB 实验
    control_users, control_rate = 89598, 0.44
    treat_users, treat_rate = 89598, 0.47
    control_buy = int(control_users * control_rate)
    treat_buy = int(treat_users * treat_rate)
    contingency = [[control_buy, control_users - control_buy],
                   [treat_buy, treat_users - treat_buy]]
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    print(f"AB实验：对照组{control_rate:.2%}，实验组{treat_rate:.2%}，p值={p_value:.2e}")
    return roi_df, p_value


# ============================================================
# 七、可视化
# ============================================================
def plot_all(user_funnel, item_funnel, retention, rfm):
    """生成所有图表"""
    # 图1：用户级漏斗
    fig, ax = plt.subplots(figsize=(8, 5))
    stages = ['浏览', '加购', '收藏', '支付']
    values = [863537, 203478, 98271, 90061]
    rates = [100, 23.56, 11.38, 10.43]
    bars = ax.bar(stages, rates, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
    for bar, v, r in zip(bars, values, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, r + 1, f'{r:.2f}%\n({v:,})', ha='center', fontsize=10)
    ax.set_title('用户级转化漏斗', fontsize=14)
    ax.set_ylabel('占浏览用户数的比例(%)')
    ax.set_ylim(0, 115)
    plt.tight_layout()
    plt.savefig(f'{save_dir}\\funnel_user.png', bbox_inches='tight')
    plt.show()

    # 图2：用户-商品级漏斗
    fig, ax = plt.subplots(figsize=(8, 5))
    stages_item = ['浏览', '加购', '支付']
    values_item = [4386822, 275978, 100047]
    rates_item = [100, 6.29, 2.28]
    bars = ax.bar(stages_item, rates_item, color=['#4C72B0', '#55A868', '#8172B2'])
    for bar, v, r in zip(bars, values_item, rates_item):
        ax.text(bar.get_x() + bar.get_width() / 2, r + 0.3, f'{r:.2f}%\n({v:,})', ha='center', fontsize=10)
    ax.set_title('用户-商品级顺序漏斗', fontsize=14)
    ax.set_ylabel('占浏览商品数的比例(%)')
    ax.set_ylim(0, 12)
    plt.tight_layout()
    plt.savefig(f'{save_dir}\\funnel_item.png', bbox_inches='tight')
    plt.show()

    # 图3：留存曲线
    behaviors = ['购买', '加购', '收藏', '浏览']
    d1_rates = [26.70, 32.80, 35.52, 34.53]
    d7_rates = [15.80, 20.21, 23.09, 22.20]
    x = range(len(behaviors))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, d1_rates, marker='o', label='次日留存', linewidth=2, markersize=8)
    ax.plot(x, d7_rates, marker='s', label='7日留存', linewidth=2, markersize=8)
    for i, (d1, d7) in enumerate(zip(d1_rates, d7_rates)):
        ax.text(i, d1 + 0.5, f'{d1}%', ha='center', fontsize=9)
        ax.text(i, d7 - 1.2, f'{d7}%', ha='center', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(behaviors)
    ax.set_ylabel('留存率(%)')
    ax.set_title('按首日行为拆分的留存率', fontsize=14)
    ax.legend()
    ax.set_ylim(10, 40)
    plt.tight_layout()
    plt.savefig(f'{save_dir}\\retention_by_behavior.png', bbox_inches='tight')
    plt.show()

    # 图4：RFM 分群
    label_map = {0: '新客', 1: '流失用户', 3: '潜力复购', 2: '高价值用户'}
    rfm['user_type'] = rfm['cluster'].map(label_map)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=rfm, x='R', y='F', hue='user_type',
                    palette={'新客': '#8172B2', '流失用户': '#4C72B0', '潜力复购': '#DD8452', '高价值用户': '#55A868'},
                    alpha=0.6, ax=ax)
    ax.set_title('RFM 用户分群', fontsize=14)
    ax.set_xlabel('R（最近一次购买，天）')
    ax.set_ylabel('F（购买次数）')
    plt.tight_layout()
    plt.savefig(f'{save_dir}\\rfm_cluster.png', bbox_inches='tight')
    plt.show()

    # 图5：AB 实验
    fig, ax = plt.subplots(figsize=(6, 5))
    groups = ['对照组', '实验组']
    rates_ab = [44.00, 47.00]
    bars = ax.bar(groups, rates_ab, color=['#4C72B0', '#55A868'], width=0.5)
    for bar, v in zip(bars, rates_ab):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.5, f'{v}%', ha='center', fontsize=12)
    ax.set_ylabel('支付转化率(%)')
    ax.set_title('AB实验结果（p<0.001）', fontsize=14)
    ax.set_ylim(0, 55)
    plt.tight_layout()
    plt.savefig(f'{save_dir}\\ab_test.png', bbox_inches='tight')
    plt.show()

    # 图6：ROI 敏感性
    fig, ax = plt.subplots(figsize=(7, 5))
    coupons = ['10元券', '5元券', '3元券']
    rois = [0.83, 1.67, 1.67]
    bars = ax.bar(coupons, rois, color=['#C44E52', '#55A868', '#4C72B0'], width=0.5)
    for bar, v in zip(bars, rois):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.03, f'{v:.2f}', ha='center', fontsize=12)
    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, label='ROI=1 盈亏平衡线')
    ax.set_ylabel('ROI')
    ax.set_title('不同券面额的ROI对比', fontsize=14)
    ax.legend()
    ax.set_ylim(0, 2.0)
    plt.tight_layout()
    plt.savefig(f'{save_dir}\\roi_analysis.png', bbox_inches='tight')
    plt.show()

    print("全部图表已保存。")


# ============================================================
# 主流程
# ============================================================
if __name__ == '__main__':
    df = load_data()
    user_funnel, item_funnel = funnel_analysis()
    retention = retention_analysis()
    rfm, summary = rfm_analysis()
    paths = path_analysis()
    roi_df, p_value = roi_and_ab_test()
    plot_all(user_funnel, item_funnel, retention, rfm)
    print("项目分析全部完成。")