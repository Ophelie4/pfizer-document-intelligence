"""Run the Pharma Document Intelligence app.

    python app.py              # http://127.0.0.1:7860
    python app.py --share      # also create a temporary public gradio.live link

On Hugging Face Spaces this file is the entry point and runs as-is.
"""
import argparse
import os

from interface import CSS, FORCE_LIGHT, THEME, build_demo

demo = build_demo()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--share", action="store_true", help="create a temporary public link")
    ap.add_argument("--port", type=int, default=int(os.getenv("PORT", 7860)))
    ap.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    args = ap.parse_args()
    demo.queue().launch(server_name=args.host, server_port=args.port, share=args.share,
                        theme=THEME, css=CSS, js=FORCE_LIGHT)
