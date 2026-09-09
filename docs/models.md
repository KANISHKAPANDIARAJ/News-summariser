# Model Cards & AI Transparency Documentation

This document describes the models used in the platform, their operational characteristics, limitations, and ethical considerations.

---

## 1. Summarization Model

- **Model Identifier**: `sshleifer/distilbart-cnn-12-6`
- **Architecture**: Distilled BART (Bidirectional and Auto-Regressive Transformers) Seq2Seq model.
- **Task**: Abstractive News Summarization.
- **Pretraining / Finetuning**: Pretrained on English corpus; fine-tuned on CNN/DailyMail news dataset.
- **Input Limit**: 1024 tokens per forward pass.
- **V2 Strategy**: Sentence-aware chunking (max 750 tokens) with hierarchical Map-Reduce synthesis.
- **Memory Footprint**: ~1.2 GB RAM (CPU FP32).
- **Known Limitations**:
  - Tends to adopt the journalistic style of the CNN/DailyMail dataset.
  - Can occasionally hallucinate dates, proper nouns, or numerical figures if input sentences are ambiguous.
  - Performance degrades on highly colloquial or non-standard syntax.

---

## 2. Sentiment Analysis Model

- **Model Identifier**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Architecture**: Distilled BERT Transformer Classifier.
- **Task**: Sentence-level binary polarity classification (Positive / Negative).
- **V2 Strategy**: Evaluates representative sentences across the beginning, middle, and tail of documents to compute a continuous distribution (`positive`, `neutral`, `negative`).
- **Memory Footprint**: ~260 MB RAM.
- **Critical Disclaimer**:
  - *Sentiment analysis measures linguistic emotion and polarity; it is NOT an indicator of factual accuracy, political bias, or credibility.*
  - The platform explicitly displays a disclaimer alongside sentiment outputs.

---

## 3. Translation Models

- **Primary Tamil Model**: `suriya7/English-to-Tamil`
- **Multilingual Models**: `Helsinki-NLP/opus-mt-en-{lang}` (Hindi, French, German, Spanish, etc.)
- **Task**: Machine Translation.
- **V2 Strategy**: Sentence-by-sentence translation with SHA-256 caching.
- **Known Limitations**:
  - Nuances of regional dialects or colloquial idioms may not translate accurately.
  - Technical acronyms or proper nouns can occasionally undergo literal mistranslation.

---

## 4. Hallucination & Factuality Safeguards

1. **Extractive MMR Anchors**: The platform pairs abstractive summaries with extractive key points (`KeypointExtractor`) pulled verbatim from the source article. This allows readers to cross-reference model-generated assertions against source sentences.
2. **Transparency in UI**: Model outputs are clearly designated as AI-synthesized summaries, not guaranteed objective facts.
