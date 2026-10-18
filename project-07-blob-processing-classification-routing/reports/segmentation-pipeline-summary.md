# Step 1: Full Segmentation Pipeline with Metadata Output

**Notebook:** [`Pfizer_Step1_Segmentation_Pipeline.ipynb`](../notebooks/Pfizer_Step1_Segmentation_Pipeline.ipynb)

## Which open-source model I used and why

I used Mistral-7B-Instruct-v0.3, loaded in 4-bit (NF4) on a Colab T4. At 7B it follows formatting instructions well enough to return clean JSON under greedy decoding, so the run is deterministic and reproducible. It is Apache-2.0 licensed, which matters for pharmaceutical work that may eventually have to run on-premise behind a firewall, and quantised it leaves plenty of headroom on a free GPU.

## Edge cases that were tricky

The hard one was pages 1 and 2: two Certificates of Quality with identical titles, issuers and test tables, differing only in lot number (18356721 vs 15102934). Even with a few-shot example covering exactly this case, Mistral answered "No" and merged them into a single two-page certificate. I added a deterministic identifier check (a page that repeats a document title but carries a disjoint set of lot, document and part numbers starts a new document) and that recovered it. Page 2 was the only page in the whole run that needed a fallback.

Continuation pages were the mirror problem: pages 4 and 8 open with fresh-looking section headings such as "4. Configuration Change History", which read as new documents until you notice the "(continued)" marker.

## How I would improve reliability further

I would add grammar-constrained decoding so malformed JSON becomes impossible, use self-consistency voting on the pages the model flags as ambiguous, and emit a per-page confidence score that routes low-confidence pages into a human review queue.

## Final output (10 pages, 8 documents)

| Page | is_new_doc | doc_type | page_in_doc |
|---|---|---|---|
| 0 | Yes | Cover Letter | 0 |
| 1 | Yes | Certificate of Quality | 0 |
| 2 | Yes | Certificate of Quality | 0 |
| 3 | Yes | Packaging Component Specification | 0 |
| 4 | No | Packaging Component Specification | 1 |
| 5 | Yes | BSE/TSE Declaration | 0 |
| 6 | Yes | Material Description Sheet | 0 |
| 7 | Yes | Supplier Qualification Record | 0 |
| 8 | No | Supplier Qualification Record | 1 |
| 9 | Yes | Chain of Custody | 0 |
