"""Level 3: rewrite, judge, then retrieve with the rewrite or the original.

If the judge sets safe_to_use, the retriever gets the rewritten query.
Otherwise it gets the original query. The rewrite is not attempted again.
The original query is always what the generator answers.
"""

from __future__ import annotations

from src.config import RETRIEVE_K
from src.generator import Generator
from src.query_judge import QueryJudge
from src.query_rewriter import QueryRewriter
from src.retriever import FaissRetriever
from src.types import RAGResult, RewriteResult


def run_judge(
    query: str,
    retriever: FaissRetriever,
    generator: Generator,
    rewriter: QueryRewriter,
    judge: QueryJudge,
    rewrite: RewriteResult | None = None,
    retrieve_k: int = RETRIEVE_K,
) -> RAGResult:
    original = query.strip()
    produced = rewrite or rewriter.rewrite(original)
    decision = judge.judge(original, produced.rewritten_query)
    if decision["safe_to_use"]:
        retrieval_query = produced.rewritten_query
        used_fallback = False
    else:
        retrieval_query = original
        used_fallback = True
    hits = retriever.search(retrieval_query, k=retrieve_k)
    answer = generator.generate(original, hits)
    return RAGResult(
        level="judge",
        original_query=original,
        rewritten_query=produced.rewritten_query,
        retrieval_query=retrieval_query,
        judge_decision=decision,
        used_fallback=used_fallback,
        failure_mode=produced.failure_mode,
        retrieved=hits,
        answer=answer,
    )
