# TruthLayer · Evidence-based PDF Fact Checker

**Part 2 — Product Management Trainee assessment**

TruthLayer is a deployable Gradio web app that turns a marketing/research PDF into an auditable list of factual claims and evaluates each claim against **live Google Search-grounded evidence**. It flags misinformation, shows corrected facts when established, and links to retrieved sources.

## What the app does

1. **Upload a PDF:** PDFs up to 12 MB and 35 pages, including scanned pages when Tesseract is available. Pages remain linked to findings.
2. **Extract claims:** Gemini extracts verbatim checkable statements (statistics, dates, financial/technical figures) from actual page text. An exact-quote guard rejects hallucinated claims.
3. **Verify:** Each claim is evaluated separately, with the Gemini **Google Search** tool enabled for current information.
4. **Classify:** **Verified** (supported), **Inaccurate** (materially wrong/outdated), **False** (directly contradicted), and **Unverified** (insufficient source-backed evidence or API issue). No evidence does not automatically imply a false statement.
5. **Correct + cite:** For false or inaccurate claims, provide a source-grounded correction when available. The app shows only URLs extracted from the API's `groundingMetadata` — never invented URLs.
6. **Export:** Download an easy-to-read PDF audit, CSV and JSON with original quotes, page numbers, reasoning, corrections, URLs and verification timestamps.

**Important:** The app requires a valid Gemini API key from a project with Google Search grounding access (billing may be required). The app does **not** guarantee perfect truth detection; source quality and context still require human judgment. Do not share confidential documents with a public third-party AI service.

## Tech stack

- **Frontend:** Gradio Blocks + custom responsive CSS.
- **Document extraction:** PyMuPDF, optional Tesseract OCR (`pytesseract`).
- **Reasoning:** Gemini `gemini-3.8-flash` via the Google Gemini REST API.
- **Live retrieval:** `google_search` grounding; returned `groundingMetadata.groundingChunks` used as source URLs.
- **Reporting:** ReportLab PDF, standard-library CSV and JSON.
- **Deployment:** Docker on Render (`render.yaml`), with secret-based configuration.

No vector database or long-term document storage is used. Temporary Gradio upload and export files exist on the hosting instance; Render free instances have ephemeral storage.

## Setup locally

You need Python 3.11+ (recommended), an internet connection, and a Gemini API key. Create a key at **https://aistudio.google.com/apikey**. Google Search grounding may require an enabled paid/billing tier for Gemini 3.8 Flash; check the current Google API pricing and quotas. A basic free API key alone may not unlock grounded search.

```bash
pip install -r requirements.txt
# macOS/Linux
export GEMINI_API_KEY="YOUR_KEY_HERE"
# Windows PowerShell
# $env:GEMINI_API_KEY="YOUR_KEY_HERE"
python app.py
```

Open **http://localhost:7860**. `GEMINI_API_KEY` can be supplied at runtime via the advanced field if no server key has been configured. Never commit keys to GitHub.

For scanned PDFs, install the `tesseract` command-line program; the Dockerfile installs it automatically for Render.

## Deploy publicly to Render

> A GitHub repository and a Render account are required for a real public URL. The repo in this project is ready for pushing; no deployed URL or GitHub URL exists until the owner performs those external account steps.

1. Create a **new public GitHub repository** named `truthlayer-fact-checker`. Upload the contents of this folder to the repository root (`app.py`, `engine.py`, `requirements.txt`, `Dockerfile`, `render.yaml`, `README.md`, `assets/`). Never upload `.env` or any real API key.
2. Open **https://dashboard.render.com/** and select **New → Blueprint**. Connect the GitHub repository. Render reads `render.yaml` and creates a Docker web service on the free plan.
3. During setup, set the environment variable **`GEMINI_API_KEY`** to your key. Alternatively add it in the web service's **Environment** page, then redeploy. Keep the value secret.
4. Wait for the deployment to show **Live**. Open the actual Render URL shown in the service dashboard (the app will run on a `*.onrender.com` host).
5. Upload `assets/sample_trap.pdf`, choose 8 claims, run verification, check that the app produces sources and corrections, then test a second PDF.
6. Copy the actual working web app URL and your GitHub repo URL into the assignment submission. Record a 30-second screen capture (suggested walkthrough below).

