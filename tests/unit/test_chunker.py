"""Unit tests for SentenceAwareChunker."""

from app.services.chunker import SentenceAwareChunker


def test_chunker_short_text():
    chunker = SentenceAwareChunker(max_tokens=200)
    text = "Sentence one. Sentence two. Sentence three."
    chunks = chunker.chunk_document(text)
    assert len(chunks) == 1
    assert chunks[0]["sentence_count"] == 3


def test_chunker_long_text_no_cut_sentences():
    chunker = SentenceAwareChunker(max_tokens=30, overlap_sentences=1)
    sentences = [
        f"This is informative sentence number {i} containing details."
        for i in range(15)
    ]
    text = " ".join(sentences)
    chunks = chunker.chunk_document(text)
    assert len(chunks) > 1

    # Verify every chunk ends with full punctuation (never cut halfway through a sentence)
    for c in chunks:
        assert c["text"].strip().endswith(".")
