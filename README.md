#  AI-Powered Multilingual News Intelligence Platform

An enterprise-grade, production-oriented **AI News Intelligence Platform** that transforms long-form unstructured web journalism into structured, multi-dimensional intelligence briefings.

The system combines **hierarchical Map-Reduce summarization**, **multilingual NLP**, **extractive MMR key-point discovery**, **document-level sentiment analysis**, **named entity recognition**, **article comparison**, **translation**, **text-to-speech**, **extractive question answering**, and **Unicode PDF report generation**.

---

## Key Features

###  Multi-Strategy Article Extraction

* Primary article extraction using `newspaper3k`.
* Automatic fallback to semantic HTML extraction using `BeautifulSoup`.
* Text normalization and boilerplate removal.
* Duplicate-content reduction.
* URL validation and anti-SSRF protection.
* Article metadata preservation.

###  Hierarchical Map-Reduce Summarization

* Sentence-aware document chunking.
* Maximum 750-token processing chunks.
* Intermediate summaries generated during the Map phase.
* Recursive reduction for long documents.
* Final synthesis according to the requested summary profile:

  * `short`
  * `medium`
  * `detailed`
* Prevents important information from being lost because of simple token truncation.

###  Extractive Key-Point Discovery

* TF-IDF sentence vectorization.
* Maximal Marginal Relevance (MMR).
* Relevance and diversity balancing.
* Configurable number of key points.
* Returns salient sentences directly from the original article.

###  Document Sentiment Analysis

* Full-document sentiment processing.
* Multi-segment analysis instead of analyzing only the beginning of an article.
* Positive, neutral, and negative probability distributions.
* Overall sentiment label and score.

###  Named Entities & Keywords

Extracts structured information including:

* Person
* Organization
* Location
* Date
* Money
* Percentage
* Important keywords

###  Multilingual Translation

Supports translation of generated content into multiple languages.

* English
* Tamil
* Hindi
* French
* German
* Spanish
* Other supported OPUS-MT languages

Dedicated English-to-Tamil translation is provided using:

`suriya7/English-to-Tamil`

---

## AI & NLP Capabilities

### 1. Long-Document Summarization

The platform uses:

* **DistilBART**
* Sentence-aware chunking
* Map-Reduce summarization
* Recursive reduction
* Configurable summary profiles

This allows the system to process long news articles without simply discarding content beyond a fixed token limit.

### 2. Sentiment Intelligence

Uses:

`distilbert-base-uncased-finetuned-sst-2-english`

The complete article is divided into segments and analyzed to produce a more representative sentiment distribution.

### 3. Extractive MMR Analysis

The MMR pipeline balances:

* Sentence relevance
* Information diversity
* Redundancy reduction

This produces concise factual key points while avoiding repetitive sentences.

### 4. Multilingual NLP

The system uses:

* `suriya7/English-to-Tamil`
* `Helsinki-NLP/opus-mt-en-{lang}`

This enables multilingual news intelligence and regional-language output.

### 5. Article Comparison

Two articles can be compared using semantic similarity to identify:

* Shared topics
* Similar reporting
* Unique information
* Differences between sources

### 6. Extractive Article Q&A

Users can ask questions about article content and retrieve answers from the provided article context.

### 7. Text-to-Speech

The platform provides:

* Browser-based speech support.
* Server-side MP3 generation.
* File-backed audio storage.
* 24-hour audio cache lifecycle.
* Streaming endpoints for generated audio.

---

## Web Interface

The application provides a responsive **Golden Emerald** workspace with:

* Article URL input.
* News article extraction.
* AI-generated summaries.
* Summary length selection.
* Multilingual translation.
* Sentiment visualization.
* Key-point display.
* Named entity information.
* Keyword extraction.
* Article comparison.
* Text-to-speech playback.
* Article question answering.
* PDF report generation.
* Summary history.
* Async processing controls.

---

## Architecture

The system follows a **modular monolith architecture** built around Flask, service-layer separation, model management, repositories, and relational persistence.

