# SDF Extraction Results: PyMuPDF

**Task:** Extract & Structure Data from SDFs (Mandatory)
**Document:** sample-sdf-document.pdf (3 pages: a Cytiva letter with a product table, a Certificate of Quality, and a Certificate of Quality with a test results table)
**Method:** `fitz.get_text("words")` and `fitz.get_text("blocks")` across all pages

## 1. Did PyMuPDF accurately extract all the text?

Yes. The extraction pulled 617 individual words across all 3 pages (203 on page 1, 201 on page 2, 213 on page 3), and spot-checking the output against the actual PDF confirmed the text matches: headers, body paragraphs, table contents, and footer page numbers were all captured correctly, including special characters like the trademark symbol in "AKTA(™)" and degree symbols in temperature values.

## 2. Were there issues with certain areas or layouts (tables, columns)?

The main issue was with tables. Word-level extraction returns each word with its own bounding box and a `line_no`/`word_no`, but it does not tell you which table column a word belongs to. That has to be inferred separately, usually from x-coordinate ranges. Multi-word table cells (for example "High Flow Kit F, Modified, AKTA ready") get split into many separate word entries, so reconstructing a full cell value takes extra grouping logic rather than being available directly. Block-level extraction grouped paragraph text well, but for the tables it tended to merge multiple rows into a single block, which lost the row-by-row structure that mattered most. Also worth noting: the PDF's built-in metadata fields (title, author, creation date, etc.) were all empty, so that wasn't a usable fallback source of document context.

## 3. What challenges or observations did you encounter?

The biggest challenge was mentally separating "PyMuPDF extracted this correctly" from "PyMuPDF structured this the way I need." The raw extraction was accurate at the word level every time, but turning that into something usable (like a table row, or a label-value pair) requires an extra layer of logic on top of the raw output. It also took a moment to realize that `line_no` groups words that are visually on the same line, which is useful, but a "line" in a table can span multiple columns at once.

## 4. What would you adjust for the next step (extracting fields like Manufacturing Date and Expiration Date)?

For the next step I'd cluster words into table columns using x-coordinate ranges rather than relying on `line_no` or `block_no` alone, since columns share a consistent horizontal band across rows. For labeled fields like "Manufacturing Date:" or "Expiration Date:", I'd use regex/anchor phrases to locate the label word first, then search nearby bounding boxes (same line, or within a small y-range and to the right) to pull the associated value, using proximity in coordinate space rather than plain text order. This should make field extraction more robust across the mixed layouts (free text, tables, certificates) that appear in this document.
