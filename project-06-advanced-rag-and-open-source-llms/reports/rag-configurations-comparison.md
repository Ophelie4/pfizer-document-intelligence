# RAG Configurations Comparison Results

**Date:** August 11, 2026
**Document tested:** Sample SDF Document
**Query used:** "What test methods were used for quality control?"
**Notebook:** [`Ophelie_RAG_Configurations_Comparison.ipynb`](../notebooks/Ophelie_RAG_Configurations_Comparison.ipynb)

## Part 1: Configuration comparison

| Config | Chunks retrieved | Best chunk (excerpt) | Answer (shortened) | Confidence (1–5) | Notes |
|---|---|---|---|---|---|
| **A** | 5 | "Autoclave–Pump tubing 121°C>15min; Flow Rate Test Per SOP-QC-042; Pressure Integrity Max 0.5 bar 5min" (score 0.337) | Lists 6 test methods (Autoclave, Gamma Irradiation, Flow Rate, Pressure Integrity, Visual & Package Integrity) + Bio-safety (USP <88> Class VI). Notes other products' methods aren't detailed in context. | 4 | Baseline, no filtering. Retrieved a very weak match (score 0.147) alongside the strong ones. |
| **B** | 4 | Same top chunk as A (score 0.337) | Same core test methods. The Bio-safety chunk fell below the 0.15 threshold, so USP <88> is omitted here. | 4 | Raising top_k to 8 didn't add surviving chunks vs A's threshold-filtered set; still 4. Fastest retrieval step (0.021s). |
| **C** | 4 | Same top chunk as A/B (score 0.337), but the reranker moved the regulatory Bio-safety chunk above the device-spec chunk. | Same 6 test methods as A, plus Bio-safety (USP <88> Class VI). The reranker's semantic reordering surfaced that chunk over a lower-relevance product-spec chunk. | **5** | LLM reranker promoted regulatory content over device specs. Most complete answer, but retrieve+rerank cost 4.517s vs B's 0.021s. |

## Part 2: Analysis

**Describe the three configurations. What changed in each?**
All three configs used the same query, same document, same chunking (200/30), and the same embedding index. Only the retrieval logic changed.
- **Config A** is the default: `top_k=5`, no threshold, no reranker.
- **Config B** raised `top_k` to 8 and added a 0.15 similarity-score threshold to filter weak matches (the threshold value came from the real MiniLM score range observed in the earlier embedding-comparison task).
- **Config C** kept A's `top_k=5` and B's 0.15 threshold, but added a custom LLM-based reranker (built from scratch, since LlamaIndex's built-in `LLMRerank` isn't reliable with non-OpenAI models) that asks Gemini to reorder the retrieved chunks by relevance before generating the answer.

**Which configuration gave the best result, and why?**
Config C (`top_k=5`, threshold 0.15, reranker on). All three configs surfaced the same top-scoring chunk and produced very similar answers, since the document is short and the strongest chunk (score 0.337) dominated every config. The real difference showed up in what got included: A's unfiltered top-5 included a weak 0.147-score chunk that just added noise, while B's threshold quietly dropped the Bio-safety/regulatory chunk, so B's answer left out the USP <88> compliance detail. C used the same filtered set as B, but the LLM reranker semantically reordered the chunks and pulled the regulatory chunk back to the top, so its final answer was the most complete of the three (it kept both the test-method table and the bio-safety detail). The cost was real latency, 4.517s for retrieve+rerank versus 0.021–0.032s for A/B. So C is the right choice when answer completeness matters more than speed, while B is the better choice for a latency-sensitive pipeline where the default top-k is already picking up noise.
