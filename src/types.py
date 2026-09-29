"""Shared records passed between pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Document:
    doc_id: str
    title: str
    text: str
    source: str


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    source: str


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float
    rank: int


@dataclass
class RewriteResult:
    original_query: str
    rewritten_query: str
    failure_mode: str | None = None


@dataclass
class RAGResult:
    level: str
    original_query: str
    rewritten_query: str | None
    retrieval_query: str
    judge_decision: dict | None
    used_fallback: bool
    failure_mode: str | None
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    answer: str = ""
