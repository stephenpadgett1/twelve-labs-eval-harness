# Video-Understanding Eval — Side-by-Side Report

Corpus: **demo** · 6 videos · 20 questions

> **Run notes:**
> - twelve_labs ran in fixture mode (no TWELVE_LABS_API_KEY set). Responses are pre-recorded illustrative shapes, not live model output.
> - clip_baseline ran in fixture mode (no ANTHROPIC_API_KEY for the multimodal call). Responses are pre-recorded illustrative shapes.
> - judge ran in fixture mode (no ANTHROPIC_API_KEY). Scores are pre-recorded against the fixture responses, not live judge calls.

## Rollup

| Metric | Twelve Labs (Marengo + Pegasus) | CLIP baseline + Claude reasoning |
|---|---:|---:|
| Relevance | 5.00 | 3.75 |
| Faithfulness | 4.90 | 4.15 |
| Specificity | 4.65 | 2.80 |
| Overall | 4.85 | 3.57 |

### By question kind

| Kind | Pipeline | n | Relevance | Faithfulness | Specificity | Overall |
|---|---|---:|---:|---:|---:|---:|
| retrieval | Twelve Labs | 12 | 5.00 | 4.92 | 4.75 | 4.89 |
| retrieval | CLIP baseline | 12 | 3.75 | 4.17 | 2.83 | 3.59 |
| reasoning | Twelve Labs | 8 | 5.00 | 4.88 | 4.50 | 4.79 |
| reasoning | CLIP baseline | 8 | 3.75 | 4.12 | 2.75 | 3.54 |

## Per-question detail

### Q-001 · VID-PROD-001 · _retrieval_

**Q.** At what point does the espresso start pouring into the cup?

**Expected.** Around the 11-13 second mark, after the machine is engaged.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 480 ms)

Top matches:
[10.8s–13.2s] score=0.91
[12.4s–14.6s] score=0.84
[11.0s–12.0s] score=0.79

_judge:_ Pinpoints the pour at 10.8–13.2s with high confidence — matches the reference and is specific to the second.
_notes: Marengo marengo3.0, top-3 clips, visual+audio_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 220 ms)

Top frames matching 'espresso pouring into cup':
[12.0s] cosine=0.31
[13.0s] cosine=0.28
[11.0s] cosine=0.24

_judge:_ Identifies the right frames but lacks a clip range; coarser temporal granularity than Marengo.
_notes: ViT-B-32/openai, 1 fps frame sampling, top-3 frames_

---

### Q-002 · VID-PROD-001 · _reasoning_

**Q.** Summarize the preparation steps shown.

**Expected.** Grinder activated → portafilter filled and tamped → espresso machine engaged → coffee pours into cup.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 4/5 · 1840 ms)

The clip shows espresso preparation in four steps: (1) a grinder is activated and ground coffee is collected; (2) the portafilter is filled and tamped flat; (3) the portafilter is locked into the espresso machine and the brew cycle is started; (4) espresso pours from the spouts into a single cup placed beneath. No milk or additional ingredients are added.

_judge:_ Full step sequence with correct ordering; the 'no milk' note is correct but the step labels are slightly generic vs the reference's precise vocabulary.
_notes: Pegasus pegasus1.5, full-video grounding_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 2300 ms)

Frames sampled at 0s, 4s, 8s, 12s, 16s, 20s suggest a coffee-making sequence with a person at a counter, a metal machine, and a final shot of a cup with dark liquid. Specific steps are inferred (grinding, filling, brewing) but the model could not always distinguish the portafilter from a tamper at the resolution available.

_judge:_ Captures the gist but hedges on portafilter/tamper distinction; less specific than the reference.
_notes: claude-haiku-4-5, 6 evenly-sampled frames_

---

### Q-003 · VID-PROD-001 · _retrieval_

**Q.** Is milk added to the coffee?

**Expected.** No milk is added in this clip.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 4/5 · 410 ms)

No clip matches above the 0.5 threshold. Returning zero results — the audio and visual signals do not contain a milk-pour event.

_judge:_ Correctly returns a negative result with confidence; explicit about the threshold.
_notes: Marengo marengo3.0, threshold=0.5_

**CLIP baseline** (relevance 5/5 · faithfulness 5/5 · specificity 4/5 · 190 ms)

No frames in the 1-fps sampled set show milk being added. Negative answer.

_judge:_ Same correct negative answer; slightly less specific framing.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-004 · VID-PROD-002 · _reasoning_

**Q.** What are the major stages of bread-making shown?

**Expected.** Mixing ingredients → kneading → proofing/rising → shaping → baking.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 2410 ms)

