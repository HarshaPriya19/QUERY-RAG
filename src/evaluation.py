"""Retrieval, answer, and judge metrics.

Harmful Rewrite Detection Rate (HRDR) is the project-specific judge metric:

    HRDR = harmful rewrites correctly rejected / total harmful rewrites

False acceptance is the share of harmful rewrites the judge lets through.
Useful-rewrite rejection is the share of safe rewrites the judge blocks.
A useful judge is high on HRDR and low on both error rates.
"""

from __future__ import annotations

from src.config import ANSWER_K
from src.types import RAGResult


def retrieved_doc_ids(result: RAGResult) -> list[str]:
    return [hit.chunk.doc_id for hit in result.retrieved]


def answer_passages(result: RAGResult, answer_k: int = ANSWER_K) -> str:
    parts = [hit.chunk.text for hit in result.retrieved[:answer_k]]
    return "\n".join(parts)


def recall_at_k(doc_ids: list[str], gold_doc_ids: list[str], k: int) -> float:
    if not gold_doc_ids:
        return 0.0
    found = set(doc_ids[:k])
    gold = set(gold_doc_ids)
    return len(found & gold) / len(gold)


def hit_at_1(doc_ids: list[str], gold_doc_ids: list[str]) -> float:
    if not doc_ids or not gold_doc_ids:
        return 0.0
    return 1.0 if doc_ids[0] in set(gold_doc_ids) else 0.0


def fact_coverage(text: str, facts: list[str]) -> float:
    if not facts:
        return 1.0
    haystack = text.casefold()
    hits = sum(1 for fact in facts if fact.casefold() in haystack)
    return hits / len(facts)


def faithfulness(answer: str, context: str) -> float:
    """Share of answer words that also appear in the retrieved context."""
    answer_tokens = _tokens(answer)
    context_tokens = _tokens(context)
    if not answer_tokens:
        return 1.0
    return len(answer_tokens & context_tokens) / len(answer_tokens)


def _tokens(text: str) -> set[str]:
    return {token for token in text.casefold().split() if len(token) > 2}


def judge_rates(cases: list[dict]) -> dict:
    """HRDR and the two error rates. Ambiguous cases are not included."""
    decided = [case for case in cases if case.get("label") in {None, "safe", "harmful"}]
    if any(case.get("label") for case in cases):
        harmful = [case for case in cases if case.get("label") == "harmful"]
        useful = [case for case in cases if case.get("label") == "safe"]
    else:
        harmful = [case for case in decided if not case["expected_safe"]]
        useful = [case for case in decided if case["expected_safe"]]
    harmful_rejected = sum(1 for case in harmful if not case["safe_to_use"])
    harmful_accepted = sum(1 for case in harmful if case["safe_to_use"])
    useful_rejected = sum(1 for case in useful if not case["safe_to_use"])
    return {
        "harmful_total": len(harmful),
        "useful_total": len(useful),
        "hrdr": _ratio(harmful_rejected, len(harmful)),
        "harmful_false_acceptance_rate": _ratio(harmful_accepted, len(harmful)),
        "useful_rewrite_rejection_rate": _ratio(useful_rejected, len(useful)),
        "safe_rewrite_rejection_rate": _ratio(useful_rejected, len(useful)),
    }


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def ambiguous_scores(cases: list[dict]) -> dict:
    """Accuracy and macro F1 against the preferred label on ambiguous rewrites.

    Positive class for the reject F1 is 'block the rewrite'. Macro F1 averages
    that with the F1 of 'allow the rewrite'.
    """
    ambiguous = [case for case in cases if case.get("label") == "ambiguous"]
    if not ambiguous:
        return {
            "ambiguous_total": 0,
            "ambiguous_accuracy": 0.0,
            "ambiguous_f1_reject": 0.0,
            "ambiguous_f1_accept": 0.0,
            "ambiguous_macro_f1": 0.0,
        }
    tp = sum(1 for case in ambiguous if not case["expected_safe"] and not case["safe_to_use"])
    fp = sum(1 for case in ambiguous if case["expected_safe"] and not case["safe_to_use"])
    fn = sum(1 for case in ambiguous if not case["expected_safe"] and case["safe_to_use"])
    tn = sum(1 for case in ambiguous if case["expected_safe"] and case["safe_to_use"])
    f1_reject = _f1(tp, fp, fn)
    f1_accept = _f1(tn, fn, fp)
    return {
        "ambiguous_total": len(ambiguous),
        "ambiguous_accuracy": _ratio(tp + tn, len(ambiguous)),
        "ambiguous_f1_reject": f1_reject,
        "ambiguous_f1_accept": f1_accept,
        "ambiguous_macro_f1": (f1_reject + f1_accept) / 2,
    }


def category_rates(cases: list[dict]) -> dict[str, dict]:
    grouped: dict[str, list] = {}
    for case in cases:
        grouped.setdefault(case.get("category") or "uncategorized", []).append(case)
    return {name: {**judge_rates(group), **ambiguous_scores(group)} for name, group in sorted(grouped.items())}


def harmful_reach_rate(rows: list[dict], level: str) -> float:
    """Share of known-harmful rewrites that were actually sent to the retriever."""
    harmful = [row for row in rows if row.get("expected_failure_mode")]
    if not harmful:
        return 0.0
    reached = 0
    for row in harmful:
        retrieval_query = row[level]["retrieval_query"]
        original = row["query"]
        if retrieval_query.strip() != original.strip():
            reached += 1
    return reached / len(harmful)


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
