# Gemini vs Mistral 7B / Phi-2 / TinyLlama: SDF Evaluation Results

**Date:** August 30, 2026
**Document tested:** sample-sdf-document.pdf (Cytiva ÄKTA ready Flow Kit storage-conditions letter + two Certificates of Quality, 3 pages, 4,025 characters)
**Notebook:** [`Ophelie_Gemini_vs_OpenSource_LLM_Comparison_v3.ipynb`](../notebooks/Ophelie_Gemini_vs_OpenSource_LLM_Comparison_v3.ipynb)
**Hardware:** Google Colab, Tesla T4 runtime

---

## Part 0: Experimental design

The goal was to isolate the generator LLM. Everything upstream of generation was held constant:

| Layer | Setting | Varies? |
|---|---|---|
| Document | sample-sdf-document.pdf, PyMuPDF extraction, 6 chunks | No |
| Chunking | SentenceSplitter, chunk_size=200, chunk_overlap=30 | No |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 | No |
| Retriever | Vector similarity, top_k=4 | No |
| Prompt | Retrieved chunks assembled into one string, byte-identical across models | No |
| Decoding | temperature=0.1, max_tokens=300 | No |
| Generator LLM | Gemini / Mistral 7B / Phi-2 / TinyLlama | **Yes** |

Retrieval ran once per query and the resulting prompt string was sent unchanged to all four models. Every difference below is therefore attributable to the model, not to one model getting luckier chunks.

### Models compared

| Model | How it ran | File size | Context window |
|---|---|---|---|
| Gemini (models/gemini-flash-lite-latest) | Hosted API | n/a | Very large |
| Mistral-7B-Instruct-v0.2, Q4_K_M GGUF | Local, llama.cpp | 4.07 GB | 4096 |
| Phi-2, Q4_K_M GGUF | Local, llama.cpp | 1.67 GB | 2048 |
| TinyLlama-1.1B-Chat-v1.0, Q4_K_M GGUF | Local, llama.cpp | 0.62 GB | 2048 |

Phi-2 is a base model with no chat template, so it was prompted in its documented Instruct / Output format. Mistral and TinyLlama used their own chat templates.

### Two caveats about these numbers

1. **The local models ran on CPU, not the T4.** They were loaded with `n_gpu_layers=-1` (full GPU offload), but the observed throughput (0.17 to 2.6 tokens/sec) is CPU speed, not GPU speed. The prebuilt llama-cpp-python CUDA wheel did not engage the T4 in this runtime. The speed figures below are real measurements, but they measure CPU inference. With working GPU offload the local models would be substantially faster, and the speed gap reported here would narrow.
2. **The context-limit test is partial.** Gemini's run completed. The local models' runs were stopped after about 9 minutes because, at the CPU throughput above, Mistral alone would have needed roughly 50 minutes to generate the 600-token summary. What is reported for the local models under Part 4 is their context-window capacity, not a completed generation.

---

## Part 1: Retrieval (shared by all four models)

The index built in 0.027s over 6 chunks. Retrieval was effectively instant in every case.

| Query | Chunks | Similarity scores | Retrieve time | Prompt size |
|---|---|---|---|---|
| What sterilization method was used for this product? | 4 | 0.3662, 0.3626, 0.2977, 0.1885 | 0.0357s | 3,318 chars |
| Summarize the key specifications in this document. | 4 | 0.2377, 0.1654, 0.1569, 0.1451 | 0.0128s | 3,104 chars |
| What are the storage conditions for this product? | 4 | 0.2410, 0.1617, 0.1581, 0.1173 | 0.0130s | 3,380 chars |

Retrieval did its job. For the sterilization query the top chunk was the Product Release Criteria table containing "Autoclave / Pump tubing / 121°C > 15 min" and "Gamma Irradiation / Inlets / 25.0 – 40.0 kGy", exactly the right passage. For the storage query the top chunk was the Cytiva letter, which is where the > +5 °C guidance actually lives (not in either Certificate of Quality). So every model below was handed correct context. Every failure that follows is a generation failure, not a retrieval failure.

---

## Part 2: Speed test