Five major stages: (1) Mixing — flour, water, salt, and visibly yeast combined in a bowl. (2) Kneading — extended, hands-on. (3) Proofing — covered bowl, time-compressed cut showing rise. (4) Shaping — dough divided and formed into a loaf. (5) Baking — placed in a preheated oven; final shot shows the baked loaf.

_judge:_ All five stages with the right ordering; correctly identifies yeast as a discrete ingredient.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 2920 ms)

Visible stages from sampled frames: ingredients in a bowl, hands kneading dough, dough sitting covered, dough being shaped, a loaf in an oven. The proofing duration cannot be inferred from the static frame samples; one of the samples shows the same covered bowl as another, suggesting a time cut.

_judge:_ Gets the stages but is less confident on proofing; correctly notes the time cut.
_notes: claude-haiku-4-5, 8 frames over 95s_

---

### Q-005 · VID-PROD-002 · _retrieval_

**Q.** Where in the video does the dough first go into the oven?

**Expected.** Approximately the 70-80 second mark.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 520 ms)

Top matches:
[74.0s–76.5s] score=0.88
[71.8s–74.0s] score=0.83
[76.5s–80.0s] score=0.71

_judge:_ Clip range 74–76.5s aligns with the reference window of 70–80s, with sub-second precision.
_notes: Marengo marengo3.0, top-3_

**CLIP baseline** (relevance 4/5 · faithfulness 5/5 · specificity 3/5 · 230 ms)

Frames at 72s and 76s show dough near an oven door; 76s shows it entering. Best match: 76s.

_judge:_ Correct moment identified but reported with a coarser timestamp granularity.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-006 · VID-PROD-002 · _retrieval_

**Q.** Is yeast visibly added as a separate ingredient?

**Expected.** Yes, yeast is added during the mixing stage.

**Twelve Labs** (relevance 5/5 · faithfulness 4/5 · specificity 4/5 · 470 ms)

Top matches:
[8.4s–11.2s] score=0.93  (packet emptied into bowl, possible yeast)
[10.0s–12.0s] score=0.87

_judge:_ Identifies the moment with a clip range but hedges with 'possible yeast' — fair, since packet content isn't visually distinguishable; faithful to what's actually visible.
_notes: Marengo marengo3.0, visual_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 200 ms)

Frame at 10s shows a small packet being emptied into the bowl. Best match: 10s.

_judge:_ Identifies a packet but does not name it as yeast — same uncertainty, less specific framing.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-007 · VID-PROD-002 · _reasoning_

**Q.** Roughly how long does the proofing/rising stage appear to take in the video's edited timeline?

**Expected.** A short time-compressed segment; the actual proofing is implied to be hours but is shown in seconds.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 4/5 · 2090 ms)

Proofing is shown as a short ~6-second segment around 42–48 seconds, compressed with a visible fade — i.e., the on-screen time is short but the depicted real-world duration is much longer (typically 45–90 min).

_judge:_ Specific timestamp window with an inferred real-world duration; the inference is reasonable but introduces a number not directly shown.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 2150 ms)

Two of the sampled frames show the same covered bowl, suggesting a time cut. Exact duration on screen is not clear from sparse frame sampling.

_judge:_ Detects the time cut but cannot bound the on-screen duration.
_notes: claude-haiku-4-5, 8 frames_

---

### Q-008 · VID-SPORT-001 · _retrieval_

**Q.** How many free throws are made (i.e., go through the net)?

**Expected.** Three made; one miss.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 540 ms)

Detected ball-through-net events: 3.
[6.2s–7.4s] score=0.92 (made)
[19.8s–20.6s] score=0.34 (miss — rim only)
[24.1s–25.0s] score=0.89 (made)
[31.6s–32.5s] score=0.87 (made)

_judge:_ Counts three makes, flags the second attempt as a miss with a low score — fully matches reference.
_notes: Marengo marengo3.0, audio+visual; ball-through-net concept_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 240 ms)

Three frames clearly show ball-through-net at ~7s, ~24s, ~32s. The frame at 20s shows the rim/ball but is ambiguous; cannot confirm a make.

_judge:_ Same count but hedges on the miss; less confident temporal precision.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-009 · VID-SPORT-001 · _retrieval_

**Q.** When does the only missed shot occur?

**Expected.** On the second attempt, around the 18-20 second mark.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 460 ms)

Top match: [18.4s–20.9s] score=0.86 (rim-only, no swish; categorized as miss)

_judge:_ Pinpoints the miss at 18.4–20.9s; matches the reference window.
_notes: Marengo marengo3.0, 'missed free throw' concept_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 210 ms)

Frame at 19s shows the ball at the rim but doesn't clearly show whether it went in. Inferred miss based on no follow-on swish.

_judge:_ Same moment, fuzzier evidence.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-010 · VID-SPORT-001 · _reasoning_

**Q.** Describe the shooter's form on the first attempt.

