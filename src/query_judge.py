"""Intent-preservation judge.

This is not a similarity check. Two queries can share most of their words and
still be unsafe for retrieval if a number, date, entity, negation, or
constraint changed. Minor wording, abbreviations, typos, and format changes
are accepted so the judge does not reject useful rewrites.

The decision is the boolean safe_to_use. The reason is an explanation of the
failed factors, not a substitute for them.
"""

from __future__ import annotations

import json
import re

from src.llm import LLMClient
from src.text_norm import (
    GENERIC_TOKENS,
    content_tokens,
    extract_months,
    extract_numbers,
    extract_products,
    extract_years,
    has_negation,
    normalize_for_compare,
)

_OPS: list[tuple[str, str]] = [
    ("under", r"\bunder\b"),
    ("over", r"\bover\b"),
    ("at_least", r"\bat least\b"),
    ("at_most", r"\bat most\b"),
    ("before", r"\bbefore\b"),
    ("after", r"\bafter\b"),
    ("since", r"\bsince\b"),
    ("until", r"\buntil\b"),
    ("only", r"\bonly\b"),
    ("except", r"\bexcept\b"),
    ("without", r"\bwithout\b"),
]

_SCOPE = ("only", "all", "any", "every")

# These words are judged by the constraint, scope, date, or entity checks.
_SLOT_WORDS = {
    "under",
    "over",
    "least",
    "most",
    "before",
    "after",
    "since",
    "until",
    "only",
    "except",
    "without",
    "all",
    "any",
    "every",
}

_DATE_RELS = (
    ("before", r"\bbefore\b"),
    ("after", r"\bafter\b"),
    ("since", r"\bsince\b"),
    ("until", r"\buntil\b"),
)

LLM_JUDGE_SYSTEM = """You judge whether a rewritten search query is safe to send to a retriever.
Do not decide from overall similarity. Score each factor from the original query and the rewrite.
Rules:
- Minor wording changes are acceptable when the intent is the same.
- Critical entities must not be changed.
- Important numbers must not be changed.
- Important dates and time periods must not be changed.
- Negation must not be removed or reversed.
- Explicit constraints must not be removed.
- Unsupported assumptions must be rejected when they can change retrieval.
- If critical information is lost, reject the rewrite even if the wording looks similar.
Return only JSON with these boolean fields and a short reason string:
intent_preserved, entities_preserved, constraints_preserved, numbers_preserved,
dates_preserved, negation_preserved, scope_preserved, unsupported_additions,
critical_information_lost, safe_to_use, reason.
safe_to_use must be false if any preservation field is false or if
unsupported_additions or critical_information_lost is true."""

_REQUIRED_KEYS = (
    "intent_preserved",
    "entities_preserved",
    "constraints_preserved",
    "numbers_preserved",
    "dates_preserved",
    "negation_preserved",
    "scope_preserved",
    "unsupported_additions",
    "critical_information_lost",
    "safe_to_use",
    "reason",
)


def _ops(text: str) -> set[str]:
    return {name for name, pattern in _OPS if re.search(pattern, text)}


def _scope(text: str) -> set[str]:
    return {word for word in _SCOPE if re.search(rf"\b{word}\b", text)}


def _bindings(text: str) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for name, pattern in _DATE_RELS:
        for match in re.finditer(pattern, text):
            window = text[match.end() : match.end() + 24]
            year = re.search(r"\b(?:19|20)\d{2}\b", window)
            if year:
                found.add((name, year.group(0)))
    return found


def _meaningful(text: str) -> set[str]:
    return content_tokens(text, drop_products=True) - GENERIC_TOKENS - _SLOT_WORDS


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _entities_preserved(original: set[str], rewritten: set[str]) -> bool:
    if original <= rewritten:
        return True
    missing = original - rewritten
    # "NovaBook" is preserved when the rewrite still names Air or Pro.
    if missing == {"novabook"} and ({"novabook air", "novabook pro"} & rewritten):
        return True
    return False


