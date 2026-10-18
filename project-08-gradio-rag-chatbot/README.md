# Project 8: Gradio Chatbot with RAG Integration

**Weeks 8–9.** Building Gradio interfaces, then wiring a full RAG pipeline (OCR fallback, metadata tagging, FAISS, open-source LLM, citations and confidence) into a chat UI.

## Notebooks

| Notebook | Task |
|---|---|
| [`Pfizer_Gradio_Math_Superpowers.ipynb`](notebooks/Pfizer_Gradio_Math_Superpowers.ipynb) | Build a simple app with Gradio (square + factorial) |
| [`Pfizer_Document_QA_Chatbot.ipynb`](notebooks/Pfizer_Document_QA_Chatbot.ipynb) | My own document Q&A chatbot interface |
| [`Pfizer_Capstone_Full_RAG_UI.ipynb`](notebooks/Pfizer_Capstone_Full_RAG_UI.ipynb) | Full RAG UI (capstone) |

> The Gradio apps ran on temporary `gradio.live` share links, which expire. To see an app, open its notebook in Colab and run all cells.

## Reports and decks

- [Full RAG Pipeline: Project Write-up](reports/full-rag-pipeline-writeup.md)
- [Document Q&A Chatbot: slide deck (text)](reports/document-qa-chatbot-deck.md)
- [Full RAG UI: Capstone deck (text)](reports/full-rag-ui-capstone-deck.md)

---

## Task answers

### Build a simple app with Gradio
**If the outputs were wrong, what would I check first: the math, the input type, or the return format?**
The input type first. The math is three lines and easy to check by hand, and the return format either shows up or it doesn't, so both fail loudly. The input is the quiet one. If the number arrives as a string, `number ** 2` either throws or silently does something strange, and `math.factorial` rejects a float like 5.0 even though it looks like a whole number on screen. That's why I used `gr.Number` rather than a text box, and why the function checks `number != int(number)` before calling factorial. I'd print the value and its type inside the function as the very first debugging step.

**What would change to return the square root instead of the factorial?**
Two small changes. Swap `math.factorial(int(number))` for `math.sqrt(number)`, and change the guard, since square root cares about a different thing than factorial does. Factorial rejects negatives and non-whole numbers; square root is happy with 2.5 but has no real answer for a negative, so the whole-number check goes away and the negative check stays. I'd also rename the dictionary key from `factorial` to `square_root` and update the output label, otherwise the app returns the right value under the wrong name.

### Create my own chatbot interface
**What I added or changed compared to the tutorial:**

The tutorial version was one chat box wired to a model. Mine is a small application. It reads real PDFs, chunks them with overlap and embeds them with bge-small, then answers only from the passages retrieved for that specific question, and every answer ends with the file and page each passage came from so it can be checked rather than trusted.

On top of that I added multiple PDF upload, a "Search in" dropdown that restricts retrieval to one file, an answer-style dropdown (short, detailed or bullet summary) that rewrites one line of the prompt, a two-column layout instead of a single stacked one, a teal theme with emoji labels, a Save transcript button that exports the conversation to Markdown, and a Load sample PDF button so the app can be demoed without uploading anything. The chat handler is a generator, so the status line moves through "Searching the document" and "Writing the answer" instead of the UI sitting frozen. The prompt also tells it to say when the passages do not contain the answer, rather than guessing.

One thing I did not plan: Colab ran out of free GPU quota, so I added an automatic model fallback. It uses 4-bit Mistral-7B when a GPU is available and Qwen2.5-1.5B on CPU when there is not, which keeps the notebook running end to end. The first fallback I tried, Qwen2.5-0.5B, answered "yes, the product contains animal-origin material" when the source document says the exact opposite, so I moved up a size. Grounding the model in retrieved passages does not protect you from a model too small to read a negation.

### Build the full RAG UI
See the [full RAG pipeline write-up](reports/full-rag-pipeline-writeup.md) and the [capstone deck](reports/full-rag-ui-capstone-deck.md).