**Expected.** Standard set form: bent knees, elbow under the ball, follow-through with the wrist.

**Twelve Labs** (relevance 5/5 · faithfulness 4/5 · specificity 4/5 · 1980 ms)

On the first attempt the shooter exhibits standard set form: feet shoulder-width apart, knees bent for a small dip, ball cocked with the shooting elbow under the ball, follow-through with the wrist flexed forward. No hop or jump on release.

_judge:_ Detailed form description matches reference for the elements visible; some details (elbow alignment from this camera angle) may be slightly over-claimed.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 2060 ms)

From the sampled frames, the shooter is upright with knees slightly bent, ball held near the forehead, then arms extending toward the rim. Specifics of elbow alignment are not clearly visible at the resolution.

_judge:_ Reasonable description but lacks the elbow specificity.
_notes: claude-haiku-4-5, 6 frames_

---

### Q-011 · VID-SPORT-002 · _retrieval_

**Q.** How many distinct tricks are attempted?

**Expected.** Four: ollie, kickflip, heelflip, and a 180.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 510 ms)

Trick attempts detected: 4.
[3.2s–5.8s] ollie (landed)
[14.0s–17.1s] kickflip (bailed)
[24.5s–27.6s] heelflip (landed)
[38.4s–41.2s] 180 (landed)

_judge:_ All four tricks named correctly with timestamp ranges and outcomes.
_notes: Marengo marengo3.0, skateboarding concept set_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 2/5 · 250 ms)

From the sampled frames: a flat ground board pop (5s), a board rotation with the skater off it (15s), another flip (25s), a body rotation (39s). Likely four tricks total.

_judge:_ Counts four but does not name the tricks; significantly less specific.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-012 · VID-SPORT-002 · _retrieval_

**Q.** Which trick is landed cleanly first?

**Expected.** The ollie, the first attempt of the clip.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 440 ms)

First clean landing: [3.2s–5.8s] — the ollie. Subsequent attempts include a kickflip bail before the next clean landing.

_judge:_ Names the ollie explicitly and times it; matches reference exactly.
_notes: Marengo marengo3.0_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 180 ms)

First trick attempted (and the first that appears to be ridden out): ~5s, a board pop without rotation.

_judge:_ Identifies the moment without naming the trick.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-013 · VID-SPORT-002 · _reasoning_

**Q.** Is there a progression from easier to harder tricks?

**Expected.** Yes — starts with the ollie, escalates through kickflip and heelflip, ends on the rotational 180.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 2120 ms)

Yes — there is a clear escalation. The clip opens with an ollie (simplest flat-ground trick), moves to a kickflip and heelflip (adding board rotation on different sides), and ends on a 180 (adding body rotation). The arc adds a single new degree of difficulty per attempt.

_judge:_ Names each trick and articulates the dimension being added at each step.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 2080 ms)

From the sampled frames, the tricks appear to increase in complexity from a basic pop to flips to a rotational move, suggesting a progression.

_judge:_ Correct conclusion but generic phrasing.
_notes: claude-haiku-4-5, 6 frames_

---

### Q-014 · VID-LEC-001 · _retrieval_

**Q.** What definition of a graph database does the speaker give?

**Expected.** A data store that models entities as nodes and relationships as first-class edges, optimized for traversal.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 690 ms)

Top matches:
[24.0s–38.0s] score=0.89 — speaker defines a graph database as 'a data store that models entities as nodes and relationships as first-class edges, optimized for traversal'
[64.0s–72.0s] score=0.71 — restates the definition more loosely

_judge:_ Returns the exact definition with a clip range; uses both audio and visual signals as expected.
_notes: Marengo marengo3.0, visual+audio (speech retrieval is the load-bearing signal here)_

**CLIP baseline** (relevance 2/5 · faithfulness 4/5 · specificity 2/5 · 280 ms)

CLIP-only retrieval cannot directly retrieve speech content. Frames with slide text containing 'graph database' appear at 24s, 38s, and 65s — manual transcription needed to extract the definition.

_judge:_ Surfaces the right frames but cannot deliver the definition — a known limitation of pure CLIP.
_notes: ViT-B-32/openai, 1 fps; CLIP does not transcribe speech_

---

### Q-015 · VID-LEC-001 · _reasoning_

**Q.** What problem does the speaker say graph databases solve poorly with relational tables?

**Expected.** Many-to-many traversal of relationships across multiple hops without expensive joins.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 2400 ms)

The speaker argues that many-to-many relationship traversal across multiple hops is expensive in relational tables because each hop requires a join. Graph databases store edges as first-class objects indexed for traversal, so multi-hop queries are constant-cost per step rather than join-cost.

_judge:_ Captures the multi-hop join cost argument exactly.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 3/5 · faithfulness 4/5 · specificity 2/5 · 2330 ms)

