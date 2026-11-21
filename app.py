"""TruthLayer | Fact-checking web application. Deploy on Render, or run locally."""
from __future__ import annotations

import html
import os
from pathlib import Path
from urllib.parse import urlparse

import gradio as gr

from engine import (AppError, counts, export_files, extract_claims, read_pdf,
                    verify_all)

BASE = Path(__file__).resolve().parent
SAMPLE_PATH = BASE / "assets" / "sample_trap.pdf"

CSS = """
:root {--ink:#16253A;--muted:#66768A;--teal:#087B74;--border:#E1E8EE;--bg:#F5F8FA;}
.gradio-container {max-width:1180px !important;margin:auto !important;padding:0 20px 40px !important;background:#F5F8FA !important;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif !important;}
body, .gradio-container, .main, .wrap {background:#F5F8FA !important;color:#16253A !important;}
footer {display:none !important;}
#brand-header{border-bottom:1px solid #E0E8EE;padding:23px 0 18px;margin:0 0 30px;}
.tl-nav{display:flex;justify-content:space-between;align-items:center;gap:16px;}
.tl-logo{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:800;letter-spacing:-.5px;color:#15283E;}
.tl-mark{background:#087B74;color:white;width:31px;height:31px;display:grid;place-items:center;border-radius:10px;font-weight:900;font-size:20px;line-height:1;}
.tl-nav-right{display:flex;align-items:center;gap:8px;color:#536E79;font-size:12px;font-weight:600;}
.tl-online{height:7px;width:7px;background:#21B79A;border-radius:50%;display:inline-block;box-shadow:0 0 0 3px #E0F6EF;}
.tl-hero {padding:17px 0 24px;}
.tl-kicker{font-size:11px;color:#087B74;letter-spacing:2.3px;font-weight:800;text-transform:uppercase;margin-bottom:14px;}
.tl-hero h1{font-size:clamp(32px,4.2vw,52px);line-height:1.12;letter-spacing:-1.75px;font-weight:800;color:#12253B;margin:0 0 14px;max-width:750px;}
.tl-hero h1 span{color:#087B74;}
.tl-hero p{font-size:15px;line-height:1.75;color:#607185;max-width:700px;margin:0;}
.tl-steps{display:flex;gap:7px;flex-wrap:wrap;margin:22px 0 22px;}
.tl-step{font-size:11px;font-weight:700;color:#526579;border:1px solid #DEE6EC;border-radius:22px;padding:8px 11px;background:white;}
.tl-step b{color:#087B74;margin-right:6px;}
.tl-panel{border:1px solid #E1E8EE!important;border-radius:18px!important;background:white!important;padding:21px!important;box-shadow:0 5px 18px rgba(20,45,67,.025)!important;}
.tl-panel h3{margin:0 0 8px;color:#172B40;font-size:17px;}
.tl-section-title{font-weight:800;font-size:20px;color:#142A3D;letter-spacing:-.4px;margin:28px 0 16px;}
.tl-caption{font-size:12px;color:#7A8B99;margin:8px 0;}
.tl-notice{background:#EFF7F6;border:1px solid #D8EAE7;color:#41656A;border-radius:12px;padding:13px 15px;font-size:12px;line-height:1.7;margin:10px 0 0;}
.tl-metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin:12px 0 23px;}
.tl-metric{background:white;border:1px solid #E2EAF0;border-radius:14px;padding:17px 15px 16px;}
.tl-metric .num{font-size:29px;font-weight:850;letter-spacing:-.9px;line-height:1.1;color:#132840;}
.tl-metric .lab{font-size:10px;color:#718195;letter-spacing:.8px;text-transform:uppercase;font-weight:800;margin-top:7px;}
.tl-metric.verified .num{color:#16846D;}.tl-metric.inaccurate .num{color:#B17811;}.tl-metric.false .num{color:#C53D42;}.tl-metric.unverified .num{color:#60758E;}
.tl-docline{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;margin-bottom:18px;color:#66768A;font-size:12px;}
.tl-docline strong{color:#1E3245;}
.tl-card{border:1px solid #E3EAF0;background:white;border-radius:16px;margin:13px 0;padding:22px 22px 19px;box-shadow:0 5px 17px rgba(17,44,66,.023);}
.tl-cardhead{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:15px;}
.tl-id{font-size:11px;color:#728295;font-weight:800;letter-spacing:.7px;}
.tl-tag{border-radius:999px;padding:6px 10px;font-size:11px;font-weight:800;display:inline-flex;align-items:center;gap:5px;}
.tl-tag.verified{background:#E5F7F0;color:#147E63;}.tl-tag.inaccurate{background:#FFF3D8;color:#986518;}.tl-tag.false{background:#FBE8E7;color:#B23B40;}.tl-tag.unverified{background:#EDF1F5;color:#607185;}
.tl-quote{font-size:15px;font-weight:750;line-height:1.65;color:#1B3045;margin:0 0 16px;letter-spacing:-.14px;}
.tl-meta{font-size:11px;color:#7A8B9A;letter-spacing:.35px;margin:0 0 7px;font-weight:700;}
.tl-reason{color:#53677A;line-height:1.65;font-size:13px;margin:0;}
.tl-correction{background:#ECF7F4;border-left:3px solid #168C75;border-radius:7px;padding:11px 13px;margin-top:15px;color:#234F49;font-size:13px;line-height:1.65;}
.tl-evid{border-top:1px solid #EDF1F4;margin-top:17px;padding-top:13px;display:flex;flex-wrap:wrap;gap:7px;}
.tl-evid a{display:inline-flex;gap:4px;text-decoration:none;background:#F3F8F9;border:1px solid #E4EFF0;border-radius:8px;padding:7px 9px;color:#137970;font-size:11px;font-weight:700;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.tl-evid a:hover{text-decoration:underline;}
.tl-note{font-size:11px;color:#8A7780;margin:10px 0 0;}
.tl-empty{background:#fff;border:1px dashed #CAD7DD;border-radius:14px;padding:39px 28px;text-align:center;color:#718396;}
.tl-empty .symbol{font-size:34px;margin-bottom:12px;color:#0C857B;}
.tl-empty h3{color:#31485C;font-size:17px;margin-bottom:7px;}
.tl-empty p{font-size:13px;margin:0;line-height:1.65;}
.tl-src{background:white;border:1px solid #E3EAF0;border-radius:13px;padding:14px 17px;margin:10px 0;}
.tl-src a{font-size:13px;color:#08796D;text-decoration:none;font-weight:750;overflow-wrap:anywhere;}
.tl-src small{display:block;color:#8290A0;font-size:11px;margin-top:4px;overflow-wrap:anywhere;}
.tl-footer{color:#8593A1;font-size:11px;line-height:1.6;border-top:1px solid #E3EAF0;padding-top:18px;margin-top:34px;}
#analyze-button {margin-top:6px;}#analyze-button button{background:#087C73!important;border:1px solid #087C73!important;box-shadow:0 6px 12px rgba(7,123,114,.12)!important;color:white!important;font-weight:750!important;}
#analyze-button button:hover{background:#07665F!important;}
.gradio-container input,.gradio-container button,.gradio-container textarea {font-family:inherit!important;}
@media(max-width:650px){.tl-metrics{grid-template-columns:repeat(2,minmax(0,1fr));}.tl-metric:first-child{grid-column:span 2;}.tl-card{padding:17px;}.tl-hero{padding-top:0;}.tl-nav-right{font-size:10px;}}
"""


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def safe_link(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("https", "http") and bool(p.hostname)
    except ValueError:
        return False


def empty_view() -> str:
    return '<div class="tl-empty"><div class="symbol">◇</div><h3>Your analysis starts here</h3><p>Upload a PDF and select <b>Verify document</b> to extract checkable claims, look them up online, and see evidence-backed verdicts.</p></div>'


def source_link(title: str, url: str) -> str:
    if not safe_link(url):
        return ""
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">↗ {esc(title[:65])}</a>'


def render_summary(findings, filename, pages):
    cs = counts(findings)
    values = [("Claims reviewed", len(findings), ""), ("Verified", cs["Verified"], "verified"),
              ("Inaccurate", cs["Inaccurate"], "inaccurate"),
              ("False", cs["False"], "false"), ("Unverified", cs["Unverified"], "unverified")]
    html_cards = "".join(f'<div class="tl-metric {cls}"><div class="num">{number}</div><div class="lab">{label}</div></div>'
                         for label, number, cls in values)
    return (f'<div class="tl-section-title">Verification overview</div>'
            f'<div class="tl-docline"><span><strong>{esc(filename)}</strong> &nbsp;·&nbsp; {pages} pages</span>'
            f'<span>Live web check · AI-assisted</span></div>'
            f'<div class="tl-metrics">{html_cards}</div>'
            f'<div class="tl-notice">Verdicts are based on the sources returned during this analysis. '
            f'<strong>False</strong> means directly contradicted; <strong>Unverified</strong> means insufficient attributable evidence. '
            f'Review source links before relying on important claims.</div>')


def render_claims(findings) -> str:
    if not findings:
        return empty_view()
    icons = {"Verified": "✓", "Inaccurate": "!", "False": "×", "Unverified": "?"}
    result = '<div class="tl-section-title">Claim-by-claim findings</div>'
    for f in findings:
        status = f.verdict.lower()
        label = f'{icons.get(f.verdict,"?")} &nbsp;{f.verdict}'
        sources = ''.join(source_link(e.title or f'Source {i}', e.url) for i, e in enumerate(f.evidence[:5], 1))
        evid = f'<div class="tl-evid">{sources}</div>' if sources else '<div class="tl-note">No attributable source links were returned for this check.</div>'
        corrected = f'<div class="tl-correction"><strong>Correct information</strong><br>{esc(f.correction)}</div>' if f.correction else ''
        note = f'<div class="tl-note">{esc(f.note)}</div>' if f.note else ''
        result += (f'<article class="tl-card"><div class="tl-cardhead">'
                   f'<span class="tl-id">{esc(f.claim.id)} &nbsp; / &nbsp; PAGE {f.claim.page} &nbsp; / &nbsp; {esc(f.claim.category.upper())}</span>'
                   f'<span class="tl-tag {status}">{label}</span></div>'
                   f'<p class="tl-quote">“{esc(f.claim.quote)}”</p>'
                   f'<div class="tl-meta">ASSESSMENT</div><p class="tl-reason">{esc(f.explanation)}</p>'
                   f'{corrected}{evid}{note}</article>')
    return result


def render_sources(findings) -> str:
    seen, sources = set(), []
    for f in findings:
        for ev in f.evidence:
            if ev.url not in seen and safe_link(ev.url):
                seen.add(ev.url)
                sources.append((ev, f.claim.id))
    if not sources:
        return '<div class="tl-empty"><h3>No attributable sources collected</h3><p>Sources appear only after a successful grounded search.</p></div>'
    blocks = '<div class="tl-section-title">Evidence register</div><p class="tl-caption">Links come from the Google Search grounding metadata. They are not generated URLs.</p>'
    for ev, claim_id in sources:
        blocks += f'<div class="tl-src"><a href="{esc(ev.url)}" target="_blank" rel="noopener noreferrer">↗ {esc(ev.title)}</a><small>{esc(claim_id)} · {esc(ev.url)}</small></div>'
    return blocks


def render_document(pages: list[dict]) -> str:
    blocks = '<div class="tl-section-title">Extracted document text</div><p class="tl-caption">For auditing the source text and claim page numbers. Long pages are previewed at 2,000 characters.</p>'
    for pg in pages:
        snippet = pg["text"][:2000]
        blocks += f'<div class="tl-src"><strong>Page {pg["page"]}</strong><p style="white-space:pre-wrap;color:#5D6C7D;font-size:12px;line-height:1.55">{esc(snippet)}</p></div>'
    return blocks


def analyze(pdf_path, max_claims, supplied_key, progress=gr.Progress()):
    empty = ("", empty_view(), "", "", [])
    if not pdf_path:
        return ('<div class="tl-notice">Upload a PDF to begin.</div>', *empty[1:])
    api_key = os.environ.get("GEMINI_API_KEY", "").strip() or str(supplied_key or "").strip()
    if not api_key:
        return ('<div class="tl-notice">An API key is required to run live checks. Set GEMINI_API_KEY on the server or use the optional key field.</div>', *empty[1:])
    try:
        progress(0.03, desc="Opening PDF")
        with open(pdf_path, "rb") as fp:
            pages, stats = read_pdf(fp.read())
        progress(0.13, desc="Identifying factual claims")
        claims = extract_claims(pages, api_key, max_claims=int(max_claims))
        if not claims:
            return ('<div class="tl-notice">No exact, independently checkable claims were found. Try a document with statistics, figures, or dated factual statements.</div>',
                    empty_view(), "", render_document(pages), [])
        progress(0.26, desc=f"Checking {len(claims)} claims against live web sources")
        def tick(done, total):
            progress(0.26 + (0.70 * done / total), desc=f"Live verification {done}/{total}")
        findings = verify_all(claims, api_key, on_progress=tick)
        progress(0.97, desc="Preparing audit report")
        filename = Path(pdf_path).name
        # Gradio uploads often prefix temp names. Preserve source filename if provided by Gradio.
        downloadable = export_files(findings, filename, stats["page_count"])
        progress(1.0, desc="Complete")
        return (render_summary(findings, filename, stats["page_count"]), render_claims(findings),
                render_sources(findings), render_document(pages), list(downloadable))
    except AppError as exc:
        return (f'<div class="tl-notice"><strong>Unable to complete:</strong> {esc(exc)}</div>', empty_view(), "", "", [])
    except Exception:
        return ('<div class="tl-notice"><strong>Unable to complete:</strong> An unexpected processing error occurred. Check the hosting logs.</div>', empty_view(), "", "", [])


with gr.Blocks(title="TruthLayer — Evidence-based PDF fact checking") as demo:
    gr.HTML('''<div id="brand-header"><div class="tl-nav"><div class="tl-logo"><span class="tl-mark">✓</span> TruthLayer<span style="color:#148778">.</span></div><div class="tl-nav-right"><i class="tl-online"></i> GOOGLE SEARCH-GROUNDED VERIFICATION</div></div></div>''')
    gr.HTML('''<section class="tl-hero"><div class="tl-kicker">AI FACT-CHECKING WORKSPACE</div><h1>Turn claims into<br><span>verified knowledge.</span></h1><p>Drop in a report, research document, or marketing PDF. TruthLayer extracts measurable claims, checks current web evidence, flags discrepancies, and shows what the facts actually say.</p><div class="tl-steps"><span class="tl-step"><b>01</b> Upload</span><span class="tl-step"><b>02</b> Extract</span><span class="tl-step"><b>03</b> Cross-check</span><span class="tl-step"><b>04</b> Export</span></div></section>''')
    with gr.Row(equal_height=False):
        with gr.Column(scale=7, elem_classes=["tl-panel"]):
            gr.HTML('<h3 style="margin:0 0 5px">Upload your document</h3><p class="tl-caption">PDF only · Up to 12 MB · Maximum 35 pages · Text or scanned PDF</p>')
            upload = gr.File(label="PDF document", file_types=[".pdf"], type="filepath", show_label=False)
            with gr.Row():
                analyze_button = gr.Button("Verify document →", variant="primary", elem_id="analyze-button", scale=3)
                sample_button = gr.Button("Use sample PDF", variant="secondary", scale=2)
            gr.HTML('<div class="tl-notice">Your document is processed for claim extraction and evidence lookup. No claims are treated as verified without source links returned by the search service.</div>')
        with gr.Column(scale=5, elem_classes=["tl-panel"]):
            gr.HTML('<h3 style="margin:0 0 8px">Analysis preferences</h3><p class="tl-caption">Focus on the most relevant, externally checkable claims.</p>')
            limit = gr.Slider(3, 20, value=8, step=1, label="Maximum claims", info="More claims require additional live search requests")
            with gr.Accordion("Advanced · API key", open=False):
                api_key_input = gr.Textbox(label="Gemini API key (optional)", type="password", placeholder="Server key is used automatically if configured", info="Only use a personal key on a deployment you trust. This key is not saved by the app.")
            gr.HTML('<div class="tl-caption">Classification: Verified · Inaccurate · False · Unverified<br>Time-sensitive findings are checked at the time of your request.</div>')
    with gr.Tabs():
        with gr.Tab("Overview"):
            summary = gr.HTML('')
            findings = gr.HTML(empty_view())
        with gr.Tab("Evidence library"):
            sources = gr.HTML('<div class="tl-empty"><h3>Sources will appear here</h3><p>Every evidence link comes from live-search grounding metadata.</p></div>')
        with gr.Tab("Document text"):
            doc_text = gr.HTML('<div class="tl-empty"><h3>Document text preview</h3><p>Extracted page text will appear after analysis.</p></div>')
        with gr.Tab("Downloads"):
            gr.Markdown("### Export your audit\nDownload a shareable PDF summary, spreadsheet-ready CSV, and complete machine-readable JSON with all source links.")
            downloadable_files = gr.File(label="Fact-check reports · PDF / CSV / JSON", file_count="multiple", interactive=False)
    gr.HTML('<div class="tl-footer">TruthLayer provides AI-assisted verification, not a definitive legal, scientific, or editorial determination. Review original sources before publishing sensitive or consequential claims. Powered by Gemini and Google Search grounding.</div>')

    analyze_button.click(fn=analyze, inputs=[upload, limit, api_key_input],
                         outputs=[summary, findings, sources, doc_text, downloadable_files],
                         concurrency_limit=1, show_progress="minimal")
    sample_button.click(fn=lambda: str(SAMPLE_PATH) if SAMPLE_PATH.exists() else None, outputs=upload)

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=2)
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")), show_error=False,
                css=CSS, theme=gr.themes.Soft(primary_hue="teal", neutral_hue="slate"))
