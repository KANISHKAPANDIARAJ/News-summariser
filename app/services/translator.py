"""Centralized translation service with language validation, chunking, and caching."""

from typing import Dict, Any, Optional
import torch
from app.constants import SUPPORTED_LANGUAGES, ErrorCodes
from app.ml.model_manager import get_model_manager
from app.utils.cache import cache, compute_content_hash
from app.services.text_cleaner import TextCleaner
from app.utils.logger import logger

class TranslationError(Exception):
    pass

class TranslationService:
    def __init__(self):
        self.model_manager = get_model_manager()

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> Dict[str, Any]:
        """Translates text into target language respecting sentence boundaries and caching results."""
        if not text or not text.strip():
            return {
                "source_language": source_lang,
                "target_language": target_lang,
                "translation": "",
                "model_name": None,
                "cached": False,
            }

        target_lang = target_lang.lower().strip()
        if target_lang == source_lang or target_lang == "en":
            return {
                "source_language": source_lang,
                "target_language": target_lang,
                "translation": text,
                "model_name": None,
                "cached": False,
            }

        if target_lang not in SUPPORTED_LANGUAGES:
            supported = list(SUPPORTED_LANGUAGES.keys())
            raise TranslationError(
                f"Language '{target_lang}' is not supported. Supported languages: {supported}"
            )

        # Cache check
        content_hash = compute_content_hash(text)
        cache_key = f"trans_{content_hash}_{source_lang}_{target_lang}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached translation for key {cache_key}")
            return {
                "source_language": source_lang,
                "target_language": target_lang,
                "translation": cached_result,
                "model_name": SUPPORTED_LANGUAGES[target_lang]["model"],
                "cached": True,
            }

        model, tokenizer = self.model_manager.get_translation_model(target_lang)
        if model is None or tokenizer is None:
            raise TranslationError(f"Failed to load translation model for language '{target_lang}'.")

        # Sentence-by-sentence translation to avoid truncation on longer summaries
        sentences = TextCleaner.segment_sentences(text)
        if not sentences:
            sentences = [text]

        translated_sentences = []
        model_name = SUPPORTED_LANGUAGES[target_lang]["model"]

        try:
            for s in sentences:
                inputs = tokenizer([s], return_tensors="pt", truncation=True, max_length=512).to(self.model_manager.device)
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_length=512)
                translated_s = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                translated_sentences.append(translated_s)

            final_translation = " ".join(translated_sentences)
            # Store in cache for 2 hours
            cache.set(cache_key, final_translation, ttl=7200)

            return {
                "source_language": source_lang,
                "target_language": target_lang,
                "translation": final_translation,
                "model_name": model_name,
                "cached": False,
            }

        except Exception as e:
            logger.error(f"Translation forward pass error for '{target_lang}': {e}")
            raise TranslationError(f"Translation failed: {str(e)}")
