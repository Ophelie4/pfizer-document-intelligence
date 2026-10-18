# Project 1: How AI Reads Pharmaceutical Documents

**Week 1.** This project covers the basics: machine learning, deep learning, LLMs, NLP, computer vision and OCR, and why pharmaceutical documentation is hard for AI to process.

Everything I submitted for this project was written, so all of it is on this page.

---

## Task: Research and explain how LLMs work

**Prompt:** Explain LLMs to someone who has never heard of them, focusing on how they generate responses and learn from data.

> Large Language Models (LLMs) are AI systems trained on huge amounts of text data like books, websites, and articles, so they learn the patterns of how words and ideas connect. At their core, they use an architecture called the Transformer, which allows the model to pay attention to different parts of a sentence at the same time, helping it understand context rather than reading one word at a time. When you ask an LLM a question, it does not look up a pre-written answer but instead predicts the most likely next word, then the next, building a response piece by piece based on everything it learned during training. Models like ChatGPT are also refined through a process called reinforcement learning from human feedback (RLHF), where human raters score responses and the model gradually learns to give more helpful and accurate answers. So in simple terms, LLMs are pattern-matching systems that have absorbed so much human writing that they can hold fluent conversations and work through complex questions.

---

## Task: Review sample pharmaceutical documentation

**Which document types were in the file?**
A Product Specification, Certificate of Analysis, Compliance with International Standards, Pharmacopoeia Compliance Statement, BSE-TSE Statement, a Melamine Free Statement, a Phthalate Statement, a Supply Chain Traceability Description, Production Information, and a Technical Information sheet.

**Which date formats did I see?**
The dates were all over the place, which was kind of surprising. I found at least five different formats being used across the documents: `06/17/2025`, `01. Jul 2024`, `13.Oct.2025`, `2025-12-11`, and `22 May, 2024`.

**Were any documents older than 3–4 years?**
Just one that really stood out, the Pharmacopoeia Compliance Statement, dated October 4, 2022. That puts it at about 3.5 years old, which just barely crosses the threshold.

**What challenges might AI face with this documentation?**
Honestly, there is a lot that could trip up an AI here. The date formats alone are a mess, and an AI would have to somehow recognize all of them as dates. Then there are the graphs, chemical structures, and tables in the Technical Information sheet that are really hard to extract meaning from without being able to "see" them properly. On top of that, almost every document has the same legal disclaimer copied and pasted at the end, which could easily confuse a model trying to pull out what actually matters. And if any pages were scanned rather than digitally generated, reading them accurately would be a whole other challenge.

---

## Project recap

**Highlight reel:** Honestly, the moment it all clicked for me. Reading through a real pharmaceutical document and actually being able to make sense of it. Going from "what even is a Certificate of Analysis" to being able to identify different document types and spot inconsistencies felt like a real win.

**Skill I leveled up most:** Critical thinking for sure. I went in expecting a straightforward read, but I had to actually slow down and pay attention to details like date formats, document structure, and what each document was trying to communicate. I noticed the growth when I started connecting the dots between documents without needing to re-read everything multiple times.

**Hardest part:** Keeping track of so many different document types that all looked pretty similar at first glance. A lot of them shared the same BASF branding and boilerplate legal text, so figuring out what made each one unique took more focus than I expected. I pushed through by taking it one document at a time instead of trying to process everything at once.

**What I'd change:** I would add more variety to the sample file, maybe include documents from different companies or with different formatting styles, not just BASF. It would make the exercise feel more realistic and give a better sense of the range of challenges AI would actually face in the real world.

**Project emoji:** 😅 challenging but worth it
