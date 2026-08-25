def _login(client, username="koffi"):
    response = client.post("/auth/login", json={"username": username})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_record_success_updates_progress(client):
    headers = _login(client)
    response = client.post(
        "/progress/result",
        headers=headers,
        json={"notion": "Fractions", "subject": "Mathématiques", "success": True},
    )
    assert response.status_code == 200
    assert response.json()["analysis"] is None

    progress_response = client.get("/progress", headers=headers)
    entries = progress_response.json()
    assert entries[0]["notion_name"] == "Fractions"
    assert entries[0]["success"] == 1


def test_record_failure_returns_error_analysis(client):
    headers = _login(client)
    response = client.post(
        "/progress/result",
        headers=headers,
        json={
            "notion": "Fractions",
            "subject": "Mathématiques",
            "success": False,
            "learner_note": "j'ai fait une erreur de calcul sur le signe",
        },
    )
    assert response.status_code == 200
    analysis = response.json()["analysis"]
    assert analysis is not None
    assert analysis["error_type"] == "calculation"


def test_progress_requires_auth(client):
    response = client.get("/progress")
    assert response.status_code in (401, 403)
