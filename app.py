import logging
from flask import Flask, render_template, request, redirect, url_for, abort, make_response
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, BartForConditionalGeneration, BartTokenizer, pipeline
from newspaper import Article
import torch
import uuid
import re
import os
from gtts import gTTS
from io import BytesIO
import base64

os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

app = Flask(__name__)

# In-memory DB for storing past summaries
summaries_db = {}

# Load lightweight summarization model (CPU-friendly)
SUMM_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
summ_model = BartForConditionalGeneration.from_pretrained(SUMM_MODEL_NAME)
summ_tokenizer = BartTokenizer.from_pretrained(SUMM_MODEL_NAME)

# Sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Translation models for English to target languages
TRANSLATION_MODELS = {
    "en": None,
    "fr": "Helsinki-NLP/opus-mt-en-fr",
    "es": "Helsinki-NLP/opus-mt-en-es",
    "de": "Helsinki-NLP/opus-mt-en-de",
    "it": "Helsinki-NLP/opus-mt-en-it",
    "pt": "Helsinki-NLP/opus-mt-en-pt",
    "ru": "Helsinki-NLP/opus-mt-en-ru",
    "zh": "Helsinki-NLP/opus-mt-en-zh",
    "ja": "Helsinki-NLP/opus-mt-en-ja",
    "ko": "Helsinki-NLP/opus-mt-en-ko",
    "ar": "Helsinki-NLP/opus-mt-en-ar",
    "hi": "Helsinki-NLP/opus-mt-en-hi",
    "mr": "Helsinki-NLP/opus-mt-en-mr",
    "bn": "Helsinki-NLP/opus-mt-en-bn",
    "ta": "suriya7/English-to-Tamil",
}

loaded_translators = {}

def get_translation_model_and_tokenizer(lang_code):
    if lang_code == "en" or TRANSLATION_MODELS.get(lang_code) is None:
        return None, None
    if lang_code not in loaded_translators:
        model_name = TRANSLATION_MODELS[lang_code]
        app.logger.debug(f"Loading translation model for English to {lang_code}: {model_name}")
        loaded_translators[lang_code] = {
            "model": AutoModelForSeq2SeqLM.from_pretrained(model_name),
            "tokenizer": AutoTokenizer.from_pretrained(model_name)
        }
    return loaded_translators[lang_code]["model"], loaded_translators[lang_code]["tokenizer"]

def translate_en_to_target(text, lang_code):
    model, tokenizer = get_translation_model_and_tokenizer(lang_code)
    if not model or not tokenizer or lang_code == "en":
        return text
    inputs = tokenizer([text], return_tensors="pt", truncation=True, max_length=512)
    outputs = model.generate(**inputs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def summarize_text(text, max_length, min_length):
    inputs = summ_tokenizer([text], max_length=1024, return_tensors="pt", truncation=True)
    with torch.no_grad():
        ids = summ_model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=max_length,
            min_length=min_length,
            early_stopping=True,
        )
    summary = summ_tokenizer.decode(ids[0], skip_special_tokens=True)
    app.logger.debug(f"Summary (first 100 chars): {summary[:100]}")
    return summary

def extract_key_sentences(text, num_sentences=3):
    if not text or len(text.strip()) < 20:
        return []
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if s.strip()][:num_sentences]

def get_sentiment(text):
    if not text.strip():
        return None
    results = sentiment_analyzer(text[:512])
    if results and isinstance(results, list):
        return results[0]
    return None

def fetch_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        app.logger.error(f"Error fetching article: {e}")
        return None

# Smarter chunking by sentences for TTS
def split_text_for_tts(text, max_len=200):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_len:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(sentence) > max_len:
                for i in range(0, len(sentence), max_len):
                    chunks.append(sentence[i:i+max_len])
                current_chunk = ""
            else:
                current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# gTTS with language fallback and chunking
