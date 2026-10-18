# Full RAG UI: Capstone Deck (text version)

**August 31, 2026**
**Notebook:** [`Pfizer_Capstone_Full_RAG_UI.ipynb`](../notebooks/Pfizer_Capstone_Full_RAG_UI.ipynb)

## My chatbot interface

**Main chat interface:** Two-column demo layout. Left: upload, index, answer style, type filter, k slider, transcript export. Right: conversation with a sources panel underneath. After indexing the samples: 2 files, 20 pages, 8 documents, 49 chunks, 0 pages needed OCR.

**Sample question:** "Does the product contain any material of animal origin?"
Answer style: Short answer. Restrict to type: All types. k = 4 passages.

**Bot response:** "No, the product does not contain any material of animal origin."
🟢 Confidence 76.5% (High) · 4 chunks used
[1] BSE/TSE Declaration · page 6 · sim 0.77

## What I added beyond the base tutorial

- **Ingestion + OCR.** PyMuPDF per page; a page with under 40 characters is treated as scanned, rasterised at 200 dpi and passed through Tesseract. Each page records whether it came via OCR.
- **Metadata tagging.** `doc_type`, `doc_id`, `page`, `page_range`, `source_file`, `chunk_index`, `ocr`. Titles are read across 12 header lines; "(continued)" inherits; different lot numbers under the same title start a new `doc_id`.
- **Chunking, embeddings, FAISS.** 700 chars with 120 overlap, breaking on paragraph then line then sentence then word. Embedded with bge-small-en-v1.5 into a FAISS `IndexFlatIP` over normalised vectors, so inner product is exact cosine.
- **Prompt, model, response.** Numbered passages, cite-your-sources instruction, refuse when unsupported. Mistral-7B-Instruct 4-bit on GPU or Qwen2.5-1.5B on CPU. Every response returns answer + sources + confidence + chunk count.

## What I learned

**What was challenging?** Chunk boundaries, not retrieval. The animal-origin question retrieved exactly the right pages at 0.73 similarity, yet the model answered the opposite of what the documents say. My first splitter cut on raw character offsets, so a chunk began mid-phrase with "terials of animal or human origin" and the model completed the fragment. Breaking on paragraph, line, sentence and word boundaries fixed it. Trying to force Yes/No answers made it worse, so I reverted that. Colab also ran out of GPU quota, so the model auto-selects GPU or CPU.

**What would you improve next time?** Add a lexical (BM25) leg beside the dense search so exact lot and document numbers cannot be missed, return a ranked shortlist of document types with confidence instead of one label, stream tokens rather than waiting for the full generation, and keep a labelled evaluation set so a change that sounds right can be shown to actually help.

**Performance observations.** Corpus: 2 files, 20 pages, 8 documents, 49 chunks, 7 document types. Ingestion is the slow half and runs once; embedding 49 chunks takes about a second on GPU, and OCR adds roughly a second per scanned page. FAISS `IndexFlatIP` returns in under a millisecond at this size, so an exact index is correct here and an approximate one would only pay off in the tens of thousands of chunks. Generation dominates response time, which is why k is a slider. Confidence is computed from retrieval scores, not the model's tone: 76.5% High on the animal-origin query, from a 0.77 top similarity with 4 supporting chunks.
