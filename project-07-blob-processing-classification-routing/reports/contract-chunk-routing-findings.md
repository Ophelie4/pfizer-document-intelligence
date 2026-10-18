# Route Queries Within a Large Contract PDF: Experiment Findings

**Notebook:** [`Pfizer_Step2_Contract_Chunk_Routing.ipynb`](../notebooks/Pfizer_Step2_Contract_Chunk_Routing.ipynb)

## Setup

pharma-blob-sample.pdf: 10 pages holding 8 separate documents. Each page was tagged with `page`, `doc_type`, `doc_id`, `source_file` and `page_in_doc`, then the pages were concatenated and split with `RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)`, giving 28 chunks. Each chunk was mapped back to the page containing its midpoint and inherited that page's metadata. Indexed with LlamaIndex using `BAAI/bge-small-en-v1.5` embeddings; answers synthesized with Mistral-7B-Instruct-v0.3 in 4-bit on a Colab T4 (no OpenAI key). Metadata was excluded from the embedded text so the vector search could not read the label it was about to be filtered on.

## Measured results

6 questions, top-k = 4, gold = the page that actually holds the answer.

| Configuration | hit@4 | Off-target chunks per query |
|---|---|---|
| Sliding window, no filter | 6/6 | 1.50 |
| Sliding window, doc_type filter | 6/6 | 0.00 |
| One chunk per page, doc_type filter | 6/6 | 0.00 |

Query routing accuracy: 6/6. In every configuration the first correct chunk came back at rank 1.

## 1. Which chunking approach worked better: single page or sliding window?

For this document they tied on accuracy: both put the correct chunk at rank 1 for all six questions. The sliding window is still the better choice, for two reasons that this PDF makes visible.

First, granularity: a page here runs 700 to 1,200 characters, so a page-level chunk hands the synthesizer an entire certificate when the question is about one test result, and the answer gets diluted. The 512-character window returned the exact "Configuration Change History" and "Drawing Changes" sections for the packaging question rather than the whole two-page spec.

Second, boundaries: a sliding window crosses page breaks, so a table or clause split across two pages stays in one chunk. Page chunking cannot do that by construction. The tie here is an artifact of a small, cleanly-structured document; on a real contract with long clauses spanning pages, page chunking would start losing.

## 2. How well did metadata filtering improve retrieval accuracy?

It bought precision, not recall. Dense search alone already found the right page for all six questions, so the filter added nothing to hit rate, but it removed all the noise. Unfiltered retrieval returned 1.5 off-target chunks per query on average; with the `doc_type` filter that dropped to zero, and every returned chunk came from the correct document. The clearest case: "Were there any packaging configuration changes?" pulled a Chain of Custody chunk into rank 4 unfiltered, purely on surface similarity, and the filter removed it without displacing any of the three correct chunks.

The important caveat is that the filter is only as good as the router in front of it. My first version used a bare one-line routing prompt; it scored 3/6 on query classification and dragged filtered hit@4 down to 3/6, because when the router picks the wrong `doc_type` the filter confidently excludes the answer. Rewriting the prompt with an explicit cue-to-document mapping and three worked examples took routing to 6/6 and filtered retrieval to 6/6. That asymmetry matters: unfiltered search degrades gracefully, filtered search fails hard.

One more thing that only shows up if you look for it. Attaching the same `doc_type` to every chunk, as the task template does, makes the filter a no-op, because every chunk passes it. The filter only does work because each chunk inherits the metadata of the page it actually came from.

## 3. Would you trust this setup to find specific terms in a legal contract?

Not on its own. I probed four exact identifiers and dense retrieval found three of them in the top 3 (ECN-2023-0847, DWG-29477427-PKG-R3 and BSE-RA-2023-AKTA-001) but missed lot number 18356721 entirely. The pattern is clear: identifiers with alphabetic structure carry enough signal for an embedding model, a bare digit string does not. That is exactly the failure mode you cannot tolerate in a contract, where the question is often "what does clause 7.3 say" or "find every mention of this lot".

For legal text I would run a hybrid: BM25 or a regex pass for exact terms alongside the dense search, fused before re-ranking, so an exact identifier match cannot be outvoted by semantic similarity. I would also add a cross-encoder re-ranker over the top 20, keep the metadata filter as a soft boost rather than a hard exclusion so a router mistake cannot hide the answer, and return citations with page and chunk index (which this setup already does) so every answer can be checked against the source.
