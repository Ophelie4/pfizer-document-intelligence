# Page-Level Metadata and Document Boundaries: pharma-blob-sample.pdf

**Date:** August 30, 2026
**Document:** pharma-blob-sample.pdf (10 pages)
**Notebook:** [`Ophelie_Page_Level_Metadata_Boundaries.ipynb`](../notebooks/Ophelie_Page_Level_Metadata_Boundaries.ipynb)
**Model:** Gemini (`models/gemini-flash-lite-latest`), temperature 0

## Final JSON output

```json
[
  {"page": 0, "doc_id": 0, "doc_type": "Cover Letter"},
  {"page": 1, "doc_id": 1, "doc_type": "Certificate of Quality"},
  {"page": 2, "doc_id": 2, "doc_type": "Certificate of Quality"},
  {"page": 3, "doc_id": 3, "doc_type": "Packaging Specification"},
  {"page": 4, "doc_id": 3, "doc_type": "Packaging Specification"},
  {"page": 5, "doc_id": 4, "doc_type": "BSE/TSE Declaration"},
  {"page": 6, "doc_id": 5, "doc_type": "Material Description"},
  {"page": 7, "doc_id": 6, "doc_type": "Supplier Qualification"},
  {"page": 8, "doc_id": 6, "doc_type": "Supplier Qualification"},
  {"page": 9, "doc_id": 7, "doc_type": "Chain of Custody"}
]
```

8 documents detected across 10 pages.

## Verification against the actual page headers

The classification was checked against the first line of each extracted page rather than accepted on trust.

| Page | First line of extracted text | Assigned doc_id | Assigned doc_type |
|---|---|---|---|
| 0 | Cytiva (letter re: ÄKTA ready Flow Kit Storage Conditions) | 0 | Cover Letter |
| 1 | Certificate of Quality (Low Flow Kit, Lot 18356721) | 1 | Certificate of Quality |
| 2 | Certificate of Quality (High Flow Kit, Lot 15102934) | 2 | Certificate of Quality |
| 3 | Packaging Component Specification | 3 | Packaging Specification |
| 4 | Packaging Component Specification (continued) | 3 | Packaging Specification |
| 5 | Declaration Regarding Transmissible Spongiform Encephalopathies | 4 | BSE/TSE Declaration |
| 6 | Material Description Sheet | 5 | Material Description |
| 7 | Supplier Qualification Record | 6 | Supplier Qualification |
| 8 | Supplier Qualification Record (continued) | 6 | Supplier Qualification |
| 9 | Cytiva, Global Chain of Custody | 7 | Chain of Custody |

Every page matches. The two multi-page documents (pages 3 to 4, and pages 7 to 8) are correctly grouped under a single `doc_id`, and the two consecutive Certificates of Quality are correctly split into two separate documents despite sharing a template.

## Baseline comparison

The prompts from the training module were run first, unmodified, before any changes were made. That run produced:

```json
[
  {"page": 0, "doc_id": 0, "doc_type": "Other"},
  {"page": 1, "doc_id": 1, "doc_type": "Certificate Of Quality"},
  {"page": 2, "doc_id": 2, "doc_type": "Certificate Of Quality"},
  {"page": 3, "doc_id": 3, "doc_type": "Packaging Specification"},
  {"page": 4, "doc_id": 3, "doc_type": "Packaging Specification"},
  {"page": 5, "doc_id": 4, "doc_type": "Bse/Tse Declaration"},
  {"page": 6, "doc_id": 5, "doc_type": "Material Description"},
  {"page": 7, "doc_id": 5, "doc_type": "Material Description"},
  {"page": 8, "doc_id": 5, "doc_type": "Material Description"},
  {"page": 9, "doc_id": 5, "doc_type": "Material Description"}
]
```

6 documents detected instead of 8, with 7 of 10 pages differing from the corrected run.
