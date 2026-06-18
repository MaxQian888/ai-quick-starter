# 信息密度 12 条修复规则

每条都有"修改前 → 修改后"微例子，可直接训给 rewriter。
源头：Strunk & White、Orwell《Politics and the English Language》、Paul Graham《Writing, Briefly》、Hemingway。

## 核心原则

**信息密度 = 每个字传递的新信息量。** 删掉一个字如果不影响意思，那个字就是负密度。

Paul Graham 的话：**"删到不能再删，再删一遍。"**

## 规则 1：删元评论（meta-commentary）

不要告诉读者"我要讲什么"，直接讲。

- ❌ "In this article we will explore the topic of X."
- ✅ "X 是 ..."（直接讲）

- ❌ "本文将探讨 X 的相关问题。"
- ✅ 直接陈述对 X 的观察

- ❌ "下面让我们来看 ..."
- ✅ 直接看

**删一切承上启下、过门、自我介绍式句子。**

## 规则 2：删"the fact that" / "事实是 ..."

Strunk 标准：用名词替代名词从句。

- ❌ "owing to the fact that" → ✅ "because"
- ❌ "the fact that he had not succeeded" → ✅ "his failure"
- ❌ "call your attention to the fact that" → ✅ "remind you that"
- ❌ "事实是这种做法行不通" → ✅ "这种做法行不通"

## 规则 3：删冗余的"this/that/which/这/那"

- ❌ "the proposal which was rejected" → ✅ "the rejected proposal"
- ❌ "他提出的这个方案" → ✅ "他的方案"
- ❌ "这一现象表明 ..." → ✅ "（直接讲后面的判断）"

## 规则 4：删限定词（Strunk 的"水蛭"）

英文常见水蛭：

```
rather  very  little  pretty  quite  really  actually
basically  literally  certainly  probably  fairly  somewhat
```

中文常见水蛭：

```
非常  其实  基本上  实际上  大概  相对  确实  的确
应该说  可以说  在某种程度上  当然  显然
```

- ❌ "really very important" → ✅ "important"
- ❌ "其实这个其实就是很简单的事情" → ✅ "这事很简单"

**规则**：每段最多 1 个限定词，连续 3 个删 2 个。

## 规则 5：副词 → 强动词（Hemingway）

副词意味着你选错了动词。

- ❌ "ran quickly" → ✅ "sprinted"
- ❌ "carefully held" → ✅ "cradled"
- ❌ "completely destroyed" → ✅ "demolished"
- ❌ "迅速跑过" → ✅ "冲过去"
- ❌ "彻底毁掉" → ✅ "砸了"

## 规则 6：被动 → 主动（Orwell #4）

- ❌ "Mistakes were made." → ✅ "We made mistakes."
- ❌ "It was decided that ..." → ✅ "X decided that ..."
- ❌ "该方案被团队采纳" → ✅ "团队采纳了该方案"
- ❌ "被发现了一个问题" → ✅ "发现了一个问题"

**例外**：当真不知道动作发出者，或者强调动作本身而非主体时，被动可以保留。

## 规则 7：长词 → 短词（Orwell #2 + #5）

英文：

- ❌ utilize → ✅ use
- ❌ facilitate → ✅ help
- ❌ endeavor → ✅ try
- ❌ commence → ✅ start
- ❌ terminate → ✅ end
- ❌ purchase → ✅ buy
- ❌ paradigm shift → ✅ major change

中文：

- ❌ 进行优化 → ✅ 优化
- ❌ 做出贡献 → ✅ 贡献
- ❌ 加以解决 → ✅ 解决
- ❌ 实施部署 → ✅ 部署
- ❌ 给予帮助 → ✅ 帮

## 规则 8：名词化 → 动词

中文 AI 最爱"做出 X" / "进行 X" 这种把动词当宾语的结构。

- ❌ "做出了一个决定" → ✅ "决定了"
- ❌ "made a decision to leave" → ✅ "decided to leave"
- ❌ "进行了讨论" → ✅ "讨论了"
- ❌ "give consideration to" → ✅ "consider"
- ❌ "起到推动作用" → ✅ "推动"

## 规则 9：删 "There is / There are / 存在" 开头

- ❌ "There are many people who think ..." → ✅ "Many think ..."
- ❌ "There is a need to ..." → ✅ "We need to ..."
- ❌ "存在一些问题需要解决" → ✅ "有几个问题要解决" 或直接列问题
- ❌ "存在这样一种现象" → ✅ 直接描述这个现象

## 规则 10：砍熟词比喻（Orwell #1）

任何"想都不用想就能说出来"的比喻，都是死的。

英文死比喻：

```
at the end of the day  move the needle  low-hanging fruit
think outside the box  push the envelope  game changer
paradigm shift  level the playing field
```

中文死比喻：

```
画上句号  再上新台阶  勇立潮头  携手共进
赋能千行百业  迈入新阶段  开启新篇章
让 X 飞起来  乘风破浪
```

**Orwell 原话**：能想出一个新鲜比喻就想，想不到就用平铺直叙，**别用死掉的比喻**。

## 规则 11：三联词 → 单词

英文：

- ❌ "powerful, robust, and scalable" → ✅ 选一个
- ❌ "fast, secure, and reliable" → ✅ 选一个最关键的

中文：

- ❌ "高效、稳定、可靠" → ✅ "稳定"
- ❌ "快速、安全、便捷" → ✅ "快"

**规则**：保留三联词最多 1 次/文章（确实需要并列时）。

## 规则 12：删多余指代

如果上文唯一指代清晰，删指代词重读名词反而更省。

- ❌ "This shows that the approach works." → ✅ "The approach works."
- ❌ "这表明该方案是有效的" → ✅ "该方案有效"
- ❌ "It is important to note that ..." → ✅ "（直接讲后面的内容）"

## 综合自测：5 个字 / 1 句话原则

读完一句话后，问自己：

1. 这句话有几个**新信息**？（少于 1 个就该删）
2. 我能不能砍 5 个字保留意思？（能砍就砍）
3. 这是不是个动词？（如果是"是 / 进行 / 做"，能不能换成实义动词？）
4. 这句话有没有**具体名词**或**数字**？（一段里至少要有 1 个）
5. 删了这句话上下文断不断？（不断就该删）

**Paul Graham 原句**：
> Write a bad version 1 as fast as you can; rewrite it over and over; cut out everything unnecessary; ... write in a conversational tone; ... don't try to sound impressive.
