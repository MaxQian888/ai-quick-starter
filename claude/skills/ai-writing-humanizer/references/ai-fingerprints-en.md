# English AI Writing Fingerprints

Tier 1 = hard ban on hit. Tier 2 = soft warning, context-dependent.
Sources: Walter Writes word list, ACL 2025 "Why does ChatGPT delve", Sabrina.dev banned list, Pangram research.

## Tier 1: Hard ban (rewrite on any hit)

### Overused verbs (the strongest signals)

```
delve  embark  harness  leverage  utilize  foster  underscore
illuminate  unveil  elucidate  navigate  streamline  amplify
bolster  transcend  unlock  empower  spearhead  catalyze
revolutionize  redefine  reshape  reimagine  pioneer
```

Replacement strategy: pick the concrete verb the AI was hiding.
- "delve into the topic" → "look at" / "examine" / "study"
- "leverage X to Y" → "use X to Y"
- "utilize" → "use"
- "harness the power of" → just say what it does

### Overused adjectives

```
pivotal  robust  seamless  intricate  cutting-edge  groundbreaking
bespoke  paramount  profound  indelible  meticulous  dynamic
vital  unparalleled  unprecedented  comprehensive  holistic
multifaceted  nuanced  myriad
```

Replacement: most can be deleted. "A pivotal moment" → "the moment that mattered."

### Overused nouns

```
tapestry  realm  landscape  beacon  testament  treasure trove
synergy  interplay  cacophony  symphony  paradigm  ecosystem
journey  voyage  odyssey  framework (when vague)
```

### Transition fillers

```
Furthermore  Moreover  In addition  Hence  Thus  Therefore (overused)
It is worth noting that  It's important to note (that)
In conclusion  In summary  To sum up  All things considered
On the other hand (when not actually contrasting)
At the end of the day  When all is said and done
```

### Setup language (opening clichés)

```
In a world where...
In today's fast-paced [whatever]...
When it comes to...
Imagine a [scenario]...
Picture this:
Have you ever wondered...
Did you know...
```

These are AI's nervous tics before saying anything real. Cut and start with the actual point.

### Em-dash overuse (the single strongest visual signal)

- More than 1 em-dash `—` per paragraph → hit
- More than 1 em-dash per 200 words across the doc → hit
- Em-dashes used in pairs to insert asides → especially AI-flavored

Real humans use em-dashes, but rarely. Target ≤ 1 / 200 words.

## Tier 2: Soft warnings (context-dependent)

### Hedge inflation

```
generally speaking  to some extent  in many ways  in a sense
from a broader perspective  arguably  one could argue
it could be said that
```

Delete unless the hedge is load-bearing.

### Empty intensifiers

```
really  very  quite  rather  pretty  literally  actually
basically  certainly  probably  definitely  truly
```

Strunk's "leeches." Delete most.

### Negative parallelism

```
It's not just X — it's Y.
This isn't just A; it's B.
Not only X, but also Y.
```

The single most overused rhetorical pattern in AI prose. Kill on sight.

### Triadic structures

```
"powerful, robust, and scalable"
"fast, secure, and reliable"
"X, Y, and Z" patterns
```

Humans use triads too. The tell is *every paragraph* having one. If a doc has triads in 3+ paragraphs, reduce.

### Bold-mid-sentence

```
"The **key** thing here is **value**."
```

AI bolds abstract nouns. Real writers bold key concepts or terms of art.

### Header Title Case where it doesn't belong

In running prose, AI sometimes capitalizes phrases like "The Path Forward" or "A New Way of Thinking" — outside actual section headers, this is artificial.

## Structural fingerprints

1. **Sentence length variance too low** — 3 consecutive sentences within 5 words of each other = low burstiness
2. **Paragraph opener uniformity** — 80%+ paragraphs starting with the subject = monotone
3. **Perfect 5-paragraph essay**: intro → 3 points → conclusion (the schoolroom shape)
4. **Symmetric "challenges and opportunities" framing** — every paragraph balances pros and cons
5. **Listicle reflex** — bullets used when prose would be tighter
6. **Bold + ":" patterns** in prose: "**Speed:** matters." If used in 3+ consecutive paragraphs, suspicious

## Semantic fingerprints

- Zero concrete nouns (no brand names, tool names, person names, place names, numbers)
- Zero first-person ("I", "we", "I'd argue", "I think")
- Perfect balance — every positive claim has a hedge
- No idiosyncrasy — could have been written by anyone

If ≥ 3 of these hit, mark as **"severe voice loss"** in the diagnostic.

## Sycophantic closers (always delete)

```
I hope this helps!
Let me know if you have any questions!
Feel free to ask if you need clarification.
Thanks for reading!
Hope you found this useful.
```

These are ChatGPT's factory smell. Always cut.

## The compounding problem

The real AI tell is rarely one fingerprint — it's the *density*. A single "delve" in a 1000-word essay is fine. Five "delves" + three em-dashes + two "it's worth noting" is fatal. Count hits per 200 words; > 5 hits / 200 words = "obvious AI" territory.
