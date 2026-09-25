"""Qualitative RAG agent: semantic search over enterprise documents + LLM synthesis."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src import config
from src.llm_client import LLMClient, get_llm_client


@dataclass
class Citation:
    source: str
    chunk_id: str
    similarity: float
    text: str


@dataclass
class QualitativeAnswer:
    answer: str
    citations: List[Citation] = field(default_factory=list)
    found_relevant_docs: bool = True


class QualitativeAgent:
    """Retrieves relevant document chunks and asks an LLM to answer from them."""

    def __init__(
        self,
        docs_dir: Path = config.DOCS_DIR,
        persist_dir: Path = config.VECTORSTORE_DIR,
        llm_client: Optional[LLMClient] = None,
        collection_name: str = "enterprise_docs",
        relevance_threshold: float = config.RELEVANCE_THRESHOLD,
        top_k: int = config.RETRIEVAL_TOP_K,
    ):
        import chromadb
        from sentence_transformers import SentenceTransformer

        self.llm = llm_client or get_llm_client()
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold
        self._embedder = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

        if self._collection.count() == 0:
            self._ingest(docs_dir)

    # -- ingestion -----------------------------------------------------
    def _chunk_text(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paragraphs

    def _ingest(self, docs_dir: Path) -> None:
        ids, documents, metadatas = [], [], []
        for path in sorted(docs_dir.glob("*.md")):
            chunks = self._chunk_text(path.read_text(encoding="utf-8"))
            for idx, chunk in enumerate(chunks):
                ids.append(f"{path.stem}::{idx}")
                documents.append(chunk)
                metadatas.append({"source": path.name})

        if not documents:
            return

        embeddings = self._embedder.encode(documents, normalize_embeddings=True).tolist()
        self._collection.add(
            ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings
        )

    # -- retrieval -------------------------------------------------------
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Citation]:
        k = k or self.top_k
        query_embedding = self._embedder.encode([query], normalize_embeddings=True).tolist()
        results = self._collection.query(query_embeddings=query_embedding, n_results=k)

        citations: List[Citation] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_id, doc_text, meta, distance in zip(ids, docs, metas, distances):
            similarity = 1 - distance  # cosine space: distance = 1 - cosine_similarity
            if similarity >= self.relevance_threshold:
                citations.append(
                    Citation(
                        source=meta.get("source", "unknown"),
                        chunk_id=doc_id,
                        similarity=round(similarity, 4),
                        text=doc_text,
                    )
                )
        return citations

    # -- answering ---------------------------------------------------------
    def answer(self, query: str) -> QualitativeAnswer:
        citations = self.retrieve(query)

        if not citations:
            return QualitativeAnswer(
                answer="I could not find relevant documentation to answer that question.",
                citations=[],
                found_relevant_docs=False,
            )

        context = "\n\n".join(
            f"[{c.source} | similarity={c.similarity}]\n{c.text}" for c in citations
        )
        prompt = (
            "Answer the user's question using ONLY the context below. "
            "Cite sources by filename inline where relevant.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        )
        answer_text = self.llm.complete(
            prompt, system="You are an enterprise documentation assistant."
        )
        return QualitativeAnswer(answer=answer_text, citations=citations, found_relevant_docs=True)