def _fmt(values: set) -> str:
    if not values:
        return "none"
    return ", ".join(str(value) for value in sorted(values, key=str))


def rule_judge(original: str, rewritten: str) -> dict:
    """Explicit factor rules. The JSON decision does not depend on free text."""
    if not rewritten or not rewritten.strip():
        return _decision(
            intent_preserved=False,
            entities_preserved=False,
            constraints_preserved=False,
            numbers_preserved=False,
            dates_preserved=False,
            negation_preserved=False,
            scope_preserved=False,
            unsupported_additions=False,
            critical_information_lost=True,
            reasons=["The rewrite is empty."],
        )

    original_norm = normalize_for_compare(original)
    rewritten_norm = normalize_for_compare(rewritten)

    if original_norm == rewritten_norm:
        return _decision(
            intent_preserved=True,
            entities_preserved=True,
            constraints_preserved=True,
            numbers_preserved=True,
            dates_preserved=True,
            negation_preserved=True,
            scope_preserved=True,
            unsupported_additions=False,
            critical_information_lost=False,
            reasons=[],
        )

    original_products = extract_products(original_norm)
    rewritten_products = extract_products(rewritten_norm)
    original_numbers = extract_numbers(original_norm)
    rewritten_numbers = extract_numbers(rewritten_norm)
    original_years = extract_years(original_norm)
    rewritten_years = extract_years(rewritten_norm)
    original_months = extract_months(original_norm)
    rewritten_months = extract_months(rewritten_norm)
    original_ops = _ops(original_norm)
    rewritten_ops = _ops(rewritten_norm)
    original_scope = _scope(original_norm)
    rewritten_scope = _scope(rewritten_norm)
    original_bindings = _bindings(original_norm)
    rewritten_bindings = _bindings(rewritten_norm)
    original_neg = has_negation(original_norm)
    rewritten_neg = has_negation(rewritten_norm)
    lost_content = _meaningful(original_norm) - _meaningful(rewritten_norm)
    added_content = _meaningful(rewritten_norm) - _meaningful(original_norm)

    intent_preserved = _overlap(
        content_tokens(original_norm, drop_products=False),
        content_tokens(rewritten_norm, drop_products=False),
    ) >= 0.5
    entities_preserved = _entities_preserved(original_products, rewritten_products)
    constraints_preserved = original_ops == rewritten_ops
    numbers_preserved = original_numbers == rewritten_numbers
    dates_preserved = (
        original_years == rewritten_years
        and original_months == rewritten_months
        and original_bindings == rewritten_bindings
    )
    negation_preserved = original_neg == rewritten_neg
    scope_preserved = original_scope == rewritten_scope

    unsupported_additions = bool(
        (rewritten_products - original_products)
        or (rewritten_numbers - original_numbers)
        or (rewritten_years - original_years)
        or (rewritten_months - original_months)
        or (rewritten_ops - original_ops)
        or (rewritten_bindings - original_bindings)
        or (rewritten_scope - original_scope)
        or (rewritten_neg and not original_neg)
        or added_content
    )
    critical_information_lost = bool(
        (original_products - rewritten_products)
        or (original_numbers - rewritten_numbers)
        or (original_years - rewritten_years)
        or (original_months - rewritten_months)
        or (original_ops - rewritten_ops)
        or (original_bindings - rewritten_bindings)
        or (original_scope - rewritten_scope)
        or (original_neg and not rewritten_neg)
        or lost_content
    )

    reasons: list[str] = []
    if not entities_preserved:
        reasons.append(
            "A critical entity was changed or removed "
            f"({_fmt(original_products)} -> {_fmt(rewritten_products)})."
        )
    if not numbers_preserved:
        reasons.append(
            "A quantity, price, or limit changed "
            f"({_fmt(original_numbers)} -> {_fmt(rewritten_numbers)})."
        )
    if not dates_preserved:
        reasons.append(
            "A date, year, or time period changed "
            f"(years {_fmt(original_years)} -> {_fmt(rewritten_years)})."
        )
    if not negation_preserved:
        reasons.append("Negation was removed, added, or reversed.")
    if not constraints_preserved:
        reasons.append(
            "An explicit constraint changed "
            f"({_fmt(original_ops)} -> {_fmt(rewritten_ops)})."
        )
    if not scope_preserved:
        reasons.append(
            f"Scope changed ({_fmt(original_scope)} -> {_fmt(rewritten_scope)})."
        )
    if lost_content:
        reasons.append(
            "The rewrite drops information that could change retrieval: "
            f"{_fmt(lost_content)}."
        )
    if added_content or (rewritten_products - original_products):
        extra = added_content | {
            product for product in (rewritten_products - original_products)
        }
        reasons.append(
            "The rewrite introduces information that was not in the original query: "
            f"{_fmt(extra)}."
        )
    if not intent_preserved:
        reasons.append("The rewrite does not appear to pursue the same request.")

    return _decision(
        intent_preserved=intent_preserved,
        entities_preserved=entities_preserved,
        constraints_preserved=constraints_preserved,
        numbers_preserved=numbers_preserved,
        dates_preserved=dates_preserved,
        negation_preserved=negation_preserved,
        scope_preserved=scope_preserved,
        unsupported_additions=unsupported_additions,
        critical_information_lost=critical_information_lost,
        reasons=reasons,
    )


