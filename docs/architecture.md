# System Architecture: AI News Intelligence Platform

## 1. High-Level Architecture

The platform is designed as a **production-oriented modular monolith** combining robust web extraction, NLP inference services, relational persistence, and secure REST APIs.

```mermaid
graph TD
    Client[Web Browser / API Client] -->|HTTP / JSON| ReverseProxy[Reverse Proxy / Gunicorn WSGI]
    ReverseProxy -->|Routes| FlaskApp[Flask Application Factory]

    subgraph API Layer
        FlaskApp --> WebUI[Web Dashboard & Shareable Reports]
        FlaskApp --> ArticlesAPI[/api/articles/extract]
        FlaskApp --> SummarizeAPI[/api/summarize]
        FlaskApp --> AnalysisAPI[/api/analyze]
        FlaskApp --> TranslateAPI[/api/translate]
        FlaskApp --> CompareAPI[/api/compare]
        FlaskApp --> AudioAPI[/api/tts]
    end

    subgraph Service Layer
        ArticlesAPI --> Extractor[Article Extractor + SSRF Guard]
        SummarizeAPI --> Summarizer[Hierarchical Map-Reduce Summarizer]
        SummarizeAPI --> Chunker[Sentence-Aware Chunker]
        AnalysisAPI --> MMR[MMR Key-Point Extractor]
        AnalysisAPI --> Sentiment[Multi-Segment Sentiment Analyzer]
        AnalysisAPI --> NER[Named Entity Recognizer]
        AnalysisAPI --> Keywords[TF-IDF Keyword Saliency]
        TranslateAPI --> Translator[Multilingual Translation Service]
        AudioAPI --> TTSService[File-Backed TTS + TTL Cache]
    end

    subgraph ML & Model Management
        Summarizer --> ModelManager[Thread-Safe Model Manager]
        Sentiment --> ModelManager
        Translator --> ModelManager
        ModelManager --> CPU_GPU[CPU / GPU PyTorch Runtime]
    end

    subgraph Storage Layer
        FlaskApp --> Repositories[Repository Pattern]
        Repositories --> DB[(SQLite / PostgreSQL via SQLAlchemy 2.0)]
        TTSService --> FileCache[Disk Audio Cache]
        Summarizer --> Cache[In-Memory / Redis Cache]
    end
```

---

## 2. Long-Document Hierarchical Summarization Pipeline

```mermaid
sequenceDiagram
    participant User as Client
    participant API as /api/summarize
    participant Chunker as SentenceAwareChunker
    participant MM as ModelManager
    participant DB as SQLite / PostgreSQL

    User->>API: POST /api/summarize (URL or Long Text)
    API->>Chunker: Segment along sentence boundaries (Max 750 tokens)
    Chunker-->>API: Chunks [C1, C2, ..., Cn]

    alt Single Chunk (<750 tokens)
        API->>MM: Generate Direct Summary
        MM-->>API: Final Summary
    else Multi-Chunk Long Document
        loop Map Phase
            API->>MM: Generate Intermediate Summary for Ci
            MM-->>API: Intermediate Summary Si
        end
        API->>API: Concatenate Intermediate Summaries [S1..Sn]
        API->>MM: Synthesize Final Abstractive Summary
        MM-->>API: Coherent Final Summary
    end

    API->>DB: Persist Article, Summary & Metrics
    API-->>User: JSON Response (Summary, Compression Ratio, Latency)
```

---

## 3. Data Model Schema

```mermaid
erDiagram
    ARTICLES ||--o{ SUMMARIES : "has"
    ARTICLES ||--o| ANALYSIS_RESULTS : "has"
    SUMMARIES ||--o{ TRANSLATIONS : "has"
    ARTICLES ||--o{ ARTICLE_COMPARISONS : "compares"

    ARTICLES {
        string id PK
        string url
        string content_hash UK
        string title
        string author
        string publisher
        string published_date
        text raw_text
        text cleaned_text
        string language
        int word_count
        datetime created_at
    }

    SUMMARIES {
        string id PK
        string article_id FK
        string summary_type
        string length_profile
        text text
        float compression_ratio
        float processing_time_ms
        string model_name
        datetime created_at
    }

    ANALYSIS_RESULTS {
        string id PK
        string article_id FK
        string sentiment_label
        float sentiment_score
        json sentiment_distribution
        json key_points
        json keywords
        json entities
        datetime created_at
    }

    TRANSLATIONS {
        string id PK
        string summary_id FK
        string source_language
        string target_language
        text translated_text
        string model_name
        datetime created_at
    }

    PROCESSING_JOBS {
        string id PK
        string status
        int progress
        string stage
        text error_message
        json result_data
        datetime completed_at
    }
```
