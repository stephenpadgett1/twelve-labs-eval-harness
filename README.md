# Video-Understanding Eval Harness

A side-by-side eval harness for video-understanding models, tracking the current product surface area as of Marengo 3.0 (Dec 2025 GA) and Pegasus 1.5 (NAB 2026 GA):

- **Twelve Labs** — Marengo 3.0 (retrieval) + Pegasus 1.5 (reasoning) + **Pegasus 1.5 Time-Based Metadata** (structured extraction)
- **Open-source baseline** — CLIP (retrieval) + frame-sampled Claude (reasoning + schema-mode structured extraction)
- **LLM-as-judge** — Claude Sonnet 4.6 scoring each pipeline's response on relevance, faithfulness, and specificity (1–5)
- **Cost-aware scoring** — illustrative $/call estimates from posted pricing pages, surfacing the segment-billing pitfall customers hit
- **Audio-modality ablation** — `--ablation visual_only` measures Marengo's audio contribution on speech-heavy queries

Built as a Solutions-Architect reference scaffold — the kind of artifact you'd hand a strategic customer in week two to anchor an honest model evaluation, not a benchmark exercise.

## Why this exists

Most "Twelve Labs vs X" content on the internet is either marketing collateral or a single notebook with no real eval. This harness is a small, opinionated reference for *how* to evaluate video models for a real customer use case:

- A real corpus (bring your own — placeholder URLs ship in `corpus/videos.yaml`)
- A real question set (`questions/questions.yaml`) with **expected answers** so the judge has a reference, not guesswork
- A real LLM judge with a strict-JSON contract
- A side-by-side report you can put in front of a non-technical stakeholder

The harness is video-source-agnostic — swap in any short videos with stable URLs and rerun.

## What's in the box

```
.
├── corpus/videos.yaml          # 6 demo videos across 3 use cases (product / sports / lecture)
├── questions/questions.yaml    # 24 questions across 3 kinds:
│                               #   12 retrieval + 8 reasoning + 4 structured (TBM)
├── src/eval_harness/
│   ├── clients/
│   │   ├── twelve_labs.py      # Marengo 3.0 + Pegasus 1.5 + TBM extract + visual-only ablation
│   │   ├── clip_baseline.py    # CLIP retrieval + Claude reasoning + Claude schema-mode
│   │   └── judge.py            # LLM-as-judge with ablation-aware fixture routing
│   ├── corpus.py               # YAML loaders + validation
│   ├── runner.py               # orchestrates the eval
│   ├── report.py               # renders markdown side-by-side incl. cost rollup
│   ├── types.py                # pydantic domain model (Question.schema_, cost_usd, Ablation)
│   └── cli.py                  # click entry point with --ablation flag
├── fixtures/                   # pre-recorded responses for offline / no-key runs
│   └── twelve_labs/
│       ├── search/             # Marengo full modality
│       ├── search_visual_only/ # Marengo ablation (audio-heavy queries only)
│       ├── generate/           # Pegasus reasoning
│       └── structured/         # Pegasus 1.5 Time-Based Metadata
├── output/
│   ├── eval-report.md          # full-modality sample (committed)
│   └── eval-report-visual-only.md  # ablation sample (committed; for diffing)
├── scripts/generate_fixtures.py
└── tests/                      # pytest — 15 tests covering corpus, end-to-end,
                                # judge parsing, structured kind, costs, ablation
```

## Architecture

```
┌──────────────────┐         ┌─────────────────────┐
│ corpus/videos    │         │ questions/questions │
└────────┬─────────┘         └──────────┬──────────┘
         │                              │
         └─────────────┬────────────────┘
                       ▼
              ┌─────────────────┐
              │  runner.py      │
              └────────┬────────┘
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 ┌─────────────┐ ┌────────────┐ ┌────────────┐
 │ Twelve Labs │ │ CLIP base- │ │  Judge     │
 │ Marengo +   │ │ line +     │ │  (Claude)  │
 │ Pegasus     │ │ Claude     │ │            │
 └──────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │              │              │
        └──────────────┴──────────────┘
                       ▼
              ┌─────────────────┐
              │  report.py      │
              │  markdown out   │
              └─────────────────┘
```

Each client has a fixture-mode fallback. If `TWELVE_LABS_API_KEY` / `ANTHROPIC_API_KEY` aren't set, the corresponding client serves pre-recorded responses from `fixtures/` so a fresh clone produces a complete, inspectable report.

## Quick start

