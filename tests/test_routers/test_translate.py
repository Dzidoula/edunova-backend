def _login(client, username="koffi"):
    response = client.post("/auth/login", json={"username": username})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_translate_text_without_api_key_returns_fallback_message(client):
    headers = _login(client)
    response = client.post(
        "/translate",
        headers=headers,
        json={"text": "Bonjour le monde", "target_lang": "english"},
    )
    assert response.status_code == 200
    body = response.json()
    # No API key configured for this user -> Tutor.translate() falls back to its
    # "unavailable without an API key" message rather than calling an LLM.
    assert "Traduction automatique indisponible sans clé API." in body["translation"]
    assert "english" in body["translation"]


def test_translate_document_uses_extracted_text(client):
    headers = _login(client)
    create_resp = client.post(
        "/documents",
        headers=headers,
        data={
            "title": "Cours de fractions",
            "subject": "Mathématiques",
            "document_type": "course",
            "text_override": "Une fraction représente une division entre deux nombres entiers.",
        },
    )
    doc_id = create_resp.json()["id"]

    response = client.post(
        "/translate",
        headers=headers,
        json={"document_id": doc_id, "target_lang": "english"},
    )
    assert response.status_code == 200
    assert response.json()["translation"]


def test_translate_document_not_owned_returns_404(client):
    headers_a = _login(client, "koffi")
    create_resp = client.post(
        "/documents",
        headers=headers_a,
        data={"title": "Doc A", "subject": "Maths", "document_type": "course", "text_override": "Contenu A suffisant."},
    )
    doc_id = create_resp.json()["id"]

    headers_b = _login(client, "amina")
    response = client.post(
        "/translate",
        headers=headers_b,
        json={"document_id": doc_id, "target_lang": "english"},
    )
    assert response.status_code == 404


def test_translate_requires_auth(client):
    response = client.post("/translate", json={"text": "Bonjour", "target_lang": "english"})
    assert response.status_code in (401, 403)


def test_translate_empty_text_returns_400(client):
    headers = _login(client)
    response = client.post("/translate", headers=headers, json={"text": "   ", "target_lang": "english"})
    assert response.status_code == 400
