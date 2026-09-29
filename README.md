# Harmful query rewrites in RAG

This project tests one claim:

**Query rewriting can retrieve better context than the raw user question, and it can also change the question enough to retrieve the wrong context. An intent-preservation judge can reject the unsafe rewrites and fall back to the original query.**

It is a small, local experiment. There is no agent, no web search, and no chat UI. Three pipelines run on the same questions so the difference is only the rewrite, and then the judge.

The scored benchmark is 40 policy pages and 96 questions, split into 27 development items and 69 held-out test items. The judge was not edited against either split. Headline numbers are the test split:

| Level | What it does | Hit@1 | Fact coverage | Harmful rewrites sent to the retriever |
| --- | --- | ---: | ---: | ---: |
| 1 Baseline | Original query only | 0.855 | 0.870 | 0.000 |
| 2 Rewrite | Always retrieve with the rewrite | 0.870 | 0.870 | 1.000 |
| 3 Judge | Use the rewrite only if the judge accepts it | 0.899 | 0.913 | 0.000 |

On the same test questions the judge's HRDR is 1.000 and its harmful false-acceptance rate is 0.000, but it rejects 0.480 of the safe rewrites. Every meaning-preserving number paraphrase in the test set (`14 days` to `two weeks`, `1 year` to `twelve months`, `Rs 2000` to `two thousand rupees`) is rejected. Ambiguous rewrites score 0.769 accuracy against a preferred label and 0.435 macro F1, because the judge never accepts the ambiguous cases whose preferred label is accept.

Reproduce the table with:

```bash
python -m experiments.run_experiment
```

Results are written to `results/comparison.md` and `results/comparison.json`.

## The problem

A retriever matches a query against document chunks. Users often phrase that query in a way the documents do not: abbreviations (`NB Pro`), typos (`warrenty`), or everyday words (`send back`, `student deal`, `gift voucher`).

A rewriter turns the question into a search query. That helps when it only repairs wording. It hurts when it drops or changes something the retriever needs:

- a product name (`NovaBook Air` becomes `NovaBook Pro`)
- a number, price, or percentage
- a date or a relation such as `since 2024`
- a negation (`not`, `except`, `without`)
- a scope word (`only`)
- any other detail that would select a different passage (`unopened`, `refurbished`, `remote islands`)

Those are **harmful rewrites**. The sentences can still look similar. Similarity is the wrong test. `NovaBook Air warranty` and `NovaBook Pro warranty` overlap a lot and mean different things.

## Why this is not "are these two queries similar?"

The judge scores retrieval-critical slots. High word overlap does not make a rewrite safe.

This pair is from the negation probe. The rewriter turned "the Air, not the Pro" into a Pro query. Intent overlap stays true, and the judge still rejects it:

```json
{
  "intent_preserved": true,
  "entities_preserved": false,
  "constraints_preserved": true,
  "numbers_preserved": true,
  "dates_preserved": true,
  "negation_preserved": false,
  "scope_preserved": true,
  "unsupported_additions": false,
  "critical_information_lost": true,
  "safe_to_use": false,
  "reason": "A critical entity was changed or removed (novabook air, novabook pro -> novabook pro). Negation was removed, added, or reversed. The rewrite drops information that could change retrieval: warranty."
}
```

`safe_to_use` is the decision. The reason only explains which factors failed.

## Level 1 — baseline RAG

```
User query → embedding → FAISS retriever → top chunk → answer
```

`src/rag_baseline.py`

1. Load markdown files from `data/`.
2. Chunk them (`src/ingestion.py`). These files are short, so each file is one chunk.
3. Embed chunks with `sentence-transformers/all-MiniLM-L6-v2`.
4. Store the vectors in a FAISS inner-product index. Vectors are normalized, so the score is cosine similarity (`src/retriever.py`).
5. Embed the original query and take the top 3 chunks.
6. The answer is built from the top chunk. The generator is asked the **original** question.

There is no rewrite and nothing for the judge to do. This is the control.

## Level 2 — RAG plus query rewriting

```
Original query → rewriter → rewritten query → retriever → top chunk → answer
```

`src/rag_rewrite.py` and `src/query_rewriter.py`

The original string is kept on the result. The retriever sees the rewrite. The generator is still asked the original question, so a bad retrieval is not hidden by also changing the question.

The rewriter is an LLM call when `LLM_PROVIDER=openai`. The prompt tells the model to preserve entities, numbers, dates, negations, and constraints, and to fix typos and catalog abbreviations.

