"""Production Translation Manager with bidirectional pairs, pivot routing, and quality validation."""

import re
import threading
import torch
from typing import Dict, Tuple, Optional, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from app.config import get_config
from app.utils.cache import cache, compute_content_hash
from app.utils.logger import logger
from app.services.text_cleaner import TextCleaner


class TranslationValidationError(Exception):
    pass


class TranslationPairError(Exception):
    pass


# Direct translation models registry
SUPPORTED_PAIRS: Dict[Tuple[str, str], str] = {
    # English -> Other
    ("en", "ta"): "suriya7/English-to-Tamil",
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
    ("en", "pt"): "Helsinki-NLP/opus-mt-en-pt",
    ("en", "ru"): "Helsinki-NLP/opus-mt-en-ru",
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
    ("en", "ja"): "Helsinki-NLP/opus-mt-en-ja",
    ("en", "ko"): "Helsinki-NLP/opus-mt-en-ko",
    ("en", "ar"): "Helsinki-NLP/opus-mt-en-ar",
    ("en", "bn"): "Helsinki-NLP/opus-mt-en-bn",
    ("en", "mr"): "Helsinki-NLP/opus-mt-en-mr",
    # Other -> English
    ("ta", "en"): "Helsinki-NLP/opus-mt-dra-en",
    ("te", "en"): "Helsinki-NLP/opus-mt-dra-en",
    ("ml", "en"): "Helsinki-NLP/opus-mt-dra-en",
    ("kn", "en"): "Helsinki-NLP/opus-mt-dra-en",
    ("hi", "en"): "Helsinki-NLP/opus-mt-mul-en",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
    ("pt", "en"): "Helsinki-NLP/opus-mt-mul-en",
    ("ru", "en"): "Helsinki-NLP/opus-mt-ru-en",
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("ja", "en"): "Helsinki-NLP/opus-mt-ja-en",
    ("ar", "en"): "Helsinki-NLP/opus-mt-ar-en",
}


