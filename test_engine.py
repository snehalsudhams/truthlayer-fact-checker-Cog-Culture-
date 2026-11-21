"""Offline regression tests. No API key or internet needed."""
import io
import json
from pathlib import Path

import fitz
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from engine import (AppError, Claim, Evidence, Finding, _parse_json, batch_pages,
                    counts, extract_claims, findings_to_csv, findings_to_json,
                    grounding_evidence, read_pdf, report_pdf, verify_claim)


def pdf_bytes(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for line in lines:
        c.drawString(50, 700, line)
        c.showPage()
    c.save()
    return buf.getvalue()


def fake_response(payload, evidence=None):
    data = {"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}
    if evidence is not None:
        data["candidates"][0]["groundingMetadata"] = {
            "groundingChunks": [{"web": {"title": title, "uri": url}} for title, url in evidence],
            "webSearchQueries": ["fact check lunar landing date"]}
    return data


def test_valid_pdf_reading_and_pagination():
    pages, stats = read_pdf(pdf_bytes(["The moon landing happened in July 1969.",
                                       "Gold's chemical symbol is Au, not Ag."]))
    assert stats["page_count"] == 2
    assert [p["page"] for p in pages] == [1, 2]
    assert "July 1969" in pages[0]["text"]


def test_invalid_pdf_rejected():
    with pytest.raises(AppError):
        read_pdf(b"bad data")
    with pytest.raises(AppError):
        read_pdf(b"%PDF" + b"A" * (12 * 1024 * 1024))


def test_exact_quote_guard_dedupe_and_page_number():
    pages = [{"page": 1, "text": "The moon landing happened in July 1969. This is one fact."}]
    def fake(_api_key, _prompt, grounded):
        assert not grounded
        return fake_response({"claims": [
            {"quote": "The moon landing happened in July 1969.", "page": 1, "category": "Date"},
            {"quote": "The moon landing happened in July 1969.", "page": 1, "category": "Date"},
            {"quote": "The moon landing happened in July 1999.", "page": 1, "category": "Date"},
            {"quote": "The moon landing happened in July 1969.", "page": 2, "category": "Date"}]})
    claims = extract_claims(pages, "fake-key", 10, gemini=fake)
    assert len(claims) == 1
    assert claims[0].id == "CLM-01"


def test_source_metadata_filter_and_url_safety():
    raw = fake_response({}, [("NASA", "https://nasa.gov/moon"),
                             ("NASA duplicate", "https://nasa.gov/moon"),
                             ("Malicious", "javascript:alert(1)")])
    evid, queries = grounding_evidence(raw)
    assert len(evid) == 1
    assert evid[0].title == "NASA"
    assert queries == ["fact check lunar landing date"]


def test_no_grounding_means_unverified_even_if_model_says_verified():
    claim = Claim("CLM-01", "The first iPhone was launched in 2007.", 1, "Date")
    result = verify_claim(claim, "fake-key", gemini=lambda *_args, **_kwargs:
                          fake_response({"verdict": "Verified", "explanation": "Apple confirms.", "correction": ""}))
    assert result.verdict == "Unverified"
    assert not result.evidence
    assert "no attributable" in result.note


def test_grounded_false_claim_includes_correction():
    claim = Claim("CLM-02", "Mount Everest is 6,500 metres high.", 1, "Statistic")
    result = verify_claim(claim, "fake-key", gemini=lambda *_args, **_kwargs:
                          fake_response({"verdict": "False", "explanation": "Official survey disagrees.",
                                         "correction": "The official height is 8,848.86 m."},
                                        [("Survey", "https://example.org/everest")]))
    assert result.verdict == "False"
    assert "8,848.86" in result.correction
    assert len(result.evidence) == 1


def test_json_csv_and_rendered_pdf():
    finding = Finding(claim=Claim("CLM-01", "The moon landing occurred in 1985.", 1, "Date"),
                      verdict="False", explanation="It was in 1969.",
                      correction="Apollo 11 landed in July 1969.",
                      evidence=[Evidence("NASA", "https://www.nasa.gov/")], checked_at="2026-11-21 00:00 UTC")
    data = json.loads(findings_to_json([finding], "sample.pdf", 1))
    assert data["summary"]["False"] == 1
    assert "https://www.nasa.gov/" in findings_to_csv([finding])
    pdf = report_pdf([finding], "sample.pdf", 1)
    assert pdf.startswith(b"%PDF")
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        body = doc[0].get_text()
        assert "Apollo 11 landed" in body
        links = doc[0].get_links()
        assert any(l.get("uri") == "https://www.nasa.gov/" for l in links)


def test_batch_pages_limits_prompt_size():
    data = [{"page": 1, "text": "x" * 25000}, {"page": 2, "text": "y" * 500}]
    batches = batch_pages(data, 14000)
    assert len(batches) >= 2
    assert all(sum(len(p["text"]) for p in batch) <= 14000 for batch in batches)


def test_code_fence_json_parser():
    assert _parse_json('```json\n{"verdict":"False"}\n```')["verdict"] == "False"


def test_http_gemini_payload_has_grounded_search_and_no_json_mode(monkeypatch):
    from engine import _gemini
    sent = []
    class Reply:
        status_code = 200
        def json(self):
            return fake_response({'verdict': 'Verified'}, [('Source','https://example.org')])
    def fake_post(url, headers, json, timeout):
        sent.append((url, headers, json))
        return Reply()
    monkeypatch.setattr('engine.requests.post', fake_post)
    _gemini('dummy-key', 'look this up', grounded=True)
    _, headers, data = sent[0]
    assert headers['x-goog-api-key'] == 'dummy-key'
    assert data['tools'] == [{'google_search': {}}]
    assert 'responseMimeType' not in data['generationConfig']
    sent.clear()
    _gemini('dummy-key', 'extract quotes', grounded=False)
    assert sent[0][2]['generationConfig']['responseMimeType'] == 'application/json'
    assert 'tools' not in sent[0][2]


def test_csv_blocks_untrusted_spreadsheet_formulas():
    f = Finding(Claim('CLM-01', '=CMD()', 1, 'Other'), 'Unverified', 'No evidence')
    csv_text = findings_to_csv([f])
    assert "'=CMD()" in csv_text
