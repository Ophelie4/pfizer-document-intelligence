# Project 5: Introduction to Retrieval-Augmented Generation (RAG)

**Weeks 5–6.** A first chatbot with LlamaIndex, chunking strategies and embeddings, hybrid retrieval with re-ranking, and a complete RAG pipeline over a pharmaceutical SDF.

## Notebooks

| Notebook | Task |
|---|---|
| [`Ophelie_LlamaIndex_Chatbot.ipynb`](notebooks/Ophelie_LlamaIndex_Chatbot.ipynb) | Build a simple chatbot with LlamaIndex and Gemini |
| [`Ophelie_Chunking_Embeddings.ipynb`](notebooks/Ophelie_Chunking_Embeddings.ipynb) | Fixed-length, overlapping and semantic chunking plus embeddings |
| [`Ophelie_Query_Retrieval_Optimization.ipynb`](notebooks/Ophelie_Query_Retrieval_Optimization.ipynb) | Hybrid retrieval (vector + BM25) and cross-encoder re-ranking |
| [`Ophelie_RAG_Pipeline.ipynb`](notebooks/Ophelie_RAG_Pipeline.ipynb) | Complete RAG pipeline for document retrieval |

## Reports

- [RAG Pipeline for Document Retrieval](reports/rag-pipeline-for-document-retrieval.md)

> API keys are read from Colab Secrets. None are hardcoded in the notebooks.

---

## Task answers

### Build a simple chatbot with LlamaIndex
I generated my own Gemini key and added it through Colab Secrets. Along the way I hit and fixed three real bugs:
1. A 429 quota error on the deprecated `llama-index-llms-gemini` package
2. An asyncio event-loop conflict
3. A 404 from a deprecated model name

These three bugs were also the trickiest part of the task. **How I felt after building my first chatbot:** It was a bit tricky.

### Implementing chunking and embeddings in LlamaIndex
The chunking steps themselves (fixed-length, overlapping, semantic) were straightforward once I had a real document loaded. The tricky part was again the Gemini/LlamaIndex integration from the task instructions: `llama-index-llms-gemini` and `models/gemini-2.0-flash` both broke in the previous chatbot task (429 quota error, then a 404 model-deprecation error), so I went straight to `llama-index-llms-google-genai` with `models/gemini-flash-latest` and `nest_asyncio` this time, which worked.

The more interesting finding was in the retrieval test. When I asked a targeted question about storage temperature, the two chunks the query engine actually retrieved (by similarity score) weren't cleanly the "Storage Conditions" section. They were chunks that straddled the Manufacturing and Safety Data sections, because the 300-token/50-token-overlap boundaries cut across topics. Gemini still answered correctly because the storage info happened to fall inside the overlap, but it was a good, concrete illustration of why chunk size and overlap choices actually matter for retrieval quality, not just something the task describes abstractly.

### Hands-on query processing and retrieval optimization
**Challenges:** The retrieval code itself worked once I had a document and an index, but the task instructions skip a step: the hybrid retrieval and reranking code assumes an `index` already exists without showing how it was built from the PDF, so I had to add a chunking + `VectorStoreIndex` step myself between extracting the PDF text and running the rest of the pipeline. I also hit the same Gemini integration issue as the last two tasks (`llama-index-llms-gemini` and `gemini-2.0-flash` are broken for new keys), so I reused the `llama-index-llms-google-genai` + `gemini-flash-latest` fix from before. One interesting result: the BM25 keyword retriever's top hit for "refund policy" actually scored the late-payment/suspension sentence highest (0.53) over the literal Refund Policy section text, because of where the chunk boundary landed relative to keyword overlap.

**What happened when I changed the ranking parameters:** I set the initial `similarity_top_k` to 5 candidates, then reranked down to just the single best result (`top_n=1`) instead of `top_n=2`. The cross-encoder reranker was decisive about it: the top-ranked chunk after reranking (score 2.13) was the same chunk that already ranked first in the `top_n=2` pass, but its relative separation from the next-best result was much clearer, and it correctly stayed anchored on the late-payment/suspension clause rather than drifting toward the more general overview text. So widening the candidate pool didn't change the winner here, but it did make the reranker's confidence gap more visible, which would matter more on a longer, noisier document.

### Build and optimize a RAG pipeline
See the [RAG pipeline report](reports/rag-pipeline-for-document-retrieval.md).

---

## Project recap

**Highlight reel:** The hybrid retriever moment: watching BM25 catch exact values like lot numbers and SOP codes that vector search alone missed, then seeing the RAG pipeline correctly keep the Certificate of Quality separate from the storage letter instead of blending the two.

**Skill I leveled up most:** Debugging under pressure. Between a corrupted notebook upload, a recurring Colab secrets timeout, and a broken LlamaIndex/Gemini integration, I got noticeably faster at reading the actual error instead of the assumed one, isolating what broke, and testing a real fix rather than guessing.

**Hardest part:** Getting hybrid retrieval to actually behave. Vector search alone missed exact values like lot numbers and SOP codes, and BM25 alone missed paraphrased questions. I pushed through by merging both retrievers on node ID, keeping the higher score on overlap, and testing against real queries until the ranking made sense instead of guessing at weights.

**What I'd change:** I'd add a small evaluation set with known expected answers so retrieval and answer quality could be measured with numbers instead of spot-checking outputs by eye.

**Project emoji:** 🤯 my brain got a workout
