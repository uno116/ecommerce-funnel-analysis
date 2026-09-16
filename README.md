\# 电商用户行为漏斗与留存分析



\## 1. 项目背景



模拟某电商平台运营场景：平台发现支付转化率持续走低，运营总监要求定位流失环节、识别高价值用户、制定召回策略。本项目基于阿里天池 UserBehavior 公开数据集，完成从数据清洗、漏斗分析、留存分析、用户分群到策略验证的完整分析闭环。



\## 2. 数据来源



| 项目 | 说明 |

|---|---|

| 来源 | 阿里天池 UserBehavior 数据集 |

| 原始规模 | 约 1 亿条用户行为记录 |

| 采样规模 | 500 万条 |

| 覆盖用户 | 约 86 万 |

| 时间范围 | 2017-11-25 至 2017-12-03 |

| 行为类型 | pv（浏览）、cart（加购）、fav（收藏）、buy（支付） |



\## 3. 技术栈



\- \*\*数据处理\*\*：MySQL（窗口函数、CTE、条件聚合）、Python（Pandas、NumPy）

\- \*\*建模\*\*：Scikit-learn（K-Means、StandardScaler）

\- \*\*统计检验\*\*：SciPy（卡方检验）

\- \*\*可视化\*\*：Matplotlib、Seaborn、Power BI

\- \*\*开发工具\*\*：Git、Jupyter Notebook、DataGrip



\## 4. 分析流程



\### 4.1 数据清洗与采样

从 1 亿条原始数据中采样 5%，得到 500 万条记录，导入 MySQL 建表。



\### 4.2 双口径转化漏斗

\- \*\*用户级漏斗\*\*：按用户去重，计算浏览→加购→收藏→支付的转化率。

\- \*\*用户-商品级顺序漏斗\*\*：按“用户-商品”组合去重，要求同一用户对同一商品完成完整路径。



\### 4.3 留存分析

按首日行为（pv/cart/fav/buy）拆分，计算次日留存和 7 日留存。



\### 4.4 用户分群

基于 RFM 模型计算 R（最近购买）、F（购买频次）、M（购买商品数），使用 K-Means 聚类划分 4 类用户。



\### 4.5 路径分析

统计用户高频行为序列，定位最大流失路径。



\### 4.6 策略模拟与 ROI 测算

针对加购未支付用户设计分层发券策略，做 ROI 敏感性分析。



\### 4.7 AB 实验设计

设计实验组与对照组，用卡方检验验证策略显著性。



\## 5. 核心结论



| 分析模块 | 核心发现 |

|---|---|

| 用户级漏斗 | 浏览 863,537 → 加购 203,478 → 支付 90,061，加购到支付转化率 44.26% |

| 用户-商品级漏斗 | 加购到支付转化率 36.25%，与用户级差 8 个百分点 |

| 留存分析 | 收藏用户 7 日留存 23.09% 最高，购买用户 15.80% 最低 |

| RFM 分群 | 高价值用户 198 人，人均购买 4.52 次，复购频次是普通用户的 4 倍以上 |

| 路径分析 | 加购未支付用户 179,196 人，为最大可召回群体 |

| ROI 测算 | 10 元券 ROI 0.83，5 元券 ROI 1.67 |

| AB 实验 | 实验组转化率 47% vs 对照组 44%，p<0.001，策略显著有效 |



\### 关键洞察



\- \*\*双口径差异 8 个百分点\*\*：说明大量用户加购 A 商品后购买了 B 商品，用户级漏斗高估了单品转化率，购物车关联推荐有优化空间。

\- \*\*收藏用户留存最高\*\*：说明“未满足需求”比“已满足需求”更能驱动回访，收藏代表“想买但还没买”，这种张力促使用户持续回访。

\- \*\*加购未支付是最大流失环节\*\*：179,196 人加购后未支付，是召回策略的首要目标。



\## 6. 策略建议



1\. \*\*加购未支付用户\*\*：优先发 5 元券，设计 AB 实验验证真实提升，避免盲目发 10 元券导致 ROI 亏损。

2\. \*\*收藏用户\*\*：强化收藏后定向触达，利用“未满足需求”驱动回访。

3\. \*\*高价值用户\*\*：专属权益维护，提升复购频次。



\## 7. 可视化
\### Python 分析图表

!\[用户级漏斗](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/images/funnel\_user.png)

!\[用户-商品级漏斗](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/images/funnel\_item.png)

!\[留存曲线](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/images/retention\_by\_behavior.png)

!\[RFM分群](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/images/rfm\_cluster.png)

!\[AB实验](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/images/ab\_test.png)

!\[ROI分析](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/images/roi\_analysis.png)



\### Power BI 看板



\*\*第1页：总览\*\*
!\[总览](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/dashboard/dashboard\_p1.png)



\*\*第2页：漏斗与留存\*\*
!\[漏斗与留存](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/dashboard/dashboard\_p2.png)



\*\*第3页：策略与AB实验\*\*
!\[策略与AB实验](https://raw.githubusercontent.com/uno116/ecommerce-funnel-analysis/main/dashboard/dashboard\_p3.png)


完整看板 PDF：[dashboard/ecommerce_dashboard.pdf](https://github.com/uno116/ecommerce-funnel-analysis/blob/main/dashboard/ecommerce_dashboard.pdf)



\## 8. 目录结构

ecommerce-funnel-analysis/

├── README.md

├── requirements.txt

├── .gitignore

├── data/

│ └── sample\_1000.csv

├── sql/

│ └── funnel\_analysis.sql

├── notebooks/

│ └── analysis.py

├── images/

│ ├── funnel\_user.png

│ ├── funnel\_item.png

│ ├── retention\_by\_behavior.png

│ ├── rfm\_cluster.png

│ ├── ab\_test.png

│ └── roi\_analysis.png

└── dashboard/

├── ecommerce\_dashboard.pdf

├── dashboard\_p1.png

├── dashboard\_p2.png

└── dashboard\_p3.png



\## 9. 如何运行



1\. 将 `data/sample\_1000.csv` 导入 MySQL，建表 `user\_behavior`

2\. 安装依赖：`pip install -r requirements.txt`

3\. 修改 `notebooks/analysis.py` 中的数据库连接配置

4\. 运行：`python notebooks/analysis.py`



\## 10. 作者



邹新招 | 华南师范大学 | 大数据管理与应用  

GitHub：https://github.com/uno116

