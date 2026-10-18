# Reading the Blob

*Final presentation to the Pfizer team, 3 September 2026 (text version of the slides)*

An AI pipeline that splits pharmaceutical supplier packets into separate documents, routes a question to the right one, and shows its receipts.

| | |
|---|---|
| **8** | documents recovered from a single packet |
| **20/20** | pages classified correctly |
| **100%** | open-source models, no external API |

*Extern AI Document Intelligence · 9-week build*

---

## The problem: one file, eight documents, no boundaries

A Supplier Documentation File arrives as a single PDF. Inside one packet I tested: a cover letter, two certificates of quality, a packaging specification, a BSE/TSE declaration, a material description sheet, a supplier qualification record and a chain of custody.

Nothing in the file marks where one document ends and the next begins.

So a question as ordinary as "which lots were released, and did they pass their tests?" becomes a person scrolling until they find it, and hoping they stopped in the right document.

- **1** PDF received: the whole packet arrives as one attachment
- **8** documents inside, each with its own type, issuer and validity
- **0** separators: no bookmarks, no page index, no metadata

*Test corpus: two real supplier packets, 20 pages, 8 distinct documents.*

---

## How it works: five stages, each one able to fail loudly

1. **Extract.** PyMuPDF reads every page. A page with no text layer is rasterised and passed through Tesseract OCR, and it is flagged as OCR so a reader knows.
2. **Split & tag.** Detects where each document starts, then tags every page with type, document ID and page range.
3. **Index.** Pages are chunked on sentence boundaries, embedded with a small open-source model, and stored in a FAISS index.
4. **Route.** The question is classified first, so the search only looks inside the document type that could answer it.
5. **Answer.** An open-source LLM answers from the retrieved passages only, with page citations and a confidence score.

Runs end to end on open-source models: PyMuPDF + Tesseract · bge-small embeddings · FAISS · Mistral-7B-Instruct · Gradio interface. No external API, no data leaving the environment.

---

## Does it work? (1 of 2): splitting the packet into documents

- **20/20** pages given the correct document type
- **8** documents recovered from two packets
- **1** page that needed a deterministic fallback

**The hard case.** Two Certificates of Quality, back to back. Same title, same issuer, same test table, same layout. The only thing separating them is a lot number buried in the middle of the page: 18356721 and 15102934. The model merged them into one document. A rule that compares lot and document numbers across consecutive pages recovered the split.

**Why it matters.** Merging those two pages would collapse two lots' release data into a single record. Every downstream answer about either lot would then be quietly wrong, and would still look confident.

---

## Does it work? (2 of 2): every answer arrives with its receipts

**Question:** "Does the product contain any material of animal origin?"
**Answer:** "No, the product does not contain any material of animal origin."

**Sources returned with the answer:**
- BSE/TSE Declaration · pharma-blob-sample.pdf · page 6 · similarity 0.77
- BSE/TSE Declaration · pharma-blob-test.pdf · page 6 · similarity 0.76

Confidence 76.5% (High) · 4 passages used

**Confidence is measured, not performed.** The score comes from retrieval similarity and how much of the top-k agrees with it, not from how the model sounds. A fluent, well-written answer sitting on one weak match still reads Low. That matters here: a wrong answer that carries a citation is more dangerous than no answer at all.

---

## What I learned: three things that broke

1. **The filter that hid the answer.** My first question router scored 3 out of 6. Because a wrong route makes the metadata filter exclude the right passages, filtering performed worse than no filtering at all. Rewriting the routing prompt took it to 6 of 6. Unfiltered search degrades gracefully; filtered search fails hard.
2. **The chunk that inverted a fact.** Retrieval found the correct page at 0.73 similarity, but a chunk began mid-phrase. The system answered "Yes, contains animal-origin material," which is the opposite of the declaration. Splitting on sentence and paragraph boundaries fixed it. The retrieval was never wrong; the chunk boundary was.
3. **The fix that made it worse.** I told the model to begin yes/no answers with Yes or No, expecting more discipline. It produced a bare, confident "Yes." I reverted it. The lesson I keep: a change that sounds right has to be measured, or it is just a guess with better prose.

Each one was found by testing against a set of questions with known answers, not by reading the code again.

---

## Two questions I asked the team

1. **Are these the documents that actually cause friction?** I chose certificates of quality, packaging specifications, BSE/TSE declarations, material description sheets, supplier qualification records and chain of custody, because that is what was in the packets I had. Are those the ones that slow down material planning and supplier onboarding? Or am I automating the easy half?
2. **Where does this need to be most accurate to be trusted?** My instinct is that the dangerous failure is not a missing answer. It is a wrong answer that arrives with a citation and a confidence score attached. Where would your threshold sit before you would let something like this into a real workflow?

---

## Status: where it stands, and what is next

**Built and tested**
- End-to-end pipeline handling digital and scanned PDFs
- Page classification 20/20 across two supplier packets
- Metadata filtering cut off-target passages from 1.50 per query to 0.00, with no loss of recall
- Retrieval found the correct page for 6 of 6 test questions
- Live Gradio interface with sources and confidence on every answer

**What I would build next**
- Keyword search running beside the embeddings, so an exact lot number can never be missed
- A ranked shortlist of document types instead of forcing one label on an ambiguous question
- A labelled evaluation set that grows every time the system gets something wrong
- Confidence thresholds that route low-scoring answers to a human rather than returning them
