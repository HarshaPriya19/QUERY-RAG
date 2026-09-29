"""Equivalence normalization shared by the rewriter and the judge.

The judge compares a normalized form of both queries. Format changes, catalog
abbreviations, typos, and true paraphrases collapse to the same tokens.
Failure modes are not implemented here. This module only describes equivalents.
"""

from __future__ import annotations

import re

# Longer aliases first. "the pro" is the short sibling name in this catalog.
ALIAS_PATTERNS: list[tuple[str, str]] = [
    (r"\bnb\s+pro\b", "novabook pro"),
    (r"\bnb\s+air\b", "novabook air"),
    (r"\bn\.?\s*b\.?\s+pro\b", "novabook pro"),
    (r"\bn\.?\s*b\.?\s+air\b", "novabook air"),
    (r"\bpixel\s+tab\b", "pixeltab"),
    (r"\bpt\b", "pixeltab"),
    (r"\bnot the pro\b", "not the novabook pro"),
    (r"\bnot the air\b", "not the novabook air"),
    (r"\bthe pro\b", "the novabook pro"),
    (r"\bthe air\b", "the novabook air"),
]

# Typos and paraphrases that preserve meaning.
SYNONYM_PATTERNS: list[tuple[str, str]] = [
    (r"\bwarrenty\b", "warranty"),
    (r"\bwarranties\b", "warranty"),
    (r"\bguarantees?\b", "warranty"),
    (r"\brefrubished\b", "refurbished"),
    (r"\bgift vouchers?\b", "gift card"),
    (r"\bsend back\b", "return"),
    (r"\bgive back\b", "return"),
    (r"\bstudent deals?\b", "student discount"),
    (r"\bexpiry\b", "expiration"),
    (r"\bexpires\b", "expiration"),
    (r"\bexpiration\b", "expiration"),
    (r"\bless than\b", "under"),
    (r"\bbelow\b", "under"),
    (r"\bmore than\b", "over"),
    (r"\bgreater than\b", "over"),
    (r"\babove\b", "over"),
    (r"\bearlier than\b", "before"),
    (r"\bprior to\b", "before"),
    (r"\blater than\b", "after"),
    (r"\bexcluding\b", "except"),
    (r"\bother than\b", "except"),
    (r"\bno less than\b", "at least"),
    (r"\bat least\b", "at least"),
    (r"\bminimum\b", "at least"),
    (r"\bno more than\b", "at most"),
    (r"\bat most\b", "at most"),
    (r"\bmaximum\b", "at most"),
    (r"\bper cent\b", "%"),
    (r"\bpercent\b", "%"),
    (r"\breturnable\b", "return"),
    (r"\breturned\b", "return"),
    (r"\breturning\b", "return"),
    (r"\breturns\b", "return"),
    (r"\bfiled\b", "file"),
    (r"\bfiling\b", "file"),
    (r"\bdays\b", "day"),
    (r"\bmonths\b", "month"),
    (r"\byears\b", "year"),
    (r"\bwindows\b", "window"),
    (r"\bclaims\b", "claim"),
    (r"\blaptops\b", "laptop"),
    (r"\bphones\b", "phone"),
    (r"\borders\b", "order"),
    (r"\bcards\b", "card"),
    (r"\bislands\b", "island"),
    (r"\bunits\b", "unit"),
    (r"\bcustomers\b", "customer"),
    (r"\bdetails\b", "detail"),
]

WORD_NUMBERS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "fourteen": "14",
    "thirty": "30",
}

# Retrieval filler. Adding or dropping these does not by itself fail the judge.
GENERIC_TOKENS = {
    "policy",
    "detail",
    "information",
    "info",
    "duration",
    "period",
    "length",
    "rule",
    "process",
    "question",
    "help",
    "window",
    "time",
    "price",
    "cost",
}

PRODUCT_PARTS = {"novabook", "air", "pro", "pixeltab"}

PRODUCTS = ("novabook air", "novabook pro", "pixeltab", "novabook")

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "to",
    "for",
    "of",
    "on",
    "in",
    "and",
    "or",
    "how",
    "what",
    "when",
    "where",
    "who",
    "why",
    "can",
    "i",
    "do",
    "does",
    "me",
    "my",
    "we",
    "you",
    "please",
    "tell",
    "need",
    "want",
    "with",
    "from",
    "by",
    "at",
    "it",
    "this",
    "that",
    "about",
    "into",
    "am",
    "our",
    "your",
    "could",
    "would",
    "should",
    "just",
    "really",
    "very",
    "also",
    "there",
    "have",
    "has",
    "had",
    "been",
    "being",
    "if",
    "than",
    "then",
    "so",
    "as",
    "its",
}

