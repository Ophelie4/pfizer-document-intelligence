"""Gradio interface for the document intelligence pipeline.

Header with model status, packet KPIs, a document inventory, chat with suggested
questions, and an evidence panel with a confidence meter and every cited passage.
"""
import datetime
import html as _html
import tempfile

import gradio as gr

import pipeline as P

TYPE_COLORS = {   # doc_type -> (background, text)
    "Cover Letter":                  ("#EEF2F7", "#334155"),
    "Certificate of Quality":        ("#E7F6EE", "#166534"),
    "Packaging Specification":       ("#FEF3E2", "#9A4D00"),
    "BSE/TSE Declaration":           ("#F1ECFE", "#5B21B6"),
    "Material Description Sheet":    ("#E8F0FE", "#1E40AF"),
    "Supplier Qualification Record": ("#E3F6F5", "#0F6E6A"),
    "Chain of Custody":              ("#FDECEF", "#9F1239"),
    "Unknown":                       ("#F1F5F9", "#64748B"),
}
LEVEL_COLORS = {"High": "#16A34A", "Medium": "#D97706", "Low": "#DC2626", "none": "#94A3B8"}

SUGGESTIONS = [
    ("Animal-origin material?",  "Does the product contain any material of animal origin?"),
    ("Packaging changes",        "Were there any packaging configuration changes?"),
    ("Last supplier audit",      "When was the supplier last audited and what was the result?"),
    ("Released lots",            "Which lots were released and did they pass their tests?"),
]

esc = lambda s: _html.escape(str(s))

def type_tag(t):
    bg, fg = TYPE_COLORS.get(t, TYPE_COLORS["Unknown"])
    return f'<span class="pdi-tag" style="background:{bg};color:{fg}">{esc(t)}</span>'


def header_html():
    return f"""
<div class="pdi-header">
  <div class="pdi-brand">
    <div class="pdi-logo">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="white" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
           <path d="M14 2v6h6"/><circle cx="11.5" cy="14.5" r="2.5"/><path d="M13.3 16.3 16 19"/></svg>
    </div>
    <div>
      <div class="pdi-title">Pharma Document Intelligence</div>
      <div class="pdi-sub">Ask questions across supplier documentation. Every answer is cited and scored.</div>
    </div>
  </div>
  <div class="pdi-pills">
    <span class="pdi-pill"><span class="pdi-dot"></span>{esc(P.model_label())}</span>
    <span class="pdi-pill">Open-source stack · no external APIs</span>
  </div>
</div>"""


def kpi_html(store=None):
    if store:
        pages = store["pages"]
        vals = [len({p["source_file"] for p in pages}), len(pages),
                len({(p["source_file"], p["doc_id"]) for p in pages}),
                len(store["chunks"]), sum(1 for p in pages if p["ocr"])]
    else:
        vals = ["—"] * 5
    labels = ["Files", "Pages", "Documents found", "Chunks indexed", "Pages via OCR"]
    cards = "".join(f'<div class="pdi-kpi"><div class="pdi-kpi-val">{v}</div>'
                    f'<div class="pdi-kpi-label">{l}</div></div>' for v, l in zip(vals, labels))
    return f'<div class="pdi-kpis">{cards}</div>'


def inventory_html(store=None):
    if not store:
        return ('<div class="pdi-empty-sm">No packet loaded yet. Upload PDFs or load the '
                'sample packet to see the documents it contains.</div>')
    docs = {}
    for p in store["pages"]:
        docs.setdefault(p["source_file"], {}).setdefault(p["doc_id"], (p["doc_type"], p["page_range"]))
    out = ['<div class="pdi-inv">']
    for f, ds in docs.items():
        out.append(f'<div class="pdi-inv-file">{esc(f)} <span>{len(ds)} docs</span></div>')
        for did, (t, rng) in ds.items():
            out.append(f'<div class="pdi-inv-row">{type_tag(t)}'
                       f'<span class="pdi-inv-pages">p. {esc(rng)}</span></div>')
    out.append("</div>")
    return "".join(out)


