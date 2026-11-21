"""UI/controller smoke tests, still run offline without credentials."""
from pathlib import Path
import app
from engine import Claim, Evidence, Finding


def test_app_controller_end_to_end_with_stubbed_web(monkeypatch):
    monkeypatch.setattr(app, 'extract_claims', lambda pages, api_key, max_claims:
                        [Claim('CLM-01', 'Neil Armstrong first walked on the Moon in 1985.', 1, 'Date')])
    monkeypatch.setattr(app, 'verify_all', lambda claims, key, on_progress:
                        [Finding(claims[0], 'False', 'NASA confirms it happened in 1969.',
                                 'Neil Armstrong first walked on the Moon in July 1969.',
                                 [Evidence('NASA', 'https://www.nasa.gov/')], checked_at='2026-11-21 01:00 UTC')])
    sample = str(Path(app.__file__).parent / 'assets' / 'sample_trap.pdf')
    summary, claims, sources, extracted, paths = app.analyze(sample, 8, 'dummy', progress=lambda *args, **kw: None)
    assert 'Claims reviewed' in summary
    assert 'Neil Armstrong' in claims
    assert 'NASA confirms' in claims
    assert 'https://www.nasa.gov/' in sources
    assert 'Page 1' in extracted
    assert len(paths) == 3 and all(Path(p).exists() for p in paths)


def test_missing_api_key_yields_helpful_message(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    sample = str(Path(app.__file__).parent / 'assets' / 'sample_trap.pdf')
    summary, claims, sources, extracted, paths = app.analyze(sample, 5, '', progress=lambda *args, **kw: None)
    assert 'API key is required' in summary
    assert paths == []