| Model | Avg latency per answer | Avg tokens/sec | Range |
|---|---|---|---|
| Gemini Flash Lite | 0.82s | 173.2 | 0.64s to 1.10s |
| TinyLlama-1.1B Q4_K_M | 104.7s | 2.39 | 91s to 114s |
| Phi-2 Q4_K_M | 226.0s | 0.46 | 179s to 293s |
| Mistral-7B-Instruct-v0.2 Q4_K_M | 524.6s | 0.26 | 498s to 567s |

Model load time: Mistral 17.8s. Downloads: Mistral 4.07 GB in 42s, Phi-2 1.67 GB in 28s, TinyLlama 638 MB in 7s.

Gemini answered every query in about a second. Mistral took eight to nine and a half minutes per answer, roughly 600 to 700 times slower in tokens/sec. Note the inverse relationship between size and speed among the local models: TinyLlama (0.62 GB) was about 9x faster than Mistral (4.07 GB), which is what you would expect when the bottleneck is CPU compute.

---

## Part 3: Accuracy test

Fact recall is a keyword check counting how many values that genuinely appear in the source document show up in the answer. It is a crude proxy, so the answers were also read directly; the notes column reflects that reading.

| Model | Q1 sterilization | Q2 specifications | Q3 storage | Total | Notes |
|---|---|---|---|---|---|
| Gemini Flash Lite | 5/5 | 4/5 | 5/5 | **14/15** | Correct and cleanly structured throughout. Q2 was cut off by the 300-token cap. |
| Mistral-7B-Instruct-v0.2 | 5/5 | 5/5 | 4/5 | **14/15** | Correct on all three. Only model to explain which method applied to which component. |
| TinyLlama-1.1B-Chat | 2/5 | 2/5 | 5/5 | 9/15 | Repetitive and self-contradictory. High Q3 score comes from copying source text, not from understanding. |
| Phi-2 | 3/5 | 1/5 | 1/5 | 5/15 | Worst performer. Hallucinated a false negative and leaked the prompt format. Two answers stopped mid-sentence. |

### Gemini Flash Lite
On sterilization it returned both methods with their limits, correctly paired: Autoclave (for Pump tubing) at 121°C > 15 min, and Gamma Irradiation (for Inlets) at 25.0 to 40.0 kGy. On storage it correctly separated the > +5 °C storage recommendation from the +2 °C to +40 °C operating range, and included the brittleness warning. One quirk worth noting for a document pipeline: it emitted LaTeX math markup for the temperature values, which would need stripping before the text went anywhere downstream.

### Mistral-7B-Instruct-v0.2
The most complete answers of the four. On sterilization it did something no other model did: it attributed each method to the correct component and said so explicitly: "the pump tubing was autoclaved at 121°C for more than 15 minutes and ... the inlets were exposed to gamma irradiation with a dose between 25.0 and 40.0 kGy. Therefore, both the pump tubing and the inlets were sterilized using different methods." Its specifications summary was the only local answer to catch the USP <88> regulatory conformance. It scored 4/5 rather than 5/5 on storage only because the keyword check looked for "brittle", which Mistral omitted while otherwise answering correctly.

### TinyLlama-1.1B-Chat
Fluent but unreliable. On the sterilization query it never named a sterilization method as the answer. It drifted into ISO 9001 certification and USP <88> compliance, mentioning gamma irradiation only in passing. Its answers loop, repeating the same clause several times. Most importantly, on the storage query (its highest-scoring answer) it stated "The recommended storage temperature for these kits is +2 C to +40 C", which is wrong; that is the operating range, and it had already given the correct > +5 C figure one sentence earlier. This is exactly the failure mode a keyword metric cannot see.

### Phi-2
The clearest failure. Asked which sterilization method was used, it answered "gamma irradiation" only, and then justified it with a fabricated claim: "The context does not provide the information that the product is autoclaved." The autoclave line was in the top-scoring retrieved chunk, directly in its prompt. It then ran past its answer and began generating its own follow-up questions and answers, echoing the prompt template back: a prompt-format leak that ate its entire 300-token budget. On the other two queries it stopped mid-sentence: "with a Part Number of" and "and specified as". Two of three answers are unusable as written.

---

## Part 4: Context-limit test

The whole document (1,156 prompt tokens) was placed in a single prompt with a request for a detailed structured summary, capped at 600 output tokens.