From sampled frames showing slide text about 'joins' and 'relationships,' the lecture appears to discuss query performance for relational vs graph stores. Full reasoning not recoverable from frames alone.

_judge:_ Right topic, missing the specific argument.
_notes: claude-haiku-4-5, 8 frames_

---

### Q-016 · VID-LEC-001 · _retrieval_

**Q.** Does the speaker name any specific graph database product?

**Expected.** Yes — Neo4j is mentioned; Neptune is referenced briefly.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 510 ms)

Top matches:
[112.0s–119.0s] score=0.88 — 'Neo4j' named
[141.0s–144.0s] score=0.74 — 'Neptune' referenced briefly

_judge:_ Both products named with timestamps; matches reference exactly.
_notes: Marengo marengo3.0, audio+visual_

**CLIP baseline** (relevance 3/5 · faithfulness 4/5 · specificity 3/5 · 220 ms)

Frames with the text 'Neo4j' appear at 112s and 118s; no clear frame mentions Neptune.

_judge:_ Catches Neo4j but misses the audio-only Neptune mention.
_notes: ViT-B-32/openai, 1 fps; no audio understanding_

---

### Q-017 · VID-LEC-002 · _reasoning_

**Q.** Summarize the speaker's main argument in one sentence.

**Expected.** Most production prompt-engineering value comes from structure and evaluation, not clever wording.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 2310 ms)

The speaker argues that most production prompt-engineering value comes from structure (clear input/output contracts) and evaluation (small fixture sets you iterate against), not from clever wording or magic phrases.

_judge:_ Captures the main argument in one sentence as the reference does.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 4/5 · faithfulness 5/5 · specificity 3/5 · 2250 ms)

Based on sampled slide text mentioning 'structure', 'eval', and 'examples,' the talk seems to argue that production prompts depend on testing and design rather than phrasing.

_judge:_ Same conclusion, less crisp phrasing.
_notes: claude-haiku-4-5, 8 frames_

---

### Q-018 · VID-LEC-002 · _retrieval_

**Q.** Does the speaker mention chain-of-thought?

**Expected.** Yes — discussed briefly as a structural technique, not a magic phrase.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 4/5 · 530 ms)

Top matches:
[178.0s–192.0s] score=0.84 — 'chain-of-thought' discussed briefly as a structural technique, with explicit pushback against treating it as a magic phrase

_judge:_ Yes with full context and explicit framing; very lightly extrapolated from a brief mention.
_notes: Marengo marengo3.0, audio+visual_

**CLIP baseline** (relevance 3/5 · faithfulness 4/5 · specificity 2/5 · 210 ms)

Frames with the on-screen text 'CoT' appear briefly around 180s.

_judge:_ Confirms presence of the topic but no context.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-019 · VID-LEC-002 · _retrieval_

**Q.** What does the speaker recommend as the first thing to add when adopting prompts in production?

**Expected.** An eval set — even a small one — before iterating on the prompt itself.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 5/5 · 500 ms)

Top match: [245.0s–266.0s] score=0.91 — speaker recommends adding an eval set first, even a small one (5-10 fixtures), before iterating on the prompt itself

_judge:_ Names the recommendation and includes the speaker's '5-10 fixtures' qualifier.
_notes: Marengo marengo3.0_

**CLIP baseline** (relevance 4/5 · faithfulness 4/5 · specificity 3/5 · 200 ms)

Slide text near the end of the talk mentions 'evals first.' Best frame: 250s.

_judge:_ Right answer, less specific.
_notes: ViT-B-32/openai, 1 fps_

---

### Q-020 · VID-LEC-002 · _reasoning_

**Q.** How does the speaker frame the role of model choice vs prompt design?

**Expected.** Model choice sets the ceiling; prompt design is how you get close to it. Picking the right tier matters more than perfect wording.

**Twelve Labs** (relevance 5/5 · faithfulness 5/5 · specificity 4/5 · 2440 ms)

The speaker frames model choice as setting the ceiling and prompt design as the work of getting close to it. The implication is that picking the right model tier matters more than perfecting wording — a small fast model with a great prompt will not beat a large model with a mediocre prompt on hard tasks, but for easy tasks the small model is sufficient and cheaper.

_judge:_ Full reasoning with the ceiling analogy and cost implication; the cost-tradeoff sentence is the model's framing, not a verbatim quote.
_notes: Pegasus pegasus1.5_

**CLIP baseline** (relevance 3/5 · faithfulness 4/5 · specificity 2/5 · 2210 ms)

The talk seems to argue that model choice and prompt design are complementary, with model choice as the primary lever based on frame text mentioning 'ceiling' and 'tier.'

_judge:_ Right framing, missing the cost dimension.
_notes: claude-haiku-4-5, 8 frames_

---
