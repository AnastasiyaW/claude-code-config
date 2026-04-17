---
name: English Text Humanization
description: |
  Make AI-generated English text sound natural and human. Use when: writing blog posts,
  articles, marketing copy, any English content that must not read as AI-generated.
  Covers: burstiness, perplexity, banned words, sentence patterns, transitions, tone.
  Based on: Liang et al. (arxiv 2406.07016, 15M+ abstracts), GPTZero/Originality research.
  Use BEFORE publishing any AI-generated English text.
---

# English Text Humanization Skill

## When to Use

- Writing blog posts, articles, marketing copy in English
- Polishing AI-generated drafts to sound human
- Any English text that needs to pass AI detectors
- Content that must feel authentic to readers

## Core Principle

**Specificity vs generality.** Human text references exact things, takes positions, makes mistakes, shows personality. AI text covers all bases, hedges everything, uses the safest phrasings, produces text that could apply to any similar topic. "Surface polish with nothing underneath" is AI's signature.

## Core Concepts

### Burstiness (sentence rhythm variation)

AI writes flat, uniform sentences (15-25 words, clustered). Humans alternate wildly - a 5-word sentence next to a 40-word one.

**Rules:**
- Mix short (3-7 words), medium (10-18 words), and long (20-30 words) sentences
- NEVER write 3+ consecutive sentences of similar length
- Use one-sentence paragraphs for emphasis
- Use sentence fragments deliberately. Like this.
- Vary paragraph length: 1-sentence → 3-sentence → 2-sentence → 4-sentence

**Before (low burstiness - AI-like):**
```
AI retouching has become an important tool for photographers. It allows them to
enhance their images quickly and efficiently. Many professionals are now adopting
this technology in their workflow. The results are consistently impressive and
save considerable time.
```

**After (high burstiness - human):**
```
AI retouching changed everything. Not gradually - overnight. Photographers who
spent three hours on a single portrait now finish in seconds. The quality? Better
than most manual edits. Not all of them, sure. But enough that the 23 retouchers
I talked to last month all said the same thing: "I can't go back."
```

### Perplexity (word unpredictability)

AI picks the most probable next word - consistently low perplexity, every word is the safest statistical choice. Human writing has perplexity spikes: unexpected metaphors, unusual word pairings, surprising verbs.

**Rules:**
- Replace the first word that comes to mind with the second or third
- Use specific nouns: "23 retouchers" not "many professionals"
- Use unexpected verbs: "grab" not "utilize", "ship" not "implement", "kill" not "eliminate"
- Drop in concrete details the AI wouldn't know: names, dates, specific tools
- Numbers > vague quantities. Always.

**Weak (predictable):** "Many users find the tool helpful for their work."
**Strong (surprising):** "84% of beta testers shipped their first edit in under 90 seconds."

---

## Banned Words & Phrases

### Tier 1 - NEVER use (research-confirmed AI markers)

Based on Liang et al. (arxiv 2406.07016) - 15M+ PubMed abstracts analysis. The 10 most effective marker words (highest excess ratio post-ChatGPT):

**across, additionally, comprehensive, crucial, enhancing, exhibited, insights, notably, particularly, within**

Other high-excess words (>5x frequency spike):

| Kill this | Replace with |
|-----------|-------------|
| delve (25.2x spike) | dig into, explore, look at |
| showcasing (9.2x) | showing, demo |
| underscores (9.1x) | highlights, shows |
| tapestry | mix, blend, combination |
| leverage | use, grab, tap into |
| utilize | use |
| enhance | boost, sharpen, improve |
| elevate | raise, lift, push |
| embark | start, kick off, jump into |
| resonate | click, land, hit home |
| landscape | space, market, field |
| multifaceted | complex, layered |
| intricate | detailed, complex |
| interplay | relationship, tension, push-pull |
| cutting-edge | latest, newest, bleeding-edge |
| game-changer | shift, breakthrough |
| revolutionize | reshape, rethink, flip |
| seamlessly | smoothly, without friction |
| illuminate | show, reveal, expose |
| unveil | launch, drop, release |
| remarkable | striking, sharp, wild |
| dramatically / significantly / drastically / substantially | concrete number ("2x faster", "by 40%"), or plain "fast/big/huge". LLMs love vague amplifiers - humans name the scale |

