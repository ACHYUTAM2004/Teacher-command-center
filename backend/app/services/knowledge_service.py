import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

import frontmatter
import fitz  # PyMuPDF
from fastembed import TextEmbedding
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.core import Standard, Resource, ResourceChunk

# Resolve root knowledge directory (D:\tcc\knowledge)
KNOWLEDGE_DIR = Path(__file__).resolve().parents[3] / "knowledge"

# Singleton local CPU embedding model (384 dimensions, $0 cost)
_embedding_model: Optional[TextEmbedding] = None


def get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    return [vec.tolist() for vec in model.embed(texts)]


# ---------------------------------------------------------------------------
# TIER 1: Deterministic OKF Curriculum Registry
# ---------------------------------------------------------------------------
def load_okf_standards_from_disk(
    grade: Optional[int] = None,
    subject: Optional[str] = None,
    topic_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Deterministically reads YAML frontmatter + Markdown from knowledge/curriculum/."""
    curriculum_dir = KNOWLEDGE_DIR / "curriculum"
    if not curriculum_dir.exists():
        return []

    results: List[Dict[str, Any]] = []
    for md_file in curriculum_dir.glob("*.md"):
        post = frontmatter.load(md_file)
        meta = post.metadata

        if grade is not None and meta.get("grade") != grade:
            continue
        if subject is not None and meta.get("subject", "").lower() != subject.lower():
            continue
        if topic_query:
            searchable = f"{meta.get('code', '')} {meta.get('topic', '')} {post.content}".lower()
            if not any(word.lower() in searchable for word in topic_query.split() if len(word) > 2):
                continue

        results.append({
            "code": meta.get("code"),
            "framework": meta.get("framework", "NCERT/CBSE"),
            "subject": meta.get("subject"),
            "grade": meta.get("grade"),
            "topic": meta.get("topic"),
            "prerequisites": meta.get("prerequisites", []),
            "assessed_skills": meta.get("assessed_skills", []),
            "forbidden_topics": meta.get("forbidden_topics", []),
            "required_safety_rules": meta.get("required_safety_rules", []),
            "instructional_guidelines": post.content.strip(),
        })

    return results


# ---------------------------------------------------------------------------
# TIER 2: Unstructured PDF Ingestion & Hybrid RAG (PyMuPDF + FastEmbed + pgvector)
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Splits text into overlapping character chunks while preserving paragraph boundaries."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start += chunk_size - overlap
    return chunks


def ingest_pdf_bytes(
    db: Session,
    file_bytes: bytes,
    filename: str,
    grade: int,
    subject: str,
) -> Dict[str, Any]:
    """Parses a PDF with PyMuPDF, embeds chunks locally with FastEmbed, and stores in pgvector."""
    resource_id = f"res_{uuid.uuid4().hex[:8]}"
    resource = Resource(
        id=resource_id,
        title=filename,
        resource_type="pdf_textbook",
        s3_key=f"local/{resource_id}/{filename}",
    )
    db.add(resource)
    db.flush()

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    raw_chunks_meta: List[Dict[str, Any]] = []

    chunk_counter = 0
    for page_index in range(len(doc)):
        page_text = doc[page_index].get_text("text")
        page_chunks = chunk_text(page_text)
        for c_text in page_chunks:
            raw_chunks_meta.append({
                "chunk_index": chunk_counter,
                "page_number": page_index + 1,
                "content": c_text,
            })
            chunk_counter += 1

    if not raw_chunks_meta:
        db.commit()
        return {"resource_id": resource_id, "chunks_indexed": 0}

    embeddings = embed_texts([item["content"] for item in raw_chunks_meta])

    for item, vector in zip(raw_chunks_meta, embeddings):
        db_chunk = ResourceChunk(
            id=f"chk_{uuid.uuid4().hex[:10]}",
            resource_id=resource_id,
            grade=grade,
            subject=subject,
            chunk_index=item["chunk_index"],
            page_number=item["page_number"],
            content=item["content"],
            embedding=vector,
        )
        db.add(db_chunk)

    db.commit()
    return {
        "resource_id": resource_id,
        "title": filename,
        "chunks_indexed": len(raw_chunks_meta),
    }


def hybrid_retrieve(
    db: Session,
    query: str,
    grade: int,
    subject: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Combines:
    1. Deterministic OKF curriculum lookup (YAML/Markdown)
    2. Metadata-filtered pgvector cosine similarity + keyword boost
    """
    # 1. Deterministic OKF rules
    okf_matches = load_okf_standards_from_disk(grade=grade, subject=subject, topic_query=query)

    # 2. Vector + Keyword Search in pgvector
    query_vector = embed_texts([query])[0]
    distance_col = ResourceChunk.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(ResourceChunk, distance_col)
        .where(
            ResourceChunk.grade == grade,
            ResourceChunk.subject.ilike(subject),
        )
        .order_by(distance_col.asc())
        .limit(top_k * 2)
    )

    rows = db.execute(stmt).all()
    keywords = [w.lower() for w in query.split() if len(w) > 3]

    scored_chunks = []
    for chunk_obj, distance in rows:
        semantic_score = max(0.0, 1.0 - float(distance))
        keyword_hits = sum(1 for kw in keywords if kw in chunk_obj.content.lower())
        keyword_boost = min(0.2, keyword_hits * 0.05)
        hybrid_score = round(semantic_score + keyword_boost, 4)

        scored_chunks.append({
            "chunk_id": chunk_obj.id,
            "resource_id": chunk_obj.resource_id,
            "page_number": chunk_obj.page_number,
            "content": chunk_obj.content,
            "hybrid_score": hybrid_score,
        })

    scored_chunks.sort(key=lambda x: x["hybrid_score"], reverse=True)

    return {
        "okf_standards": okf_matches,
        "rag_chunks": scored_chunks[:top_k],
    }