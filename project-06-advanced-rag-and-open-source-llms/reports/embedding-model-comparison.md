# Embedding Model Comparison Results

**Date:** August 11, 2026
**Document tested:** Sample SDF Document
**Notebook:** [`Ophelie_Embedding_Model_Comparison.ipynb`](../notebooks/Ophelie_Embedding_Model_Comparison.ipynb)

## Part 1: Model scorecards

| Criteria | Model 1: MiniLM | Model 2: E5 | Model 3: BGE |
|---|---|---|---|
| **Answer quality** (clear and complete?) | Clear and correct on all 3 queries. | Clear, correct, and most detailed. Explicitly named the missing SOP detail. | Clear and correct on all 3 queries, similar to MiniLM. |
| **Context relevance** (right chunks?) | Retrieved correct chunks; lower similarity scores (0.20–0.42). | Retrieved correct chunks with much higher similarity scores (0.79–0.83). | Retrieved correct chunks with mid-range similarity scores (0.61–0.65). |
| **Speed** (embedding + retrieval) | Build: 6.138s. Avg retrieve: 0.0235s (fastest of the 3). | Build: 6.153s. Avg retrieve: 0.0478s. | Build: 5.704s (fastest build). Avg retrieve: 0.0500s (slowest retrieval). |
| **Consistency** (different queries?) | Correct answers on all 3 queries, no failures. | Correct on all 3, with the most confident/highest scores throughout. | Correct answers on all 3 queries, no failures. |
| **Overall score (1–5)** | 4 | **5** | 4 |

### Model 1: MiniLM (`sentence-transformers/all-MiniLM-L6-v2`)
**Query:** What test methods were used for quality control?
**Answer:** Autoclave (Pump tubing) 121C > 15 min; Gamma Irradiation (Inlets) 25.0–40.0 kGy; Flow Rate Test per SOP-QC-042; Pressure Integrity (Max 0.5 bar, 5 min hold); Visual Inspection; Package Integrity; Bio-safety/USP <88> conformance.
**Retrieved chunks:** Top-3 via `similarity_top_k=3`; top chunk score = 0.3374 (Chunk 5, the QC test-results table).
**Observations:**
- Correct answer despite the lowest raw similarity score among the 3 models on this query. This shows the RAG pipeline is forgiving of a weaker embedding when the corpus is small.
- Retrieval was easy here because the doc is short (~4,000 chars) and the query keywords match the source text almost verbatim, so all 3 models found the right chunks.

### Model 2: E5 (`intfloat/e5-small-v2`)
**Query:** What test methods were used for quality control?
**Answer:** Autoclave (Pump tubing) 121C > 15 min; Gamma Irradiation (Inlets) 25.0–40.0 kGy; Flow Rate Test per SOP-QC-042; Pressure Integrity; Visual Inspection; Package Integrity. Explicitly noted what was missing: the detailed SOP-QC-042 procedural steps aren't in the context.
**Retrieved chunks:** Top-3 via `similarity_top_k=3`; top chunk score = 0.7915 (Chunk 5), much higher than MiniLM's 0.3374 on the same query.
**Observations:**
- This notebook deliberately does NOT add E5's trained "query: "/"passage: " input prefixes, to keep the model swap a fair drop-in comparison. Despite that, E5 still had the highest similarity scores of the 3. That's a documented trade-off, not a bug.
- Slightly slower average retrieval than MiniLM (0.0478s vs 0.0235s), but the gap is small in absolute terms on this small corpus.

### Model 3: BGE (`BAAI/bge-small-en-v1.5`)
**Query:** What test methods were used for quality control?
**Answer:** Flow Rate Test per SOP-QC-042; Pressure Integrity; Visual Inspection; Package Integrity; Autoclave (Pump tubing) 121C > 15 min; Gamma Irradiation (Inlets) 25.0–40.0 kGy; Bio-safety/USP <88> conformance.
**Retrieved chunks:** Top-3 via `similarity_top_k=3`; top chunk score = 0.6146 (Chunk 5), between MiniLM (0.3374) and E5 (0.7915).
**Observations:**
- Correct, clear answer, phrased in a slightly different order (led with Flow Rate Test instead of Autoclave), but equally complete.
- Fastest embed+index build time of the 3 (5.704s), but slowest average retrieval (0.0500s). Build speed and query speed didn't move together across models.

## Part 2: Analysis

**1. Which model performed best across the board?**
E5 (`intfloat/e5-small-v2`). It scored highest on retrieval confidence (top-chunk similarity 0.79–0.83 across all 3 queries) while still producing fully correct, clear answers on every query.

**2. What did that model excel at?**
Retrieval confidence. E5's cosine similarity scores were consistently the highest of the 3 models (0.79–0.83 vs MiniLM's 0.20–0.42 and BGE's 0.61–0.65), and it was the only model whose answer explicitly flagged what was missing from the context (the SOP-QC-042 procedural details).

**3. Why did you pick it as the best?**
It combined the highest, most consistent retrieval confidence with equally correct answers, and did so without any tuning (no query:/passage: prefixes applied). On a longer or more ambiguous document, where retrieval is less trivial, that confidence margin over MiniLM and BGE would likely translate into a real accuracy advantage rather than just a scoring difference.

**4. Any surprising results or trade-offs?**
Answer quality barely differed between the 3 models. MiniLM, E5, and BGE all produced essentially correct answers on all 3 queries, because the test document is short (~4,000 characters) and the queries closely match the source wording, making retrieval easy regardless of the embedding used. The real differentiator turned out to be retrieval confidence (similarity score) and speed, not correctness. Two other trade-offs worth flagging: E5 scored highest despite this notebook deliberately NOT using its recommended "query: "/"passage: " input prefixes (a fair drop-in swap, but not how E5 was intended to be used); and BGE had the fastest embed+index build time (5.704s) but the slowest average retrieval (0.0500s).
