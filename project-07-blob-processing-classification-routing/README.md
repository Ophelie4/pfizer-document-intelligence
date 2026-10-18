# Project 7: Blob Processing, Classification, and Routing

**Weeks 7–8.** Splitting a bundled "blob" PDF (one file, many documents) into separate documents, classifying each page, and routing questions to the right document type using metadata filters.

## Notebooks

| Notebook | Task |
|---|---|
| [`Ophelie_Page_Level_Metadata_Boundaries.ipynb`](notebooks/Ophelie_Page_Level_Metadata_Boundaries.ipynb) | Page-level metadata and document boundaries (Gemini) |
| [`Ophelie_Full_Segmentation_Pipeline.ipynb`](notebooks/Ophelie_Full_Segmentation_Pipeline.ipynb) | First version of the segmentation pipeline |
| [`Pfizer_Step1_Segmentation_Pipeline.ipynb`](notebooks/Pfizer_Step1_Segmentation_Pipeline.ipynb) | Full segmentation pipeline with metadata output (Mistral-7B, 4-bit) |
| [`Pfizer_Step2_Query_Routing.ipynb`](notebooks/Pfizer_Step2_Query_Routing.ipynb) | Route queries across multiple PDF files |
| [`Pfizer_Step2_Contract_Chunk_Routing.ipynb`](notebooks/Pfizer_Step2_Contract_Chunk_Routing.ipynb) | Route queries within a large contract PDF |

## Reports

- [Page-Level Metadata and Document Boundaries](reports/page-level-metadata-and-document-boundaries.md)
- [Step 1: Segmentation Pipeline Summary](reports/segmentation-pipeline-summary.md)
- [Contract Chunk Routing Findings](reports/contract-chunk-routing-findings.md)

---

## Task answers

### Extract page-level metadata and determine document boundaries
**Did I have to modify the prompt logic to make it work better for this file?**

Yes. I ran the module's prompts unmodified first so I could see what actually broke, and three things did.

First, `is_same_document()` merged pages 7, 8 and 9 into the Material Description document, so the Supplier Qualification Record and the Global Chain of Custody page never got their own `doc_id` and the run ended with 6 documents instead of 8. The original prompt only asks whether two pages belong to the same document, which gives the model nothing to look at except general similarity, and every page in this file is a Cytiva document about ÄKTA ready flow kits, so everything looks similar. I rewrote it to name the actual boundary signals: a new title block, a different document or lot or article number, a "Page 1 of N" marker, versus continuation signals like the word "continued" or a section sequence carrying on. I also added an explicit instruction that two pages can share a type and a layout and still be different documents, and told it to compare identifiers before answering. That was aimed at pages 1 and 2, which are two Certificates of Quality on the same template for different lots (18356721 and 15102934).

Second, `classify_document_type()` labelled page 0 as "Other" when it is clearly the cover letter, so I constrained the prompt to the exact allowed list and validated the reply against that list instead of accepting free text.

Third, and this one is a code bug rather than a prompt bug, the `.title()` call in the original mangles the category strings: "BSE/TSE Declaration" comes back as "Bse/Tse Declaration" and "Certificate of Quality" as "Certificate Of Quality". That looks harmless but it silently breaks any downstream routing rule that matches on the type string, so I dropped `.title()` and returned the canonical value from the allowed list.

After these changes all 10 pages match the real document structure, which I checked against the first line of each extracted page. One practical note: the free-tier Gemini quota is 15 requests per minute and a 10-page run makes about 15 calls, so I had to throttle the calls to roughly 12 per minute to stop the second run dying on a 429.

### Route queries across multiple PDF files
**Which part of the routing setup made the biggest difference: metadata, prompt, or filtering?**
The metadata, clearly. Once every page in `pdf_metadata_store` carried a `doc_type`, one dictionary filter cut 20 pages down to the 2–5 that could plausibly hold the answer, and it did that before any embedding or full-text search ran. The prompt mattered mostly because it defines the closed label list that both classifiers share: `classify_query_llm` and `classify_doc_type_llm` draw from the same eight labels, so a query label and a page label are guaranteed comparable. Drop that and the filter silently returns nothing. Filtering itself was the cheapest part (a single list comprehension), but it only works because the metadata underneath it is correct, which is why I ended up adding a deterministic header check on top of the model. Keyword scoring never routes; it only re-ranks inside the already filtered set.

