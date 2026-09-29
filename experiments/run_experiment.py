"""Run Level 1, Level 2, and Level 3 on the same queries and score the judge.

Usage (from the project root):

    python -m experiments.run_experiment
    python -m experiments.run_experiment --judge-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import ANSWER_K, EXPERIMENTS_DIR, RESULTS_DIR, RETRIEVE_K  # noqa: E402
from src.evaluation import (  # noqa: E402
    ambiguous_scores,
    answer_passages,
    category_rates,
    fact_coverage,
    faithfulness,
    harmful_reach_rate,
    hit_at_1,
    judge_rates,
    mean,
    recall_at_k,
    retrieved_doc_ids,
)
from src.llm import LLMClient  # noqa: E402
from src.query_judge import QueryJudge  # noqa: E402
from src.query_rewriter import QueryRewriter  # noqa: E402
from src.rag_baseline import run_baseline  # noqa: E402
from src.rag_judge import run_judge  # noqa: E402
from src.rag_rewrite import run_rewrite  # noqa: E402
from src.types import RAGResult, RewriteResult  # noqa: E402


def _load_benchmark() -> dict:
    return json.loads((EXPERIMENTS_DIR / "benchmark.json").read_text(encoding="utf-8"))


def _result_view(result: RAGResult, gold: list[str], facts: list[str]) -> dict:
    doc_ids = retrieved_doc_ids(result)
    answer_text = answer_passages(result, ANSWER_K)
    answer_body = result.answer
    for hit in result.retrieved[:ANSWER_K]:
        answer_body = answer_body.replace(f"[{hit.chunk.doc_id}]", " ")
    return {
        "retrieval_query": result.retrieval_query,
        "used_fallback": result.used_fallback,
        "top_doc": doc_ids[0] if doc_ids else None,
        "top3": doc_ids[:3],
        "hit_at_1": hit_at_1(doc_ids, gold),
        "recall_at_3": recall_at_k(doc_ids, gold, 3),
        "fact_coverage": fact_coverage(answer_text, facts),
        "faithfulness": faithfulness(answer_body, answer_text),
        "answer": result.answer,
    }


def evaluate_judge(judge: QueryJudge, cases: list[dict]) -> list[dict]:
    scored = []
    for case in cases:
        decision = judge.judge(case["original"], case["rewritten"])
        scored.append(
            {
                **case,
                "safe_to_use": decision["safe_to_use"],
                "correct": decision["safe_to_use"] == case["expected_safe"],
                "decision": decision,
            }
        )
    return scored


def _level_means(rows: list[dict], level: str) -> dict:
    return {
        "hit_at_1": mean([row[level]["hit_at_1"] for row in rows]),
        "recall_at_3": mean([row[level]["recall_at_3"] for row in rows]),
        "fact_coverage": mean([row[level]["fact_coverage"] for row in rows]),
        "faithfulness": mean([row[level]["faithfulness"] for row in rows]),
        "harmful_reach_rate": harmful_reach_rate(rows, level),
    }


def _metric_table(summary: dict) -> list[str]:
    lines = [
        "| Level | Hit@1 | Recall@3 | Fact coverage | Faithfulness | Harmful rewrites reaching retriever |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    labels = {
        "baseline": "Level 1 baseline",
        "rewrite": "Level 2 rewrite",
        "judge": "Level 3 judge",
    }
    for key, label in labels.items():
        metrics = summary[key]
        lines.append(
            "| {label} | {hit:.3f} | {recall:.3f} | {fact:.3f} | {faith:.3f} | {reach:.3f} |".format(
                label=label,
                hit=metrics["hit_at_1"],
                recall=metrics["recall_at_3"],
                fact=metrics["fact_coverage"],
                faith=metrics["faithfulness"],
                reach=metrics["harmful_reach_rate"],
            )
        )
    return lines


def _rate(value: float, total: int) -> str:
    if total == 0:
        return "—"
    return f"{value:.3f}"


def _judge_lines(title: str, rates: dict, ambiguous: dict) -> list[str]:
    return [
        f"### {title}",
        "",
        f"- Harmful Rewrite Detection Rate (HRDR): {rates['hrdr']:.3f} ({rates['harmful_total']} harmful)",
        f"- Harmful false acceptance rate: {rates['harmful_false_acceptance_rate']:.3f}",
        f"- Safe rewrite rejection rate: {rates['safe_rewrite_rejection_rate']:.3f} ({rates['useful_total']} safe)",
        f"- Ambiguous accuracy: {ambiguous['ambiguous_accuracy']:.3f} ({ambiguous['ambiguous_total']} ambiguous)",
        f"- Ambiguous macro F1: {ambiguous['ambiguous_macro_f1']:.3f}",
        "",
    ]


def _markdown(bundle: dict) -> str:
    test = bundle["test"]
    dev = bundle["dev"]
    lines = [
        "# Held-out comparison",
        "",
        "Headline numbers are the test split. Development items were not used to change the judge.",
        "Level 2 retrieves with the benchmark rewrite. Level 3 uses that rewrite only if the judge accepts it.",
        "Hit@1 is against the document for the original request. Recall@3 uses the top 3 chunks.",
        "",
        "## Test judge",
        "",
        *_judge_lines("Test", test["judge"], test["ambiguous"]),
        "## Test retrieval",
        "",
        *_metric_table(test["summary"]),
        "",
        "### Test retrieval by rewrite label",
        "",
        "| Label | n | L1 Hit@1 | L2 Hit@1 | L3 Hit@1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, metrics in test["by_label"].items():
        lines.append(
            f"| {label} | {metrics['n']} | {metrics['baseline']:.3f} | {metrics['rewrite']:.3f} | {metrics['judge']:.3f} |"
        )
    lines.extend(["", "## Test by category", "", "| Category | n | HRDR | False acceptance | Safe rejection | Ambiguous accuracy |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for name, rates in test["by_category"].items():
        lines.append(
            "| {name} | {n} | {hrdr} | {far} | {rej} | {acc} |".format(
                name=name,
                n=rates["harmful_total"] + rates["useful_total"] + rates["ambiguous_total"],
                hrdr=_rate(rates["hrdr"], rates["harmful_total"]),
                far=_rate(rates["harmful_false_acceptance_rate"], rates["harmful_total"]),
                rej=_rate(rates["safe_rewrite_rejection_rate"], rates["useful_total"]),
                acc=_rate(rates["ambiguous_accuracy"], rates["ambiguous_total"]),
            )
        )
    lines.extend(
        [
            "",
            "## Development split (not used to tune)",
            "",
            *_judge_lines("Development", dev["judge"], dev["ambiguous"]),
            *_metric_table(dev["summary"]),
            "",
            "## Test queries",
            "",
            "| ID | Label | Category | Judge | Correct | L1 | L2 | L3 | Fallback |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in test["rows"]:
        lines.append(
            "| {qid} | {label} | {cat} | {decision} | {ok} | {l1} | {l2} | {l3} | {fb} |".format(
                qid=row["id"],
                label=row["label"],
                cat=row["category"],
                decision="PASS" if row["judge"]["safe_to_use"] else "REJECT",
                ok="yes" if row["judge_correct"] else "no",
                l1=row["baseline"]["top_doc"],
                l2=row["rewrite"]["top_doc"],
                l3=row["judge"]["top_doc"],
                fb="yes" if row["judge"]["used_fallback"] else "no",
            )
        )
    lines.extend(["", "## Findings", ""])
    lines.extend(f"- {item}" for item in test["summary"]["findings"])
    lines.append("")
    return "\n".join(lines)


def _cell(text: str, limit: int = 72) -> str:
    compact = " ".join(text.split())
    if len(compact) > limit:
        compact = compact[: limit - 1] + "…"
    return compact.replace("|", "/")


def _findings(summary: dict, judge_summary: dict, ambiguous: dict) -> list[str]:
    base = summary["baseline"]["hit_at_1"]
    rewrite = summary["rewrite"]["hit_at_1"]
    judged = summary["judge"]["hit_at_1"]
    reach_2 = summary["rewrite"]["harmful_reach_rate"]
    reach_3 = summary["judge"]["harmful_reach_rate"]
    return [
        f"On the held-out test queries, Hit@1 is {base:.3f} for Level 1, {rewrite:.3f} for Level 2, and {judged:.3f} for Level 3.",
        f"Harmful rewrites reach the retriever on {reach_2:.0%} of harmful test queries at Level 2 and {reach_3:.0%} at Level 3.",
        (
            f"Test HRDR is {judge_summary['hrdr']:.3f}, harmful false acceptance is "
            f"{judge_summary['harmful_false_acceptance_rate']:.3f}, and safe rewrite rejection is "
            f"{judge_summary['safe_rewrite_rejection_rate']:.3f}."
        ),
        (
            f"On ambiguous test rewrites, accuracy against the preferred label is "
            f"{ambiguous['ambiguous_accuracy']:.3f} and macro F1 is {ambiguous['ambiguous_macro_f1']:.3f}."
        ),
        "Semantic equivalents such as '14 days' and 'two weeks' are labeled safe. A slot judge that requires the same digits will reject them, and that rejection is counted in the safe rewrite rejection rate.",
    ]


def run(judge_only: bool = False) -> dict:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import os

    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    benchmark = _load_benchmark()
    llm = LLMClient()
    judge = QueryJudge(llm)
    scored = evaluate_judge(judge, benchmark["items"])
    by_id = {case["id"]: case for case in scored}
    dev_cases = [case for case in scored if case["split"] == "dev"]
    test_cases = [case for case in scored if case["split"] == "test"]
    dev_rates = judge_rates(dev_cases)
    test_rates = judge_rates(test_cases)
    dev_ambiguous = ambiguous_scores(dev_cases)
    test_ambiguous = ambiguous_scores(test_cases)
    print(
        "TEST  HRDR={hrdr:.3f}  false_acceptance={far:.3f}  safe_rejection={rej:.3f}  "
        "ambiguous_acc={acc:.3f}  ambiguous_f1={f1:.3f}".format(
            hrdr=test_rates["hrdr"],
            far=test_rates["harmful_false_acceptance_rate"],
            rej=test_rates["safe_rewrite_rejection_rate"],
            acc=test_ambiguous["ambiguous_accuracy"],
            f1=test_ambiguous["ambiguous_macro_f1"],
        )
    )
    print(
        "DEV   HRDR={hrdr:.3f}  false_acceptance={far:.3f}  safe_rejection={rej:.3f}  "
        "ambiguous_acc={acc:.3f}  ambiguous_f1={f1:.3f}".format(
            hrdr=dev_rates["hrdr"],
            far=dev_rates["harmful_false_acceptance_rate"],
            rej=dev_rates["safe_rewrite_rejection_rate"],
            acc=dev_ambiguous["ambiguous_accuracy"],
            f1=dev_ambiguous["ambiguous_macro_f1"],
        )
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if judge_only:
        report = {
            "meta": benchmark["meta"],
            "test": {"judge": test_rates, "ambiguous": test_ambiguous, "by_category": category_rates(test_cases)},
            "dev": {"judge": dev_rates, "ambiguous": dev_ambiguous, "by_category": category_rates(dev_cases)},
            "cases": scored,
        }
        (RESULTS_DIR / "judge_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    print("Loading embedding model and building the FAISS index...")
    from src.system import build_runtime

    runtime = build_runtime()
    print(f"Indexed {len(runtime.retriever.chunks)} chunks with {runtime.embedder.model_name}.")
    rewriter = QueryRewriter(runtime.llm)
    rows = []
    for item in benchmark["items"]:
        produced = RewriteResult(
            original_query=item["query"],
            rewritten_query=item["rewrite"],
            failure_mode="harmful" if item["label"] == "harmful" else None,
        )
        baseline = run_baseline(item["query"], runtime.retriever, runtime.generator, RETRIEVE_K)
        rewritten = run_rewrite(
            item["query"],
            runtime.retriever,
            runtime.generator,
            rewriter,
            rewrite=produced,
            retrieve_k=RETRIEVE_K,
        )
        judged = run_judge(
            item["query"],
            runtime.retriever,
            runtime.generator,
            rewriter,
            runtime.judge,
            rewrite=produced,
            retrieve_k=RETRIEVE_K,
        )
        gold = item["gold_doc_ids"]
        facts = item["expected_facts"]
        decision = by_id[item["id"]]
        rows.append(
            {
                "id": item["id"],
                "split": item["split"],
                "label": item["label"],
                "query": item["query"],
                "category": item["category"],
                "note": item["note"],
                "gold_doc_ids": gold,
                "expected_facts": facts,
                "expected_safe": item["expected_safe"],
                "expected_failure_mode": produced.failure_mode,
                "rewritten_query": produced.rewritten_query,
                "failure_mode": produced.failure_mode,
                "judge_correct": decision["correct"],
                "judge": judged.judge_decision,
                "baseline": _result_view(baseline, gold, facts),
                "rewrite": _result_view(rewritten, gold, facts),
                "judge_level": _result_view(judged, gold, facts),
            }
        )

    for row in rows:
        row["judge"] = {
            **row["judge_level"],
            "safe_to_use": row["judge"]["safe_to_use"],
            "decision": row["judge"],
        }

    def pack(split_name: str, rates: dict, ambiguous: dict, cases: list[dict]) -> dict:
        split_rows = [row for row in rows if row["split"] == split_name]
        summary = {
            "baseline": _level_means(split_rows, "baseline"),
            "rewrite": _level_means(split_rows, "rewrite"),
            "judge": _level_means(split_rows, "judge"),
            "n": len(split_rows),
            "answer_k": ANSWER_K,
            "retrieve_k": RETRIEVE_K,
            "provider": runtime.llm.provider,
        }
        by_label = {}
        for label in ("safe", "harmful", "ambiguous"):
            subset = [row for row in split_rows if row["label"] == label]
            by_label[label] = {
                "n": len(subset),
                "baseline": mean([row["baseline"]["hit_at_1"] for row in subset]),
                "rewrite": mean([row["rewrite"]["hit_at_1"] for row in subset]),
                "judge": mean([row["judge"]["hit_at_1"] for row in subset]),
            }
        summary["findings"] = _findings(summary, rates, ambiguous)
        return {
            "summary": summary,
            "judge": rates,
            "ambiguous": ambiguous,
            "by_label": by_label,
            "by_category": category_rates(cases),
            "rows": split_rows,
        }

    bundle = {
        "meta": benchmark["meta"],
        "test": pack("test", test_rates, test_ambiguous, test_cases),
        "dev": pack("dev", dev_rates, dev_ambiguous, dev_cases),
    }
    (RESULTS_DIR / "comparison.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    (RESULTS_DIR / "judge_report.json").write_text(
        json.dumps(
            {
                "meta": benchmark["meta"],
                "test": {"judge": test_rates, "ambiguous": test_ambiguous},
                "dev": {"judge": dev_rates, "ambiguous": dev_ambiguous},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = _markdown(bundle)
    (RESULTS_DIR / "comparison.md").write_text(report, encoding="utf-8")
    print()
    print(report)
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the three RAG levels.")
    parser.add_argument(
        "--judge-only",
        action="store_true",
        help="Score the judge without loading the embedding model.",
    )
    args = parser.parse_args()
    run(judge_only=args.judge_only)


if __name__ == "__main__":
    main()
