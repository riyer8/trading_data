"""Lightweight RAG over the project README for tool discovery and Q&A context."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_README = PROJECT_ROOT / "README.md"

_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    title: str
    text: str
    category: str
    run_command: str | None = None
    module: str | None = None


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _module_from_command(command: str | None) -> str | None:
    if not command:
        return None
    match = re.search(r"python -m ([\w.]+)", command)
    return match.group(1) if match else None


def _parse_tool_table_rows(section_text: str, category: str) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    row_pattern = re.compile(
        r"\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(?:`([^`]+)`\s*\|)?",
        re.MULTILINE,
    )
    for index, match in enumerate(row_pattern.finditer(section_text)):
        filename, description, run_command = match.groups()
        filename = filename.strip()
        description = description.strip()
        run_command = run_command.strip() if run_command else None
        module = _module_from_command(run_command)
        title = filename.replace(".py", "")
        text = f"{filename}: {description}"
        if run_command:
            text += f"\nRun: {run_command}"
        chunks.append(
            DocumentChunk(
                chunk_id=f"{category}:{title}:{index}",
                title=title,
                text=text,
                category=category,
                run_command=run_command,
                module=module,
            )
        )
    return chunks


FOLDER_READMES = {
    "screeners": PROJECT_ROOT / "screeners" / "README.md",
    "charts": PROJECT_ROOT / "charts" / "README.md",
    "fundamentals": PROJECT_ROOT / "fundamentals" / "README.md",
    "launchers": PROJECT_ROOT / "launchers" / "README.md",
    "chatbot": PROJECT_ROOT / "chatbot" / "README.md",
}


def load_readme_chunks(readme_path: Path | None = None) -> list[DocumentChunk]:
    path = readme_path or DEFAULT_README
    chunks: list[DocumentChunk] = []

    if path.exists():
        overview = path.read_text(encoding="utf-8").strip()
        if overview:
            chunks.append(
                DocumentChunk(
                    chunk_id="intro:overview",
                    title="Overview",
                    text=overview,
                    category="overview",
                )
            )

    for category, folder_readme in FOLDER_READMES.items():
        if not folder_readme.exists():
            continue
        text = folder_readme.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks.append(
            DocumentChunk(
                chunk_id=f"guide:{category}",
                title=category,
                text=text,
                category=category,
            )
        )
        chunks.extend(_parse_tool_table_rows(text, category))

    return chunks


class ReadmeIndex:
    """TF-IDF index over README chunks (no extra ML dependencies)."""

    def __init__(self, chunks: list[DocumentChunk] | None = None):
        self.chunks = chunks or load_readme_chunks()
        self._chunk_tokens = [_tokenize(f"{c.title} {c.text}") for c in self.chunks]
        self._idf = self._compute_idf(self._chunk_tokens)

    @staticmethod
    def _compute_idf(all_tokens: list[list[str]]) -> dict[str, float]:
        doc_count = len(all_tokens)
        df: Counter[str] = Counter()
        for tokens in all_tokens:
            df.update(set(tokens))
        return {
            term: math.log((1 + doc_count) / (1 + freq)) + 1.0
            for term, freq in df.items()
        }

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        total = len(tokens) or 1
        return {
            term: (count / total) * self._idf.get(term, 0.0)
            for term, count in counts.items()
        }

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in set(a) | set(b))
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_vec = self._vectorize(_tokenize(query))
        scored = [
            RetrievedChunk(chunk=chunk, score=self._cosine(query_vec, self._vectorize(tokens)))
            for chunk, tokens in zip(self.chunks, self._chunk_tokens)
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return [item for item in scored[:top_k] if item.score > 0]

    def format_context(self, retrieved: list[RetrievedChunk]) -> str:
        if not retrieved:
            return "No closely matching README sections were found."
        parts: list[str] = []
        for item in retrieved:
            chunk = item.chunk
            header = f"[{chunk.category}] {chunk.title} (relevance {item.score:.2f})"
            parts.append(f"{header}\n{chunk.text}")
        return "\n\n---\n\n".join(parts)