class TranslationManager:
    _instance: Optional["TranslationManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TranslationManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.config = get_config()
        self.device = (
            "cuda"
            if (
                self.config.MODEL_DEVICE.lower() == "cuda" and torch.cuda.is_available()
            )
            else "cpu"
        )
        self._loaded_models: Dict[str, Dict[str, Any]] = {}
        self._load_lock = threading.Lock()
        logger.info(f"TranslationManager initialized. Device: {self.device}")

    def _get_model(self, model_name: str) -> Tuple[Any, Any]:
        with self._load_lock:
            if model_name not in self._loaded_models:
                logger.info(
                    f"Loading translation model {model_name} onto {self.device}..."
                )
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                model.to(self.device)
                model.eval()
                self._loaded_models[model_name] = {
                    "model": model,
                    "tokenizer": tokenizer,
                }
            return self._loaded_models[model_name]["model"], self._loaded_models[
                model_name
            ]["tokenizer"]

    @staticmethod
    def validate_translation_output(
        src: str, trans: str, src_lang: str, tgt_lang: str
    ) -> bool:
        """Validates that translation output is non-empty, contains no tokenizer artifacts, and matches expected scripts."""
        if not trans or not trans.strip():
            raise TranslationValidationError("Translation output is empty.")

        clean_trans = trans.strip()

        # Reject model tokens
        for bad_token in ["<pad>", "<unk>", "</s>", "[PAD]", "[UNK]", "NaN", "null"]:
            if bad_token in clean_trans:
                raise TranslationValidationError(
                    f"Translation output contains model special token: {bad_token}"
                )

        # Check repetition of identical phrases
        words = clean_trans.split()
        if len(words) >= 6:
            trigrams = [tuple(words[i : i + 3]) for i in range(len(words) - 2)]
            unique_trigrams = set(trigrams)
            rep_ratio = 1.0 - (len(unique_trigrams) / max(1, len(trigrams)))
            if rep_ratio > 0.45:
                raise TranslationValidationError(
                    "Translation output contains excessive repetitive loops."
                )

        # Script consistency check for Tamil target
        if tgt_lang == "ta":
            tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", clean_trans))
            if tamil_chars < 5 and len(clean_trans) > 20:
                raise TranslationValidationError(
                    "Expected Tamil script in translation output but none was found."
                )

        # Script consistency check for Hindi target
        if tgt_lang == "hi":
            hindi_chars = len(re.findall(r"[\u0900-\u097F]", clean_trans))
            if hindi_chars < 5 and len(clean_trans) > 20:
                raise TranslationValidationError(
                    "Expected Devanagari script in translation output but none was found."
                )

        return True

    def _translate_single_step(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Executes translation for a directly supported language pair with sentence chunking."""
        pair = (src_lang, tgt_lang)
        model_name = SUPPORTED_PAIRS.get(pair)
        if not model_name:
            raise TranslationPairError(
                f"No direct translation model registered for {src_lang} -> {tgt_lang}"
            )

        model, tokenizer = self._get_model(model_name)
        sentences = TextCleaner.segment_sentences(text)
        if not sentences:
            sentences = [text]

        translated_chunks = []
        for s in sentences:
            if not s.strip():
                continue
            inputs = tokenizer(
                [s], return_tensors="pt", truncation=True, max_length=512
            ).to(self.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs, max_length=512, num_beams=3, early_stopping=True
                )
            decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            # Clean up residual artifacts
            decoded = re.sub(r"\s+", " ", decoded).strip()
            translated_chunks.append(decoded)

        result_text = " ".join(translated_chunks)
        self.validate_translation_output(text, result_text, src_lang, tgt_lang)
        return result_text

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> Dict[str, Any]:
        """Translates text from src_lang to tgt_lang with caching, direct routing, or pivot routing."""
        src_lang = src_lang.lower().strip()
        tgt_lang = tgt_lang.lower().strip()

        if not text or not text.strip():
            return {
                "source_language": src_lang,
                "target_language": tgt_lang,
                "translation": "",
                "pipeline": "identity",
                "cached": False,
            }

        if src_lang == tgt_lang:
            return {
                "source_language": src_lang,
                "target_language": tgt_lang,
                "translation": text,
                "pipeline": "identity",
                "cached": False,
            }

        # Cache check
        content_hash = compute_content_hash(text)
        cache_key = f"trans_v21_{content_hash}_{src_lang}_{tgt_lang}"
        cached = cache.get(cache_key)
        if cached:
            return {
                "source_language": src_lang,
                "target_language": tgt_lang,
                "translation": cached,
                "pipeline": "cache",
                "cached": True,
            }

        # Case 1: Direct Pair exists
        if (src_lang, tgt_lang) in SUPPORTED_PAIRS:
            logger.info(f"Executing direct translation: {src_lang} -> {tgt_lang}")
            trans = self._translate_single_step(text, src_lang, tgt_lang)
            cache.set(cache_key, trans, ttl=7200)
            return {
                "source_language": src_lang,
                "target_language": tgt_lang,
                "translation": trans,
                "pipeline": "direct",
                "model_name": SUPPORTED_PAIRS[(src_lang, tgt_lang)],
                "cached": False,
            }

        # Case 2: Pivot through English (e.g. Tamil -> English -> French)
        if (src_lang, "en") in SUPPORTED_PAIRS and ("en", tgt_lang) in SUPPORTED_PAIRS:
            logger.info(f"Executing pivot translation: {src_lang} -> en -> {tgt_lang}")
            intermediate_en = self._translate_single_step(text, src_lang, "en")
            final_trans = self._translate_single_step(intermediate_en, "en", tgt_lang)
            cache.set(cache_key, final_trans, ttl=7200)
            return {
                "source_language": src_lang,
                "target_language": tgt_lang,
                "translation": final_trans,
                "pipeline": "pivot_en",
                "cached": False,
            }

        raise TranslationPairError(
            f"Translation route from '{src_lang}' to '{tgt_lang}' is currently unavailable."
        )


# Global accessor
def get_translation_manager() -> TranslationManager:
    return TranslationManager()
