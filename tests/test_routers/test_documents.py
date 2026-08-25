import io


def _auth_headers(client):
    response = client.post("/auth/login", json={"username": "koffi"})
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_document_with_manual_text(client):
    headers = _auth_headers(client)
    response = client.post(
        "/documents",
        headers=headers,
        data={
            "title": "Cours de fractions",
            "subject": "Mathématiques",
            "document_type": "course",
            "text_override": "Une fraction représente une division entre deux nombres entiers.",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Cours de fractions"
    assert body["has_content"] is True


def test_list_documents_only_returns_current_user_documents(client):
    headers_a = _auth_headers(client)
    client.post(
        "/documents",
        headers=headers_a,
        data={"title": "Doc A", "subject": "Maths", "document_type": "course", "text_override": "Contenu A suffisant pour compter."},
    )

    response_login_b = client.post("/auth/login", json={"username": "amina"})
    headers_b = {"Authorization": f"Bearer {response_login_b.json()['token']}"}

    response = client.get("/documents", headers=headers_b)
    assert response.status_code == 200
    assert response.json() == []


def test_update_document_text(client):
    headers = _auth_headers(client)
    create_resp = client.post(
        "/documents",
        headers=headers,
        data={"title": "Doc vide", "subject": "Maths", "document_type": "course"},
    )
    doc_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/documents/{doc_id}/text",
        headers=headers,
        json={"text": "Un texte collé manuellement, assez long pour être considéré comme du contenu."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["has_content"] is True


def test_delete_document(client):
    headers = _auth_headers(client)
    create_resp = client.post(
        "/documents",
        headers=headers,
        data={"title": "À supprimer", "subject": "Maths", "document_type": "course", "text_override": "Contenu suffisant pour être indexé."},
    )
    doc_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/documents/{doc_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/documents/{doc_id}", headers=headers)
    assert get_resp.status_code == 404


def test_create_document_requires_auth(client):
    response = client.post(
        "/documents",
        data={"title": "Doc", "subject": "Maths", "document_type": "course", "text_override": "x" * 50},
    )
    assert response.status_code in (401, 403)
