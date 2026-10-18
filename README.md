# AI-Powered Pharmaceutical Document Intelligence

My work from the **Pfizer Advanced: AI-Powered Document Insights & Data Extraction Externship**, a 10-week program run by [Extern](https://www.extern.com) (June–September 2026).

Over nine projects I built a document intelligence system for pharmaceutical supplier documentation (SDFs). The finished system takes a single PDF "blob" that holds many documents, splits it into its separate documents, classifies every page, and answers questions through a Gradio chat interface. Every answer comes with page citations and a confidence score. The whole pipeline runs on open-source models.

**Author:** Ophelie Bisamaza · [GitHub](https://github.com/Ophelie4) · [LinkedIn](https://www.linkedin.com/in/ophelie-bisamaza)

---

## Highlights

- **20/20 pages classified correctly** across two real supplier packets, recovering 8 separate documents from single-file PDFs.
- **Metadata-filtered retrieval** cut off-target passages from 1.50 per query to 0.00 with no loss of recall.
- **A controlled LLM evaluation** of Gemini vs Mistral-7B vs Phi-2 vs TinyLlama with identical retrieval. Mistral matched Gemini on accuracy (14/15) with no data leaving the machine.
- **An OCR engine comparison** (Tesseract vs EasyOCR vs PaddleOCR) on a scanned Certificate of Quality, including debugging PaddleOCR's oneDNN backend crash.
- **Confidence measured from retrieval**, not from the model's tone, because a fluent wrong answer with a citation is the most dangerous failure in a compliance workflow.

## Tech stack

**Extraction & OCR:** PyMuPDF, pdfplumber, PyPDF2, Tesseract, EasyOCR, PaddleOCR, OpenCV, Pillow
**Data:** pandas, regex, JSON, ftfy, unicodedata
**RAG:** LlamaIndex, LangChain text splitters, FAISS, BM25, cross-encoder re-ranking
**Embeddings:** all-MiniLM-L6-v2, e5-small-v2, bge-small-en-v1.5
**LLMs:** Gemini (API), Mistral-7B-Instruct (4-bit / GGUF), Phi-2, TinyLlama, Qwen2.5 via llama.cpp and Hugging Face Transformers
**Interface:** Gradio · **Environment:** Google Colab (T4 GPU)

## Projects

| # | Project | What I built |
|---|---|---|
| 1 | [How AI Reads Pharmaceutical Documents](project-01-how-ai-reads-pharma-documents/) | Foundations of ML, LLMs, NLP and OCR; analysis of a real pharma document packet |
| 2 | [Python for Document Processing](project-02-python-for-document-processing/) | Python practice, pandas cleaning, JSON flattening, a 9-step text-cleaning pipeline, image preprocessing (denoise, CLAHE, Otsu) |
| 3 | [Data Extraction from Documents](project-03-data-extraction-from-documents/) | PDF library comparison; date and field extraction with regex, anchor phrases and bounding boxes |
| 4 | [OCR Comparison & Layout-Aware Extraction](project-04-ocr-comparison-and-layout-extraction/) | Scanned-PDF extraction; Tesseract vs EasyOCR vs PaddleOCR |
| 5 | [Introduction to RAG](project-05-intro-to-rag/) | LlamaIndex chatbot, chunking strategies, hybrid vector + BM25 retrieval with re-ranking, a complete RAG pipeline |
| 6 | [Advanced RAG & Open-Source LLMs](project-06-advanced-rag-and-open-source-llms/) | Embedding comparison, retriever tuning with a custom LLM re-ranker, local LLMs, the Gemini vs open-source evaluation |
| 7 | [Blob Processing, Classification & Routing](project-07-blob-processing-classification-routing/) | Splitting multi-document PDFs, page classification, query routing with metadata filters |
| 8 | [Gradio Chatbot with RAG](project-08-gradio-rag-chatbot/) | Document Q&A chatbot and the full RAG UI capstone: OCR fallback, FAISS, citations, confidence |
| 9 | [Final Integration & Evaluation](project-09-final-integration/) | End-to-end system and the final presentation to the Pfizer team |

## What's in each folder

- `README.md`: the project summary and every written answer I submitted, including my reflections
- `notebooks/`: the Google Colab notebooks, with their outputs
- `reports/`: my write-ups and slide decks, converted to Markdown
- `data/`: output files, where a task produced them

## Running the notebooks

Each notebook was built in Google Colab. Open one on GitHub and use **Open in Colab**, or upload it to Colab. Notebooks that call Gemini read `GOOGLE_API_KEY` from Colab Secrets. The open-source model notebooks need a GPU runtime (T4).

---

*This was an educational externship run by Extern. The sample documents were provided by the program for training purposes. This repository contains my own work and does not include confidential Pfizer data.*
