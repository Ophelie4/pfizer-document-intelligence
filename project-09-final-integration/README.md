# Project 9: Final Integration, Testing, and Evaluation

**Week 10.** Bringing every piece together into one end-to-end document intelligence system: extraction and OCR, document splitting and classification, metadata-filtered RAG retrieval, and a Gradio interface. I presented the results to the Pfizer team on 3 September 2026.

The end-to-end system lives in the Project 8 capstone notebook: [`Pfizer_Capstone_Full_RAG_UI.ipynb`](../project-08-gradio-rag-chatbot/notebooks/Pfizer_Capstone_Full_RAG_UI.ipynb). It builds on the segmentation and routing work from [Project 7](../project-07-blob-processing-classification-routing/).

## Final presentation

- [Reading the blob: final presentation to Pfizer (text version)](reports/final-presentation-reading-the-blob.md)

## Headline results

| Metric | Result |
|---|---|
| Pages given the correct document type | **20/20** across two supplier packets |
| Documents recovered from single-file packets | **8** |
| Off-target passages per query with metadata filtering | **1.50 → 0.00**, with no loss of recall |
| Correct page retrieved | **6/6** test questions |
| External APIs needed | **None**: fully open-source stack |