**Key finding from Liang et al.:** unlike content shifts (COVID terms = nouns), LLM excess is almost entirely STYLE words - 66% verbs, 18% adjectives. This is what makes them detectable.

**Note:** "delve" showed 25.2x spike but dropped sharply in 2025 after being called out. LLMs and humans co-evolve - static word lists go stale. The principles matter more than specific words.

### Tier 2 - Avoid (padding / filler)

| Kill this | Replace with |
|-----------|-------------|
| In order to | To |
| Due to the fact that | Because |
| It is important to note | (delete entirely) |
| It is worth mentioning | (delete entirely) |
| At the end of the day | (delete entirely) |
| In today's world | (delete entirely) |
| As a matter of fact | Actually / In fact |
| For all intents and purposes | (delete entirely) |
| needless to say | (delete - if needless, don't say it) |
| a wide range of | many / various |
| in the realm of | in |

### Tier 3 - Banned transitions

| Kill this | Replace with |
|-----------|-------------|
| Furthermore | And / Plus / On top of that |
| Moreover | And / What's more |
| Additionally | Also / And |
| In conclusion | (use "Conclusion" as H2, never "In conclusion") |
| To summarize | (just summarize, don't announce it) |
| It's worth noting | (delete - just note it) |
| That being said | But / Still / That said |
| On the other hand | But / Then again |

---

## Structural Anti-Patterns to Avoid

### The "AI Shape" of Text

- **Symmetrical paragraphs** - every paragraph roughly the same length
- **Symmetrical lists** - every bullet the same structure/length
- **Predictable headers** - "Understanding X", "The Role of Y", "Why Z Matters"
- **The sandwich** - broad claim → supporting detail → restatement, repeated identically
- **Over-structuring** - not everything needs H2 → H3 → bullet list. Sometimes a paragraph is just a paragraph

### Tone Traps

- **Excessive enthusiasm** - "Fascinating!", "Remarkable!", unearned excitement about mundane topics
- **Hedge-heavy** - "It's worth noting...", "While it may seem...", never taking a definitive position
- **Balanced-to-a-fault** - always "On the one hand... On the other hand..." even when one side is clearly correct. Non-committal conclusions ("It depends on your specific needs")
- **Missing human markers** - no "I think", no uncertainty, no humor, no self-correction, no register shifts, perfect grammar throughout

---

## Sentence Openers - Vary These

Never start 2+ consecutive sentences the same way.

**Good openers to rotate:**
- Direct statement: "The model ships with 4K support."
- Number: "73% of creators switched within a month."
- Question: "What happens when your editor can't keep up?"
- Quote: "'I deleted Photoshop,' she told me."
- Contrast: "But here's the catch."
- Time: "Two weeks later, the results spoke."
- Command: "Try this: upload a raw selfie."
- Fragment: "Not anymore."

---

## Contractions - Always Use

| Formal (AI-like) | Natural (human) |
|-------------------|-----------------|
| it is | it's |
| you are | you're |
| do not | don't |
| cannot | can't |
| we have | we've |
| they will | they'll |
| here is | here's |
| that is | that's |

---

## Human Texture Techniques

### 1. Rhetorical questions (1-2 per article)
- "Sound familiar?"
- "So what's the catch?"
- "Why does this matter?"

### 2. Direct address
- "You" and "your" - talk TO the reader, not about them
- "Here's what you need to know."
- "Your first edit takes 30 seconds."

### 3. Specificity over abstraction
- Not "improves quality" → "reduces grain by 40% without losing skin texture"
- Not "saves time" → "cuts a 3-hour session to 12 minutes"
- Not "many users" → "2,400 photographers in the beta"

### 4. Analogies from everyday life
- "It's like autocomplete, but for your entire photo."
- "Think of it as a spell-checker for skin tones."

### 5. Imperfection signals
- "Not perfect - nothing is. But close enough."
- "Honestly? I was skeptical too."
- "Does it work every time? No. But 9 out of 10."

### 6. Dead ends and honesty
- "I tried X but it failed because..."
- "I still don't fully understand why..."
- Include actual error messages, version numbers, time stamps

### 7. Sentence fragments for punch
- "Fast. Accurate. Done."
- "Not just better. Different."
- "The result? Silence. Then applause."

---

## Self-Audit Checklist

After writing, verify:

- [ ] No 3+ consecutive sentences of similar length
- [ ] No words from Tier 1 banned list
- [ ] No banned transitions from Tier 3
- [ ] At least 2 sentences under 6 words per 500 words
- [ ] At least 1 rhetorical question per 500 words
- [ ] At least 3 specific numbers per article
- [ ] All contractions used (no "it is", "do not")
- [ ] No paragraph starts the same way as the previous one
- [ ] At least 1 analogy or comparison
- [ ] At least 1 admission of uncertainty or limitation
- [ ] At least 1 opinion or stance taken
- [ ] CTA is specific action, not vague invitation
- [ ] Paragraph lengths vary (1-sentence mixed with 3-4-sentence)

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Text "feels" AI | Low burstiness - all sentences same length | Chop some in half, merge others |
| Flagged by GPTZero | High predictability - obvious word choices | Replace 5-10 nouns with specific alternatives |
| Sounds like a textbook | Too formal, no contractions | Add contractions + 2 rhetorical questions |
| Repetitive paragraph starts | Same transition pattern | Rotate: statement → number → question → quote |
| Reads like a press release | No personality, no "I" or "you" | Add 1 personal observation + direct "you" address |
| Vague / generic | Abstraction over specificity | Replace every "many/some/various" with a number |
| Surface polish, nothing underneath | Generic frameworks, verbose padding | Cut 30% of text, add 3 concrete examples |

## Gotchas

- **Em-dash overuse**: AI loves em-dashes. Use max 2 per article. Prefer commas or periods.
- **Bold in lists**: AI writes `**Bold header**: explanation` in every bullet. Vary: some bold, some not, some just text.
- **Uniform list items**: AI makes every bullet the same length/structure. Mix: short + long, sentence + fragment.
- **"Not just X, but also Y"**: Classic AI construction. Kill it. Say it directly.
- **Over-structuring**: Not everything needs H2 → H3 → bullet list. Sometimes a paragraph is just a paragraph.
- **Co-evolution**: Specific flagged words change over time (delve peaked 2024, dropped 2025). The structural patterns (burstiness, perplexity, symmetry) are more stable signals.
- **Static word lists go stale**: Lists of "AI words" degrade as models adapt. Focus on principles (specificity, rhythm, honesty) over word-level avoidance.

## Sources

### Academic (peer-reviewed)
- Liang et al. (2024) - "Delving into LLM-assisted writing" (arxiv 2406.07016) - 15M+ abstracts, 280 excess words
- Human-LLM Coevolution (arxiv 2502.09606) - delve dropped after being called out
- Measuring AI "Slop" in Text (arxiv 2509.19163) - coherence/relevance dimensions
- Why Does ChatGPT "Delve"? (arxiv 2412.11385) - lexical overrepresentation sources

### Research data
- berenslab/chatgpt-excess-words (GitHub) - raw CSV data behind Liang paper
- Foadsf/avoid-gpt-phrases (GitHub) - CLI tool, 80 flagged words for LaTeX

### Practitioner guides
- Originality.AI - Perplexity and Burstiness in writing
- Habr article 918226 - 14-point authenticity checklist (Russian, high quality)
