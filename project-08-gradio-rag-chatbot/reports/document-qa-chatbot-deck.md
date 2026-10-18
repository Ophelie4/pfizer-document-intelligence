# Document Q&A Chatbot (slide deck, text version)

**August 31, 2026**
**Notebook:** [`Pfizer_Document_QA_Chatbot.ipynb`](../notebooks/Pfizer_Document_QA_Chatbot.ipynb)

## My chatbot interface

**Main chat interface:** Two-column layout: upload, indexing and controls on the left, conversation on the right. Status line after loading the sample: "Indexed 1 file(s), 10 pages, 20 chunks. Ask me anything."

**Sample question:** "Does the product contain any material of animal origin?"
Answer style: Short answer. Search in: All documents.

**Bot response:** "No, the product does not contain any materials of animal origin."
Sources: pharma-blob-sample.pdf p.6 · p.7 · p.9

## What I added beyond the base tutorial

- **Page-level citations.** Every answer ends with the file and page each passage came from, so a claim can be checked rather than trusted.
- **Multi-file upload + scope filter.** `gr.File(file_count="multiple")` takes several PDFs at once, and a "Search in" dropdown narrows retrieval to a single file.
- **Answer-style dropdown.** Short answer, detailed answer or bullet summary. The choice rewrites one line of the prompt, so the same passages come back in a different shape.
- **Live status + transcript export.** The handler is a generator that yields "Searching…" then "Writing the answer…", and the conversation saves to a Markdown file.

## What I learned

**What was challenging?** Colab ran out of free GPU quota partway through, so the 4-bit Mistral-7B would not load. I added an automatic fallback to a smaller CPU model. The first fallback I tried, Qwen2.5-0.5B, answered "yes, the product does contain animal-origin material" when the declaration says the opposite, so I moved up to Qwen2.5-1.5B, which reads the passages correctly. Small models invert negations, and grounding alone does not save you from that.

**What would you improve next time?** Stream the answer token by token instead of waiting for the whole generation, add a confidence signal when the top retrieval score is low, and keep a lexical search beside the embeddings so exact lot and document numbers are never missed.

**How does it compare to the tutorial version?** The tutorial version was one chat box wired to a model. Mine reads real PDFs, retrieves only the passages that answer the question, cites the page each one came from, and refuses when the passages do not contain the answer. It also has a two-column layout, two dropdowns that change behaviour without touching code, a live status line and a transcript download.
