# News Summarizer: V1 vs V2 Benchmark Evaluation Report

Evaluation performed on test dataset using real model inference on CPU.

| Metric | V1 (Baseline Truncation) | V2 (Hierarchical Map-Reduce) | Delta / Improvement |
|---|---|---|---|
| **ROUGE-1 (F1)** | 0.2928 | 0.3649 | +24.6% |
| **ROUGE-2 (F1)** | 0.0396 | 0.1198 | +202.2% |
| **ROUGE-L (F1)** | 0.1971 | 0.2570 | +30.4% |
| **Avg Latency (s)** | 9.96s | 10.60s | +6.5% |
| **Compression Ratio** | 63.9% | 60.0% | -3.9% |

### Key Technical Observations
1. **Tail Information Retention**: V1 hard-truncated input at 1024 characters, completely discarding concluding facts and recommendations. V2 preserved facts across all document sections.
2. **Sentence Integrity**: V1 cut text across arbitrary character boundaries. V2 chunking operates along sentence boundaries, preventing fragmented summary tokens.
3. **Extractive MMR**: Extractive key point discovery eliminated duplicate sentences that previously occurred in naive slicing.