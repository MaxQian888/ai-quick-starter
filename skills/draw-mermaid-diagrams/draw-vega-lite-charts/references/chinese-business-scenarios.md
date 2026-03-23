# Chinese Business Scenarios for Vega-Lite

## Table of Contents

- [Usage](#usage)
- [1. 电商场景](#1-电商场景)
- [2. 增长场景](#2-增长场景)
- [3. 运营看板场景](#3-运营看板场景)
- [Output Convention for Chinese Requests](#output-convention-for-chinese-requests)

## Usage

当用户用中文描述业务问题时，优先复用本文件中的 prompt 模板与字段映射建议，再输出 Vega-Lite JSON。
先明确指标、维度、时间粒度，再决定 mark 和 encoding。

## 1. 电商场景

### A. 销售趋势看板

- 用户常见提法:
  - "按月看各区域销售额趋势"
  - "最近 12 个月 GMV 走势，按渠道分组"
- 推荐图形:
  - `line`（多序列趋势）
- 默认编码:
  - `x`: 时间（`temporal`, `timeUnit: yearmonth`）
  - `y`: `sum(sales)` 或 `sum(gmv)`
  - `color`: 区域/渠道
- 可直接复用的中文 prompt:
  - "请用 Vega-Lite 生成一个折线图，展示最近 12 个月按渠道拆分的 GMV 趋势，包含 tooltip。"

### B. 商品 Top N

- 用户常见提法:
  - "销售额前 10 的商品"
  - "按品类看销量排名"
- 推荐图形:
  - 排序 `bar`
- 默认编码:
  - `x`: 商品或品类（`nominal`）
  - `y`: `sum(sales)` 或 `sum(quantity)`
  - `sort`: `-y`
- 常用 transform:
  - `window` 生成 rank
  - `filter` 保留 Top N
- 可直接复用的中文 prompt:
  - "请输出 Vega-Lite 柱状图，展示销售额 Top10 商品，并按销售额降序排序。"

### C. 转化漏斗近似表达

- 用户常见提法:
  - "浏览-加购-下单-支付 转化"
- 推荐图形:
  - 排序 `bar`（如果必须用标准 Vega-Lite，优先用条形图表达漏斗阶段）
- 默认编码:
  - `y`: 阶段（`ordinal`）
  - `x`: 用户数或会话数（`quantitative`）
- 可直接复用的中文 prompt:
  - "请用 Vega-Lite 画一个横向条形图表示转化漏斗，各阶段按流程顺序展示，并加上转化率 tooltip。"

## 2. 增长场景

### A. 拉新与激活趋势

- 用户常见提法:
  - "每周新增与激活用户趋势"
- 推荐图形:
  - `line` + `color`
- 默认编码:
  - `x`: 周（预处理成 week_start 或使用 temporal）
  - `y`: `sum(new_users)` / `sum(activated_users)`
  - `color`: 指标名称（可先折成长表）
- 可直接复用的中文 prompt:
  - "请生成 Vega-Lite 折线图，对比每周新增用户和激活用户趋势。"

### B. 渠道投放效果

- 用户常见提法:
  - "广告花费和转化率的关系"
  - "不同渠道 ROI 对比"
- 推荐图形:
  - 相关性用 `point`
  - 对比用排序 `bar`
- 默认编码（散点）:
  - `x`: `ad_spend`
  - `y`: `conversion_rate` 或 `roi`
  - `color`: `channel`
  - `size`: `impressions` 或 `clicks`
- 可直接复用的中文 prompt:
  - "请输出 Vega-Lite 散点图，x 为广告花费，y 为转化率，按渠道着色，点大小表示曝光量。"

### C. 留存表现

- 用户常见提法:
  - "看 D1/D7/D30 留存按注册周分组"
- 推荐图形:
  - `line`（多条留存曲线）或 `bar`（分组对比）
- 默认编码:
  - `x`: 留存天（`ordinal` 或 `quantitative`）
  - `y`: 留存率（`quantitative`）
  - `color`: 注册周或 cohort
- 可直接复用的中文 prompt:
  - "请给我一个 Vega-Lite 图，展示不同注册周 cohort 的 D1/D7/D30 留存率对比。"

## 3. 运营看板场景

### A. 工单与 SLA

- 用户常见提法:
  - "每天工单量和超时率"
  - "各团队 SLA 达成情况"
- 推荐图形:
  - 趋势: `line`
  - 团队对比: `bar`
- 默认编码:
  - `x`: 日期或团队
  - `y`: 工单量/超时率/SLA 达成率
  - `color`: 团队或优先级
- 可直接复用的中文 prompt:
  - "请生成 Vega-Lite 图表，展示最近 30 天每天工单量与超时率趋势。"

### B. 库存健康度

- 用户常见提法:
  - "库存周转天数按仓库对比"
  - "缺货 SKU 排名"
- 推荐图形:
  - 排序 `bar`
- 默认编码:
  - `x`: 仓库或 SKU
  - `y`: 周转天数或缺货次数
  - `sort`: `-y`
- 可直接复用的中文 prompt:
  - "请输出 Vega-Lite 柱状图，对比各仓库库存周转天数，并按从高到低排序。"

### C. 客服效率

- 用户常见提法:
  - "首响时长和满意度的关系"
- 推荐图形:
  - `point`
- 默认编码:
  - `x`: 首响时长
  - `y`: 满意度
  - `color`: 客服组
  - `size`: 会话量
- 可直接复用的中文 prompt:
  - "请用 Vega-Lite 生成散点图，分析首响时长与满意度关系，按客服组着色。"

## Output Convention for Chinese Requests

- 保持用户原始中文业务术语，不擅自改字段含义。
- 若字段名未知，先列出所需字段清单，再给占位 `data.url` 的可运行 spec。
- 默认输出一个主方案；仅在用户明确要求时给 2 个备选方案。
