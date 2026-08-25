def test_full_learner_journey(client):
    login = client.post("/auth/login", json={"username": "amina"})
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    create_resp = client.post(
        "/documents",
        headers=headers,
        data={
            "title": "Cours sur les fractions",
            "subject": "Mathématiques",
            "document_type": "course",
            "text_override": (
                "Une fraction représente une division entre deux nombres entiers. "
                "Le numérateur est au-dessus, le dénominateur en dessous."
            ),
        },
    )
    assert create_resp.status_code == 201
    doc_id = create_resp.json()["id"]

    chat_resp = client.post(
        "/chat",
        headers=headers,
        json={"message": "explique-moi le numérateur", "document_id": doc_id},
    )
    assert chat_resp.status_code == 200
    assert chat_resp.json()["reply"]

    history_resp = client.get(f"/chat/history?document_id={doc_id}", headers=headers)
    assert len(history_resp.json()) == 2

    fail_resp = client.post(
        "/progress/result",
        headers=headers,
        json={
            "notion": "Fractions",
            "subject": "Mathématiques",
            "success": False,
            "learner_note": "je confonds numérateur et dénominateur",
        },
    )
    assert fail_resp.status_code == 200
    assert fail_resp.json()["analysis"]["error_type"] == "concept"

    progress_resp = client.get("/progress", headers=headers)
    assert progress_resp.json()[0]["failure"] == 1

    settings_resp = client.put(
        "/settings",
        headers=headers,
        json={"api_key": "", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile", "ocr_engine": "auto"},
    )
    assert settings_resp.status_code == 200

    delete_resp = client.delete(f"/documents/{doc_id}", headers=headers)
    assert delete_resp.status_code == 204
