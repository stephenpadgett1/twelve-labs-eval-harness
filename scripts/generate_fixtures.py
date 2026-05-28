"""One-shot script that wrote the fixture JSON files in fixtures/.

Kept in-repo as documentation of how the fixtures were synthesized — not run
during normal eval execution. The intent is that a reader can see exactly
what each fixture is meant to represent.

Live runs (with API keys set) bypass fixtures entirely.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"


# --------------------------------------------------------------------------
# Per-question fixture data, written from the perspective of:
#   - twelve_labs/search: what Marengo would return (clip ranges + scores)
#   - twelve_labs/generate: what Pegasus would generate (free-text reasoning)
#   - clip_baseline/retrieve: what CLIP+frames would return (frame timestamps)
#   - clip_baseline/reason: what frame-sampled Claude would generate
#   - judge: scored responses on relevance/faithfulness/specificity
# --------------------------------------------------------------------------

# (question_id, twelve_labs_answer, twelve_labs_kind, clip_answer, judge_tl, judge_cb)
DATA: list[dict] = [
    # ---- VID-PROD-001 (coffee prep, 22s) ----
    {
        "qid": "Q-001",
        "kind": "retrieval",
        "tl_answer": (
            "Top matches:\n"
            "[10.8s–13.2s] score=0.91\n"
            "[12.4s–14.6s] score=0.84\n"
            "[11.0s–12.0s] score=0.79"
        ),
        "tl_notes": "Marengo marengo3.0, top-3 clips, visual+audio",
        "tl_latency_ms": 480,
        "cb_answer": (
            "Top frames matching 'espresso pouring into cup':\n"
            "[12.0s] cosine=0.31\n"
            "[13.0s] cosine=0.28\n"
            "[11.0s] cosine=0.24"
        ),
        "cb_notes": "ViT-B-32/openai, 1 fps frame sampling, top-3 frames",
        "cb_latency_ms": 220,
        "judge_tl": (5, 5, 5, "Pinpoints the pour at 10.8–13.2s with high confidence — matches the reference and is specific to the second."),
        "judge_cb": (4, 4, 3, "Identifies the right frames but lacks a clip range; coarser temporal granularity than Marengo."),
    },
    {
        "qid": "Q-002",
        "kind": "reasoning",
        "tl_answer": (
            "The clip shows espresso preparation in four steps: (1) a grinder is "
            "activated and ground coffee is collected; (2) the portafilter is filled "
            "and tamped flat; (3) the portafilter is locked into the espresso machine "
            "and the brew cycle is started; (4) espresso pours from the spouts into a "
            "single cup placed beneath. No milk or additional ingredients are added."
        ),
        "tl_notes": "Pegasus pegasus1.5, full-video grounding",
        "tl_latency_ms": 1840,
        "cb_answer": (
            "Frames sampled at 0s, 4s, 8s, 12s, 16s, 20s suggest a coffee-making "
            "sequence with a person at a counter, a metal machine, and a final shot "
            "of a cup with dark liquid. Specific steps are inferred (grinding, "
            "filling, brewing) but the model could not always distinguish the "
            "portafilter from a tamper at the resolution available."
        ),
        "cb_notes": "claude-haiku-4-5, 6 evenly-sampled frames",
        "cb_latency_ms": 2300,
        "judge_tl": (5, 5, 4, "Full step sequence with correct ordering; the 'no milk' note is correct but the step labels are slightly generic vs the reference's precise vocabulary."),
        "judge_cb": (4, 4, 3, "Captures the gist but hedges on portafilter/tamper distinction; less specific than the reference."),
    },
    {
        "qid": "Q-003",
        "kind": "retrieval",
        "tl_answer": "No clip matches above the 0.5 threshold. Returning zero results — the audio and visual signals do not contain a milk-pour event.",
        "tl_notes": "Marengo marengo3.0, threshold=0.5",
        "tl_latency_ms": 410,
        "cb_answer": "No frames in the 1-fps sampled set show milk being added. Negative answer.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 190,
        "judge_tl": (5, 5, 4, "Correctly returns a negative result with confidence; explicit about the threshold."),
        "judge_cb": (5, 5, 4, "Same correct negative answer; slightly less specific framing."),
    },

    # ---- VID-PROD-002 (bread baking, 95s) ----
    {
        "qid": "Q-004",
        "kind": "reasoning",
        "tl_answer": (
            "Five major stages: (1) Mixing — flour, water, salt, and visibly yeast "
            "combined in a bowl. (2) Kneading — extended, hands-on. (3) Proofing — "
            "covered bowl, time-compressed cut showing rise. (4) Shaping — dough "
            "divided and formed into a loaf. (5) Baking — placed in a preheated "
            "oven; final shot shows the baked loaf."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 2410,
        "cb_answer": (
            "Visible stages from sampled frames: ingredients in a bowl, hands "
            "kneading dough, dough sitting covered, dough being shaped, a loaf in "
            "an oven. The proofing duration cannot be inferred from the static "
            "frame samples; one of the samples shows the same covered bowl as "
            "another, suggesting a time cut."
        ),
        "cb_notes": "claude-haiku-4-5, 8 frames over 95s",
        "cb_latency_ms": 2920,
        "judge_tl": (5, 5, 5, "All five stages with the right ordering; correctly identifies yeast as a discrete ingredient."),
        "judge_cb": (4, 4, 3, "Gets the stages but is less confident on proofing; correctly notes the time cut."),
    },
    {
        "qid": "Q-005",
        "kind": "retrieval",
        "tl_answer": (
            "Top matches:\n"
            "[74.0s–76.5s] score=0.88\n"
            "[71.8s–74.0s] score=0.83\n"
            "[76.5s–80.0s] score=0.71"
        ),
        "tl_notes": "Marengo marengo3.0, top-3",
        "tl_latency_ms": 520,
        "cb_answer": "Frames at 72s and 76s show dough near an oven door; 76s shows it entering. Best match: 76s.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 230,
        "judge_tl": (5, 5, 5, "Clip range 74–76.5s aligns with the reference window of 70–80s, with sub-second precision."),
        "judge_cb": (4, 5, 3, "Correct moment identified but reported with a coarser timestamp granularity."),
    },
    {
        "qid": "Q-006",
        "kind": "retrieval",
        "tl_answer": (
            "Top matches:\n"
            "[8.4s–11.2s] score=0.93  (packet emptied into bowl, possible yeast)\n"
            "[10.0s–12.0s] score=0.87"
        ),
        "tl_notes": "Marengo marengo3.0, visual",
        "tl_latency_ms": 470,
        "cb_answer": "Frame at 10s shows a small packet being emptied into the bowl. Best match: 10s.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 200,
        "judge_tl": (5, 4, 4, "Identifies the moment with a clip range but hedges with 'possible yeast' — fair, since packet content isn't visually distinguishable; faithful to what's actually visible."),
        "judge_cb": (4, 4, 3, "Identifies a packet but does not name it as yeast — same uncertainty, less specific framing."),
    },
    {
        "qid": "Q-007",
        "kind": "reasoning",
        "tl_answer": (
            "Proofing is shown as a short ~6-second segment around 42–48 seconds, "
            "compressed with a visible fade — i.e., the on-screen time is short but "
            "the depicted real-world duration is much longer (typically 45–90 min)."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 2090,
        "cb_answer": (
            "Two of the sampled frames show the same covered bowl, suggesting a "
            "time cut. Exact duration on screen is not clear from sparse frame "
            "sampling."
        ),
        "cb_notes": "claude-haiku-4-5, 8 frames",
        "cb_latency_ms": 2150,
        "judge_tl": (5, 5, 4, "Specific timestamp window with an inferred real-world duration; the inference is reasonable but introduces a number not directly shown."),
        "judge_cb": (4, 4, 3, "Detects the time cut but cannot bound the on-screen duration."),
    },

    # ---- VID-SPORT-001 (free throws, 35s) ----
    {
        "qid": "Q-008",
        "kind": "retrieval",
        "tl_answer": (
            "Detected ball-through-net events: 3.\n"
            "[6.2s–7.4s] score=0.92 (made)\n"
            "[19.8s–20.6s] score=0.34 (miss — rim only)\n"
            "[24.1s–25.0s] score=0.89 (made)\n"
            "[31.6s–32.5s] score=0.87 (made)"
        ),
        "tl_notes": "Marengo marengo3.0, audio+visual; ball-through-net concept",
        "tl_latency_ms": 540,
        "cb_answer": (
            "Three frames clearly show ball-through-net at ~7s, ~24s, ~32s. The "
            "frame at 20s shows the rim/ball but is ambiguous; cannot confirm a make."
        ),
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 240,
        "judge_tl": (5, 5, 5, "Counts three makes, flags the second attempt as a miss with a low score — fully matches reference."),
        "judge_cb": (4, 4, 3, "Same count but hedges on the miss; less confident temporal precision."),
    },
    {
        "qid": "Q-009",
        "kind": "retrieval",
        "tl_answer": (
            "Top match: [18.4s–20.9s] score=0.86 (rim-only, no swish; categorized as miss)"
        ),
        "tl_notes": "Marengo marengo3.0, 'missed free throw' concept",
        "tl_latency_ms": 460,
        "cb_answer": "Frame at 19s shows the ball at the rim but doesn't clearly show whether it went in. Inferred miss based on no follow-on swish.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 210,
        "judge_tl": (5, 5, 5, "Pinpoints the miss at 18.4–20.9s; matches the reference window."),
        "judge_cb": (4, 4, 3, "Same moment, fuzzier evidence."),
    },
    {
        "qid": "Q-010",
        "kind": "reasoning",
        "tl_answer": (
            "On the first attempt the shooter exhibits standard set form: feet "
            "shoulder-width apart, knees bent for a small dip, ball cocked with the "
            "shooting elbow under the ball, follow-through with the wrist flexed "
            "forward. No hop or jump on release."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 1980,
        "cb_answer": (
            "From the sampled frames, the shooter is upright with knees slightly "
            "bent, ball held near the forehead, then arms extending toward the rim. "
            "Specifics of elbow alignment are not clearly visible at the resolution."
        ),
        "cb_notes": "claude-haiku-4-5, 6 frames",
        "cb_latency_ms": 2060,
        "judge_tl": (5, 4, 4, "Detailed form description matches reference for the elements visible; some details (elbow alignment from this camera angle) may be slightly over-claimed."),
        "judge_cb": (4, 4, 3, "Reasonable description but lacks the elbow specificity."),
    },

    # ---- VID-SPORT-002 (skateboarding, 48s) ----
    {
        "qid": "Q-011",
        "kind": "retrieval",
        "tl_answer": (
            "Trick attempts detected: 4.\n"
            "[3.2s–5.8s] ollie (landed)\n"
            "[14.0s–17.1s] kickflip (bailed)\n"
            "[24.5s–27.6s] heelflip (landed)\n"
            "[38.4s–41.2s] 180 (landed)"
        ),
        "tl_notes": "Marengo marengo3.0, skateboarding concept set",
        "tl_latency_ms": 510,
        "cb_answer": (
            "From the sampled frames: a flat ground board pop (5s), a board "
            "rotation with the skater off it (15s), another flip (25s), a body "
            "rotation (39s). Likely four tricks total."
        ),
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 250,
        "judge_tl": (5, 5, 5, "All four tricks named correctly with timestamp ranges and outcomes."),
        "judge_cb": (4, 4, 2, "Counts four but does not name the tricks; significantly less specific."),
    },
    {
        "qid": "Q-012",
        "kind": "retrieval",
        "tl_answer": "First clean landing: [3.2s–5.8s] — the ollie. Subsequent attempts include a kickflip bail before the next clean landing.",
        "tl_notes": "Marengo marengo3.0",
        "tl_latency_ms": 440,
        "cb_answer": "First trick attempted (and the first that appears to be ridden out): ~5s, a board pop without rotation.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 180,
        "judge_tl": (5, 5, 5, "Names the ollie explicitly and times it; matches reference exactly."),
        "judge_cb": (4, 4, 3, "Identifies the moment without naming the trick."),
    },
    {
        "qid": "Q-013",
        "kind": "reasoning",
        "tl_answer": (
            "Yes — there is a clear escalation. The clip opens with an ollie "
            "(simplest flat-ground trick), moves to a kickflip and heelflip "
            "(adding board rotation on different sides), and ends on a 180 "
            "(adding body rotation). The arc adds a single new degree of "
            "difficulty per attempt."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 2120,
        "cb_answer": (
            "From the sampled frames, the tricks appear to increase in complexity "
            "from a basic pop to flips to a rotational move, suggesting a "
            "progression."
        ),
        "cb_notes": "claude-haiku-4-5, 6 frames",
        "cb_latency_ms": 2080,
        "judge_tl": (5, 5, 5, "Names each trick and articulates the dimension being added at each step."),
        "judge_cb": (4, 4, 3, "Correct conclusion but generic phrasing."),
    },

    # ---- VID-LEC-001 (graph db lecture, 180s) ----
    {
        "qid": "Q-014",
        "kind": "retrieval",
        "tl_answer": (
            "Top matches:\n"
            "[24.0s–38.0s] score=0.89 — speaker defines a graph database as "
            "'a data store that models entities as nodes and relationships as "
            "first-class edges, optimized for traversal'\n"
            "[64.0s–72.0s] score=0.71 — restates the definition more loosely"
        ),
        "tl_notes": "Marengo marengo3.0, visual+audio (speech retrieval is the load-bearing signal here)",
        "tl_latency_ms": 690,
        "cb_answer": (
            "CLIP-only retrieval cannot directly retrieve speech content. Frames "
            "with slide text containing 'graph database' appear at 24s, 38s, and "
            "65s — manual transcription needed to extract the definition."
        ),
        "cb_notes": "ViT-B-32/openai, 1 fps; CLIP does not transcribe speech",
        "cb_latency_ms": 280,
        "judge_tl": (5, 5, 5, "Returns the exact definition with a clip range; uses both audio and visual signals as expected."),
        "judge_cb": (2, 4, 2, "Surfaces the right frames but cannot deliver the definition — a known limitation of pure CLIP."),
    },
    {
        "qid": "Q-015",
        "kind": "reasoning",
        "tl_answer": (
            "The speaker argues that many-to-many relationship traversal across "
            "multiple hops is expensive in relational tables because each hop "
            "requires a join. Graph databases store edges as first-class objects "
            "indexed for traversal, so multi-hop queries are constant-cost per "
            "step rather than join-cost."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 2400,
        "cb_answer": (
            "From sampled frames showing slide text about 'joins' and "
            "'relationships,' the lecture appears to discuss query performance "
            "for relational vs graph stores. Full reasoning not recoverable from "
            "frames alone."
        ),
        "cb_notes": "claude-haiku-4-5, 8 frames",
        "cb_latency_ms": 2330,
        "judge_tl": (5, 5, 5, "Captures the multi-hop join cost argument exactly."),
        "judge_cb": (3, 4, 2, "Right topic, missing the specific argument."),
    },
    {
        "qid": "Q-016",
        "kind": "retrieval",
        "tl_answer": (
            "Top matches:\n"
            "[112.0s–119.0s] score=0.88 — 'Neo4j' named\n"
            "[141.0s–144.0s] score=0.74 — 'Neptune' referenced briefly"
        ),
        "tl_notes": "Marengo marengo3.0, audio+visual",
        "tl_latency_ms": 510,
        "cb_answer": "Frames with the text 'Neo4j' appear at 112s and 118s; no clear frame mentions Neptune.",
        "cb_notes": "ViT-B-32/openai, 1 fps; no audio understanding",
        "cb_latency_ms": 220,
        "judge_tl": (5, 5, 5, "Both products named with timestamps; matches reference exactly."),
        "judge_cb": (3, 4, 3, "Catches Neo4j but misses the audio-only Neptune mention."),
    },

    # ---- VID-LEC-002 (prompt engineering lightning talk, 300s) ----
    {
        "qid": "Q-017",
        "kind": "reasoning",
        "tl_answer": (
            "The speaker argues that most production prompt-engineering value "
            "comes from structure (clear input/output contracts) and evaluation "
            "(small fixture sets you iterate against), not from clever wording or "
            "magic phrases."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 2310,
        "cb_answer": (
            "Based on sampled slide text mentioning 'structure', 'eval', and "
            "'examples,' the talk seems to argue that production prompts depend "
            "on testing and design rather than phrasing."
        ),
        "cb_notes": "claude-haiku-4-5, 8 frames",
        "cb_latency_ms": 2250,
        "judge_tl": (5, 5, 5, "Captures the main argument in one sentence as the reference does."),
        "judge_cb": (4, 5, 3, "Same conclusion, less crisp phrasing."),
    },
    {
        "qid": "Q-018",
        "kind": "retrieval",
        "tl_answer": (
            "Top matches:\n"
            "[178.0s–192.0s] score=0.84 — 'chain-of-thought' discussed briefly as "
            "a structural technique, with explicit pushback against treating it "
            "as a magic phrase"
        ),
        "tl_notes": "Marengo marengo3.0, audio+visual",
        "tl_latency_ms": 530,
        "cb_answer": "Frames with the on-screen text 'CoT' appear briefly around 180s.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 210,
        "judge_tl": (5, 5, 4, "Yes with full context and explicit framing; very lightly extrapolated from a brief mention."),
        "judge_cb": (3, 4, 2, "Confirms presence of the topic but no context."),
    },
    {
        "qid": "Q-019",
        "kind": "retrieval",
        "tl_answer": (
            "Top match: [245.0s–266.0s] score=0.91 — speaker recommends adding an "
            "eval set first, even a small one (5-10 fixtures), before iterating "
            "on the prompt itself"
        ),
        "tl_notes": "Marengo marengo3.0",
        "tl_latency_ms": 500,
        "cb_answer": "Slide text near the end of the talk mentions 'evals first.' Best frame: 250s.",
        "cb_notes": "ViT-B-32/openai, 1 fps",
        "cb_latency_ms": 200,
        "judge_tl": (5, 5, 5, "Names the recommendation and includes the speaker's '5-10 fixtures' qualifier."),
        "judge_cb": (4, 4, 3, "Right answer, less specific."),
    },
    {
        "qid": "Q-020",
        "kind": "reasoning",
        "tl_answer": (
            "The speaker frames model choice as setting the ceiling and prompt "
            "design as the work of getting close to it. The implication is that "
            "picking the right model tier matters more than perfecting wording — "
            "a small fast model with a great prompt will not beat a large model "
            "with a mediocre prompt on hard tasks, but for easy tasks the small "
            "model is sufficient and cheaper."
        ),
        "tl_notes": "Pegasus pegasus1.5",
        "tl_latency_ms": 2440,
        "cb_answer": (
            "The talk seems to argue that model choice and prompt design are "
            "complementary, with model choice as the primary lever based on "
            "frame text mentioning 'ceiling' and 'tier.'"
        ),
        "cb_notes": "claude-haiku-4-5, 8 frames",
        "cb_latency_ms": 2210,
        "judge_tl": (5, 5, 4, "Full reasoning with the ceiling analogy and cost implication; the cost-tradeoff sentence is the model's framing, not a verbatim quote."),
        "judge_cb": (3, 4, 2, "Right framing, missing the cost dimension."),
    },
    # ---- Structured (Pegasus 1.5 Time-Based Metadata) ----
    # These four exercise the Pegasus 1.5 TBM path — define a JSON schema,
    # get timestamped structured output. The pedagogical point is that
    # Pegasus produces video-native temporal boundaries; frame-sampled
    # Claude produces schema-conforming JSON but with weaker timestamps.
    {
        "qid": "Q-021",
        "kind": "structured",
        "tl_answer": json.dumps(
            {
                "stages": [
                    {"name": "mixing", "start_s": 0.0, "end_s": 14.6},
                    {"name": "kneading", "start_s": 14.6, "end_s": 39.8},
                    {"name": "proofing", "start_s": 39.8, "end_s": 54.0},
                    {"name": "shaping", "start_s": 54.0, "end_s": 70.2},
                    {"name": "baking", "start_s": 70.2, "end_s": 178.4},
                ]
            },
            indent=2,
        ),
        "tl_notes": "Pegasus pegasus1.5 (Time-Based Metadata)",
        "tl_latency_ms": 2680,
        "cb_answer": json.dumps(
            {
                "stages": [
                    {"name": "mixing", "start_s": 0, "end_s": 30},
                    {"name": "kneading", "start_s": 30, "end_s": 50},
                    {"name": "rising", "start_s": 50, "end_s": 90},
                    {"name": "baking", "start_s": 90, "end_s": 180},
                ]
            },
            indent=2,
        ),
        "cb_notes": "claude-haiku-4-5, 6 frames, schema-mode",
        "cb_latency_ms": 2740,
        "judge_tl": (5, 5, 5, "Five stages with sub-second boundaries — matches the reference and produces the schema-required fields exactly."),
        "judge_cb": (4, 4, 3, "Right shape, but only 4 stages (drops shaping) and timestamps are coarse 10-second buckets from sparse frame sampling."),
    },
    {
        "qid": "Q-022",
        "kind": "structured",
        "tl_answer": json.dumps(
            {
                "attempts": [
                    {"index": 1, "outcome": "made", "start_s": 0.4, "end_s": 5.8},
                    {"index": 2, "outcome": "miss", "start_s": 16.2, "end_s": 21.6},
                    {"index": 3, "outcome": "made", "start_s": 26.0, "end_s": 31.4},
                    {"index": 4, "outcome": "made", "start_s": 38.8, "end_s": 44.0},
                ]
            },
            indent=2,
        ),
        "tl_notes": "Pegasus pegasus1.5 (Time-Based Metadata)",
        "tl_latency_ms": 2310,
        "cb_answer": json.dumps(
            {
                "attempts": [
                    {"index": 1, "outcome": "made", "start_s": 0, "end_s": 10},
                    {"index": 2, "outcome": "miss", "start_s": 15, "end_s": 25},
                    {"index": 3, "outcome": "made", "start_s": 25, "end_s": 35},
                    {"index": 4, "outcome": "made", "start_s": 35, "end_s": 45},
                ]
            },
            indent=2,
        ),
        "cb_notes": "claude-haiku-4-5, 6 frames, schema-mode",
        "cb_latency_ms": 2210,
        "judge_tl": (5, 5, 5, "All four attempts with correct outcome and sub-second boundaries."),
        "judge_cb": (4, 4, 3, "Outcomes correct, but time ranges are 5-second buckets that overlap unrealistically."),
    },
    {
        "qid": "Q-023",
        "kind": "structured",
        "tl_answer": json.dumps(
            {
                "tricks": [
                    {"name": "ollie", "outcome": "landed", "start_s": 3.2, "end_s": 5.8},
                    {"name": "kickflip", "outcome": "bailed", "start_s": 13.6, "end_s": 18.4},
                    {"name": "heelflip", "outcome": "landed", "start_s": 23.8, "end_s": 28.1},
                    {"name": "180", "outcome": "landed", "start_s": 38.4, "end_s": 41.2},
                ]
            },
            indent=2,
        ),
        "tl_notes": "Pegasus pegasus1.5 (Time-Based Metadata)",
        "tl_latency_ms": 2540,
        "cb_answer": json.dumps(
            {
                "tricks": [
                    {"name": "ollie", "outcome": "landed", "start_s": 3, "end_s": 7},
                    {"name": "flip trick", "outcome": "uncertain", "start_s": 14, "end_s": 19},
                    {"name": "flip trick", "outcome": "landed", "start_s": 24, "end_s": 29},
                    {"name": "spin", "outcome": "landed", "start_s": 38, "end_s": 42},
                ]
            },
            indent=2,
        ),
        "cb_notes": "claude-haiku-4-5, 6 frames, schema-mode",
        "cb_latency_ms": 2470,
        "judge_tl": (5, 5, 5, "All four tricks named specifically with correct outcomes and tight boundaries."),
        "judge_cb": (3, 3, 2, "Right count and rough timing, but Claude can't disambiguate kickflip vs heelflip from 6 sampled frames — collapses to 'flip trick.'"),
    },
    {
        "qid": "Q-024",
        "kind": "structured",
        "tl_answer": json.dumps(
            {
                "sections": [
                    {"title": "Definition", "start_s": 0.0, "end_s": 31.6, "key_terms": ["graph database", "nodes", "edges", "traversal"]},
                    {"title": "Why relational fails for multi-hop", "start_s": 31.6, "end_s": 95.4, "key_terms": ["joins", "many-to-many", "traversal cost"]},
                    {"title": "Products", "start_s": 95.4, "end_s": 150.2, "key_terms": ["Neo4j", "Neptune"]},
                ]
            },
            indent=2,
        ),
        "tl_notes": "Pegasus pegasus1.5 (Time-Based Metadata)",
        "tl_latency_ms": 2870,
        "cb_answer": json.dumps(
            {
                "sections": [
                    {"title": "Intro", "start_s": 0, "end_s": 60, "key_terms": ["graph"]},
                    {"title": "Examples", "start_s": 60, "end_s": 150, "key_terms": ["Neo4j"]},
                ]
            },
            indent=2,
        ),
        "cb_notes": "claude-haiku-4-5, 6 frames, schema-mode (no audio)",
        "cb_latency_ms": 2620,
        "judge_tl": (5, 5, 5, "Three sections with audio-grounded boundaries and rich key-term extraction; matches the reference."),
        "judge_cb": (3, 3, 2, "Section count wrong (2 vs 3), generic titles, and Neptune missed entirely — frame-sampled vision has no audio handle."),
    },
]


# ----------------------------------------------------------------------
# Visual-only ablation overrides
# ----------------------------------------------------------------------
# For audio-heavy retrieval questions (the lectures Q-014..Q-019), the
# visual-only Marengo run loses the speech signal entirely. These overrides
# generate `fixtures/twelve_labs/search_visual_only/Q-XXX.json` plus a
# `Q-XXX__twelve_labs__visual_only.json` judge fixture so the rollup reflects
# the actual audio contribution.
VISUAL_ONLY_OVERRIDES: dict[str, dict] = {
    "Q-014": {
        "tl_answer": (
            "No high-confidence visual matches for a verbal definition. "
            "Best frame: [12.0s] score=0.41 — a slide titled 'Graph databases' "
            "but no definition text is visible."
        ),
        "tl_notes": "Marengo marengo3.0, visual-only (ablation) — speech signal lost",
        "tl_latency_ms": 510,
        "judge_tl": (2, 3, 2, "Visual-only retrieval finds the topic slide but not the spoken definition — the answer is the definition, and the model can't surface it without audio."),
    },
    "Q-016": {
        "tl_answer": (
            "Top matches:\n"
            "[112.0s–115.0s] score=0.66 — slide with 'Neo4j' label visible"
        ),
        "tl_notes": "Marengo marengo3.0, visual-only (ablation) — Neptune (audio-only mention) lost",
        "tl_latency_ms": 540,
        "judge_tl": (3, 4, 3, "Catches Neo4j via slide OCR but completely misses Neptune which was named only in speech."),
    },
    "Q-018": {
        "tl_answer": "No high-confidence matches. Slide overlay 'CoT' appears briefly around 180s but no surrounding context.",
        "tl_notes": "Marengo marengo3.0, visual-only (ablation) — speaker's verbal discussion lost",
        "tl_latency_ms": 480,
        "judge_tl": (2, 3, 2, "Confirms presence via a passing slide marker but loses the speaker's actual framing of chain-of-thought as a structural technique."),
    },
    "Q-019": {
        "tl_answer": "Slide near the end reads 'Evals first.' No surrounding context available without audio.",
        "tl_notes": "Marengo marengo3.0, visual-only (ablation) — speaker's recommendation lost",
        "tl_latency_ms": 460,
        "judge_tl": (3, 4, 2, "Right answer per slide text, but the speaker's '5-10 fixtures' qualifier was audio-only."),
    },
}


def write_fixtures() -> None:
    (FIX / "twelve_labs" / "search").mkdir(parents=True, exist_ok=True)
    (FIX / "twelve_labs" / "generate").mkdir(parents=True, exist_ok=True)
    (FIX / "twelve_labs" / "structured").mkdir(parents=True, exist_ok=True)
    (FIX / "twelve_labs" / "search_visual_only").mkdir(parents=True, exist_ok=True)
    (FIX / "clip_baseline" / "retrieve").mkdir(parents=True, exist_ok=True)
    (FIX / "clip_baseline" / "reason").mkdir(parents=True, exist_ok=True)
    (FIX / "clip_baseline" / "structured").mkdir(parents=True, exist_ok=True)
    (FIX / "judge").mkdir(parents=True, exist_ok=True)

    tl_subdir_for_kind = {
        "retrieval": "search",
        "reasoning": "generate",
        "structured": "structured",
    }
    cb_subdir_for_kind = {
        "retrieval": "retrieve",
        "reasoning": "reason",
        "structured": "structured",
    }

    n_written = 0
    for entry in DATA:
        qid = entry["qid"]
        kind = entry["kind"]
        tl_subdir = tl_subdir_for_kind[kind]
        cb_subdir = cb_subdir_for_kind[kind]

        # Twelve Labs response
        (FIX / "twelve_labs" / tl_subdir / f"{qid}.json").write_text(
            json.dumps(
                {
                    "question_id": qid,
                    "answer": entry["tl_answer"],
                    "notes": entry["tl_notes"],
                    "latency_ms": entry["tl_latency_ms"],
                },
                indent=2,
            )
        )
        n_written += 1

        # CLIP baseline response
        (FIX / "clip_baseline" / cb_subdir / f"{qid}.json").write_text(
            json.dumps(
                {
                    "question_id": qid,
                    "answer": entry["cb_answer"],
                    "notes": entry["cb_notes"],
                    "latency_ms": entry["cb_latency_ms"],
                },
                indent=2,
            )
        )
        n_written += 1

        # Judge scores
        rel, faith, spec, rat = entry["judge_tl"]
        (FIX / "judge" / f"{qid}__twelve_labs.json").write_text(
            json.dumps(
                {"relevance": rel, "faithfulness": faith, "specificity": spec, "rationale": rat},
                indent=2,
            )
        )
        n_written += 1
        rel, faith, spec, rat = entry["judge_cb"]
        (FIX / "judge" / f"{qid}__clip_baseline.json").write_text(
            json.dumps(
                {"relevance": rel, "faithfulness": faith, "specificity": spec, "rationale": rat},
                indent=2,
            )
        )
        n_written += 1

    # Visual-only ablation fixtures (Marengo search + matched judge variant).
    for qid, override in VISUAL_ONLY_OVERRIDES.items():
        (FIX / "twelve_labs" / "search_visual_only" / f"{qid}.json").write_text(
            json.dumps(
                {
                    "question_id": qid,
                    "answer": override["tl_answer"],
                    "notes": override["tl_notes"],
                    "latency_ms": override["tl_latency_ms"],
                },
                indent=2,
            )
        )
        rel, faith, spec, rat = override["judge_tl"]
        (FIX / "judge" / f"{qid}__twelve_labs__visual_only.json").write_text(
            json.dumps(
                {"relevance": rel, "faithfulness": faith, "specificity": spec, "rationale": rat},
                indent=2,
            )
        )
        n_written += 2

    print(f"wrote {n_written} fixture files under {FIX}")


if __name__ == "__main__":
    write_fixtures()
