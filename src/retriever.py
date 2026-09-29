"""FAISS inner-product index over normalized embeddings (cosine similarity)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.embeddings import Embedder
from src.ingestion import chunk_documents, load_documents
from src.types import Chunk, RetrievedChunk


class FaissRetriever:
    def __init__(self, chunks: list[Chunk], embedder: Embedder) -> None:
        if not chunks:
            raise ValueError("Cannot build a retriever with no chunks.")
        self.chunks = chunks
        self.embedder = embedder
        self.vectors = embedder.embed([chunk.text for chunk in chunks])
        self._index = self._build_index(self.vectors)

    @staticmethod
    def _build_index(vectors: np.ndarray):
        try:
            import faiss
        except ImportError:
            return None
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return index

    def search(self, query: str, k: int = 3) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        query_vector = self.embedder.embed([query])
        k = max(1, min(k, len(self.chunks)))
        if self._index is not None:
            scores, indices = self._index.search(query_vector, k)
            pairs = list(zip(indices[0].tolist(), scores[0].tolist()))
        else:
            scores = (self.vectors @ query_vector.T).reshape(-1)
            order = np.argsort(-scores)[:k]
            pairs = [(int(index), float(scores[index])) for index in order]

        hits: list[RetrievedChunk] = []
        for rank, (index, score) in enumerate(pairs, start=1):
            if index < 0:
                continue
            hits.append(
                RetrievedChunk(chunk=self.chunks[index], score=float(score), rank=rank)
            )
        return hits


def build_retriever(data_dir: Path, embedder: Embedder) -> FaissRetriever:
    documents = load_documents(data_dir)
    chunks = chunk_documents(documents)
    return FaissRetriever(chunks, embedder)