Without an API key, `LocalRewriter` does the same helpful repairs, then applies five failure modes. The failure modes are linguistic rules, not a table of query ids:

| Mode | Rule | Example effect |
| --- | --- | --- |
| `negation_inversion` | `not the Pro` is treated as a request for the Pro | Air warranty query becomes a Pro query |
| `dropped_sibling_entity` | If both Air and Pro are named, Air is deleted | A comparison keeps only the Pro |
| `dropped_trailing_constraint` | A trailing `, except ...` clause is cut off | `except opened software` disappears |
| `dropped_only` | `only` is removed as if it were a stopword | `Only the original purchaser` gets wider |
| `date_off_by_one` | `since YEAR` becomes `YEAR - 1` | `since 2024` becomes `2023` |

Set `REWRITER_FAILURES=0` to keep only the helpful repairs. The 5-out-of-12 harmful rate on the probe set is a property of these rules, so the risk is visible and repeatable. It is not a measurement of how often a hosted model mis-rewrites.

## Level 3 — rewrite, judge, then maybe fall back

```
Original query → rewriter → rewritten query → judge → PASS or REJECT
                                                      → retriever → answer
```

`src/rag_judge.py` and `src/query_judge.py`

- `safe_to_use == true`: the retriever gets the **rewritten** query.
- `safe_to_use == false`: the retriever gets the **original** query.

The rewrite is not tried again. The original query is still the question passed to the generator.

## Judge factors

Each factor is a boolean computed from the original query and the rewrite after a shared normalization step (`src/text_norm.py`). Normalization only equates things that mean the same thing: `Rs 50,000` and `50000`, `NB Pro` and `NovaBook Pro`, `warrenty` and `warranty`, `below` and `under`, `10 percent` and `10%`, `cannot be returned` and `not returnable`.

| Factor | What is checked |
| --- | --- |
| Intent | Content-word overlap of the normalized queries. This can stay true while another factor fails. |
| Entities | Catalog names (`NovaBook Air`, `NovaBook Pro`, `PixelTab`) are not dropped or swapped. |
| Constraints | Hard operators still match: under, over, at least, at most, before, after, since, until, only, except, without. |
| Numbers | Prices, quantities, and percentages match, ignoring format. Years are judged as dates, not as generic numbers. |
| Dates | Years, month names, and relations such as `before 2025` match. The verb "may" is not treated as the month May. |
| Negation | `not`, `without`, `except`, `cannot`, and similar cues are present on both sides or on neither. |
| Scope | `only`, `all`, `any`, and `every` match. |
| Unsupported additions | The rewrite adds a number, date, entity, constraint, negation, or a content word that was not in the query. |
| Critical information loss | One of those slots, or a specific content word such as `unopened` or `refurbished`, was removed. |

Generic search words may be added or dropped without a failure: `policy`, `price`, `duration`, `length`, `window`, `detail`. That is deliberate. A rewrite that only says "warranty duration" instead of "warranty length" is still the same request.

## Judge rules

`safe_to_use` is true only when every preservation flag is true and both `unsupported_additions` and `critical_information_lost` are false.

- Minor wording changes are accepted when the slots above survive.
- A critical entity must not change.
- A number must not change.
- A date or time period must not change.
- Negation must not be removed or flipped.
- An explicit constraint must not be removed.
- An added assumption is rejected when it can change what is retrieved.
- Lost critical information is rejected even if the wording still looks similar.

The judge accepts format changes and the synonyms in `src/text_norm.py`. It does not accept a meaning-preserving change of digits, so `14 days` and `two weeks` are not treated as the same constraint. That shows up as safe-rewrite rejections on the held-out set.

## Fallback

Level 3 never rewrites twice.

```text
if judge.safe_to_use:
    retrieval_query = rewritten_query
else:
    retrieval_query = original_query
```

Level 1 always uses the original. Level 2 always uses the rewrite. Level 3 uses the rewrite only after a pass. The same rewrite object is passed into Level 2 and Level 3 so the comparison is paired.

## Evaluation

The benchmark lives in `experiments/benchmark_spec.py` and is written to `data/*.md` and `experiments/benchmark.json`. Regenerate it with `python -m experiments.benchmark_spec`. Development and test ids are fixed in that file. Report the test split. Do not fit the judge to it.

