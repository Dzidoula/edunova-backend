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


def test_get_settings_masks_api_key(client):
    headers = _login(client)
    put_response = client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_supersecretvalue1234", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )
    # PUT should also mask the key in its response (same read-serialization path as GET).
    assert put_response.json()["api_key"] != "gsk_supersecretvalue1234"

    get_response = client.get("/settings", headers=headers)
    body = get_response.json()
    assert body["api_key"] != "gsk_supersecretvalue1234"
    assert body["api_key"].endswith("1234")
    assert "supersecret" not in body["api_key"]


def test_get_settings_masks_empty_api_key_as_empty(client):
    headers = _login(client)
    response = client.get("/settings", headers=headers)
    assert response.json()["api_key"] == ""


def test_put_settings_stores_full_api_key(client):
    headers = _login(client)
    client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_fullkeyvalue9999", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )
    # A subsequent PUT with a real key must be accepted and stored in full, not treated
    # as a masked placeholder. We can't read the raw key back via the API (by design),
    # so verify indirectly: update again with a new key and confirm the masked suffix changes.
    response = client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_anotherkeyvalue8888", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )
    assert response.json()["api_key"].endswith("8888")


def test_put_settings_omitting_api_key_preserves_existing_key(client):
    headers = _login(client)
    client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_originalkeyvalue7777", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )

    # Omit api_key entirely; only change an unrelated field (model).
    response = client.put(
        "/settings",
        headers=headers,
        json={"api_base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile", "ocr_engine": "tesseract"},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "llama-3.3-70b-versatile"
    # The masked key should still reflect the original stored key, not have been wiped.
    assert response.json()["api_key"].endswith("7777")

    get_response = client.get("/settings", headers=headers)
    assert get_response.json()["api_key"].endswith("7777")


def test_put_settings_with_null_api_key_preserves_existing_key(client):
    headers = _login(client)
    client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_nullcheckvalue6666", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )

    response = client.put(
        "/settings",
        headers=headers,
        json={"api_key": None, "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "auto"},
    )
    assert response.status_code == 200
    assert response.json()["ocr_engine"] == "auto"
    assert response.json()["api_key"].endswith("6666")


def test_put_settings_with_real_key_still_updates(client):
    headers = _login(client)
    response = client.put(
        "/settings",
        headers=headers,
        json={"api_key": "gsk_freshkeyvalue5555", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "ocr_engine": "tesseract"},
    )
    assert response.json()["api_key"].endswith("5555")