NEGATION_TOKENS = {
    "not",
    "no",
    "never",
    "without",
    "except",
    "excluding",
    "cannot",
    "cant",
    "dont",
    "doesnt",
    "isnt",
    "non",
}

MONTHS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}

_NEGATION_RE = re.compile(
    r"\b(?:not|no|never|without|except|cannot|can't|cant|don't|dont|doesn't|doesnt|isn't|isnt)\b"
    r"|\bnon-\w+",
    re.IGNORECASE,
)


def apply_patterns(text: str, patterns: list[tuple[str, str]]) -> str:
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def pretty_products(text: str) -> str:
    text = re.sub(r"\bnovabook pro\b", "NovaBook Pro", text, flags=re.IGNORECASE)
    text = re.sub(r"\bnovabook air\b", "NovaBook Air", text, flags=re.IGNORECASE)
    text = re.sub(r"\bpixeltab\b", "PixelTab", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_compare(text: str) -> str:
    """Lowercase form used only to compare two queries."""
    text = text.lower().replace("’", "'")
    text = text.replace("₹", " ")
    text = re.sub(r"[?!;:()\"']", " ", text)
    text = re.sub(r"\brs\.?\s*", " ", text)
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(
        r"\b(\d+)\s*k\b",
        lambda match: str(int(match.group(1)) * 1000),
        text,
    )
    for word, number in WORD_NUMBERS.items():
        text = re.sub(rf"\b{word}\b", number, text)
    text = apply_patterns(text, ALIAS_PATTERNS)
    text = apply_patterns(text, SYNONYM_PATTERNS)
    text = re.sub(r"\b(\d+)\s*-\s*day\b", r"\1 day", text)
    text = re.sub(r"(\d)\s+%", r"\1%", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def has_negation(text: str) -> bool:
    """True when the query negates something.

    Phrases such as "no less than" are constraints, not negations, and are
    rewritten to "at least" before this check.
    """
    scrubbed = re.sub(r"\bno less than\b", "at least", text)
    scrubbed = re.sub(r"\bno more than\b", "at most", scrubbed)
    return _NEGATION_RE.search(scrubbed) is not None


def extract_products(text: str) -> set[str]:
    found: set[str] = set()
    occupied = [False] * len(text)
    for name in sorted(PRODUCTS, key=len, reverse=True):
        start = 0
        while True:
            index = text.find(name, start)
            if index < 0:
                break
            end = index + len(name)
            before = text[index - 1] if index > 0 else " "
            after = text[end] if end < len(text) else " "
            span_free = not any(occupied[index:end])
            if span_free and not before.isalnum() and not after.isalnum():
                # A bare "novabook" is the family name. A specific model already
                # covers that mention, so the family name is not a second entity.
                if name != "novabook":
                    found.add(name)
                elif "novabook air" not in found and "novabook pro" not in found:
                    # Only keep the family name when no specific model is present
                    # anywhere; a later specific match will replace this.
                    found.add(name)
                for position in range(index, end):
                    occupied[position] = True
            start = index + 1
    if "novabook air" in found or "novabook pro" in found:
        found.discard("novabook")
    return found


def extract_numbers(text: str) -> set[str]:
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", text))
    raw = re.findall(r"\b\d+(?:\.\d+)?%?", text)
    numbers = set()
    for token in raw:
        bare = token[:-1] if token.endswith("%") else token
        if token in years or bare in years:
            continue
        numbers.add(token)
    return numbers


def extract_years(text: str) -> set[str]:
    return set(re.findall(r"\b(?:19|20)\d{2}\b", text))


def extract_months(text: str) -> set[str]:
    """Month names. 'may' counts only next to a number so the verb 'may' is ignored."""
    found: set[str] = set()
    pattern = r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b"
    for match in re.finditer(pattern, text):
        month = match.group(1)
        if month == "may":
            window = text[max(0, match.start() - 8) : match.end() + 8]
            if not re.search(r"\b\d{1,4}\b", window):
                continue
        found.add(month)
    return found


def content_tokens(text: str, *, drop_products: bool) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9%]+", text))
    cleaned = set()
    for token in tokens:
        if token in STOPWORDS or token in NEGATION_TOKENS:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?%?", token):
            continue
        if drop_products and token in PRODUCT_PARTS:
            continue
        if token in MONTHS or re.fullmatch(r"(?:19|20)\d{2}", token):
            continue
        cleaned.add(token)
    return cleaned
