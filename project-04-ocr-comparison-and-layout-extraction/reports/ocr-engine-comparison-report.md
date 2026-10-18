# OCR Engine Comparison Report

**Document tested:** Certificate of Quality (Pharmaceutical SDF, page 3), a printed/scanned pharmaceutical supplier document.
**Engines tested:** Tesseract (pytesseract), EasyOCR, PaddleOCR (PP-OCRv6 detection + recognition models).
**Notebook:** [`Ophelie_OCR_Engine_Comparison.ipynb`](../notebooks/Ophelie_OCR_Engine_Comparison.ipynb)

## Quantitative snapshot

All three engines extracted almost identical amounts of text and all correctly matched every keyword we searched for (lot, expiration, certificate, quality, date).

| | Tesseract | PaddleOCR | EasyOCR |
|---|---|---|---|
| Characters extracted | 1,507 | 1,429 | 1,411 |
| Segments | 1 continuous block | 35 lines | 45 text regions |

On the fields that matter most for this document (Lot Number: 17242818, Product Article Number: 29-1846-12, Date of Manufacture: 20210126, Expiration Date: 20230126), all three engines got every digit right.

## 1. Which OCR tool worked best for this pharmaceutical PDF, and why?

PaddleOCR produced the cleanest, most usable output. It grouped text into coherent lines that matched the document's visual structure (label, then value, on one line), it was the only engine to correctly render the accented "ÄKTA" trademark with its diacritic, and its address block ("14 Walkup Drive, Westborough, MA 01581 USA") matched the source exactly. Tesseract was a close second and actually caught one thing PaddleOCR missed (a timestamp string in the top-left corner: "090177e19abdfceb\Approved\Approved On: 13-Jul-2022 20:47 (GMT)"), but it also introduced small character-level errors elsewhere (a misread zip code digit and a mangled "Global Life Sciences" line). EasyOCR was the least usable as raw text: it fragmented words across lines ("AKTA" / "™" / "ready Gradient…" became three separate lines instead of one), lost several label-value pairings, and produced one outright unreadable line ("Cburprodt Griginaustactured") where the other two engines had no trouble.

## 2. What surprised you?

Two things. First, Tesseract, the simplest and fastest-to-install engine, held up better than expected against two much heavier, more "modern" deep-learning-based engines; it caught a timestamp string that both EasyOCR and PaddleOCR missed entirely. Second, EasyOCR, despite being marketed as an easy, accurate, GPU-friendly option, produced the most fragmented and error-prone output of the three on this document, including one line that was pure gibberish.

## 3. Which engine felt best suited to pharmaceutical compliance workflows?

PaddleOCR. Compliance documents like Certificates of Quality live or die on getting labels and values (lot numbers, dates, product codes) correctly paired and legible, and PaddleOCR's line-level grouping preserved those label-value relationships far more reliably than EasyOCR's fragmented regions. It also handled the special character in the product's trademarked name correctly, which matters for exact-match validation against a source-of-truth system. Tesseract is a reasonable low-cost fallback for a first-pass triage, but its occasional character-level slips (like the zip code digit) would need a human review step before being trusted in a regulated workflow.

## 4. Were there any frustrations with install/setup or output structure?

Yes, mostly with PaddleOCR. Its pip install pulled in ~200 MB of extra dependencies (paddlepaddle) and took noticeably longer than the other two. More importantly, the code broke twice on real errors before it worked. First, PaddleOCR's classic `.ocr(img, cls=True)` call has been deprecated in favor of `.predict(img)`, and calling the old-style API in the newest installed version raised a `TypeError`. After switching to `.predict()`, a second, deeper error surfaced: a `NotImplementedError` from PaddlePaddle's oneDNN/PIR execution backend (`ConvertPirAttribute2RuntimeAttribute not support`) that only went away after explicitly disabling MKL-DNN acceleration (`enable_mkldnn=False`) and the extra document-orientation/unwarping/text-line-orientation preprocessing stages. Once fixed, the model ran correctly but slowly (about 3 minutes on CPU without MKL-DNN, versus seconds for Tesseract and about 15 seconds for EasyOCR). Tesseract and EasyOCR both installed and ran without any code changes.

## 5. Would you combine tools or pick one for production use?

For a production pharmaceutical-document pipeline, I would use PaddleOCR as the primary engine given its output quality and line-structure preservation, but I would not run it with MKL-DNN disabled in production. I'd invest time in resolving that acceleration bug (or pin an earlier compatible paddlepaddle/paddleocr version) so it runs at a reasonable speed, since 3 minutes per page will not scale to real document volumes. I would keep Tesseract in the pipeline as a lightweight cross-check: it is fast enough to run on every document and, as this test showed, it can catch details a heavier model misses. I would not rely on EasyOCR alone for this document type given how fragmented and occasionally garbled its output was here, though it could still be useful as a third vote in an ensemble approach where the pipeline flags a document for human review if the three engines disagree on a critical field.