Each item has an original question, a rewrite, a label (`safe`, `harmful`, or `ambiguous`), gold documents for the original request, and a category such as negation, temporal, entity, scope, multi-constraint, or semantic equivalent. Level 2 always retrieves with that rewrite. Level 3 judges the same rewrite and falls back to the original question when `safe_to_use` is false. The local rewriter's built-in failure modes are not what this comparison measures. `python -m experiments.demo` still uses that rewriter on two hand-picked questions.

### A. Retrieval and answer quality

- **Hit@1**: the top chunk is one of the gold documents for the original request.
- **Recall@3**: fraction of those gold documents present in the top 3.
- **Fact coverage**: fraction of expected fact strings present in the top passage.
- **Faithfulness**: fraction of answer words that also appear in that passage. The local generator copies the passage, so this is 1.0.

The answer uses the top chunk (`ANSWER_K=1`). The index still returns 3 chunks for Recall@3.

Held-out test Hit@1, broken out by the rewrite label:

| Label | n | Level 1 | Level 2 | Level 3 |
| --- | ---: | ---: | ---: | ---: |
| safe | 25 | 0.800 | 0.960 | 0.920 |
| harmful | 31 | 1.000 | 0.871 | 1.000 |
| ambiguous | 13 | 0.615 | 0.692 | 0.615 |

Safe rewrites help. The judge keeps most of that help and gives a little back when it rejects a safe paraphrase (`two thousand rupees` retrieves the metro shipping page; the original wording retrieves the Ladakh page, and Level 3 falls back). Harmful rewrites drop Hit@1 to 0.871, and Level 3 returns it to 1.000 because every harmful test rewrite was rejected. Ambiguous rewrites are where the fallback throws away a small gain.

### B. Judge quality

Ambiguous items are excluded from HRDR and from the two error rates. They have a preferred label for accuracy and macro F1. Macro F1 averages the F1 of "block" and the F1 of "allow".

**Harmful Rewrite Detection Rate (HRDR)**

```text
HRDR = harmful rewrites correctly rejected / total harmful rewrites
```

**Harmful rewrite false acceptance rate**

```text
harmful rewrites incorrectly accepted / total harmful rewrites
```

**Safe rewrite rejection rate**

```text
safe rewrites incorrectly rejected / total safe rewrites
```

Held-out test (31 harmful, 25 safe, 13 ambiguous):

| Metric | Test | Development |
| --- | ---: | ---: |
| HRDR | 1.000 | 0.909 |
| Harmful false acceptance | 0.000 | 0.091 |
| Safe rewrite rejection | 0.480 | 0.556 |
| Ambiguous accuracy | 0.769 | 0.714 |
| Ambiguous macro F1 | 0.435 | 0.417 |

Test HRDR is 1.000 because those harmful rewrites change an entity, number, date, negation, or scope in a way the slot rules see. It is not a perfect judge. Safe rejection is 0.480 overall and 1.000 on the semantic-equivalent slice: `14 days` / `two weeks`, `7 days` / `one week`, `1 year` / `twelve months`, `12 months` / `a year`, `Rs 3500` / `three thousand five hundred rupees`, `two thousand rupees` / `Rs 2000`, `next-day` / `within 24 hours`, `48 hours` / `two days`, `15%` / `fifteen percent`. Abbreviations and synonyms (`NB Pro`, `send back`, `gift voucher`) are accepted.

The development split contains the miss the test split does not. `What is the NovaBook Air return window?` rewritten as `Is the NovaBook Air returnable?` is harmful, and the judge accepts it, because the normalizer collapses `return window` and `returnable`. That is the 0.091 false-acceptance rate. A similar test item, `What is the PixelTab return window?` to `Are PixelTab returns allowed?`, is rejected. Wording, not a tuned threshold, is the difference.

Ambiguous macro F1 is 0.435 because F1 for the "allow" class is 0. The preferred-accept cases (`about a month`, `a couple of weeks`, `PixelTab Mini` for "latest tablet") are all rejected.

## What the comparison shows

