"""Load local documents and split them into chunks."""

from __future__ import annotations

import re
from pathlib import Path

from src.types import Chunk, Document


def load_documents(data_dir: Path) -> list[Document]:
    paths = sorted(data_dir.glob("*.md")) + sorted(data_dir.glob("*.txt"))
    documents = []
    for path in paths:
        raw = path.read_text(encoding="utf-8").strip()
        title_match = re.search(r"^#\s+(.+)$", raw, flags=re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        documents.append(
            Document(
                doc_id=path.stem,
                title=title,
                text=raw,
                source=str(path),
            )
        )
    if not documents:
        raise FileNotFoundError(f"No documents found in {data_dir}")
    return documents


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 80) -> list[str]:
    """Split on paragraphs, then pack paragraphs up to chunk_size characters."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(paragraph):
                end = min(start + chunk_size, len(paragraph))
                chunks.append(paragraph[start:end].strip())
                if end == len(paragraph):
                    break
                start = max(end - overlap, start + 1)
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = paragraph
    if current:
        chunks.append(current.strip())
    return chunks


def chunk_documents(documents: list[Document], chunk_size: int = 900) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        for index, piece in enumerate(chunk_text(document.text, chunk_size=chunk_size)):
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}::{index}",
                    doc_id=document.doc_id,
                    title=document.title,
                    text=piece,
                    source=document.source,
                )
            )
    return chunks
