"""Text-to-Speech service generating file-backed audio with TTL cleanup."""

import time
from pathlib import Path
from typing import Dict, Any
from gtts import gTTS
from app.config import get_config
from app.utils.cache import compute_content_hash
from app.utils.logger import logger

# Supported gTTS language codes
GTTS_SUPPORTED_LANGS = {
    "af",
    "ar",
    "bn",
    "bs",
    "ca",
    "cs",
    "cy",
    "da",
    "de",
    "el",
    "en",
    "eo",
    "es",
    "et",
    "fi",
    "fr",
    "gu",
    "hi",
    "hr",
    "hu",
    "id",
    "is",
    "it",
    "ja",
    "jw",
    "km",
    "kn",
    "ko",
    "la",
    "lv",
    "mk",
    "ml",
    "mr",
    "my",
    "ne",
    "nl",
    "no",
    "pl",
    "pt",
    "ro",
    "ru",
    "si",
    "sk",
    "sq",
    "sr",
    "su",
    "sv",
    "sw",
    "ta",
    "te",
    "th",
    "tl",
    "tr",
    "uk",
    "ur",
    "vi",
    "zh-CN",
    "zh-TW",
    "zh",
}


class TTSService:
    def __init__(self):
        self.config = get_config()
        self.cache_dir = Path(self.config.AUDIO_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_audio_file(self, text: str, lang: str = "en") -> Dict[str, Any]:
        """Generates or retrieves a cached MP3 file for given text and language."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty for TTS generation.")

        audio_lang = lang if lang in GTTS_SUPPORTED_LANGS else "en"
        content_hash = compute_content_hash(text)[:16]
        filename = f"{content_hash}_{audio_lang}.mp3"
        filepath = self.cache_dir / filename

        # Return cached file if it already exists
        if filepath.exists() and filepath.stat().st_size > 0:
            logger.info(f"Serving cached audio file: {filename}")
            return {
                "filename": filename,
                "filepath": str(filepath),
                "language": audio_lang,
                "cached": True,
                "size_bytes": filepath.stat().st_size,
            }

        logger.info(
            f"Synthesizing new audio file with gTTS: {filename} in '{audio_lang}'..."
        )
        tts = gTTS(text=text.strip(), lang=audio_lang, slow=False)
        tts.save(str(filepath))

        return {
            "filename": filename,
            "filepath": str(filepath),
            "language": audio_lang,
            "cached": False,
            "size_bytes": filepath.stat().st_size,
        }

    def cleanup_old_audio(self, max_age_seconds: int = 86400):
        """Deletes generated audio files older than max_age_seconds (default 24h)."""
        now = time.time()
        for f in self.cache_dir.glob("*.mp3"):
            try:
                if now - f.stat().st_mtime > max_age_seconds:
                    f.unlink()
                    logger.debug(f"Removed stale audio file: {f.name}")
            except Exception as e:
                logger.warning(f"Error deleting old audio file {f}: {e}")
