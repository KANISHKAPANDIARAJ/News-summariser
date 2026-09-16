"""Font Manager for ReportLab with multilingual Unicode and RTL support."""

from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.utils.logger import logger

# Import Arabic shaping if available
try:
    import arabic_reshaper
    from bidi.algorithm import get_display as bidi_get_display

    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False


class FontManager:
    _initialized = False

    # Font Mapping per language
    INDIC_LANGS = {"ta", "hi", "bn", "mr", "te", "kn", "ml", "gu", "pa"}
    ARABIC_LANGS = {"ar", "fa", "ur"}

    @classmethod
    def initialize_fonts(cls):
        """Registers TrueType Unicode fonts for multilingual PDF rendering."""
        if cls._initialized:
            return

        fonts_dir = Path(__file__).resolve().parent.parent.parent / "fonts"
        win_fonts_dir = Path("C:/Windows/Fonts")

        # 1. Register Indic Font (Nirmala UI)
        nirmala_path = fonts_dir / "Nirmala.ttf"
        if not nirmala_path.exists():
            nirmala_path = win_fonts_dir / "Nirmala.ttf"

        if nirmala_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("IndicUnicode", str(nirmala_path)))
                logger.info(
                    "Registered IndicUnicode font (Nirmala) for Tamil/Hindi/Bengali."
                )
            except Exception as e:
                logger.warning(f"Failed to register Nirmala font: {e}")

        # 2. Register General / Arabic / Latin Font (Arial)
        arial_path = fonts_dir / "arial.ttf"
        if not arial_path.exists():
            arial_path = win_fonts_dir / "arial.ttf"

        if arial_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("GeneralUnicode", str(arial_path)))
                logger.info("Registered GeneralUnicode font (Arial).")
            except Exception as e:
                logger.warning(f"Failed to register Arial font: {e}")

        cls._initialized = True

    @classmethod
    def get_font_for_language(cls, lang_code: str) -> str:
        """Returns the appropriate registered font name based on language code."""
        cls.initialize_fonts()
        lang = (lang_code or "en").lower().strip()
        if lang in cls.INDIC_LANGS:
            return "IndicUnicode"
        elif lang in cls.ARABIC_LANGS:
            return "GeneralUnicode"
        else:
            return (
                "GeneralUnicode"
                if "GeneralUnicode" in pdfmetrics.getRegisteredFontNames()
                else "Helvetica"
            )

    @classmethod
    def prepare_text(cls, text: str, lang_code: str) -> str:
        """Prepares text for PDF rendering, including Arabic bidirectional reshaping."""
        if not text:
            return ""

        lang = (lang_code or "en").lower().strip()
        if lang in cls.ARABIC_LANGS and HAS_ARABIC_SUPPORT:
            try:
                reshaped = arabic_reshaper.reshape(text)
                return bidi_get_display(reshaped)
            except Exception as e:
                logger.warning(f"Arabic reshaping error: {e}")
                return text

        return text
