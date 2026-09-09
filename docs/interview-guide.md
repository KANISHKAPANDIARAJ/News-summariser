# AI/ML & Backend Engineering Interview Guide

This guide provides structured talking points and in-depth explanations for technical interviews across AI/ML Engineering, Python Backend Engineering, and System Design.

---

### 1. Project Explanation (Elevator Pitch)
"I designed and engineered an enterprise-grade, multilingual News Intelligence Platform that transforms long-form unstructured web journalism into actionable intelligence. The platform performs hierarchical Map-Reduce abstractive summarization, extractive key-point discovery using Maximal Marginal Relevance (MMR), document sentiment distribution analysis, named entity recognition, and multilingual translation with dedicated Tamil support. It replaces naive truncation with token-aware chunking, provides resilient SSRF security guards, and exposes production-grade REST APIs backed by SQLAlchemy 2.0."

---

### 2. Architecture: Why a Modular Monolith?
- **Decision**: Avoided microservice sprawl (e.g. running 5 separate containers for scraper, summarizer, sentiment, etc.) in favor of a clean modular monolith with service, repository, and API layers.
- **Benefits**: Eliminates network latency between ML steps, removes distributed transaction overhead, simplifies local reproducibility, and allows CPU/GPU memory sharing within a single process.
- **Evolution Path**: The service layer is 100% decoupled from Flask/HTTP; any service can be extracted into an independent Celery worker or FastAPI service with zero rewrites.

---

### 3. ML Pipeline & Model Selection
- **Summarization**: Selected `sshleifer/distilbart-cnn-12-6` because it delivers 95% of full BART-large summarization quality at 50% lower parameter count and memory footprint, making it ideal for CPU execution and predictable horizontal scaling.
- **Key Points**: Implemented Maximal Marginal Relevance (MMR) over TF-IDF/sentence embeddings rather than naive punctuation slicing. MMR explicitly balances document relevance ($\lambda=0.65$) against redundancy suppression ($1-\lambda$).
- **Sentiment**: Used DistilBERT-SST-2 with multi-segment document sampling. Rather than a naive binary prediction on the first paragraph, it evaluates segments across the entire text to produce an aggregated positive/neutral/negative distribution.

---

### 4. How Long-Document Summarization Works
- **Problem in V1**: Hard truncation at 1024 tokens lost up to 80% of long articles.
- **Solution (Hierarchical Map-Reduce)**:
  1. Token estimation and sentence segmentation without breaking sentences across chunk boundaries.
  2. Map Phase: Summarize each 750-token chunk into an intermediate representation.
  3. Reduce Phase: Concatenate intermediate representations; if combined text exceeds chunk budget, recursively reduce.
  4. Final Synthesis: Generate coherent final summary adhering to requested length profile (`short`, `medium`, `detailed`).

---

### 5. Benchmark Evaluation (Measured Proof)
- Demonstrates genuine engineering rigor:
  - **ROUGE-1**: +24.6% improvement
  - **ROUGE-2**: +202.2% improvement (bi-gram factual retention)
  - **ROUGE-L**: +30.4% improvement
  - **Latency Overhead**: Only +6.5% on CPU for complete long-document processing.

---

### 6. Performance Optimizations
- **Lazy Model Loading**: Singleton `ModelManager` loads models on demand, reducing server cold start from 35s to <1s.
- **Content Hashing & Caching**: Deterministic SHA-256 hashes prevent re-scraping or re-summarizing identical articles.
- **Audio TTL Cache**: Replaced in-memory Base64 string concatenation with file-backed MP3 generation with automatic 24-hour cleanup.

---

### 7. Security Hardening
- **Anti-SSRF Protection**: Custom validator verifies URL scheme, resolves DNS, and cross-checks IP against private networks (RFC1918 `10/8`, `172.16/12`, `192.168/16`), loopback (`127/8`), and cloud metadata (`169.254.169.254`).
- **Input Sanitization**: NFKC Unicode normalization and HTML entity stripping to prevent stored XSS.
- **Production Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection enabled via middleware.

---

### 8. Database & Storage Design
- Upgraded from ephemeral `summaries_db = {}` to SQLAlchemy 2.0 ORM.
- Tables: `articles`, `summaries`, `analysis_results`, `translations`, `article_comparisons`, `processing_jobs`.
- Indexed on `content_hash`, `url`, `created_at`, and foreign keys (`article_id`).
- Supports SQLite for local dev and PostgreSQL for production.

---

### 9. API Design & Reliability
- RESTful standards: `/api/articles/extract`, `/api/summarize`, `/api/analyze`, `/api/translate`, `/api/tts`, `/api/compare`, `/api/health`.
- Consistent response envelope: `{ "success": true, "data": {} }` and structured error handling `{ "success": false, "error": { "code": "...", "message": "..." } }`.
- Pydantic schema validation for strict payload validation.

---

### 10. Automated Testing Strategy
- 29 automated tests across unit, integration, and failure modes.
- Tests malicious inputs (SSRF attempts, invalid schemes, unsupported languages, short texts, 404 lookups).
- 100% test pass rate with pytest.

---

### 11. Docker & Orchestration
- Multi-stage `Dockerfile` with non-root user (`appuser`).
- `docker-compose.yml` orchestrates App, PostgreSQL 16, Redis 7, with health checks and persistent named volumes.

---

### 12. Tamil Language Specialization
- Preserved and verified `suriya7/English-to-Tamil` fine-tuned model for English-to-Tamil translation.
- Sentence-by-sentence translation prevents token truncation on long summaries.
- Tested on native Tamil text in the evaluation dataset.

---

### 13. Key Technical Challenges Overcome
1. **Model Cold Start**: Solved via lazy singleton loader with thread locks.
2. **Chunk Boundary Fragmentation**: Engineered `SentenceAwareChunker` that guarantees zero sentence splitting.
3. **SSRF Vulnerabilities**: Implemented proactive DNS resolution and IP subnet checking.

---

### 14. Future Improvements (Roadmap)
- Integration of vLLM / ONNX Runtime for quantized GPU/CPU inference speedup.
- Asynchronous task distribution with Celery + Redis for high-concurrency batch document ingest.
- Fine-grained semantic entity linking against Wikidata / Wikipedia knowledge graphs.
