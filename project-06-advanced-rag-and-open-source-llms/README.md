# Project 6: Advanced RAG and Open-Source Experiments

**Weeks 6–7.** Comparing embedding models, tuning retriever configurations (top-k, thresholds, a custom LLM re-ranker), running open-source LLMs locally with llama.cpp, and a controlled Gemini vs Mistral-7B / Phi-2 / TinyLlama evaluation.

## Notebooks

| Notebook | Task |
|---|---|
| [`Ophelie_Embedding_Model_Comparison.ipynb`](notebooks/Ophelie_Embedding_Model_Comparison.ipynb) | MiniLM vs E5 vs BGE embeddings |
| [`Ophelie_RAG_Configurations_Comparison.ipynb`](notebooks/Ophelie_RAG_Configurations_Comparison.ipynb) | 3 retriever configurations, including a custom LLM re-ranker |
| [`Ophelie_Run_First_OpenSource_LLM.ipynb`](notebooks/Ophelie_Run_First_OpenSource_LLM.ipynb) | Mistral-7B-Instruct (GGUF) with llama-cpp-python on a T4 |
| [`Ophelie_Gemini_vs_OpenSource_LLM_Comparison.ipynb`](notebooks/Ophelie_Gemini_vs_OpenSource_LLM_Comparison.ipynb) | Evaluation v1 |
| [`Ophelie_Gemini_vs_OpenSource_LLM_Comparison_v2.ipynb`](notebooks/Ophelie_Gemini_vs_OpenSource_LLM_Comparison_v2.ipynb) | Evaluation v2 |
| [`Ophelie_Gemini_vs_OpenSource_LLM_Comparison_v3.ipynb`](notebooks/Ophelie_Gemini_vs_OpenSource_LLM_Comparison_v3.ipynb) | Evaluation v3 (submitted, final) |

## Reports

- [Embedding Model Comparison Results](reports/embedding-model-comparison.md)
- [RAG Configurations Comparison Results](reports/rag-configurations-comparison.md)
- [Gemini vs Mistral 7B / Phi-2 / TinyLlama: SDF Evaluation Results](reports/gemini-vs-open-source-llm-evaluation.md)

---

## Task answers

### Run 3 RAG configurations
**Confident about tuning retrievers now?** Yes. Details are in the [configurations report](reports/rag-configurations-comparison.md).

### Run your first open-source LLM
This one was a nice change of pace from the API-key-based tasks. There's no API key to generate here at all, and that's the whole point of the exercise: Mistral-7B-Instruct runs entirely inside the Colab VM once the ~4.1 GB GGUF file is downloaded from Hugging Face, with no auth or quota involved. The real friction was elsewhere: getting `llama-cpp-python` installed with the matching CUDA wheel (I had to switch the runtime to a T4 GPU first, per the instructions, or the pip install/model load would fail), and then the model download itself (4.1 GB, which took under a minute on Colab's connection). Generation was noticeably slower than Gemini, about 167 seconds for a 256-token response, because the sample code only offloads `n_gpu_layers=1` to the GPU, so most of the compute still runs on CPU. So overall: no permission/API-key friction, but real infrastructure and latency trade-offs instead.

### Integrating open-source LLMs into RAG (with a PDF)
**Was I able to run all the steps and see Mistral answer my question?** Yes.

### Evaluate Gemini vs Mistral/Phi-2 on SDF document queries
See the [full evaluation report](reports/gemini-vs-open-source-llm-evaluation.md).

---

## Project recap

**Highlight reel:** Three things would be on it. PaddleOCR reading the accented ÄKTA trademark correctly while EasyOCR turned a whole line into "Cburprodt Griginaustactured". The moment the reranker I had to build from scratch pulled the bio-safety chunk back above the device specs, which was the first time a change I made visibly improved an answer instead of just moving a number around. And Phi-2, in the final task, confidently telling me the context did not say the product was autoclaved when the autoclave line was sitting right there in its own prompt. That one goes on the reel because it taught me more than most of the things that worked.

**Skill I leveled up most:** Debugging libraries I had never touched before instead of giving up and swapping to a different one. Early on, when PaddleOCR threw a `TypeError` and then a `NotImplementedError` from its execution backend, my first instinct was to drop it and just use Tesseract. I stayed with it, actually read the errors, and got it running by disabling MKL-DNN. After that it turned into a pattern. When LlamaIndex's built-in reranker would not behave with a non-OpenAI model, I wrote my own. When the Gemini API kept returning quota errors, I switched models and kept the rest of the pipeline intact. I noticed the growth mostly in how much faster I stopped panicking at a red traceback.

**Hardest part:** The final model comparison, and not for the reason I expected. The concepts were the easy part. It was the environment that fought back. The notebook had to be rebuilt more than once, Gemini Flash kept returning 503 overloaded errors so I fell back to Flash Lite, and even with full GPU offload requested the local models ended up running on CPU at under half a token per second, which meant a single Mistral answer took roughly nine minutes. I got through it by changing one thing at a time and re-running, instead of changing three things at once and guessing which fix worked. The other thing that helped was trusting the numbers the notebook printed rather than how the output looked on screen. I also decided it was better to report the CPU problem as a caveat in my write-up than to quietly present those speeds as if they were GPU results.

**What I'd change:** I would use a longer and messier document, or two suppliers with different formats. The sample SDF is only three pages and about 4,000 characters, which splits into just six chunks, and the query keywords match the source text almost word for word. That made retrieval close to trivial, so the embedding comparison and the retriever configuration comparison kept landing on the same top chunk and the differences between them were mostly cosmetic. With a document long enough that the right passage is genuinely hard to find, both of those tasks would have taught me a lot more, and the 2,048-token context limits on Phi-2 and TinyLlama would have become a real constraint instead of a footnote.

**Project emoji:** 💡 so many lightbulb moments
