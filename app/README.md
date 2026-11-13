# Pharma Document Intelligence: the app

The capstone system from [Project 8](../project-08-gradio-rag-chatbot/) as a standalone application that runs on your own machine or on Hugging Face Spaces, not just in Colab.

Upload a supplier documentation packet (one PDF or several, digital or scanned). The app splits each file into its separate documents, classifies every page, and answers questions with page citations and a retrieval-based confidence score.

## Run it locally

```bash
cd app
pip install -r requirements.txt
python app.py            # open http://127.0.0.1:7860
python app.py --share    # optional: a temporary public link
```

Scanned PDFs need the Tesseract binary (`brew install tesseract`, or `apt-get install tesseract-ocr`). Digital PDFs work without it.

The first question takes longer because that's when the language model loads. With a CUDA GPU the app uses Mistral-7B-Instruct in 4-bit. Without one it falls back to Qwen2.5-1.5B-Instruct on CPU.

| Setting | Environment variable | Default |
|---|---|---|
| Language model | `PDI_MODEL` | Mistral-7B (GPU) or Qwen2.5-1.5B (CPU) |
| Embedding model | `PDI_EMBED_MODEL` | `BAAI/bge-small-en-v1.5` |
| Where sample PDFs are saved | `PDI_SAMPLE_DIR` | `samples/` |

## Deploy to Hugging Face Spaces

Create a Gradio Space and upload the contents of this folder: `app.py`, `interface.py`, `pipeline.py`, `requirements.txt` and `packages.txt` (which installs Tesseract). For a Space on CPU hardware, the Qwen fallback is selected automatically.

## How the code is organised

| File | What it does |
|---|---|
| `pipeline.py` | Extraction with OCR fallback, page classification and document boundaries, chunking, embeddings, FAISS retrieval with metadata filters, prompting, generation and confidence scoring |
| `interface.py` | The Gradio interface: packet summary, document inventory, chat, and the evidence panel |
| `app.py` | Entry point |
| `tests/` | Pipeline tests that run in seconds with stand-in models (`pytest app/tests`) |

The pipeline module is a cleaned-up version of [`Pfizer_Capstone_Full_RAG_UI.ipynb`](../project-08-gradio-rag-chatbot/notebooks/Pfizer_Capstone_Full_RAG_UI.ipynb). The logic is the same; the models now load on first use, so the interface starts instantly.