```text
                         ┌──────────────────────┐
                         │      Web Browser      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Flask Application  │
                         │      Factory         │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        Article Extraction      Summarization      Analysis
                 │                  │                  │
                 ▼                  ▼          ┌───────┼────────┐
          SSRF Protection       Map-Reduce      │       │        │
                 │              Chunking        ▼       ▼        ▼
                 ▼                  │         MMR   Sentiment   NER
          Article Content          ▼
                              Model Manager
                                    │
                         ┌──────────┼──────────┐
                         │          │          │
                         ▼          ▼          ▼
                      PyTorch    CPU/CUDA   Transformers
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Translation / TTS /  │
                         │ Comparison / Reports │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ SQLite / PostgreSQL  │
                         │    Persistence       │
                         └──────────────────────┘
```

---

## ML Processing Pipeline

```text
Article URL or Text
        ↓
Anti-SSRF Validation
        ↓
Article Extraction
        ↓
Text Normalization
(NFKC Unicode + Boilerplate Removal)
        ↓
Sentence-Aware Chunking
(Max 750 Tokens)
        ↓
┌───────────────────────────┬───────────────────────────┐
│   Abstractive Branch      │    Extractive Branch      │
├───────────────────────────┼───────────────────────────┤
│ DistilBART                │ TF-IDF                    │
│ Map Summarization         │ MMR Ranking               │
│ Reduce Summarization     │ Diverse Key Points        │
│ Final Synthesis           │                           │
└───────────────────────────┴───────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Sentiment + NER + Keywords + Analysis   │
└────────────────────┬────────────────────┘
                     ↓
          Multilingual Translation
                     ↓
              TTS Audio Generation
                     ↓
           PDF Report Generation
                     ↓
        Database Persistence + REST API
```

---

## Long Document Processing

Articles exceeding the processing budget are handled using a hierarchical Map-Reduce strategy.

```text
Long Article
     ↓
Sentence Boundary Detection
     ↓
750-Token Chunks
     ↓
Map Phase
     ↓
Intermediate Summaries
     ↓
Reduce Phase
     ↓
Recursive Reduction if Required
     ↓
Final Synthesis
     ↓
Short / Medium / Detailed Summary
```

The chunker preserves complete sentences instead of cutting text at arbitrary token boundaries.

This prevents the system from losing conclusions, important facts, and information appearing later in long articles.

---

## Model Selection

| Task                         | Model                                             | Purpose                        |
| ---------------------------- | ------------------------------------------------- | ------------------------------ |
| **Summarization**            | `sshleifer/distilbart-cnn-12-6`                   | Abstractive news summarization |
| **Sentiment**                | `distilbert-base-uncased-finetuned-sst-2-english` | Document sentiment analysis    |
| **Tamil Translation**        | `suriya7/English-to-Tamil`                        | English → Tamil translation    |
| **Multilingual Translation** | `Helsinki-NLP/opus-mt-en-{lang}`                  | Multilingual translation       |
| **Sentence Ranking**         | TF-IDF + MMR                                      | Extractive key-point discovery |
| **ML Runtime**               | PyTorch                                           | Model execution                |

---

## Database

The application uses **SQLAlchemy 2.0** with support for:

* SQLite for local development.
* PostgreSQL for production deployment.

### Main Entities

```text
Articles
   │
   ├── Summaries
   │      │
   │      └── Translations
   │
   ├── Analysis Results
   │      ├── Sentiment
   │      ├── Key Points
   │      ├── Keywords
   │      └── Entities
   │
   └── Article Comparisons
```

### Article Data

```text
id
url
content_hash
title
raw_text
cleaned_text
language
word_count
created_at
```

### Summary Data

```text
id
article_id
summary_type
length_profile
text
compression_ratio
processing_time_ms
model_name
created_at
```

### Analysis Data

```text
id
article_id
sentiment_label
sentiment_score
sentiment_distribution
key_points
keywords
entities
```

### Translation Data

```text
id
summary_id
source_language
target_language
translated_text
```

---

##  API Endpoints

| Method | Endpoint                | Description                                        |
| ------ | ----------------------- | -------------------------------------------------- |
| `POST` | `/api/articles/extract` | Extracts article content and metadata from a URL   |
| `POST` | `/api/summarize`        | Generates an AI summary from URL or text           |
| `GET`  | `/api/summaries/{id}`   | Retrieves a stored summary and translations        |
| `POST` | `/api/analyze`          | Performs sentiment, MMR, keyword, and NER analysis |
| `POST` | `/api/translate`        | Translates supplied text                           |
| `POST` | `/api/tts`              | Generates MP3 audio                                |
| `GET`  | `/api/tts/audio/{file}` | Streams generated audio                            |
| `POST` | `/api/compare`          | Compares two articles semantically                 |
| `POST` | `/api/multi-source`     | Performs multi-source consensus and synthesis      |
| `POST` | `/api/article/ask`      | Performs extractive article question answering     |
| `GET`  | `/api/reports/{id}/pdf` | Generates a Unicode PDF report                     |
| `POST` | `/api/reports/pdf`      | Generates a PDF from a summary payload             |
| `GET`  | `/api/history`          | Returns recent summary history                     |
| `GET`  | `/api/health`           | Database and application health check              |
| `GET`  | `/api/ready`            | Model and hardware readiness check                 |

