"""Build the three levels so they share one index and one embedder."""

from __future__ import annotations

from dataclasses import dataclass

from src.config import DATA_DIR, JUDGE_BACKEND
from src.embeddings import Embedder
from src.generator import Generator
from src.llm import LLMClient
from src.query_judge import QueryJudge
from src.query_rewriter import QueryRewriter
from src.retriever import FaissRetriever, build_retriever


@dataclass
class Runtime:
    embedder: Embedder
    retriever: FaissRetriever
    generator: Generator
    rewriter: QueryRewriter
    judge: QueryJudge
    llm: LLMClient


def build_runtime() -> Runtime:
    llm = LLMClient()
    embedder = Embedder()
    retriever = build_retriever(DATA_DIR, embedder)
    return Runtime(
        embedder=embedder,
        retriever=retriever,
        generator=Generator(llm),
        rewriter=QueryRewriter(llm),
        judge=QueryJudge(llm, backend=JUDGE_BACKEND),
        llm=llm,
    )
