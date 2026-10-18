# Full RAG Pipeline: Project Write-up

**August 31, 2026**
**Notebook:** [`Pfizer_Capstone_Full_RAG_UI.ipynb`](../notebooks/Pfizer_Capstone_Full_RAG_UI.ipynb)
**Test corpus:** two pharmaceutical supplier packets, 20 pages, 8 distinct documents, 49 chunks.

## 1. How did you build your RAG pipeline?

Seven stages, each one able to fail loudly rather than quietly.

**Extraction.** PyMuPDF reads each page. If a page comes back with fewer than 40 characters it has no text layer, so it is rasterised at 200 dpi and passed through Tesseract instead. Pages record which route they took, because an OCR page is noisier and a reader deserves to know.

**Metadata tagging.** Every page is tagged with `doc_type`, `doc_id`, `source_file`, `page`, `page_range` and an `ocr` flag. `doc_type` comes from the document title in the page header, read across the first twelve lines because company letterheads push the real title down the page. A "(continued)" page inherits the previous page's type, and two same-titled pages carrying different lot numbers are treated as two separate documents, so `doc_id` counts real documents rather than page runs. On the test corpus this produced 8 documents across 7 types from 20 pages.

**Chunking.** Pages are split into 700-character chunks with 120 characters of overlap, breaking on the largest natural boundary available: paragraph, then line, then sentence, then word. Every chunk inherits the full metadata of its page.

**Embedding and indexing.** Chunks are embedded with `BAAI/bge-small-en-v1.5` and stored in a FAISS `IndexFlatIP` over L2-normalised vectors, which makes an inner-product search an exact cosine search.

**Retrieval with filtering.** One index serves the whole corpus. When a `doc_type` filter is set, the search over-fetches from FAISS and keeps only the chunks whose metadata matches, so filtering never requires a second index.

**Prompting.** Passages are numbered and labelled with their type, file and page. The model is told to use only those passages, to cite the numbers it used, and to say so plainly when the passages do not contain the answer.

**Generation and response assembly.** Mistral-7B-Instruct-v0.3 in 4-bit on GPU, Qwen2.5-1.5B-Instruct on CPU when no GPU is available, so the notebook runs end to end either way with no API key. Each response carries the answer, the source list with page numbers and similarity scores, a confidence percentage and the number of chunks used.

On confidence specifically: it is computed from retrieval, not from the model. It blends the top cosine similarity with how much of the top-k agrees with it, so a lone weak match reads Low even when the model writes fluently. A model's confident tone is not evidence. A similarity score at least is.

## 2. Which part of the routing setup made the biggest difference: metadata, prompting, or filtering?

Metadata, and it is not close. Once every chunk carries a `doc_type`, one filter cuts the candidate set from every chunk in the corpus to the handful that could hold the answer, before any embedding comparison matters. In the earlier routing experiment this took off-target chunks from 1.5 per query to zero without losing a single correct retrieval.

But the answer has a condition attached. Metadata only helps if it is per page rather than per file. Tagging every chunk with one document type, which is the obvious shortcut, makes the filter a no-op because every chunk passes it. The work that makes metadata valuable is the tagging, not the filtering.

Prompting came second and mattered in a specific way: it defines the closed label set that both the query router and the page classifier draw from, so a query label and a chunk label are guaranteed comparable. Without that shared vocabulary the filter silently returns nothing.

Filtering itself is a single list comprehension. It is the cheapest part of the system and it gets all the credit, which is misleading.

## 3. Did the LLM ever retrieve the wrong document? What caused it, and how would you fix it?

Retrieval was rarely the problem. Generation on top of correct retrieval was.

The clearest failure: "Does the product contain any material of animal origin?" Retrieval found the right pages, the BSE/TSE declaration and the animal origin statement, with a top similarity of 0.73. The model still answered "Yes, the product contains materials of animal origin", which is the exact opposite of what those documents say. The cause was chunking, not retrieval. My first splitter cut on raw character offsets, so a chunk began mid-phrase with "terials of animal or human origin" and the model completed the fragment rather than reading the sentence. Making the splitter break on paragraph, line, sentence and word boundaries fixed it, and the same question now returns "No, the product does not contain any material of animal origin" at 76.5% confidence.

I also tried to fix it by instructing the model to begin yes/no answers with Yes or No. That made it worse: it produced a bare, confident "Yes." Worth recording, because a prompt change that sounds like it should add discipline can just as easily strip away the hedging that was carrying the correct meaning. I reverted it.

Ambiguous questions are the other category. "What are the part numbers listed in this document?" has no single right target, since a released lot carries part numbers on its certificate and a tray carries them on the packaging specification. A single-label router has to pick one and gets marked wrong either way. The fix there is not a better prompt but a different output shape: return a ranked shortlist of document types with confidence rather than forcing one winner.

## 4. How would you scale to 1,000+ PDFs or handle vague queries?

**Move classification into ingestion.** Tag and embed each page once when the PDF lands, write the metadata into a real index, and keep the router as a metadata lookup. At this scale labelling cost is a one-time charge per document instead of a per-query tax.

**Swap the index.** FAISS `IndexFlatIP` is exact and returns in under a millisecond over 49 vectors, which is the right call at this size. Past roughly a hundred thousand chunks it would become the bottleneck, and IVF-PQ or HNSW would trade a little recall for a large speed win. Not before then; an approximate index over 49 vectors is engineering theatre.

**Make the filter multi-stage rather than exact-match.** Shortlist by `doc_type` plus year plus supplier, then run the vector search inside that shortlist, so semantic search sees hundreds of chunks rather than tens of thousands.

**Add a lexical leg.** Dense retrieval found three of four exact identifiers I probed but missed a bare lot number entirely, because a digit string carries almost no semantic signal. BM25 fused with the dense results, or a regex pass for identifier-shaped queries, closes that gap. On regulated documents that failure mode is not acceptable.

**Handle vagueness explicitly instead of hoping for the best.** Return the top two or three candidate types with scores; when the top score is low, either ask one clarifying question or widen the search across all types and let a cross-encoder re-rank. Unfiltered search degrades gracefully, filtered search fails hard, so the system should only commit to a filter when it is confident in it.

**Keep a labelled evaluation set.** Every improvement above is a hypothesis, and without a fixed set of questions with known answers there is no way to tell a real gain from a lucky run. The yes/no prompt change is the proof: it sounded right and it made the system worse.
