"""Pipeline tests that run in seconds on a CPU: no model downloads.

The embedder is replaced with a deterministic bag-of-words hash and the LLM with a stub,
so these check the parts that are pure logic: page classification, document boundaries,
chunking, metadata-filtered retrieval, confidence scoring and the answer contract.

    pip install pytest pymupdf faiss-cpu numpy
    pytest app/tests
"""
import re
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline as P  # noqa: E402

PAGES = [
    "Subject: Supplier documentation for article 4471 0093\nDear Quality Team,\n"
    "Please find attached the documentation package for the material described below.",
    "CERTIFICATE OF QUALITY\nLot Number: GB-24117\nDate of Manufacture: 2025-03-14\n"
    "Expiration Date: 2028-03-13\nAssay: 99.6% PASS\nResult: lot released.",
    "PACKAGING COMPONENT SPECIFICATION\nPrimary pack: 25 kg HDPE drum with double LDPE liner.\n"
    "Change notice: the inner liner thickness changed from 60 to 80 micron in January 2025.",
    "Packaging Component Specification (continued)\n"
    "Labelling: each drum carries the lot number, net weight and expiry date.",
    "DECLARATION REGARDING TRANSMISSIBLE SPONGIFORM ENCEPHALOPATHIES (BSE/TSE)\n"
    "We hereby declare that the product does not contain, and is not manufactured using, "
    "any material of animal origin.",
    "SUPPLIER QUALIFICATION RECORD\nLast on-site audit: 12 September 2024.\n"
    "Outcome: approved with no critical or major findings.",
]


def hash_embed(texts):
    out = []
    for t in texts:
        v = np.zeros(512, dtype="float32")
        for w in re.findall(r"[a-z]+", t.lower()):
            v[zlib.crc32(w.encode()) % 512] += 1
        n = np.linalg.norm(v)
        out.append(v / n if n else v)
    return np.array(out, dtype="float32")


@pytest.fixture
def packet(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open()
    for text in PAGES:
        doc.new_page().insert_text((50, 72), text, fontsize=10)
    path = tmp_path / "packet.pdf"
    doc.save(path)
    return path


@pytest.fixture
def store(packet, monkeypatch):
    pytest.importorskip("faiss")
    monkeypatch.setattr(P, "embed", hash_embed)
    monkeypatch.setattr(P, "generate", lambda prompt: "stub answer [1]")
    return P.ingest([packet])


def test_classify_page_reads_titles():
    assert P.classify_page("CERTIFICATE OF QUALITY\nLot Number: X1") == "Certificate of Quality"
    assert P.classify_page("Some letterhead\nBSE/TSE statement") == "BSE/TSE Declaration"
    assert P.classify_page("nothing recognisable here") == "Unknown"


def test_pages_are_tagged_with_types_and_documents(store):
    types = [p["doc_type"] for p in store["pages"]]
    assert types == ["Cover Letter", "Certificate of Quality", "Packaging Specification",
                     "Packaging Specification", "BSE/TSE Declaration", "Supplier Qualification Record"]
    assert len({p["doc_id"] for p in store["pages"]}) == 5


def test_continued_page_joins_its_document(store):
    pkg = [p for p in store["pages"] if p["doc_type"] == "Packaging Specification"]
    assert pkg[0]["doc_id"] == pkg[1]["doc_id"]
    assert {p["page_range"] for p in pkg} == {"3-4"}


def test_split_text_overlaps_and_respects_size():
    text = " ".join(f"word{i}" for i in range(600))
    pieces = P.split_text(text, size=200, overlap=40)
    assert len(pieces) > 1
    assert all(len(p) <= 200 for p in pieces)
    assert pieces[0].split()[-1] in pieces[1]          # consecutive chunks share text


def test_filtered_search_only_returns_that_type(store):
    hits = P.search("drum liner labelling", store, doc_type="Packaging Specification", k=4)
    assert hits and all(h["doc_type"] == "Packaging Specification" for h in hits)


def test_confidence_levels():
    assert P.confidence([]) == (0.0, "none")
    assert P.confidence([{"score": 0.8}, {"score": 0.79}])[1] == "High"
    assert P.confidence([{"score": 0.5}])[1] == "Medium"
    assert P.confidence([{"score": 0.2}, {"score": 0.1}])[1] == "Low"


def test_rag_answer_contract(store):
    res = P.rag_answer("Does the product contain any material of animal origin?", store, k=3)
    assert res["answer"] == "stub answer [1]"
    assert res["chunks_used"] == len(res["sources"]) == 3
    assert res["sources"][0]["doc_type"] == "BSE/TSE Declaration"
    assert {"n", "doc_type", "doc_id", "file", "page", "page_range", "ocr", "score", "text"} \
        <= set(res["sources"][0])


def test_prompt_numbers_passages_and_demands_citations():
    hits = [{"doc_type": "Certificate of Quality", "source_file": "a.pdf", "page": 0, "text": "Lot X"}]
    prompt = P.build_prompt("Which lot?", hits, "Short answer")
    assert "[1] Certificate of Quality — a.pdf, page 1" in prompt
    assert "Use ONLY the numbered passages" in prompt
