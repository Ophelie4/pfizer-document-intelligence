"""Document intelligence pipeline for pharmaceutical supplier documentation.

PDF (digital or scanned) -> text with OCR fallback -> page classification and document
boundaries -> overlapping chunks -> bge-small embeddings -> FAISS -> metadata-filtered
retrieval -> grounded prompt -> open-source LLM -> answer + sources + confidence.

This is the capstone notebook's pipeline (project 8) as an importable module. The
embedding model and the LLM load lazily on first use, so the interface starts instantly.
"""
from __future__ import annotations

import io
import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

# ── configuration ─────────────────────────────────────────────────────────────
EMBED_ID = os.getenv("PDI_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
GPU_MODEL = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit"   # 4-bit Mistral-7B-Instruct-v0.3
CPU_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"                  # fallback when there is no GPU

MIN_CHARS = 40           # a page with less text than this is treated as scanned
OCR_DPI = 200
CHUNK, OVERLAP = 700, 120
SEPARATORS = ["\n\n", "\n", ". ", " "]

SAMPLE_DIR = Path(os.getenv("PDI_SAMPLE_DIR", "samples"))
SAMPLES = [("pharma-blob-sample.pdf", "1fJ7DszcjB_TerDTAhXfAw74VqJBElTyw"),
           ("pharma-blob-test.pdf", "1atOj_CzvPRm-CskbhvJdzlJIpcEanVu1")]

STYLE = {
    "Short answer":    "Answer in one or two sentences.",
    "Detailed answer": "Answer in a short paragraph, quoting exact figures, dates and identifiers.",
    "Bullet summary":  "Answer as 3 to 5 short bullet points, one fact per bullet.",
}

DOC_TYPES = ["Cover Letter", "Certificate of Quality", "Packaging Specification",
             "BSE/TSE Declaration", "Material Description Sheet",
             "Supplier Qualification Record", "Chain of Custody", "Unknown"]
SLUG = {t: re.sub(r"[^a-z]+", "_", t.lower()).strip("_") for t in DOC_TYPES}

HEADING_CUES = {
    "certificate of quality": "Certificate of Quality",
    "quality certificate": "Certificate of Quality",
    "packaging component specification": "Packaging Specification",
    "declaration regarding transmissible spongiform": "BSE/TSE Declaration",
    "bse/tse": "BSE/TSE Declaration",
    "animal origin statement": "BSE/TSE Declaration",
    "material description sheet": "Material Description Sheet",
    "compliance bulletin": "Material Description Sheet",
    "supplier qualification record": "Supplier Qualification Record",
    "vendor qualification record": "Supplier Qualification Record",
    "chain of custody": "Chain of Custody",
    "certificate of processing": "Chain of Custody",
    "to whom it may concern": "Cover Letter",
    "dear ": "Cover Letter",
    "subject:": "Cover Letter",
}
CONTINUATION = ("(continued)", "cont'd", "page 2 of", "page 3 of")
ID_PATTERNS = (r"lot number\s*:?\s*([a-z0-9\-]{4,})",
               r"document number\s*:?\s*([a-z0-9\-/]{4,})",
               r"product article number\s*:?\s*([0-9 ]{6,})")


# ── 1. reading pages ──────────────────────────────────────────────────────────
def read_page(page):
    """Return (text, used_ocr). Falls back to Tesseract when the page has no text layer."""
    text = page.get_text("text").strip()
    if len(text) >= MIN_CHARS:
        return re.sub(r"\n{3,}", "\n\n", text), False
    try:
        import pytesseract
        from PIL import Image
        pix = page.get_pixmap(dpi=OCR_DPI)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr = pytesseract.image_to_string(img).strip()
        return re.sub(r"\n{3,}", "\n\n", ocr), True
    except Exception as e:                       # Tesseract missing or the page is unreadable
        print(f"[warn] OCR failed on a page ({type(e).__name__})")
        return text, False


# ── 2. classification and document boundaries ─────────────────────────────────
def identifiers(text):
    low, ids = text.lower(), set()
    for p in ID_PATTERNS:
        ids.update(m.group(1).strip() for m in re.finditer(p, low))
    return ids


def classify_page(text):
    head = "\n".join(text.strip().splitlines()[:12]).lower()   # letterheads push the title down
    for k, v in HEADING_CUES.items():
        if k in head:
            return v
    low = text.lower()
    for k, v in HEADING_CUES.items():
        if k in low:
            return v
    return "Unknown"


def tag_pages(path, filename):
    """One tagged record per page, including the page range of its parent document.

    A "(continued)" page inherits the previous page's type, and two same-titled pages
    carrying different lot numbers are two different documents.
    """
    import pymupdf
    doc = pymupdf.open(path)
    pages, prev_type, prev_text, doc_id, counters = [], None, None, None, {}
    for i, pg in enumerate(doc):
        text, used_ocr = read_page(pg)
        dtype = classify_page(text)
        head = "\n".join(text.strip().splitlines()[:4]).lower()
        is_cont = any(c in head for c in CONTINUATION) and prev_type is not None
        if is_cont:
            dtype = prev_type
        new_doc = (not is_cont) and (
            prev_type is None or dtype != prev_type
            or (identifiers(text) and identifiers(prev_text)
                and not (identifiers(text) & identifiers(prev_text))))
        if new_doc:
            s = SLUG.get(dtype, "unknown")
            counters[s] = counters.get(s, 0) + 1
            doc_id = f"{s}_{counters[s]:02d}"
        pages.append({"page": i, "doc_type": dtype, "doc_id": doc_id,
                      "source_file": filename, "text": text, "ocr": used_ocr})
        prev_type, prev_text = dtype, text

    spans = {}
    for p in pages:
        lo, hi = spans.get(p["doc_id"], (p["page"], p["page"]))
        spans[p["doc_id"]] = (min(lo, p["page"]), max(hi, p["page"]))
    for p in pages:
        lo, hi = spans[p["doc_id"]]
        p["page_range"] = f"{lo+1}" if lo == hi else f"{lo+1}-{hi+1}"
    return pages


# ── 3. chunking ───────────────────────────────────────────────────────────────
def split_text(t, size=CHUNK, overlap=OVERLAP):
    """Recursive-style split that breaks on the largest natural boundary near the limit."""
    out, start = [], 0
    while start < len(t):
        end = min(start + size, len(t))
        if end < len(t):
            for sep in SEPARATORS:
                p = t.rfind(sep, start + size // 2, end)
                if p != -1:
                    end = p + len(sep)
                    break
        piece = t[start:end].strip()
        if piece:
            out.append(piece)
        if end >= len(t):
            break
        start = max(end - overlap, start + 1)
    return out


def chunk_pages(pages):
    """Overlapping chunks that inherit the full metadata of their page."""
    out = []
    for p in pages:
        if len(p["text"]) < 20:
            continue
        for piece in split_text(p["text"]):
            out.append({**{k: v for k, v in p.items() if k != "text"},
                        "text": piece, "chunk_index": len(out)})
    return out


# ── 4. models (loaded on first use) ───────────────────────────────────────────
def has_gpu():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def model_id():
    return os.getenv("PDI_MODEL") or (GPU_MODEL if has_gpu() else CPU_MODEL)


def model_label():
    return {GPU_MODEL: "Mistral-7B-Instruct · 4-bit GPU",
            CPU_MODEL: "Qwen2.5-1.5B-Instruct · CPU"}.get(model_id(), model_id())


@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_ID, device="cuda" if has_gpu() else "cpu")


def embed(texts):
    """L2-normalised float32 vectors, so an inner product is a cosine similarity."""
    return get_embedder().encode(list(texts), normalize_embeddings=True, batch_size=32,
                                 show_progress_bar=False).astype("float32")


@lru_cache(maxsize=1)
def get_llm():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    mid = model_id()
    tok = AutoTokenizer.from_pretrained(mid)
    if has_gpu():
        from transformers import BitsAndBytesConfig
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                 bnb_4bit_compute_dtype=torch.float16,
                                 bnb_4bit_use_double_quant=True)
        model = AutoModelForCausalLM.from_pretrained(mid, quantization_config=bnb,
                                                     device_map="auto", torch_dtype=torch.float16)
    else:
        model = AutoModelForCausalLM.from_pretrained(mid, torch_dtype=torch.float32)
    model.eval()
    return tok, model


