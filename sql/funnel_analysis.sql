-- ============================================
-- 电商用户行为漏斗与留存分析
-- 数据库：ecommerce_analysis
-- 表：user_behavior
-- ============================================

-- 1. 用户级漏斗
WITH user_funnel AS (
    SELECT
        user_id,
        MAX(CASE WHEN behavior='pv' THEN 1 ELSE 0 END) AS has_pv,
        MAX(CASE WHEN behavior='cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN behavior='fav' THEN 1 ELSE 0 END) AS has_fav,
        MAX(CASE WHEN behavior='buy' THEN 1 ELSE 0 END) AS has_buy
    FROM user_behavior
    GROUP BY user_id
)
SELECT
    SUM(has_pv) AS pv_users,
    SUM(has_cart) AS cart_users,
    SUM(has_fav) AS fav_users,
    SUM(has_buy) AS buy_users,
    ROUND(SUM(has_cart)/SUM(has_pv)*100, 2) AS pv_to_cart_rate,
    ROUND(SUM(has_buy)/SUM(has_cart)*100, 2) AS cart_to_buy_rate,
    ROUND(SUM(has_buy)/SUM(has_pv)*100, 2) AS pv_to_buy_rate
FROM user_funnel;

-- 2. 用户-商品级顺序漏斗
WITH user_item_path AS (
    SELECT
        user_id,
        item_id,
        MIN(CASE WHEN behavior='pv' THEN timestamp END) AS pv_time,
        MIN(CASE WHEN behavior='cart' THEN timestamp END) AS cart_time,
        MIN(CASE WHEN behavior='buy' THEN timestamp END) AS buy_time
    FROM user_behavior
    GROUP BY user_id, item_id
)
SELECT
    COUNT(DISTINCT CASE WHEN pv_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) AS pv_items,
    COUNT(DISTINCT CASE WHEN cart_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) AS cart_items,
    COUNT(DISTINCT CASE WHEN buy_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) AS buy_items,
    ROUND(COUNT(DISTINCT CASE WHEN buy_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END)
        / COUNT(DISTINCT CASE WHEN cart_time IS NOT NULL THEN CONCAT(user_id,'-',item_id) END) * 100, 2) AS cart_to_buy_item_rate
FROM user_item_path;

-- 3. 留存分析（按首日行为拆分）
WITH first_day AS (
    SELECT user_id, MIN(date) AS first_date
    FROM user_behavior
    GROUP BY user_id
),
first_behavior AS (
    SELECT
        user_id,
        behavior AS first_behavior,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp) AS rn
    FROM user_behavior
),
retention AS (
    SELECT
        f.user_id,
        f.first_date,
        fb.first_behavior,
        MAX(CASE WHEN a.date = DATE_ADD(f.first_date, INTERVAL 1 DAY) THEN 1 ELSE 0 END) AS d1,
        MAX(CASE WHEN a.date = DATE_ADD(f.first_date, INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS d7
    FROM first_day f
    JOIN first_behavior fb ON f.user_id = fb.user_id AND fb.rn = 1
    LEFT JOIN (SELECT DISTINCT user_id, date FROM user_behavior) a
        ON f.user_id = a.user_id
    GROUP BY f.user_id, f.first_date, fb.first_behavior
)
SELECT
    first_behavior,
    COUNT(DISTINCT user_id) AS users,
    ROUND(AVG(d1)*100, 2) AS d1_rate,
    ROUND(AVG(d7)*100, 2) AS d7_rate
FROM retention
GROUP BY first_behavior;

-- 4. 路径分析
WITH user_path AS (
    SELECT
        user_id,
        GROUP_CONCAT(behavior ORDER BY timestamp SEPARATOR '→') AS path
    FROM user_behavior
    GROUP BY user_id
)
SELECT
    path,
    COUNT(*) AS user_count
FROM user_path
WHERE path LIKE '%cart%'
GROUP BY path
ORDER BY user_count DESC
LIMIT 20;

-- 5. 加购未支付用户数
SELECT COUNT(DISTINCT cart.user_id) AS cart_no_buy_users
FROM (SELECT DISTINCT user_id FROM user_behavior WHERE behavior='cart') cart
LEFT JOIN (SELECT DISTINCT user_id FROM user_behavior WHERE behavior='buy') buy
ON cart.user_id = buy.user_id
WHERE buy.user_id IS NULL;