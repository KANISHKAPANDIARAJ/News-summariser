"""Multilingual Summarization Engine with language-aware routing, Translate-Summarize-Translate fallback, and quality scoring."""

import time
import re
from typing import Dict, Any, Optional, List
from app.services.summarizer import HierarchicalSummarizer, SummarizationError
from app.services.translation_manager import get_translation_manager
from app.services.language_detector import LanguageDetector
from app.utils.logger import logger


class MultilingualSummarizer:
    def __init__(self):
        self.english_summarizer = HierarchicalSummarizer()
        self.translation_manager = get_translation_manager()

    @staticmethod
    def calculate_quality_score(
        summary: str, original_text: str, target_lang: str
    ) -> Dict[str, Any]:
        """Calculates a multi-factor quality score for the generated summary."""
        warnings: List[str] = []
        score = 1.0

        if not summary or not summary.strip():
            return {
                "score": 0.0,
                "level": "poor",
                "warnings": ["Empty summary produced."],
            }

        orig_words = max(1, len(original_text.split()))
        summ_words = len(summary.split())

        # 1. Length Sanity: Summary should typically be 5% to 45% of source text
        ratio = summ_words / orig_words
        if ratio > 0.65:
            score -= 0.20
            warnings.append("Summary length is unusually long relative to source.")
        elif ratio < 0.03 and orig_words > 100:
            score -= 0.25
            warnings.append("Summary length is unusually short.")

        # 2. Repetition Ratio (Trigrams)
        words = summary.split()
        if len(words) >= 6:
            trigrams = [tuple(words[i : i + 3]) for i in range(len(words) - 2)]
            rep_ratio = 1.0 - (len(set(trigrams)) / max(1, len(trigrams)))
            if rep_ratio > 0.35:
                score -= 0.30
                warnings.append("High repetitive phrasing detected.")

        # 3. Target Script Consistency
        if target_lang == "ta":
            tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", summary))
            if tamil_chars < 8 and len(summary) > 30:
                score -= 0.50
                warnings.append("Missing expected Tamil script characters.")
        elif target_lang == "hi":
            hindi_chars = len(re.findall(r"[\u0900-\u097F]", summary))
            if hindi_chars < 8 and len(summary) > 30:
                score -= 0.50
                warnings.append("Missing expected Devanagari script characters.")

        # 4. Tokenizer Artifacts
        for token in ["<pad>", "<unk>", "</s>", "[PAD]", "[UNK]"]:
            if token in summary:
                score -= 0.40
                warnings.append(f"Contains model artifact: {token}")

        final_score = round(max(0.0, min(1.0, score)), 2)
        level = (
            "good" if final_score >= 0.75 else "fair" if final_score >= 0.50 else "poor"
        )

        return {
            "score": final_score,
            "level": level,
            "warnings": warnings,
        }

    def summarize(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "en",
        length_profile: str = "medium",
    ) -> Dict[str, Any]:
        """Performs language-aware summarization routing."""
        t0 = time.perf_counter()

        if not text or len(text.strip()) < 30:
            raise SummarizationError("Content is too short for summarization.")

        # 1. Detect source language if not explicitly provided
        if not source_lang or source_lang == "auto":
            det = LanguageDetector.detect(text)
            source_lang = det["language_code"]
            logger.info(
                f"Detected language '{source_lang}' ({det['language_name']}) with {det['confidence']} confidence."
            )

        source_lang = source_lang.lower().strip()
        target_lang = target_lang.lower().strip()

        # Route A: English Source & English Target -> Direct Native Pass (Zero quality regression)
        if source_lang == "en" and target_lang == "en":
            logger.info("Executing native English hierarchical summarization...")
            res = self.english_summarizer.summarize(text, length_profile=length_profile)
            quality = self.calculate_quality_score(res["summary"], text, "en")
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "summary": res["summary"],
                "source_language": "en",
                "target_language": "en",
                "summarization_language": "en",
                "pipeline_type": "native_english",
                "translation_used": False,
                "compression_ratio": res["compression_ratio"],
                "processing_time_ms": elapsed,
                "model_name": res["model_name"],
                "quality": quality,
            }

        # Route B: Non-English Source (e.g. Tamil) -> Translate-Summarize-Translate Pipeline
        logger.info(
            f"Executing Translate-Summarize-Translate pipeline for '{source_lang}' to '{target_lang}'..."
        )
        pipeline_type = "translate_summarize_translate"

        # Step 1: Translate Source to English if source is not English
        if source_lang != "en":
            try:
                logger.info(
                    f"Translating source article ({len(text)} chars) from {source_lang} to en..."
                )
                trans_to_en = self.translation_manager.translate(
                    text, src_lang=source_lang, tgt_lang="en"
                )
                english_text = trans_to_en["translation"]
            except Exception as e:
                logger.error(f"Translation from {source_lang} to English failed: {e}")
                raise SummarizationError(
                    f"Could not prepare multilingual pipeline: {e}"
                )
        else:
            english_text = text

        # Step 2: High-Quality English Summarization
        res_en = self.english_summarizer.summarize(
            english_text, length_profile=length_profile
        )
        english_summary = res_en["summary"]

        # Step 3: Translate Summary to Target Language
        if target_lang != "en":
            try:
                logger.info(
                    f"Translating English summary to target language '{target_lang}'..."
                )
                trans_final = self.translation_manager.translate(
                    english_summary, src_lang="en", tgt_lang=target_lang
                )
                final_summary = trans_final["translation"]
            except Exception as e:
                logger.warning(
                    f"Translation to {target_lang} failed: {e}. Falling back to English summary."
                )
                final_summary = english_summary
                target_lang = "en"
        else:
            final_summary = english_summary

        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        orig_words = len(text.split())
        summ_words = len(final_summary.split())
        comp_ratio = round((1.0 - (summ_words / max(1, orig_words))) * 100.0, 1)

        quality = self.calculate_quality_score(final_summary, text, target_lang)

        return {
            "summary": final_summary,
            "source_language": source_lang,
            "target_language": target_lang,
            "summarization_language": "en",
            "pipeline_type": pipeline_type,
            "translation_used": True,
            "compression_ratio": max(0.0, comp_ratio),
            "processing_time_ms": elapsed,
            "model_name": res_en["model_name"],
            "quality": quality,
        }
