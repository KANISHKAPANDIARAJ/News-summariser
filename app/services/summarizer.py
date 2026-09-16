"""Hierarchical Map-Reduce abstractive summarization service."""

import time
import torch
from typing import Dict, Any, Optional
from app.ml.model_manager import get_model_manager
from app.services.chunker import SentenceAwareChunker
from app.constants import SUMMARY_LENGTHS
from app.utils.logger import logger


class SummarizationError(Exception):
    pass


class HierarchicalSummarizer:
    def __init__(self, chunk_tokens: int = 750):
        self.model_manager = get_model_manager()
        self.chunker = SentenceAwareChunker(
            max_tokens=chunk_tokens, overlap_sentences=1
        )

    def _generate_chunk_summary(self, text: str, min_len: int, max_len: int) -> str:
        """Executes a single summarization forward pass on a chunk."""
        model, tokenizer = self.model_manager.get_summarizer()
        inputs = tokenizer(
            [text], max_length=1024, return_tensors="pt", truncation=True
        ).to(self.model_manager.device)

        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"],
                num_beams=4,
                max_length=max_len,
                min_length=min_len,
                no_repeat_ngram_size=3,
                early_stopping=True,
                length_penalty=1.2,
            )

        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
        return summary

    def summarize(
        self,
        text: str,
        length_profile: str = "medium",
        custom_min: Optional[int] = None,
        custom_max: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Summarizes an article of arbitrary length using hierarchical Map-Reduce."""
        start_time = time.time()
        if not text or len(text.strip()) < 30:
            raise SummarizationError(
                "Article content is too short for meaningful summarization."
            )

        # Resolve length constraints
        profile = SUMMARY_LENGTHS.get(length_profile, SUMMARY_LENGTHS["medium"])
        min_length = custom_min if custom_min is not None else profile["min_length"]
        max_length = custom_max if custom_max is not None else profile["max_length"]

        _, tokenizer = self.model_manager.get_summarizer()
        chunks = self.chunker.chunk_document(text, tokenizer=tokenizer)

        if not chunks:
            raise SummarizationError("Unable to extract sentences from article text.")

        intermediate_summaries = []

        # Single Chunk: Direct Fast Pass
        if len(chunks) == 1:
            logger.info(
                f"Summarizing single-chunk document ({chunks[0]['token_count']} tokens)"
            )
            final_summary = self._generate_chunk_summary(
                chunks[0]["text"], min_length, max_length
            )
        else:
            # Map Phase: Summarize each chunk
            logger.info(
                f"Executing Map Phase on {len(chunks)} chunks for long document..."
            )
            for idx, chunk in enumerate(chunks):
                # Target intermediate chunk length proportional to document size
                chunk_min = max(25, min_length // len(chunks))
                chunk_max = max(50, max_length // len(chunks) + 30)
                chunk_summ = self._generate_chunk_summary(
                    chunk["text"], chunk_min, chunk_max
                )
                intermediate_summaries.append(chunk_summ)
                logger.debug(
                    f"Chunk {idx + 1}/{len(chunks)} summarized: {len(chunk_summ)} chars"
                )

            # Reduce Phase: Combine intermediate summaries
            combined_text = " ".join(intermediate_summaries)
            logger.info(
                f"Executing Reduce Phase on combined intermediate summaries ({len(combined_text)} chars)..."
            )

            # Check if combined text itself exceeds one chunk
            combined_tokens = len(
                tokenizer.encode(combined_text, add_special_tokens=False)
            )
            if combined_tokens > 750:
                # Hierarchical secondary reduce
                second_chunks = self.chunker.chunk_document(
                    combined_text, tokenizer=tokenizer
                )
                second_summaries = [
                    self._generate_chunk_summary(c["text"], 30, 80)
                    for c in second_chunks
                ]
                combined_text = " ".join(second_summaries)

            # Final Synthesis
            final_summary = self._generate_chunk_summary(
                combined_text, min_length, max_length
            )

        elapsed_ms = (time.time() - start_time) * 1000

        # Calculate metrics
        orig_len = len(text.split())
        summ_len = len(final_summary.split())
        compression_ratio = round((1.0 - (summ_len / max(1, orig_len))) * 100.0, 1)

        return {
            "summary": final_summary,
            "length_profile": length_profile,
            "min_length": min_length,
            "max_length": max_length,
            "chunk_count": len(chunks),
            "compression_ratio": max(0.0, compression_ratio),
            "processing_time_ms": round(elapsed_ms, 2),
            "word_count": summ_len,
            "model_name": self.model_manager.config.SUMMARIZATION_MODEL,
        }