def text_to_audio_base64(text, lang):
    gtts_supported_langs = {
        'af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo',
        'es', 'et', 'fi', 'fr', 'gu', 'hi', 'hr', 'hu', 'id', 'is', 'it', 'ja',
        'jw', 'km', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr', 'my', 'ne', 'nl',
        'no', 'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw',
        'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-CN', 'zh-TW', 'zh'
    }
    audio_lang = lang if lang in gtts_supported_langs else 'en'
    if not text or not text.strip():
        app.logger.warning("Empty text for TTS generation")
        return None
    try:
        chunks = split_text_for_tts(text, 200)
        audio_bytes = BytesIO()
        for chunk in chunks:
            tts = gTTS(text=chunk.strip(), lang=audio_lang, slow=False)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            audio_bytes.write(buf.read())
        audio_bytes.seek(0)
        audio_b64 = base64.b64encode(audio_bytes.read()).decode('utf-8')
        return f"data:audio/mp3;base64,{audio_b64}"
    except Exception as e:
        app.logger.error(f"TTS generation error: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    key_sentences = []
    error = None
    summary_audio = None
    key_sentences_audio = None
    summary_length = "medium"
    language = request.form.get("language", "en") if request.method == "POST" else "en"
    sentiment = None

    if request.method == "POST":
        input_type = request.form.get("input_type")
        summary_length = request.form.get("summary_length", "medium")
        length_map = {
            "short": {"max_length": 60, "min_length": 30},
            "medium": {"max_length": 120, "min_length": 60},
            "long": {"max_length": 200, "min_length": 120},
        }
        selected = length_map.get(summary_length, length_map["medium"])

        if input_type == "url":
            url = request.form.get("url")
            if url:
                article_text = fetch_article_text(url)
                if article_text and article_text.strip():
                    summary_en = summarize_text(article_text, selected["max_length"], selected["min_length"])
                    key_sentences_en = extract_key_sentences(article_text)
                    sentiment = get_sentiment(article_text)

                    summary = translate_en_to_target(summary_en, language)
                    key_sentences = [translate_en_to_target(s, language) for s in key_sentences_en]

                    summary_audio = text_to_audio_base64(summary, language)
                    key_sentences_audio = text_to_audio_base64(" ".join(key_sentences), language)

                    sum_id = uuid.uuid4().hex[:8]
                    summaries_db[sum_id] = {
                        "summary": summary,
                        "key_sentences": key_sentences,
                        "summary_length": summary_length,
                        "url": url,
                        "language": language,
                        "sentiment": sentiment,
                        "summary_audio": summary_audio,
                        "key_sentences_audio": key_sentences_audio,
                    }
                    recent = request.cookies.get("recent_summaries", "")
                    recent_ids = recent.split(",") if recent else []
                    if sum_id in recent_ids:
                        recent_ids.remove(sum_id)
                    recent_ids.insert(0, sum_id)
                    recent_ids = recent_ids[:5]
                    response = make_response(redirect(url_for("shared_summary", sum_id=sum_id)))
                    response.set_cookie("recent_summaries", ",".join(recent_ids), max_age=7 * 24 * 3600)
                    return response
                else:
                    error = "Failed to fetch article content. Please check the URL."
            else:
                error = "Please enter a valid URL."
        elif input_type == "text":
            text = request.form.get("text")
            if text and text.strip():
                summary_en = summarize_text(text, selected["max_length"], selected["min_length"])
                key_sentences_en = extract_key_sentences(text)
                sentiment = get_sentiment(text)

                summary = translate_en_to_target(summary_en, language)
                key_sentences = [translate_en_to_target(s, language) for s in key_sentences_en]

                summary_audio = text_to_audio_base64(summary, language)
                key_sentences_audio = text_to_audio_base64(" ".join(key_sentences), language)

                sum_id = uuid.uuid4().hex[:8]
                summaries_db[sum_id] = {
                    "summary": summary,
                    "key_sentences": key_sentences,
                    "summary_length": summary_length,
                    "text": text,
                    "language": language,
                    "sentiment": sentiment,
                    "summary_audio": summary_audio,
                    "key_sentences_audio": key_sentences_audio,
                }
                recent = request.cookies.get("recent_summaries", "")
                recent_ids = recent.split(",") if recent else []
                if sum_id in recent_ids:
                    recent_ids.remove(sum_id)
                recent_ids.insert(0, sum_id)
                recent_ids = recent_ids[:5]
                response = make_response(redirect(url_for("shared_summary", sum_id=sum_id)))
                response.set_cookie("recent_summaries", ",".join(recent_ids), max_age=7 * 24 * 3600)
                return response
            else:
                error = "Please enter text to summarize."

    recent_ids = request.cookies.get("recent_summaries", "")
    recent_list = []
    if recent_ids:
        for rid in recent_ids.split(","):
            summ = summaries_db.get(rid)
            if summ:
                recent_list.append({"id": rid, "summary": summ["summary"][:100] + "..."})

    return render_template(
        "index.html",
        summary=summary,
        key_sentences=key_sentences,
        error=error,
        summary_length=summary_length,
        language=language,
        sentiment=sentiment,
        recent=recent_list,
        summary_audio=summary_audio,
        key_sentences_audio=key_sentences_audio,
    )

@app.route("/s/<sum_id>")
def shared_summary(sum_id):
    data = summaries_db.get(sum_id)
    if not data:
        abort(404)
    return render_template(
        "shared_summary.html",
        summary=data["summary"],
        key_sentences=data.get("key_sentences", []),
        summary_length=data.get("summary_length", "medium"),
        url=data.get("url"),
        text=data.get("text"),
        language=data.get("language", "en"),
        sentiment=data.get("sentiment"),
        sum_id=sum_id,
        summary_audio=data.get("summary_audio"),
        key_sentences_audio=data.get("key_sentences_audio"),
    )

if __name__ == "__main__":
    app.logger.info("🔥 Flask server is starting with translation + summarization + audio pipeline!")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
