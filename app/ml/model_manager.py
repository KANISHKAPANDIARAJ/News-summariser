"""Central Model Manager providing thread-safe lazy loading and device management."""

from __future__ import annotations
import threading

import torch
from typing import Optional, Any
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    BartForConditionalGeneration,
    BartTokenizer,
    pipeline,
)
from app.config import get_config
from app.constants import SUPPORTED_LANGUAGES
from app.utils.logger import logger

class ModelManager:
    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.config = get_config()
        self.device = self._resolve_device()
        self._summarizer_model: Optional[BartForConditionalGeneration] = None
        self._summarizer_tokenizer: Optional[BartTokenizer] = None
        self._sentiment_pipeline = None
        self._translation_models: dict[str, dict[str, Any]] = {}
        self._model_lock = threading.Lock()
        logger.info(f"ModelManager initialized. Target device: {self.device}")

    def _resolve_device(self) -> str:
        dev_cfg = self.config.MODEL_DEVICE.lower()
        if dev_cfg == "cuda":
            return "cuda" if torch.cuda.is_available() else "cpu"
        elif dev_cfg == "cpu":
            return "cpu"
        else:
            return "cuda" if torch.cuda.is_available() else "cpu"

    def get_summarizer(self) -> tuple[BartForConditionalGeneration, BartTokenizer]:
        """Lazy-loads and returns the summarization model and tokenizer."""
        with self._model_lock:
            if self._summarizer_model is None or self._summarizer_tokenizer is None:
                model_name = self.config.SUMMARIZATION_MODEL
                logger.info(f"Loading summarization model: {model_name} onto {self.device}...")
                self._summarizer_tokenizer = BartTokenizer.from_pretrained(model_name)
                self._summarizer_model = BartForConditionalGeneration.from_pretrained(model_name)
                self._summarizer_model.to(self.device)
                self._summarizer_model.eval()
                logger.info(f"Summarization model {model_name} loaded successfully.")
            return self._summarizer_model, self._summarizer_tokenizer

    def get_sentiment_pipeline(self):
        """Lazy-loads and returns the sentiment analysis pipeline."""
        with self._model_lock:
            if self._sentiment_pipeline is None:
                model_name = self.config.SENTIMENT_MODEL
                logger.info(f"Loading sentiment model: {model_name}...")
                dev_idx = 0 if self.device == "cuda" else -1
                self._sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=dev_idx,
                    top_k=None,  # Returns distribution over all classes
                )
                logger.info(f"Sentiment pipeline {model_name} loaded successfully.")
            return self._sentiment_pipeline

    def get_translation_model(self, lang_code: str) -> tuple[Optional[Any], Optional[Any]]:
        """Lazy-loads and returns the translation model and tokenizer for a specific language code."""
        if lang_code == "en":
            return None, None

        lang_info = SUPPORTED_LANGUAGES.get(lang_code)
        if not lang_info or not lang_info.get("model"):
            logger.warning(f"No translation model registered for language code: {lang_code}")
            return None, None

        model_name = lang_info["model"]
        with self._model_lock:
            if lang_code not in self._translation_models:
                logger.info(f"Loading translation model for '{lang_code}': {model_name} onto {self.device}...")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                model.to(self.device)
                model.eval()
                self._translation_models[lang_code] = {"model": model, "tokenizer": tokenizer}
                logger.info(f"Translation model {model_name} for '{lang_code}' loaded successfully.")
            return self._translation_models[lang_code]["model"], self._translation_models[lang_code]["tokenizer"]

    def is_summarizer_loaded(self) -> bool:
        return self._summarizer_model is not None

# Global ModelManager singleton accessor
def get_model_manager() -> ModelManager:
    return ModelManager()
