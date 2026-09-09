"""Tests for error handling, edge cases, and security rejections."""

def test_extract_ssrf_rejection(client):
    res = client.post("/api/articles/extract", json={"url": "http://127.0.0.1:8080/secret"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "security" in data["error"]["message"].lower() or "forbidden" in data["error"]["message"].lower()

def test_extract_invalid_url(client):
    res = client.post("/api/articles/extract", json={"url": "not-a-valid-url"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False

def test_summarize_missing_input(client):
    res = client.post("/api/summarize", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "Either 'url' or 'text'" in data["error"]["message"]

def test_summarize_unsupported_language(client):
    res = client.post("/api/summarize", json={"text": "A valid length article for summarization tests.", "language": "klingon"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNSUPPORTED_LANGUAGE"

def test_summarize_empty_or_too_short(client):
    res = client.post("/api/summarize", json={"text": "Too short"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "TEXT_TOO_SHORT"

def test_summary_not_found(client):
    res = client.get("/api/summaries/non-existent-uuid-12345")
    assert res.status_code == 404
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
