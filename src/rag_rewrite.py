"""Level 2: rewrite the query, then retrieve with the rewrite.

The original query is kept and is the question sent to the generator.
The retriever sees only the rewritten query.
"""

from __future__ import annotations

from src.config import RETRIEVE_K
from src.generator import Generator
from src.query_rewriter import QueryRewriter
from src.retriever import FaissRetriever
from src.types import RAGResult, RewriteResult


def run_rewrite(
    query: str,
    retriever: FaissRetriever,
    generator: Generator,
    rewriter: QueryRewriter,
    rewrite: RewriteResult | None = None,
    retrieve_k: int = RETRIEVE_K,
) -> RAGResult:
    original = query.strip()
    produced = rewrite or rewriter.rewrite(original)
    hits = retriever.search(produced.rewritten_query, k=retrieve_k)
    # The model still answers the user's original question.
    answer = generator.generate(original, hits)
    return RAGResult(
        level="rewrite",
        original_query=original,
        rewritten_query=produced.rewritten_query,
        retrieval_query=produced.rewritten_query,
        judge_decision=None,
        used_fallback=False,
        failure_mode=produced.failure_mode,
        retrieved=hits,
        answer=answer,
    )
