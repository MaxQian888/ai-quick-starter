# 注入"人味"的 8 条规则

每条都是**可机器执行的指令**——不是抽象建议。每条都给微例子。
"人味"不是玄学，它是 8 个具体信号的总和。

## 核心判定

读完一段，**读者能不能想到一个具体的人在写**？如果不能，缺人味。

不要追求"反检测器"——追求"读起来像深思熟虑的真人"。前者是猫鼠游戏会输，后者是真目标且永远有效。

## 规则 1：用具体替代抽象（最核心）

抽象动词后必须给数字、地点、动作、品牌名、时间任一种。

- ❌ "Puppies need exercise."
- ✅ "Take your puppy on a 20-minute walk and 15 minutes of fetch."

- ❌ "工具很重要"
- ✅ "好的 ripgrep + fd + jq 组合能省你一个小时"

- ❌ "achieve growth"
- ✅ "expand regional sales by 15% in Q3"

- ❌ "提升了用户体验"
- ✅ "首屏从 3.2s 降到 1.1s"

**硬规则**：每段至少 1 个具体名词或数字。**强制注入**——如果原文真的没有可锚定的事实，要求作者补一个。

## 规则 2：混合句长（high burstiness）

AI 文章最强信号是句长均匀。真人写作有节奏起伏。

**硬规则**：

- 连续 3 句不能字数相近（差 < 5 字 / words）
- 每段至少 1 句 < 10 字（中文）/ < 10 words（英文）
- 每段允许 1 句 > 25 字铺陈逻辑

例子：

- ✅ "She left. Without warning, without a goodbye, without even closing the door behind her — and that, somehow, hurt the most."
- ✅ "他走了。没说一句话。第二天早上我才发现房间空了。"

## 规则 3：第一/第二人称 + 选择性缩写

- 中文：用"你/我/咱们"代替"用户/读者/大家"
- 英文：加 `you/your`，加 `I/we`，**选择性**用缩写 `don't / it's / you're`（不要全局替换，会显得假）

- ❌ "用户在使用此功能时可能遇到的问题包括 ..."
- ✅ "你试这个功能时大概会撞上几个坑 ..."

- ❌ "It is generally accepted that ..."
- ✅ "I think most people agree that ..."

**注意**：缩写要有选择，不要把所有"it is"都改成"it's"——这是另一种假。

## 规则 4：敢有立场（authorial stake）

AI 最爱"完美平衡"——每句话都对一半。真人写作敢站边。

模板（中文）：
- "我认为 X 是错的，原因是 ..."
- "X 听起来好，但实际上 ..."
- "大家都说 X，其实 Y 才对"

模板（英文）：
- "I think X is wrong. Here's why."
- "X sounds good, but it isn't."
- "People keep saying X. They're wrong."

**硬规则**：长文里至少 1 处明确立场。删除完美正反平衡——选一边站。

Paul Graham 原话：**"don't try to sound impressive."**

## 规则 5：微观察 / 反高潮 / 自嘲

真人会注意到 AI 注意不到的细节。

- **微观察**：作者真的看到/经历过的具体景象
  - ✅ "凌晨 3 点的 stack trace 第 47 行"
  - ✅ "the coffee stain on the printout"
  - ✅ "地铁里有人手机外放放抖音的那个下午"

- **自嘲**：承认自己的弱点或失败
  - ✅ "I spent two hours debugging this. It was a typo."
  - ✅ "我花了一个下午查这个 bug，最后是少了个逗号。"

- **反高潮**：把"震撼结论"换成平淡观察
  - ❌ "这将彻底改变行业格局！"
  - ✅ "它也就让事情变了一点。"

**硬规则**：技术博客和公众号至少 1 处微观察或自嘲。

## 规则 6：用具体名词替代抽象名词

- ❌ "tools" → ✅ "ripgrep, fd, jq"
- ❌ "many companies" → ✅ "Stripe, Vercel, Linear"
- ❌ "一些用户" → ✅ "我们 200 个 beta 用户里有 30 个"
- ❌ "某种工具" → ✅ "Postman / curl 这种工具"

**硬规则**：每段至少 1 个专有名词（人 / 公司 / 产品 / 工具 / 地点）。

## 规则 7：偶尔违反语法（stylistic license）

AI 严格守语法。真人会用句子片段做强调。

- 用 `And` / `But` / `Because` 开头
- 用句子片段（"Not anymore." / "Worth it." / "Maybe."）
- 中文：用单字句、不完整句（"散了。" / "懂的都懂。"）

**注意**：偶尔，不是每段都用。每篇 1-2 处即可。

## 规则 8：每篇至少 1 个真实小故事 / 类比 / anecdote

模板：**"去年我在 X 做 Y，结果 Z。"**

任何带时间、地点、人物的具体经历，比 1000 字通论都更"人味"。

例子：
- "上个月帮一家创业公司改 onboarding，第一版漏斗转化 12%。改了三个字的 CTA 后，到 27%。"
- "Last year I spent a weekend trying to make our staging env match prod. The trick was just... not using Docker for it."

如果原文是纯抽象讨论，没有 anecdote 锚点，要求作者补一个。

## 综合自测

读完一篇文章问自己：

1. 通篇有几个具体名词？（< 3 个 → 加）
2. 句长方差够不够？（连续 3 句相近 → 改）
3. 有没有作者立场？（通篇中立 → 加）
4. 有没有微观察或具体故事？（没有 → 加）
5. 段首是不是都"主语 + 动词"？（80%+ 是 → 换些段首结构）

5 项里 ≥ 3 项不达标 → 缺人味，必须重写。

## Anti-pattern 提醒

不要为了"有人味"做这些（业界已证伪）：

- ❌ 加 typo
- ❌ 加感叹号 / ALL CAPS
- ❌ 强行全局缩写（"it is" → "it's"）
- ❌ 滥用语气词（"咳"、"哇"、"嘿"）
- ❌ 假装 ADHD（频繁打断自己）
- ❌ 强加"我是个累的咖啡因副作用程序员"人设
