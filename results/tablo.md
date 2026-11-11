Test set frozen 2026-11-11 15:18 (150 questions, sha256 b4bae07e3a80); primary set n = 106. Knowledge base b3c7d85cce08, chunks 2b5af885972a.
Mean evidence recall, 95% paired-bootstrap interval over questions (10,000 resamples, seed 0).

| System | R@1 | R@5 | R@10 | MRR@10 |
|---|---|---|---|---|
| BM25 + 721-character windows (baseline) | 0.142 [0.075, 0.208] | 0.274 [0.193, 0.358] | 0.335 [0.250, 0.425] | 0.186 [0.122, 0.256] |
| BM25 + article chunks (method) | — | — | — | — |
| e5 (multilingual-e5-base) + 721-character windows (baseline) | 0.189 [0.118, 0.264] | 0.429 [0.340, 0.519] | 0.571 [0.472, 0.660] | 0.275 [0.207, 0.345] |
| e5 (multilingual-e5-base) + article chunks (method) | — | — | — | — |

Method rows stay empty until the single final test run (scripts/deney.py --son).