1. **Does rewriting beat the baseline?** Slightly on the test set. Hit@1 moves from 0.855 to 0.870. The gain is concentrated in safe rewrites (0.800 to 0.960), mostly abbreviations the embedding does not expand.
2. **How often is a rewrite harmful?** 31 of 69 test rewrites are labeled harmful. That mix is the benchmark, not a model error rate.
3. **Can the judge detect them?** On the test split, yes (HRDR 1.000, false acceptance 0.000). On the development split, no for one eligibility-versus-duration rewrite (false acceptance 0.091).
4. **Does the judge stop harmful rewrites from reaching the retriever?** On the test split, the harmful reach rate goes from 1.000 to 0.000. On development it goes from 1.000 to 0.091.
5. **Does the judge keep useful rewrites?** Only partly. Safe rejection is 0.480. Level 3 Hit@1 on safe rewrites is 0.920, below Level 2's 0.960 and above the baseline's 0.800.
6. **How does Level 3 compare?** Test Hit@1 is 0.899, above Level 2 (0.870) and Level 1 (0.855). Fact coverage is 0.913, 0.870, and 0.870. Level 3 wins overall because recovering the harmful queries outweighs the safe paraphrases it throws away. It does not win on every slice.

The tradeoff is visible in one shipping question. `Free shipping on orders over two thousand rupees` finds the metro policy. The judge rejects that paraphrase, Level 3 searches the original wording, and the Ladakh page comes back instead. The same judge rejects `not the Pro` rewritten as a Pro question, and Level 3 returns to the Air page. Both behaviors come from the same slot rules.

## Project layout

```text
data/                  Northwind Gadgets catalog (40 policies)
src/ingestion.py       load and chunk
src/embeddings.py      MiniLM embeddings
src/retriever.py       FAISS index
src/generator.py       extractive answer, or a grounded LLM answer
src/query_rewriter.py  Level 2 rewriter
src/query_judge.py     Level 3 judge
src/rag_baseline.py    Level 1
src/rag_rewrite.py     Level 2
src/rag_judge.py       Level 3
src/evaluation.py      Hit@1, Recall@3, fact coverage, HRDR
experiments/benchmark_spec.py
experiments/benchmark.json
experiments/run_experiment.py
experiments/demo.py
results/               written by the experiment
```

Each level can be called on its own:

```python
from src.rag_baseline import run_baseline
from src.rag_rewrite import run_rewrite
from src.rag_judge import run_judge
```

`run_rewrite` and `run_judge` accept an existing `RewriteResult` so one rewrite can be scored by both levels.

## Setup

Python 3.10+.

```bash
pip install -r requirements.txt
python -m experiments.run_experiment
python -m experiments.demo
```

`demo` runs two queries through all three levels: a helpful abbreviation, and the Air-versus-Pro negation.

The first full run downloads `all-MiniLM-L6-v2`. Judge-only scoring does not:

```bash
python -m experiments.run_experiment --judge-only
```

### Optional hosted model

Keys are read from the environment or from a `.env` file. Nothing is hard-coded. Copy `.env.example`.

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
JUDGE_BACKEND=rules
```

`JUDGE_BACKEND=llm` asks the same factor schema of the model. If that call fails, the rule judge is used and the reason says so. The default judge is the rule judge, because the HRDR numbers have to be repeatable.

Default `LLM_PROVIDER` is `local`, so a key sitting in the environment is not used unless you opt in.

## Walkthrough for a demo

1. Show Level 1 on `NB Pro warrenty length`. The embedding does not connect `NB` to NovaBook, so the warranty-claims page wins.
2. Show the rewrite `NovaBook Pro warranty length`. The judge passes it. Level 2 and Level 3 both return the Pro page, which says the warranty lasts 2 years.
3. Show `What is the NovaBook Air warranty, not the Pro`. Level 1 returns the Air page (1 year). Level 2 rewrites it to `NovaBook Pro policy details` and returns the Pro page (2 years). The judge's intent flag stays true and `safe_to_use` is false because the entity and the negation changed. Level 3 searches with the original sentence and returns the Air page.
4. Then show `14 days` rewritten as `two weeks`. The judge rejects it. That is the false positive the held-out set is there to measure.

## Limitations

- Forty synthetic pages are still a closed catalog. Recall@3 on the test split is 0.947 to 0.976, so Hit@1 is the metric that separates the levels.
- Test HRDR of 1.000 means these harmful rewrites move a slot the rules check. The development false accept (`return window` versus `returnable`) shows the same judge missing a meaning change when the normalizer erases it.
- Safe rejection of 0.480 is the cost of those slot rules. Semantic equivalents are all rejected. Abbreviations are not.
- Ambiguous labels are a preferred call, not a unanimous one. Macro F1 is the number to cite there, because accuracy is inflated by the larger "prefer reject" group.
- The local answer is the retrieved passage. Faithfulness is 1.0 by construction. Fact coverage measures retrieval.
- Gold pages were written with the questions. The judge was not. Do not read the test scores as a fitted result, and do not read them as a general claim about every rewriter.