def _decision(**fields) -> dict:
    reasons: list[str] = fields.pop("reasons")
    safe = (
        fields["intent_preserved"]
        and fields["entities_preserved"]
        and fields["constraints_preserved"]
        and fields["numbers_preserved"]
        and fields["dates_preserved"]
        and fields["negation_preserved"]
        and fields["scope_preserved"]
        and not fields["unsupported_additions"]
        and not fields["critical_information_lost"]
    )
    failed = []
    for name, value in fields.items():
        added_or_lost = name in {"unsupported_additions", "critical_information_lost"}
        if (added_or_lost and value) or (not added_or_lost and not value):
            failed.append(name)
    return {
        **fields,
        "safe_to_use": safe,
        "reason": (
            "Minor wording changes only. Retrieval-critical details are preserved."
            if safe
            else " ".join(reasons)
        ),
        "failed_factors": failed,
    }


def _parse_llm_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Judge response did not contain JSON.")
    data = json.loads(text[start : end + 1])
    missing = [key for key in _REQUIRED_KEYS if key not in data]
    if missing:
        raise ValueError(f"Judge JSON missing keys: {missing}")
    decision = {key: bool(data[key]) if key != "reason" else str(data[key]) for key in _REQUIRED_KEYS}
    decision["failed_factors"] = [
        key
        for key in _REQUIRED_KEYS
        if key not in {"safe_to_use", "reason"}
        and (
            (key in {"unsupported_additions", "critical_information_lost"} and decision[key])
            or (key not in {"unsupported_additions", "critical_information_lost"} and not decision[key])
        )
    ]
    return decision


class QueryJudge:
    def __init__(self, llm: LLMClient | None = None, backend: str = "rules") -> None:
        self.llm = llm
        self.backend = backend

    def judge(self, original: str, rewritten: str) -> dict:
        if (
            self.backend == "llm"
            and self.llm is not None
            and self.llm.uses_api
        ):
            try:
                raw = self.llm.complete(
                    LLM_JUDGE_SYSTEM,
                    f"Original query: {original}\nRewritten query: {rewritten}",
                )
                return _parse_llm_json(raw)
            except (RuntimeError, ValueError, json.JSONDecodeError):
                decision = rule_judge(original, rewritten)
                decision["reason"] = (
                    "LLM judge was unavailable, so the rule judge decided. "
                    + decision["reason"]
                )
                return decision
        return rule_judge(original, rewritten)
