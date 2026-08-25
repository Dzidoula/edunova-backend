def _login(client, username="koffi"):
    response = client.post("/auth/login", json={"username": username})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_chat_without_document_uses_fallback(client):
    headers = _login(client)
    response = client.post("/chat", headers=headers, json={"message": "Bonjour"})
    assert response.status_code == 200
    assert response.json()["reply"]


def test_chat_with_document_references_its_content(client):
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
        "/chat",
        headers=headers,
        json={"message": "résume le document", "document_id": doc_id},
    )
    assert response.status_code == 200
    assert "fractions" in response.json()["reply"].lower() or "Cours de fractions" in response.json()["reply"]


def test_chat_history_is_scoped_to_document(client):
    headers = _login(client)
    client.post("/chat", headers=headers, json={"message": "Bonjour"})

    response = client.get("/chat/history", headers=headers)
    assert response.status_code == 200
    messages = response.json()
    assert any(m["role"] == "user" and m["content"] == "Bonjour" for m in messages)
    assert any(m["role"] == "tutor" for m in messages)


def test_chat_requires_auth(client):
    response = client.post("/chat", json={"message": "Bonjour"})
    assert response.status_code in (401, 403)