**Free-plan note:** Render may spin down the service after 15 minutes of inactivity, causing approximately one minute of cold-start delay on the next visit. Free-plan limits and Gemini API billing/quotas apply. For evaluation, consider keeping the service active on a paid instance if cold start or quota is a concern.

### Alternative: Deploy without a Render Blueprint

Create a **New → Web Service** from your repository, choose **Docker** runtime, select the Free instance, and add the `GEMINI_API_KEY` environment variable. Render assigns the final URL.

## Validate

Run offline unit tests (do not use API credits):

```bash
pip install pytest
python -m pytest -q
```

Offline tests cover PDF pages, invalid inputs, deduplication and verbatim-quote validation, evidence metadata filtering and malicious URLs, no-citation verdict downgrade, sourced false corrections, JSON/CSV export and PDF hyperlink integrity.

**Live smoke test checklist:**

- App opens without Python errors.
- Sample PDF loads; analysis extracts page-linked claims.
- At least one intentionally wrong statement is flagged False/Inaccurate, with a corrected fact and an inspectable web source.
- Accurate claims are marked Verified when the search evidence supports them.
- Unattributable searches lead to Unverified, never manufactured citations.
- PDF, CSV and JSON downloads work, and a different PDF uploads successfully.
- API key does not appear in GitHub or app output.

There is no way to guarantee live API behavior from offline tests; **run the live smoke test after configuring credentials on the host**.

## Example trap document

`assets/sample_trap.pdf` is a sample for evaluation. It contains an intentional mixture of correct and incorrect claims: the iPhone's original introduction, Neil Armstrong's lunar walk date, Everest's elevation, Microsoft's LinkedIn transaction, the chemical symbol of gold, Chandrayaan-3's landing year, YouTube's founding year and Amazon's founding year.

The claims are examples only. They are **not hard-coded** into the fact checker: new PDFs are processed using the same extraction + search workflow.

## Evaluation design decisions

- **Precise false vs. unverified distinction:** Avoid the dangerous assumption that absence of web evidence means something is false.
- **No fabricated citations:** Source links come from Google's actual grounding metadata; if no sources are available, the app refuses to issue a factual verdict.
- **Auditability:** Page number, original verbatim quote, explanation, correction, source links, and check time are all exported.
- **Defensive document handling:** Size/page limits, encrypted PDF rejection, HTML escaping, exact-quote validation, limited OCR and URL scheme filtering.
- **User trust:** Never promise 100% factual accuracy. Present findings as research assistance with easy source review.

## Suggested 30-second demo video

- **0–5s:** Show the public TruthLayer URL and clean landing page.
- **5–9s:** Click **Use sample PDF**, highlight the 8-claim selection, click **Verify document**.
- **9–19s:** Show the completed overview, a False finding, its corrected fact and clickable source.
- **19–25s:** Quickly scroll through Verified/Inaccurate examples and Evidence library.
- **25–30s:** Click Downloads, show PDF/CSV/JSON export and final URL.

Keep the demonstration authentic and record after a successful live run. Use OBS Studio or the browser/OS screen recorder. Do not record or display API keys.

## Known limitations

- Google Search grounding can return irrelevant or insufficient sources. The model may misinterpret them; review citations for consequential facts.
- Gemini API credits, quotas and grounded-search availability may vary, and searches may return unavailable or redirect links.
- A native PDF page may have poor text order; scanned documents depend on OCR quality.
- Large documents prioritize a maximum of 20 extracted claims. For more complete coverage, split the input into batches.
- No user sign-in, persistent history, automatic browser screenshot, or production-scale queue.

## Project structure

```text
truthlayer_app/
├── app.py                # Responsive Gradio UI and workflow
├── engine.py             # Extraction, live grounded fact-check, audit exports
├── requirements.txt      # Runtime dependencies
├── Dockerfile             # Includes Tesseract OCR
├── render.yaml            # Render blueprint
├── assets/sample_trap.pdf # Test PDF (deliberate fake facts)
├── make_sample.py         # Regenerate sample PDF
├── tests/test_engine.py   # Offline regression tests
├── .env.example           # Secret variable names only
└── README.md
```

**Security:** Do not include your API key in the repository or any video. Avoid uploading personal/sensitive PDFs to third-party models. This application is a demonstration, not a substitute for expert review.
