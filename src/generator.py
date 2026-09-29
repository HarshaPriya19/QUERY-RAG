"""Answer from retrieved chunks.

The local generator is extractive: the answer is the retrieved passage. That
keeps faithfulness high and makes answer quality follow retrieval quality.
With LLM_PROVIDER=openai the same context is given to a grounded chat model.
"""

from __future__ import annotations

from src.config import ANSWER_K
from src.llm import LLMClient
from src.types import RetrievedChunk

GENERATOR_SYSTEM = """You answer questions using only the retrieved context.
If the context does not contain the answer, say you do not know.
Do not use outside knowledge. Keep the answer to one or two sentences.
Preserve numbers, dates, names, and negations exactly as they appear in the context."""


class Generator:
    def __init__(self, llm: LLMClient, answer_k: int = ANSWER_K) -> None:
        self.llm = llm
        self.answer_k = answer_k

    def generate(self, query: str, hits: list[RetrievedChunk]) -> str:
        used = hits[: self.answer_k]
        if not used:
            return "No relevant document was retrieved."
        context = "\n\n".join(
            f"[{hit.chunk.doc_id}] {hit.chunk.text.strip()}" for hit in used
        )
        if not self.llm.uses_api:
            return context
        user = f"Question: {query}\n\nContext:\n{context}"
        return self.llm.complete(GENERATOR_SYSTEM, user)
