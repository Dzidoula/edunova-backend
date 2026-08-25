def _login(client, username="koffi"):
    response = client.post("/auth/login", json={"username": username})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_get_default_settings(client):
    headers = _login(client)
    response = client.get("/settings", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "llama-3.3-70b-versatile"
    assert body["ocr_engine"] == "auto"


def test_update_settings_persists(client):
    headers = _login(client)
    response = client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_test", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "llama-3.1-8b-instant"

    get_response = client.get("/settings", headers=headers)
    assert get_response.json()["ocr_engine"] == "tesseract"


def test_settings_requires_auth(client):
    response = client.get("/settings")
    assert response.status_code in (401, 403)