def evidence_html(res=None, loading=False):
    if loading:
        return ('<div class="pdi-empty"><div class="pdi-spinner"></div>'
                'Retrieving passages and writing a grounded answer…</div>')
    if not res:
        return ('<div class="pdi-empty"><b>Evidence appears here</b><br>Each answer is backed by the '
                'exact passages it came from, with page numbers and similarity scores.</div>')
    if not res["sources"]:
        return '<div class="pdi-empty">No passages matched that question.</div>'
    lvl, pct = res["confidence_label"], res["confidence"]
    color = LEVEL_COLORS.get(lvl, "#94A3B8")
    out = [f"""
<div class="pdi-conf">
  <div class="pdi-conf-top">
    <div><div class="pdi-conf-label">Retrieval confidence</div>
         <div class="pdi-conf-val">{pct}%</div></div>
    <span class="pdi-level" style="background:{color}1A;color:{color}">{esc(lvl)}</span>
  </div>
  <div class="pdi-bar"><div style="width:{min(pct, 100)}%;background:{color}"></div></div>
  <div class="pdi-conf-note">Scored from retrieval similarity across {res['chunks_used']} passages,
  not from the model's wording.</div>
</div>
<div class="pdi-src-title">Sources</div>"""]
    for s in res["sources"]:
        text = s.get("text", "")
        snippet = esc(text[:200] + ("…" if len(text) > 200 else ""))
        full = esc(text)
        ocr = '<span class="pdi-ocr">OCR</span>' if s["ocr"] else ""
        sim = round(s["score"] * 100)
        more = (f'<details><summary>Show full passage</summary><div class="pdi-full">{full}</div></details>'
                if len(text) > 200 else "")
        out.append(f"""
<div class="pdi-src">
  <div class="pdi-src-head">
    <span class="pdi-num">{s['n']}</span>{type_tag(s['doc_type'])}{ocr}
    <span class="pdi-sim"><span class="pdi-simbar"><span style="width:{sim}%"></span></span>{s['score']:.2f}</span>
  </div>
  <div class="pdi-src-meta">{esc(s['file'])} · page {s['page']} · document pages {esc(s['page_range'])}</div>
  {f'<div class="pdi-snippet">{snippet}</div>' if text else ''}
  {more}
</div>""")
    return "".join(out)


def status_md(msg, kind="info"):
    return f'<div class="pdi-status pdi-{kind}">{esc(msg)}</div>'


# ── event handlers ──
def ui_ingest(file_list):
    if not file_list:
        return (gr.update(), status_md("Choose at least one PDF to index.", "warn"),
                gr.update(), gr.update(), gr.update())
    try:
        st = P.ingest(file_list)
    except Exception as e:
        return (None, status_md(f"Could not index those files ({type(e).__name__}).", "warn"),
                gr.update(), kpi_html(None), inventory_html(None))
    if st is None:
        return (None, status_md("No readable pages found.", "warn"),
                gr.update(choices=["All types"], value="All types"), kpi_html(None), inventory_html(None))
    types = sorted({p["doc_type"] for p in st["pages"]})
    return (st, status_md("Packet indexed. Ready for questions.", "ok"),
            gr.update(choices=["All types"] + types, value="All types"), kpi_html(st), inventory_html(st))


def ui_load_samples():
    try:
        paths = P.sample_paths()
    except Exception as e:
        return (gr.update(), status_md(f"Could not download the sample packet ({type(e).__name__}).", "warn"),
                gr.update(), gr.update(), gr.update())
    return ui_ingest(paths)


def respond(message, history, mode, doc_type, k, store):
    history = list(history or [])
    message = (message or "").strip()
    if not message:
        yield history, "", status_md("Type a question first.", "warn"), gr.update()
        return
    history.append({"role": "user", "content": message})
    if not store:
        history.append({"role": "assistant",
                        "content": "Load the sample packet or upload PDFs first, then ask again."})
        yield history, "", status_md("No documents indexed yet.", "warn"), gr.update()
        return

    first = P.get_llm.cache_info().currsize == 0
    yield (history, "",
           status_md("Loading the language model (first question only, this can take a minute)…"
                     if first else "Searching the index…"),
           evidence_html(loading=True))
    res = P.rag_answer(message, store, doc_type, mode, int(k))
    lvl = res["confidence_label"]
    dot = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(lvl, "⚪")
    history.append({"role": "assistant",
                    "content": f"{res['answer']}\n\n{dot} *{lvl} confidence · {res['confidence']}% · "
                               f"{res['chunks_used']} sources cited*"})
    yield history, "", status_md("Answer ready. Sources are on the right.", "ok"), evidence_html(res)


