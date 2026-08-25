"""Cross-user isolation sweep: user B must never be able to read or act on
user A's resources via any of these endpoints."""


def _login(client, username):
    response = client.post("/auth/login", json={"username": username})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _create_document(client, headers, title="Doc A"):
    response = client.post(
        "/documents",
        headers=headers,
        data={
            "title": title,
            "subject": "Mathématiques",
            "document_type": "course",
            "text_override": "Une fraction représente une division entre deux nombres entiers.",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_get_document_as_other_user_returns_404(client):
    headers_a = _login(client, "koffi")
    doc_id = _create_document(client, headers_a)

    headers_b = _login(client, "amina")
    response = client.get(f"/documents/{doc_id}", headers=headers_b)
    assert response.status_code == 404


def test_update_document_text_as_other_user_returns_404(client):
    headers_a = _login(client, "koffi")
    doc_id = _create_document(client, headers_a)

    headers_b = _login(client, "amina")
    response = client.put(
        f"/documents/{doc_id}/text",
        headers=headers_b,
        json={"text": "Texte injecté par un autre utilisateur."},
    )
    assert response.status_code == 404


def test_delete_document_as_other_user_returns_404(client):
    headers_a = _login(client, "koffi")
    doc_id = _create_document(client, headers_a)

    headers_b = _login(client, "amina")
    response = client.delete(f"/documents/{doc_id}", headers=headers_b)
    assert response.status_code == 404

    # document must still exist for its owner
    still_there = client.get(f"/documents/{doc_id}", headers=headers_a)
    assert still_there.status_code == 200


def test_chat_with_other_users_document_id_returns_404(client):
    headers_a = _login(client, "koffi")
    doc_id = _create_document(client, headers_a)

    headers_b = _login(client, "amina")
    response = client.post(
        "/chat",
        headers=headers_b,
        json={"message": "Bonjour", "document_id": doc_id},
    )
    assert response.status_code == 404


def test_chat_history_scoped_per_user(client):
    headers_a = _login(client, "koffi")
    client.post("/chat", headers=headers_a, json={"message": "Message de koffi"})

    headers_b = _login(client, "amina")
    client.post("/chat", headers=headers_b, json={"message": "Message d'amina"})

    response_a = client.get("/chat/history", headers=headers_a)
    response_b = client.get("/chat/history", headers=headers_b)

    contents_a = [m["content"] for m in response_a.json()]
    contents_b = [m["content"] for m in response_b.json()]

    assert "Message de koffi" in contents_a
    assert "Message de koffi" not in contents_b
    assert "Message d'amina" in contents_b
    assert "Message d'amina" not in contents_a


def test_progress_scoped_per_user(client):
    headers_a = _login(client, "koffi")
    client.post(
        "/progress/result",
        headers=headers_a,
        json={"notion": "Fractions", "subject": "Mathématiques", "success": True},
    )

    headers_b = _login(client, "amina")
    response_b = client.get("/progress", headers=headers_b)
    assert response_b.status_code == 200
    assert response_b.json() == []

    response_a = client.get("/progress", headers=headers_a)
    assert len(response_a.json()) == 1


def test_memory_scoped_per_user(client):
    headers_a = _login(client, "koffi")
    client.post("/chat", headers=headers_a, json={"message": "je n'ai pas compris cette partie"})

    headers_b = _login(client, "amina")
    response_b = client.get("/memory", headers=headers_b)
    assert response_b.status_code == 200
    assert response_b.json() == []

    response_a = client.get("/memory", headers=headers_a)
    assert len(response_a.json()) >= 1
