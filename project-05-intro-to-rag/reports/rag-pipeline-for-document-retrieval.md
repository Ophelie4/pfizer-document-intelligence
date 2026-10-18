# RAG Pipeline for Document Retrieval

**Reference document:** sample-sdf-document (Project 5).pdf (Cytiva ÄKTA ready Flow Kit storage-conditions letter and Certificates of Quality)
**Notebook:** [`Ophelie_RAG_Pipeline.ipynb`](../notebooks/Ophelie_RAG_Pipeline.ipynb)

## Design choices

**Chunking:** `SentenceSplitter` with `chunk_size=200` and `chunk_overlap=30`. The reference document is short (3 pages, ~4,000 extracted characters) and structurally dense, mixing short prose paragraphs with tables (flow kit part numbers, Product Release Criteria test results). A small chunk size keeps each chunk focused on a single fact cluster rather than blending unrelated sections, which matters when a single retrieved chunk needs to answer a precise question. A 30-token overlap preserves continuity across sentence and table-row boundaries. Semantic chunking was considered but judged less reliable than sentence-based splitting for a document this short and table-heavy.

**Embedding model:** `HuggingFaceEmbedding` using `sentence-transformers/all-MiniLM-L6-v2`. This is a free, locally-run model with no API quota and no cost, producing 384-dimension vectors. It sidesteps the Gemini API rate-limit issues encountered in earlier tasks and performs well on short technical/procedural text.

**Retrieval method:** Hybrid retrieval combining vector similarity search and BM25 keyword search, merged and de-duplicated by node ID. The document mixes descriptive language (storage and operating conditions) with exact technical values (lot numbers, part numbers, kGy irradiation ranges, SOP references). Vector search handles the descriptive questions well by matching meaning; BM25 is better at surfacing exact keyword matches. Combining both gave the pipeline a better chance of retrieving the right chunk regardless of question type.

**Response generation:** Gemini via `GoogleGenAI` (model `models/gemini-flash-latest`), substituted for the task's specified `llama-index-llms-gemini` / `gemini-2.0-flash`, which returned a 429 quota error on this API key in earlier tasks. The API key is read from Colab Secrets rather than hardcoded.

## Prompt 1: What test methods were used for quality control?

**Answer:** Based on the provided context, the following test methods and specifications were used for quality control:
- Flow Rate Test, performed per SOP-QC-042
- Pressure Integrity, evaluated at a maximum of 0.5 bar with a 5-minute hold
- Visual Inspection, checked for no visible defects
- Package Integrity, checked to ensure the package is sealed with no damage
- Autoclave (Pump tubing), at 121°C for more than 15 minutes
- Gamma Irradiation (Inlets), at 25.0 to 40.0 kGy
- Bio-safety, compliance testing per United States Pharmacopeia (USP) <88> Biological Reactivity Test Class VI (and compliance with EMA/410/01 regarding animal-derived ingredients)

The model also noted that the context names SOP-QC-042 for the Flow Rate Test but does not contain the full content of that SOP, nor detailed step-by-step procedures for the other test methods.

## Prompt 2: What are the storage conditions specified in the certificate?

**Answer:** Based on the provided context, the Certificate of Quality itself does not specify any storage conditions; it only states that the product is manufactured in compliance with an ISO 9001 certified quality management system. However, the accompanying storage-conditions letter specifies a Recommended Storage Temperature of greater than +5°C (per Section 8.3 of Operating Instructions 28960345; extended storage below +5°C could lead to brittleness or cracking of plastic connectors), and an Operating Temperature of +2°C to +40°C. The model explicitly noted that storage conditions are not written within the Certificate of Quality portion of the document itself.

**Note:** Prompt 2 was a deliberately useful test of the pipeline, since the document's storage-temperature language appears in the Cytiva letter (page 1), not inside either Certificate of Quality (pages 2 to 3). The real pipeline output shows Gemini correctly distinguishing the letter's storage guidance from the certificate itself, rather than conflating the two, based on the actual retrieved chunks and generated answer captured in the notebook.
