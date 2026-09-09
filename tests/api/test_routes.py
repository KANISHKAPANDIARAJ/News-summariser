"""Integration and contract tests for REST API endpoints."""

def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"

def test_readiness_check(client):
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "ready"

def test_analyze_api(client, sample_article):
    res = client.post("/api/analyze", json={"text": sample_article, "num_key_points": 3})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    res_data = data["data"]
    assert "sentiment" in res_data
    assert "distribution" in res_data["sentiment"]
    assert len(res_data["key_points"]) <= 3
    assert len(res_data["keywords"]) > 0
    assert len(res_data["entities"]) > 0

def test_compare_api(client):
    res = client.post("/api/compare", json={
        "text_a": "Electric vehicle adoption increased by twenty percent in major cities.",
        "text_b": "Urban areas saw a twenty percent rise in electric car purchases."
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "similarity_score" in data["data"]

def test_tts_api(client):
    res = client.post("/api/tts", json={
        "text": "Breaking news briefing from the intelligence platform.",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "audio_url" in data["data"]

def test_history_api(client):
    res = client.get("/api/history")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