def _text(c):
    """Gradio 6 returns chat content as a list of {'type': 'text', 'text': ...} parts."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(_text(x) for x in c)
    if isinstance(c, dict):
        return c.get("text") or c.get("value") or ""
    return str(c)


def save_transcript(history):
    lines = ["# Pharma Document Intelligence: transcript",
             f"_{datetime.datetime.now():%Y-%m-%d %H:%M}_", ""]
    for m in history or []:
        who = "**You**" if m["role"] == "user" else "**Assistant**"
        lines.append(f"{who}: {_text(m['content'])}\n")
    with tempfile.NamedTemporaryFile("w", suffix=".md", prefix="transcript-", delete=False) as f:
        f.write("\n".join(lines))
    return gr.update(value=f.name, visible=True)


def clear_chat():
    return [], "", status_md("Conversation cleared."), evidence_html(None), gr.update(visible=False)


# ── styling ──
THEME = gr.themes.Soft(
    primary_hue="blue", secondary_hue="slate", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill="#F4F6FB",
    block_radius="12px",
    button_primary_background_fill="#1D4ED8",
    button_primary_background_fill_hover="#1E40AF",
    button_primary_text_color="white",
    block_label_background_fill="transparent",
    block_label_text_color="#334155",
    block_label_text_weight="600",
    block_title_background_fill="transparent",
    block_title_text_color="#334155",
    block_title_text_weight="600",
)

CSS = """
.gradio-container {max-width: 1480px !important; margin: 0 auto !important;}
footer {display: none !important;}
.pdi-header {display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;
  background:linear-gradient(120deg,#0B1F4D 0%,#1D4ED8 100%); color:white; padding:20px 26px;
  border-radius:16px; box-shadow:0 8px 24px rgba(29,78,216,.18);}
.pdi-brand {display:flex; align-items:center; gap:14px;}
.pdi-logo {width:44px; height:44px; border-radius:12px; background:rgba(255,255,255,.16);
  display:flex; align-items:center; justify-content:center;}
.pdi-header, .pdi-header * {color:white !important;}
.pdi-title {font-size:21px; font-weight:700; letter-spacing:-.01em;}
.pdi-sub {font-size:13.5px; opacity:.85; margin-top:2px;}
.pdi-pills {display:flex; gap:8px; flex-wrap:wrap;}
.pdi-pill {display:inline-flex; align-items:center; gap:7px; font-size:12.5px; font-weight:500;
  padding:6px 12px; border-radius:999px; background:rgba(255,255,255,.14);
  border:1px solid rgba(255,255,255,.22);}
.pdi-dot {width:8px; height:8px; border-radius:50%; background:#4ADE80; box-shadow:0 0 0 3px rgba(74,222,128,.25);}

.pdi-kpis {display:grid; grid-template-columns:repeat(5,1fr); gap:12px;}
@media (max-width: 900px) {.pdi-kpis {grid-template-columns:repeat(2,1fr);}}
.pdi-kpi {background:white; border:1px solid #E3E8F2; border-radius:12px; padding:14px 18px;}
.pdi-kpi-val {font-size:26px; font-weight:700; color:#0B1F4D; line-height:1.1;}
.pdi-kpi-label {font-size:12px; color:#64748B; margin-top:4px; text-transform:uppercase; letter-spacing:.04em;}

.pdi-card {background:white !important; border:1px solid #E3E8F2 !important; border-radius:16px !important;
  padding:18px !important; box-shadow:0 1px 3px rgba(15,23,42,.04);}
.pdi-section {font-size:13px; font-weight:700; color:#0B1F4D; text-transform:uppercase;
  letter-spacing:.06em; margin:2px 0 4px;}
.pdi-section span {font-weight:500; text-transform:none; letter-spacing:0; color:#64748B; margin-left:6px;}

.pdi-tag {display:inline-block; font-size:11.5px; font-weight:600; padding:3px 9px; border-radius:999px; white-space:nowrap;}
.pdi-inv {display:flex; flex-direction:column; gap:6px; max-height:400px; overflow-y:auto;}
.pdi-inv-file {font-size:12px; font-weight:600; color:#334155; margin-top:6px; font-family:var(--font-mono);}
.pdi-inv-file span {font-family:var(--font); font-weight:500; color:#94A3B8; margin-left:4px;}
.pdi-inv-row {display:flex; justify-content:space-between; align-items:center; padding:7px 10px;
  border:1px solid #EEF1F6; border-radius:10px; background:#FAFBFD;}
.pdi-inv-pages {font-size:12px; color:#64748B;}
.pdi-empty-sm {font-size:13px; color:#64748B; padding:12px; border:1px dashed #CBD5E1; border-radius:10px; background:#FAFBFD;}

.pdi-status {font-size:13px; padding:8px 12px; border-radius:10px; background:#F1F5F9; color:#334155;}
.pdi-ok {background:#ECFDF3; color:#166534;}
.pdi-warn {background:#FEF6E7; color:#92400E;}

.pdi-chips {gap:8px !important; flex-wrap:wrap !important;}
.pdi-chips button {flex:0 0 auto !important; min-width:0 !important; border-radius:999px !important;
  font-weight:500 !important; font-size:13px !important; background:#EEF3FF !important;
  color:#1D4ED8 !important; border:1px solid #D6E2FF !important;}
.pdi-chips button:hover {background:#DCE7FF !important;}

.pdi-empty {text-align:center; color:#64748B; font-size:13.5px; padding:36px 18px; line-height:1.6;
  border:1px dashed #CBD5E1; border-radius:12px; background:#FAFBFD;}
.pdi-empty b {color:#0B1F4D; font-size:14.5px;}
.pdi-spinner {width:22px; height:22px; margin:0 auto 10px; border:3px solid #DCE7FF;
  border-top-color:#1D4ED8; border-radius:50%; animation:pdi-spin .8s linear infinite;}
@keyframes pdi-spin {to {transform:rotate(360deg);}}

.pdi-conf {border:1px solid #E3E8F2; border-radius:12px; padding:14px 16px; background:#FAFBFD;}
.pdi-conf-top {display:flex; justify-content:space-between; align-items:flex-start;}
.pdi-conf-label {font-size:12px; color:#64748B; text-transform:uppercase; letter-spacing:.04em;}
.pdi-conf-val {font-size:30px; font-weight:700; color:#0B1F4D; line-height:1.15;}
.pdi-level {font-size:12px; font-weight:700; padding:4px 11px; border-radius:999px;}
.pdi-bar {height:8px; background:#E2E8F0; border-radius:999px; margin:10px 0 8px; overflow:hidden;}
.pdi-bar div {height:100%; border-radius:999px;}
.pdi-conf-note {font-size:12px; color:#64748B;}
.pdi-src-title {font-size:12px; font-weight:700; color:#0B1F4D; text-transform:uppercase;
  letter-spacing:.06em; margin:16px 0 8px;}
.pdi-src {border:1px solid #E3E8F2; border-radius:12px; padding:12px 14px; margin-bottom:10px; background:white;}
.pdi-src-head {display:flex; align-items:center; gap:8px; flex-wrap:wrap;}
.pdi-num {width:22px; height:22px; border-radius:6px; background:#0B1F4D; color:white; font-size:12px;
  font-weight:700; display:inline-flex; align-items:center; justify-content:center; flex:none;}
.pdi-ocr {font-size:10.5px; font-weight:700; padding:2px 7px; border-radius:6px; background:#FEF3C7; color:#92400E;}
.pdi-sim {margin-left:auto; display:inline-flex; align-items:center; gap:7px; font-size:12px;
  color:#334155; font-family:var(--font-mono);}
.pdi-simbar {width:44px; height:6px; background:#E2E8F0; border-radius:999px; overflow:hidden; display:inline-block;}
.pdi-simbar span {display:block; height:100%; background:#1D4ED8;}
.pdi-src-meta {font-size:12px; color:#64748B; margin:7px 0 6px;}
.pdi-snippet, .pdi-full {font-size:12.5px; color:#334155; line-height:1.55; border-left:3px solid #DCE7FF;
  padding:2px 0 2px 10px; white-space:pre-wrap;}
.pdi-src details {margin-top:6px;}
.pdi-src summary {font-size:12px; color:#1D4ED8; cursor:pointer; font-weight:500;}
.pdi-full {margin-top:6px; max-height:220px; overflow-y:auto;}
.pdi-foot {text-align:center; font-size:12px; color:#94A3B8; padding:4px 0 8px;}
"""

# Gradio share links follow the viewer's dark mode; this app is designed for light.
FORCE_LIGHT = """() => {
  const url = new URL(window.location);
  if (url.searchParams.get('__theme') !== 'light') {
    url.searchParams.set('__theme', 'light'); window.location.href = url.href;
  }
}"""

CHAT_PLACEHOLDER = """<div style="text-align:center;color:#64748B;font-size:14px;line-height:1.6">
<div style="font-size:16px;font-weight:700;color:#0B1F4D;margin-bottom:4px">Ask anything about the packet</div>
Load the sample packet, then try a suggested question below.<br>Answers cite the passages they came from.</div>"""


# ── layout ──
def build_demo():
    with gr.Blocks(title="Pharma Document Intelligence") as demo:
        store = gr.State(None)
        gr.HTML(header_html())
        kpis = gr.HTML(kpi_html())

        with gr.Row(equal_height=False):
            # left: the packet
            with gr.Column(scale=4, min_width=300, elem_classes="pdi-card"):
                gr.HTML('<div class="pdi-section">Document packet</div>')
                files = gr.File(label="Supplier PDFs · digital or scanned",
                                file_count="multiple", file_types=[".pdf"], height=170)
                with gr.Row():
                    index_btn  = gr.Button("Index uploads", variant="primary")
                    sample_btn = gr.Button("Load sample packet")
                status = gr.HTML(status_md("No documents indexed yet."))
                gr.HTML('<div class="pdi-section" style="margin-top:8px">Documents detected</div>')
                inventory = gr.HTML(inventory_html())
                gr.HTML('<div class="pdi-section" style="margin-top:8px">Retrieval settings</div>')
                mode     = gr.Radio(list(P.STYLE), value="Short answer", label="Answer style")
                doc_type = gr.Dropdown(["All types"], value="All types", label="Search within document type")
                k        = gr.Slider(2, 8, value=4, step=1, label="Passages to retrieve")

            # middle: the conversation
            with gr.Column(scale=7, min_width=420, elem_classes="pdi-card"):
                gr.HTML('<div class="pdi-section">Ask the packet</div>')
                chatbot = gr.Chatbot(show_label=False, height=440, placeholder=CHAT_PLACEHOLDER)
                with gr.Row(elem_classes="pdi-chips"):
                    chips = [gr.Button(label, size="sm") for label, _ in SUGGESTIONS]
                with gr.Row(equal_height=True):
                    msg  = gr.Textbox(show_label=False, scale=8, lines=1, container=False,
                                      placeholder="Ask about lots, materials, audits, packaging changes…")
                    send = gr.Button("Ask", variant="primary", scale=1, min_width=90)
                with gr.Row():
                    save_btn  = gr.Button("Export transcript", size="sm")
                    clear_btn = gr.Button("Clear conversation", size="sm")
                transcript = gr.File(label="Transcript", visible=False)

            # right: the evidence
            with gr.Column(scale=5, min_width=320, elem_classes="pdi-card"):
                gr.HTML('<div class="pdi-section">Evidence</div>')
                evidence = gr.HTML(evidence_html())

        gr.HTML('<div class="pdi-foot">Answers are generated only from retrieved passages · '
                'confidence is computed from retrieval similarity · built with open-source models</div>')

        ingest_out = [store, status, doc_type, kpis, inventory]
        index_btn.click(ui_ingest, inputs=files, outputs=ingest_out)
        sample_btn.click(ui_load_samples, outputs=ingest_out)

        chat_in  = [msg, chatbot, mode, doc_type, k, store]
        chat_out = [chatbot, msg, status, evidence]
        msg.submit(respond, chat_in, chat_out)
        send.click(respond, chat_in, chat_out)
        for btn, (_, question) in zip(chips, SUGGESTIONS):
            btn.click(lambda q=question: q, outputs=msg).then(respond, chat_in, chat_out)
        save_btn.click(save_transcript, inputs=chatbot, outputs=transcript)
        clear_btn.click(clear_chat, outputs=[chatbot, msg, status, evidence, transcript])
    return demo