### Fixture mode (no keys required)

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
eval-harness
# → wrote report → output/eval-report.md
```

That's it. The committed fixtures cover all 20 questions; the report renders fully.

### Live mode (real model calls)

```bash
export TWELVE_LABS_API_KEY=tl-...
export ANTHROPIC_API_KEY=sk-ant-...
pip install -e ".[twelve-labs,clip]"
# Edit corpus/videos.yaml — replace <replace-with-real-video-url> placeholders
eval-harness
```

The Twelve Labs path will index each video, run Marengo 3.0 for retrieval questions, Pegasus 1.5 for reasoning questions, and Pegasus 1.5 Time-Based Metadata for structured questions. The CLIP baseline path will sample frames, embed with open-clip, and submit frames to Claude for reasoning + schema-mode extraction. The judge runs against Claude Sonnet 4.6.

> **Note on the CLIP baseline:** The live-mode CLIP and PyAV paths are intentionally raised as `NotImplementedError` in this scaffold to keep the repo's heavy-dependency surface optional. The integration points are clearly marked in `clip_baseline.py` — about 40 lines to fill in for a real run. The fixture-mode path is fully functional.

### Audio ablation

```bash
eval-harness                                                              # full modality (visual + audio)
eval-harness --ablation visual_only --output output/eval-report-visual-only.md
diff output/eval-report.md output/eval-report-visual-only.md
```

On the demo corpus the visual-only run drops Marengo's retrieval rollup from 4.89 → 4.17 — the loss concentrates on the lecture videos, where speech retrieval was carrying the signal. Reasoning and structured kinds are unchanged in this scaffold; in a real run, Pegasus answers for speech-grounded questions would degrade similarly.

### Cost estimates

The report renders an illustrative `$/call` column and a per-pipeline `$/run` rollup. The numbers come from posted pricing pages:

- **TwelveLabs:** Marengo indexing $0.042/min video (one-time, amortized over `INDEX_AMORTIZE_QUERIES = 10` queries by default); Pegasus analyze $0.0292/min video per call.
- **CLIP baseline:** CLIP encoding is local ($0 OPEX). Claude Haiku 4.5 inputs $0.80/MT, outputs $4/MT — six 1024×768 frames per reasoning call ≈ 8,200 input tokens.

**The segment-billing pitfall.** TwelveLabs bills indexing per minute of video × number of segment definitions. A 1-hour video with 4 segment definitions = 240 indexed minutes, not 60. A common customer-onboarding mistake is to define a separate segment per "concept" up-front; do that on a 50,000-hour archive and the indexing bill goes 4× the back-of-envelope. The eval surfaces this — tune `INDEX_AMORTIZE_QUERIES` in `twelve_labs.py` to your customer's real query-to-index ratio before quoting.

## What the report looks like

A real sample is committed at `output/eval-report.md`. The top-of-report rollup looks like:

| Metric | Twelve Labs | CLIP baseline |
|---|---:|---:|
| Relevance     | 5.00 | 3.71 |
| Faithfulness  | 4.92 | 4.04 |
| Specificity   | 4.71 | 2.75 |
| Overall       | 4.88 | 3.50 |

Per-kind breakdown shows where each model carries its weight:

| Kind | Pipeline | n | Overall |
|---|---|---:|---:|
| retrieval | Twelve Labs | 12 | 4.89 |
| retrieval | CLIP baseline | 12 | 3.59 |
| reasoning | Twelve Labs | 8 | 4.79 |
| reasoning | CLIP baseline | 8 | 3.54 |
| structured (TBM) | Twelve Labs | 4 | 5.00 |
| structured (TBM) | CLIP baseline | 4 | 3.17 |

Cost rollup makes the trade-off explicit:

| Pipeline | Total $ | Avg $/question |
|---|---:|---:|
| Twelve Labs | $0.79 | $0.033 |
| CLIP baseline | $0.09 | $0.008 |

~8× more expensive for ~40% higher quality on this corpus — the kind of trade-off you actually want to put in front of a customer, not bury under marketing copy. **The numbers above are from the committed demo fixtures, not a real run** — see the honesty notes below.

## Honesty notes

This is a portfolio artifact, not a benchmark. Specifically:

- **Videos are placeholder.** The corpus YAML ships with `<replace-with-real-video-url>` markers. The fixtures simulate what each pipeline *would* return on representative short videos of those use-case shapes.
- **The fixture answers were hand-written**, calibrated against observed Marengo 3.0 / Pegasus 1.5 / CLIP behavior on similar video types. They are *illustrative*, not measured.
- **The 4.88 vs 3.50 gap in the demo rollup is not a benchmark claim about Twelve Labs.** It reflects the realistic structural advantage Twelve Labs has on speech-heavy content (lecture videos — pure-CLIP retrieval has no audio), Pegasus's specificity edge over frame-sampled multimodal prompting, and the Time-Based Metadata advantage on schema-conformant temporal extraction (where Pegasus 1.5 produces video-native boundaries vs Claude reading 6 sampled frames).
- **The audio-ablation delta (4.88 → 4.51 overall, 4.89 → 4.17 on retrieval) is the fixture's modeled estimate** of Marengo 3.0's native-audio contribution on speech-heavy queries. TwelveLabs' own reported MSR-VTT audio benchmark gap vs Nova (73.2% vs 36.7%) is the directional reason this should hold in live runs, but treat the magnitude here as illustrative, not measured.
- **Cost estimates are illustrative.** They come from posted public pricing as of 2026-05-28, ignore volume discounts, and amortize Marengo indexing across 10 queries per video (`INDEX_AMORTIZE_QUERIES`). Real customer bills depend on actual query/index ratio and any negotiated rates.
- **Don't extrapolate from fixture-mode rollup to a real claim about either pipeline.** The honest version of this comparison is the one you get by replacing the corpus, running live, and reading the per-question detail.

## How a Solutions Architect would use this

The intended workflow when scoping a real customer engagement:

1. Replace `corpus/videos.yaml` with 5–10 *of the customer's* videos (or close analogues).
2. Replace `questions/questions.yaml` with the question shapes the customer cares about — retrieval for "find me where X happened," reasoning for "summarize what changed."
3. Add a reference answer per question. This is the work that matters; without it the eval is guesswork.
4. Run live. Read the per-question detail, not just the rollup.
5. Use the report as the shared artifact in the next customer review.

The whole point is that the harness is reusable across customers — corpus, questions, and references change; the rest doesn't.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Covers corpus loading, judge JSON parsing, fixture-mode response shape, and report rendering against the committed fixtures.

## License

MIT. See `LICENSE`.
