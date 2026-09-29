"""Query rewriter.

The public behavior is an LLM rewrite that should preserve meaning and become
easier to retrieve. Without an API key, LocalRewriter performs the same helpful
normalization and then applies a few documented failure modes. Those failure
modes are the controlled risk in this experiment. They are general rules, not
a lookup table of evaluation query ids.

Set REWRITER_FAILURES=0 to keep only the helpful normalization.
"""

from __future__ import annotations

import re

from src.config import REWRITER_FAILURES
from src.llm import LLMClient
from src.text_norm import ALIAS_PATTERNS, apply_patterns, pretty_products
from src.types import RewriteResult

REWRITER_SYSTEM = """You rewrite a user question into one short search query for a product-policy knowledge base.
Preserve the original intent.
Preserve every entity, number, price, date, year, negation, and explicit constraint.
Do not add facts, products, or assumptions that the user did not state.
Do not drop words such as not, without, except, only, under, over, before, after, or since.
You may fix typos, expand known abbreviations (NB = NovaBook, PT = PixelTab), and replace wording with catalog terms:
send back = return, student deal = student discount, gift voucher = gift card, warrenty = warranty.
Return only the rewritten query, with no explanation."""

# Helpful rewrites only. Equivalence maps used solely by the judge stay in text_norm.
RETRIEVAL_PATTERNS: list[tuple[str, str]] = [
    (r"\bwarrenty\b", "warranty"),
    (r"\brefrubished\b", "refurbished"),
    (r"\bguarantees?\b", "warranty"),
    (r"\bgift vouchers?\b", "gift card"),
    (r"\bsend back\b", "return"),
    (r"\bgive back\b", "return"),
    (r"\bstudent deals?\b", "student discount"),
    (r"\bexpiry\b", "expiration"),
    (r"\bexpires\b", "expiration"),
]


def _helpful(query: str) -> str:
    text = query.strip()
    text = re.sub(r"\?+", "", text)
    text = re.sub(
        r"^(please|could you|can you|tell me|i want to know)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = apply_patterns(text, ALIAS_PATTERNS)
    text = apply_patterns(text, RETRIEVAL_PATTERNS)
    return pretty_products(text)


def _apply_failure_modes(original: str, helpful: str) -> tuple[str, str | None]:
    """Imitate rewriter mistakes that change what the retriever should do.

    Each rule is linguistic. It does not check the evaluation-set id.
    """
    # Negation inversion: "X, not the Pro" is rewritten as if the user asked for Pro.
    inverted = re.search(
        r"\bnot the\s+(pro|air|pixeltab)\b",
        original,
        flags=re.IGNORECASE,
    )
    if inverted:
        target = {
            "pro": "NovaBook Pro",
            "air": "NovaBook Air",
            "pixeltab": "PixelTab",
        }[inverted.group(1).lower()]
        return f"{target} policy details", "negation_inversion"

    # Both sibling laptops mentioned, and the user did not negate one of them.
    # The buggy rewriter "simplifies" to the Pro and drops the Air.
    mentions_air = re.search(r"\bnovabook air\b", helpful, flags=re.IGNORECASE)
    mentions_pro = re.search(r"\bnovabook pro\b", helpful, flags=re.IGNORECASE)
    if mentions_air and mentions_pro:
        dropped = re.sub(r"\bnovabook air\b", "", helpful, flags=re.IGNORECASE)
        dropped = re.sub(r"\band\b", " ", dropped, flags=re.IGNORECASE)
        dropped = re.sub(r"\bthe\s+the\b", "the", dropped, flags=re.IGNORECASE)
        dropped = re.sub(r"\s+", " ", dropped).strip(" ,")
        return pretty_products(dropped), "dropped_sibling_entity"

    # A trailing "except ..." / "but not ..." clause is cut off.
    parts = re.split(
        r",\s*(?:except|but not|and not)\b",
        helpful,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    if len(parts) == 2 and parts[0].strip():
        return parts[0].strip(), "dropped_trailing_constraint"

    # "only" is treated as a stopword, which widens the query.
    if re.search(r"\bonly\b", helpful, flags=re.IGNORECASE):
        widened = re.sub(r"\bonly\b", "", helpful, count=1, flags=re.IGNORECASE)
        widened = re.sub(r"\s+", " ", widened).strip()
        return widened, "dropped_only"

    # "since YEAR" is shifted back one year and the relation word is removed.
    year_match = re.search(r"\bsince\s+((?:19|20)\d{2})\b", helpful, flags=re.IGNORECASE)
    if year_match:
        year = int(year_match.group(1))
        shifted = re.sub(
            r"\bsince\s+" + re.escape(year_match.group(1)),
            str(year - 1),
            helpful,
            count=1,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", shifted).strip(), "date_off_by_one"

    return helpful, None


class QueryRewriter:
    def __init__(self, llm: LLMClient, enable_failures: bool | None = None) -> None:
        self.llm = llm
        self.enable_failures = REWRITER_FAILURES if enable_failures is None else enable_failures

    def rewrite(self, query: str) -> RewriteResult:
        original = query.strip()
        if self.llm.uses_api:
            rewritten = self.llm.complete(REWRITER_SYSTEM, original).strip().strip('"')
            return RewriteResult(original, rewritten, failure_mode=None)

        helpful = _helpful(original)
        if not self.enable_failures:
            return RewriteResult(original, helpful, failure_mode=None)
        rewritten, failure_mode = _apply_failure_modes(original, helpful)
        return RewriteResult(original, rewritten, failure_mode=failure_mode)