| Model | Context window | Result |
|---|---|---|
| Gemini Flash Lite | Very large | 1.84s, 1,156 prompt tokens, 596 output tokens, finish_reason = MAX_TOKENS (hit the 600 cap, not a context limit) |
| Mistral-7B-Instruct-v0.2 | 4,096 tokens | Prompt fits comfortably; generation not completed (see caveat 2) |
| Phi-2 | 2,048 tokens | Prompt fits; generation not completed |
| TinyLlama-1.1B-Chat | 2,048 tokens | Prompt fits; generation not completed |

The more useful finding came out of the main test rather than this one: Gemini hit MAX_TOKENS on the specifications query at the 300-token cap, producing a summary that stops in the middle of the test-methods list. Phi-2 and TinyLlama also hit their caps on the sterilization query, but for the opposite reason: they were padding, not running out of room for real content. So truncation happened for two completely different reasons, and only reading the answers distinguishes them.

A second, more structural point: this document is only 1,156 tokens. Phi-2 and TinyLlama have 2,048-token windows, which means a document roughly twice this size would not fit in their context at all, while Gemini and Mistral (4,096 here, 32k natively) would still have room. For pharmaceutical documentation, where a full batch record runs far longer than three pages, that is a hard ceiling rather than a performance trade-off.

---

## Part 5: Analysis

### 1. Which model felt most "human" in its responses?
Mistral. It was the only model that reasoned about the content rather than reciting it. On the sterilization query it worked out that two different methods applied to two different components and said so in a full sentence, which is how a person answering that question would put it. Gemini was more polished and better formatted, but it read like a well-organised extraction: bulleted, precise, slightly clinical, and dotted with LaTeX markup. TinyLlama was fluent in a superficial way and repeated itself, which reads less human the longer you look at it. Phi-2 did not read like an answer at all, since it started interviewing itself.

### 2. Was there a trade-off between speed and quality?
Not in the direction I expected. Gemini was both the fastest and among the most accurate, so between the hosted API and every local model there was no trade-off: Gemini simply won on both. The trade-off appeared strictly among the local models, and it ran the wrong way: TinyLlama was about 9x faster than Mistral and far less accurate (9/15 vs 14/15), while Phi-2 was slower than TinyLlama and the least accurate of all (5/15). So among the open-source options you pay for quality with time, but paying more time does not guarantee quality. Phi-2 cost more than twice TinyLlama's runtime and returned worse answers.

### 3. Would you trust this model with important documents?
Mistral, yes, with a human review step: it got 14/15 and did not invent anything. Gemini, yes, on the same terms, with a note that its LaTeX output needs sanitising before it feeds another system. Phi-2 and TinyLlama, no, not for regulated documentation. The specific reason is not that they scored low but how they failed: Phi-2 stated that the context did not contain information that was sitting in its prompt, and TinyLlama asserted a storage temperature that was actually the operating temperature. Both errors are stated confidently and fluently. In a compliance workflow, a wrong answer that reads as authoritative is more dangerous than an obvious refusal, because it survives a skim.

### 4. Would you use an open-source model in production, or is Gemini better? Why?
For this workload, Gemini. On measured performance it matched the best open-source model on accuracy (14/15 each) while answering in 0.82s against Mistral's 524.6s, and it needs no 4 GB download or GPU provisioning. The caveat is that the local models here ran on CPU, so the true production gap on proper GPU hardware would be much smaller, but it would not reverse the accuracy result, and it would introduce infrastructure cost that the API does not have.

Where I would choose open source is where the constraint is not speed or accuracy: data residency. These are pharmaceutical supplier documents, and Mistral answered them without a single byte leaving the machine: no API key, no quota, no third party. If Pfizer's requirement is that supplier documentation never transits an external service, that is not a preference Gemini can be tuned to satisfy at any latency. In that case Mistral 7B on a proper GPU is a viable choice, because its accuracy is already there. The decision is about where the data is allowed to go, not about which model is better.

### 5. Which model surprised you (good or bad)? Why?
Phi-2 surprised me badly. It is 2.7x larger than TinyLlama and Microsoft markets it on reasoning benchmarks, so I expected it to sit comfortably between TinyLlama and Mistral. Instead it finished last at 5/15, below the 1.1B model, and it failed in the worst possible way for a document pipeline by confidently denying a fact that was present in its own prompt. The lesson I am taking from it is that benchmark reputation did not survive contact with a real retrieval task, and that a base model without a chat template will happily keep generating past the answer and echo your prompt back at you.