---

## API Response Format

### Success Response

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

### Failure Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ARTICLE_EXTRACTION_FAILED",
    "message": "Detailed error description"
  }
}
```

---

##  Supported Languages

The platform supports multilingual news processing and translation through dedicated and OPUS-MT models.

Examples include:

* 🇬🇧 English
* 🇮🇳 Tamil
* 🇮🇳 Hindi
* 🇫🇷 French
* 🇩🇪 German
* 🇪🇸 Spanish

Tamil translation uses:

```text
suriya7/English-to-Tamil
```

Other supported languages use the corresponding:

```text
Helsinki-NLP/opus-mt-en-{lang}
```

models.

---

##  PDF Reports

The platform can generate branded PDF reports containing:

* Article title
* Summary
* Key points
* Sentiment information
* Translated content
* Article metadata
* Unicode text

Unicode font fallback enables support for scripts including:

* Tamil
* Arabic
* CJK languages

---

##  Text-to-Speech

Generated summaries can be converted into MP3 audio.

```text
Summary Text
     ↓
TTS Service
     ↓
MP3 Generation
     ↓
File Cache
     ↓
Streaming Endpoint
     ↓
Browser Playback
```

Generated audio is stored using a file-backed cache with a 24-hour TTL.

---

##  Security

### Anti-SSRF Protection

External article URLs are validated before requests are made.

Blocked network ranges include:

```text
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
127.0.0.0/8
169.254.169.254
```

This prevents requests to private networks, loopback interfaces, and cloud metadata services.

### Input Sanitization

The platform uses:

* NFKC Unicode normalization.
* HTML entity stripping.
* Sanitized article content.

### HTTP Security Headers

The application provides security headers including:

```text
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

---

##  Prerequisites

### Local Development

* Python 3.10+
* Python 3.12 recommended
* Git
* Sufficient storage for Hugging Face models
* CPU or CUDA-compatible environment

### Docker Deployment

* Docker Desktop
* Docker Compose

---

##  Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/news-intelligence.git
cd news-intelligence
```

### 2. Create a Virtual Environment

**Windows:**

```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file if required by your deployment configuration.

### 5. Start the Application

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

##  Environment Variables

| Variable                          | Default                                           | Purpose                    |
| --------------------------------- | ------------------------------------------------- | -------------------------- |
| `FLASK_ENV`                       | `development`                                     | Application environment    |
| `DATABASE_URL`                    | `sqlite:///news_intelligence.db`                  | Database connection        |
| `REDIS_URL`                       | `redis://localhost:6379/0`                        | Optional Redis connection  |
| `MODEL_DEVICE`                    | `auto`                                            | CPU / CUDA model execution |
| `SUMMARIZATION_MODEL`             | `sshleifer/distilbart-cnn-12-6`                   | Summarization model        |
| `SENTIMENT_MODEL`                 | `distilbert-base-uncased-finetuned-sst-2-english` | Sentiment model            |
| `DEFAULT_TRANSLATION_MODEL_TAMIL` | `suriya7/English-to-Tamil`                        | Tamil translation model    |
| `REQUEST_TIMEOUT_SECONDS`         | `15`                                              | External request timeout   |

---

##  Running with Docker

Build and start the complete application stack:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the application:

```bash
docker compose down
```

The application will be available at:

```text
http://localhost:5000
```

The Docker deployment includes:

```text
Flask Application
       │
       ├── PostgreSQL 16
       │
       └── Redis 7
```

---

##  Automated Testing

The project includes an automated testing suite covering:

* Unit logic
* API contracts
* Failure scenarios
* Security protections
* Article extraction
* Application behavior

Run the tests using:

```bash
pytest tests/ -v
```

Current benchmark from the project:

```text
29 passed, 12 warnings in 1.48s
```

---

##  Evaluation

The summarization pipeline is evaluated using real news articles.

