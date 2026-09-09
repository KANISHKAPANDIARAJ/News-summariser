"""Sentence-aware chunking pipeline for long document processing."""

from typing import List, Dict, Any, Optional
from app.services.text_cleaner import TextCleaner
from app.utils.logger import logger

class SentenceAwareChunker:
    """Splits long text into sentence-coherent chunks with token limits and boundary overlap."""

    def __init__(self, max_tokens: int = 700, overlap_sentences: int = 1):
        self.max_tokens = max_tokens
        self.overlap_sentences = overlap_sentences

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """Estimates token count (~1.3 tokens per word for English prose)."""
        words = text.split()
        return max(1, int(len(words) * 1.33))

    def chunk_document(self, text: str, tokenizer=None) -> List[Dict[str, Any]]:
        """Splits document text into sentence-aware chunks respecting max token budget."""
        sentences = TextCleaner.segment_sentences(text)
        if not sentences:
            return []

        def get_tokens(s: str) -> int:
            if tokenizer is not None:
                try:
                    return len(tokenizer.encode(s, add_special_tokens=False))
                except Exception:
                    return self.estimate_token_count(s)
            return self.estimate_token_count(s)

        chunks = []
        current_chunk_sentences: List[str] = []
        current_tokens = 0

        for sentence in sentences:
            sent_tokens = get_tokens(sentence)

            # If a single sentence exceeds the max chunk budget, include it as its own chunk
            if sent_tokens > self.max_tokens:
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    chunks.append({
                        "index": len(chunks),
                        "text": chunk_text,
                        "token_count": current_tokens,
                        "sentence_count": len(current_chunk_sentences)
                    })
                    current_chunk_sentences = []
                    current_tokens = 0

                chunks.append({
                    "index": len(chunks),
                    "text": sentence,
                    "token_count": sent_tokens,
                    "sentence_count": 1
                })
                continue

            # Check if adding this sentence exceeds token limit
            if current_tokens + sent_tokens > self.max_tokens and current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "index": len(chunks),
                    "text": chunk_text,
                    "token_count": current_tokens,
                    "sentence_count": len(current_chunk_sentences)
                })

                # Maintain sentence overlap for continuity
                if self.overlap_sentences > 0 and len(current_chunk_sentences) >= self.overlap_sentences:
                    overlap = current_chunk_sentences[-self.overlap_sentences:]
                    current_chunk_sentences = list(overlap)
                    current_tokens = sum(get_tokens(s) for s in overlap)
                else:
                    current_chunk_sentences = []
                    current_tokens = 0

            current_chunk_sentences.append(sentence)
            current_tokens += sent_tokens

        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "index": len(chunks),
                "text": chunk_text,
                "token_count": current_tokens,
                "sentence_count": len(current_chunk_sentences)
            })

        logger.debug(f"Chunked document into {len(chunks)} chunks with max_tokens={self.max_tokens}")
        return chunks