def generate(prompt):
    import torch
    tok, model = get_llm()
    text = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                   tokenize=False, add_generation_prompt=True)
    enc = tok(text, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        out = model.generate(**enc, max_new_tokens=320 if has_gpu() else 180, do_sample=False,
                             temperature=None, top_p=None, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()


# ── 5. indexing and retrieval ─────────────────────────────────────────────────
def build_index(chunks):
    import faiss
    vecs = embed(c["text"] for c in chunks)
    index = faiss.IndexFlatIP(vecs.shape[1])     # inner product on unit vectors == cosine
    index.add(vecs)
    return index


def ingest(paths):
    """Read, OCR, tag, chunk, embed and index a set of PDFs. Returns a store, or None."""
    pages = []
    for p in paths:
        # plain paths, or Gradio upload objects whose .name is the temp file path
        path = os.fspath(p) if isinstance(p, (str, os.PathLike)) else str(p.name)
        pages.extend(tag_pages(path, Path(path).name))
    if not pages:
        return None
    chunks = chunk_pages(pages)
    if not chunks:
        return None
    return {"chunks": chunks, "index": build_index(chunks), "pages": pages}


def sample_paths():
    """Download the two sample supplier packets on first use."""
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for name, fid in SAMPLES:
        dest = SAMPLE_DIR / name
        if not dest.exists():
            import gdown
            gdown.download(id=fid, output=str(dest), quiet=True)
        out.append(dest)
    return out


def search(question, store, doc_type="All types", k=4):
    """Retrieve k chunks, optionally restricted to one document type.

    Filtering over-fetches from FAISS and keeps only matching chunks, so one index
    serves the whole corpus.
    """
    q = embed([question])
    over = k * 6 if doc_type != "All types" else k
    scores, ids = store["index"].search(q, min(over, len(store["chunks"])))
    hits = []
    for score, i in zip(scores[0], ids[0]):
        if i < 0:
            continue
        c = store["chunks"][i]
        if doc_type != "All types" and c["doc_type"] != doc_type:
            continue
        hits.append({**c, "score": float(score)})
        if len(hits) == k:
            break
    return hits


# ── 6. answering ──────────────────────────────────────────────────────────────
def build_prompt(question, hits, mode):
    context = "\n\n".join(
        f"[{i+1}] {h['doc_type']} — {h['source_file']}, page {h['page']+1}\n{h['text']}"
        for i, h in enumerate(hits))
    return (
        "You are a document analyst answering questions about pharmaceutical supplier documents.\n"
        "Use ONLY the numbered passages below. Cite the passage numbers you used, like [1] or [2].\n"
        "If the passages do not contain the answer, say so plainly instead of guessing.\n"
        "Answer the question directly and make your answer agree with the passages: if a passage\n"
        "states that something is absent or not present, do not report it as present.\n"
        f"{STYLE.get(mode, STYLE['Short answer'])}\n\n"
        f"PASSAGES:\n{context}\n\nQUESTION: {question}\n\nANSWER:")


def confidence(hits):
    """Top similarity, plus how much of the top-k agrees with it. Returns (pct, label).

    Confidence comes from retrieval, not from the model: a fluent wrong answer with a
    citation is the most dangerous failure in a compliance workflow.
    """
    if not hits:
        return 0.0, "none"
    top = hits[0]["score"]
    support = sum(1 for h in hits if h["score"] >= top - 0.08) / len(hits)
    pct = round(100 * (0.75 * top + 0.25 * support), 1)
    label = "High" if top >= 0.62 else "Medium" if top >= 0.48 else "Low"
    return pct, label


def rag_answer(question, store, doc_type="All types", mode="Short answer", k=4):
    """Retrieval -> context -> prompt -> model -> answer + sources + confidence."""
    hits = search(question, store, doc_type, k)
    if not hits:
        return {"answer": "Nothing in the indexed documents matched that question.",
                "sources": [], "confidence": 0.0, "confidence_label": "none", "chunks_used": 0}
    answer = generate(build_prompt(question, hits, mode))
    pct, label = confidence(hits)
    sources = [{"n": i + 1, "doc_type": h["doc_type"], "doc_id": h["doc_id"],
                "file": h["source_file"], "page": h["page"] + 1,
                "page_range": h["page_range"], "ocr": h["ocr"],
                "score": round(h["score"], 3), "text": h["text"]}
               for i, h in enumerate(hits)]
    return {"answer": answer, "sources": sources, "confidence": pct,
            "confidence_label": label, "chunks_used": len(hits)}
