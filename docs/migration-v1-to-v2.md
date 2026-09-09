# Migration Guide: V1 News Summariser to V2 News Intelligence Platform

This document details the architectural and engineering transformation from the original college project (V1) to the production-grade platform (V2).

---

## 1. Architectural Evolution

| Area | V1 (College Project) | V2 (Production Platform) | Technical Rationale |
|---|---|---|---|
| **Architecture** | Monolithic 300-line `app.py` script | Modular monolith with Application Factory & Blueprints | Clear separation of concerns, testability, maintainability. |
| **Model Loading** | Global eager load at import time | Thread-safe lazy loading singleton (`ModelManager`) | Reduces process boot time from 35s to <1s, allows graceful scaling. |
| **Long Document Strategy** | Hard cut at 1024 tokens | Sentence-aware chunking + Hierarchical Map-Reduce | Prevents tail information loss, preserves 100% of article context. |
| **Key Point Discovery** | Naive split and slice `[:3]` sentences | Maximal Marginal Relevance (MMR) ranking | Extracts topical centroids while mathematically penalizing redundancy. |
| **Sentiment Analysis** | First 512 characters binary label | Multi-segment document distribution (pos/neu/neg) | Captures tonal shifts throughout long articles; includes bias disclaimer. |
| **Named Entities** | Not supported | Structured NER (PERSON, ORG, LOC, DATE, MONEY, %) | Extracts high-value journalistic entities without exposing raw tokens. |
| **Translation** | Unregistered dropdown languages, 512 token truncation | Verified registry matching UI, sentence chunked translation | UI never advertises languages that cannot be translated; long text support. |
| **Text-to-Speech** | In-memory raw MP3 Base64 string in HTML/dict | File-backed MP3 generation with TTL cache and streaming | Eliminates memory leaks and payload bloat; supports real file downloads. |
| **Persistence** | In-memory python dictionary `summaries_db = {}` | SQLAlchemy 2.0 ORM with SQLite (dev) / PostgreSQL (prod) | Full relational persistence, indexing, foreign keys, and audit trails. |
| **Security** | SSL verification disabled, no SSRF check, debug=True | Strict SSRF IP filtering, input validation, secure headers | Prevents internal network scanning, MITM vulnerabilities, and XSS. |
| **APIs** | Form POST only, no REST endpoints | Complete Pydantic-validated REST API layer | Standard JSON envelope (`success`, `data`, `error`), HTTP status codes. |
| **Testing & CI** | Zero tests, no CI/CD | 29 Pytest tests (unit, API, failure), GitHub Actions | Automated regression detection on every push/PR. |

---

## 2. Benchmark Evaluation Metrics (Measured on Real Test Articles)

The evaluation was executed using `evaluation/benchmark_runner.py` comparing the exact V1 vs V2 pipelines:

```text
| Metric                 | V1 (Baseline) | V2 (Hierarchical) | Improvement |
|------------------------|---------------|-------------------|-------------|
| ROUGE-1 (F1)           | 0.2928        | 0.3649            | +24.6%      |
| ROUGE-2 (F1)           | 0.0396        | 0.1198            | +202.2%     |
| ROUGE-L (F1)           | 0.1971        | 0.2570            | +30.4%      |
| Average Latency (s)    | 9.96s         | 10.60s            | +6.5%       |
| Compression Ratio      | 63.9%         | 60.0%             | -3.9%       |
```

### Interpretation of Results
- **ROUGE-2 Jump (+202%)**: The dramatic increase in bi-gram overlap demonstrates that the Map-Reduce pipeline preserves specific factual pairings and clauses from later paragraphs that V1 completely dropped.
- **Controlled Latency**: The +6.5% latency delta is minimal considering the platform processes 100% of multi-thousand word articles rather than slicing the first few paragraphs.