### Evaluation Metrics

| Metric                | Purpose                                                 |
| --------------------- | ------------------------------------------------------- |
| **ROUGE-1**           | Measures unigram overlap                                |
| **ROUGE-2**           | Measures bigram overlap and factual phrase preservation |
| **ROUGE-L**           | Measures longest common subsequence                     |
| **Compression Ratio** | Measures summary size relative to source                |
| **Latency**           | Measures end-to-end processing time                     |

---

##  Benchmark Results

### V1 vs V2

| Metric                |     V1 |         V2 | Improvement |
| --------------------- | -----: | ---------: | ----------: |
| **ROUGE-1 F1**        | 0.2928 | **0.3649** |  **+24.6%** |
| **ROUGE-2 F1**        | 0.0396 | **0.1198** | **+202.2%** |
| **ROUGE-L F1**        | 0.1971 | **0.2570** |  **+30.4%** |
| **Average Latency**   |  9.96s |     10.60s |       +6.5% |
| **Compression Ratio** |  63.9% |      60.0% |       -3.9% |

### Key Result

The hierarchical Map-Reduce approach produced a **202.2% improvement in ROUGE-2 F1**, demonstrating improved preservation of important factual information from later portions of long articles compared with the original truncation-based approach.

---

##  Example Use Cases

After providing an article URL or text, users can perform tasks such as:

* Generate a short news summary.
* Generate a detailed news briefing.
* Extract the most important factual points.
* Analyze article sentiment.
* Identify people, organizations, and locations.
* Translate a summary into Tamil.
* Translate content into Hindi or French.
* Compare two news articles.
* Ask questions about an article.
* Generate a PDF intelligence report.
* Listen to the generated summary using text-to-speech.
* Compare reporting across multiple news sources.

---

##  Limitations

* Sentiment analysis measures linguistic/emotional tone and does not determine factual truth.
* Sentiment scores should not be interpreted as definitive political-bias measurements.
* Abstractive summarization can occasionally introduce incorrect dates, quantities, or details.
* Extractive MMR key points are provided to retain direct factual sentences from the source.
* Translation models may require model downloads during their first execution.
* CPU inference can be slower than GPU inference.
* Model quality depends on the quality and structure of the extracted article content.

---

##  Future Roadmap

*  ONNX Runtime optimization.
*  INT8 quantization for faster CPU inference.
*  Celery + Redis distributed workers.
*  Batch news processing.
*  Knowledge graph entity linking.
*  Wikidata integration.
*  Further multilingual model support.
*  Advanced cross-source news intelligence.

---

##  Technology Stack

| Component                | Technology                        |
| ------------------------ | --------------------------------- |
| **Backend**              | Flask                             |
| **ORM**                  | SQLAlchemy 2.0                    |
| **Database**             | SQLite / PostgreSQL               |
| **Summarization**        | DistilBART                        |
| **Sentiment Analysis**   | DistilBERT                        |
| **Translation**          | MarianMT / English-to-Tamil       |
| **Key-Point Extraction** | TF-IDF + MMR                      |
| **Article Extraction**   | newspaper3k                       |
| **Fallback Extraction**  | BeautifulSoup                     |
| **ML Framework**         | PyTorch                           |
| **NLP Framework**        | Hugging Face Transformers         |
| **Text-to-Speech**       | gTTS                              |
| **PDF Generation**       | Unicode-compatible PDF generation |
| **Caching**              | Redis / File-backed audio cache   |
| **Testing**              | Pytest                            |
| **Containerization**     | Docker + Docker Compose           |

---

##  Project Status

The application currently supports:

*  News article extraction
*  Semantic HTML fallback extraction
*  Anti-SSRF URL protection
*  Long-document processing
*  Hierarchical Map-Reduce summarization
*  Sentence-aware chunking
*  Extractive MMR key points
*  Full-document sentiment analysis
*  Named entity extraction
*  Keyword extraction
*  Tamil translation
*  Multilingual translation
*  Article comparison
*  Multi-source synthesis
*  Extractive article Q&A
*  Text-to-speech
*  File-backed MP3 streaming
*  Unicode PDF reports
*  Relational database persistence
*  REST API
*  Automated testing
*  Docker deployment
*  Health and readiness endpoints

---

##  Author

**Kanishka Pandiaraj**

---

##  License

This project is licensed under the **MIT License**.

See the `LICENSE` file for details.