**Did the LLM ever pick the wrong document? What confused it, and how would I fix it?**
Yes, on both sides. On the page side, Mistral labelled four pages wrong and all four failed the same way: the visible header was a company letterhead rather than a document title. The Cytiva cover letter came back as `packaging_specification` because the top of the page is an address block, and the STERIS certificate of processing and the compliance bulletin did the same. I fixed it by reading twelve header lines for an explicit document title and letting that beat the model, plus inheriting the previous page's type on a "(continued)" page. That took page labelling to 20/20. On the query side, the one it still gets wrong is "What are the part numbers listed in this document?". It routes to `packaging_specification`, and it is not really wrong, since a released lot carries part numbers on the certificate and a tray or carton carries them on the packaging spec. Vague questions confuse it too: "Tell me about this package" gets a confident wrong label instead of `unknown`. The real fix for both is to let the classifier return a ranked shortlist of types with confidence rather than forcing a single winner.

**How would I scale to 1,000+ PDFs or vague questions?**
Three changes. First, stop classifying at query time and treat labelling as ingestion work: classify each page once when the PDF lands, write `doc_type`, year, `file_id` and issuer into a real index, and keep the router as a metadata lookup. At 1,000+ PDFs the LLM cost is then a one-time 130 seconds per 20 pages instead of a per-query tax. Second, make the filter multi-stage rather than exact-match: shortlist by `doc_type` plus year plus supplier, then run embeddings only inside that shortlist, so semantic search sees hundreds of pages rather than tens of thousands. Third, handle vagueness explicitly instead of hoping for `unknown`: return the top two or three candidate types with confidence, and when the top score is low either ask one clarifying question or search across all types and let the re-ranker decide. I would also add grammar-constrained decoding so the label is always valid, and keep a labelled evaluation set so a prompt change that helps one document type cannot quietly break another.

### Route queries within a large contract PDF
See the [contract chunk routing findings](reports/contract-chunk-routing-findings.md).

---

## Project recap

**Highlight reel:** The moment the segmentation pipeline finally got the two Certificates of Quality right. They look identical on the page (same title, same issuer, same test table) and the only thing separating them is a lot number buried in the middle. Mistral kept merging them into one document no matter how I worded the prompt. Adding a rule that compares lot and document numbers between pages fixed it, and watching that table come out clean was very satisfying.

The other one is the routing setup. Seeing a vague question get filtered down from 20 pages to 3 relevant chunks before any embedding ran made the whole metadata-first idea click for me in a way that reading about it never did.

**Skill I leveled up most:** Prompt engineering, but not in the way I expected. I came in thinking a good prompt was about clear wording. What I actually learned is that you have to design for the model being wrong. Every pipeline I built ended up with a fallback layer underneath the LLM: repairing malformed JSON, mapping off-list labels back onto a fixed list, and deterministic checks that override the model when a page header clearly says something else.

I noticed the growth when I stopped being surprised by bad output and started building for it. By the last task I was writing the fallback before I wrote the prompt.

I also got a lot more comfortable with LlamaIndex and running open-source models locally in 4-bit instead of reaching for an API.

**Hardest part:** Accepting that the model was going to be confidently wrong on the cases that mattered most, and figuring out where to draw the line between fixing the prompt and adding a hard rule.

The worst one was the query router in the last task. My first version scored 3 out of 6, and because a wrong route makes the metadata filter exclude the right chunks, filtered retrieval actually performed worse than doing no filtering at all. That was a horrible result to look at. I pushed through by measuring instead of guessing. I built a small set of questions with the page that actually answers each one, then ran three configurations side by side so I could see exactly where things broke. Rewriting the routing prompt with a cue-to-document mapping and a few examples took it to 6 out of 6.

The general lesson was that I could not fix what I was not measuring.

**What I'd change:** I would let the classifiers return a ranked shortlist with confidence instead of forcing one label.

A few questions do not have one right answer. "What are the part numbers listed in this document?" is the clearest example, since a released lot carries part numbers on the certificate and a tray carries them on the packaging spec. Right now the router has to pick one and it gets marked wrong either way. If it returned the top two or three types with scores, the filter could keep both in play and a low top score could trigger a clarifying question instead of a confident mistake.

I would also add a lexical search alongside the embeddings. Testing exact identifiers showed the vector search found three out of four but missed a plain lot number completely, which is not something you can live with on contract documents.

**Project emoji:** 😅 challenging but worth it
