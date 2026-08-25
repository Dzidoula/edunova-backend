def _login(client, username="koffi"):
    response = client.post("/auth/login", json={"username": username})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _make_memory(client, headers):
    # A "confusion" memory is written as a side effect of /chat when the message
    # matches a confusion keyword.
    client.post(
        "/chat",
        headers=headers,
        json={"message": "je n'ai pas compris cette partie"},
    )


def test_memory_returns_current_user_entries(client):
    headers = _login(client, "koffi")
    _make_memory(client, headers)

    response = client.get("/memory", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    entry = body[0]
    for key in ("id", "memory_type", "subject", "notion", "content", "weight", "created_at"):
        assert key in entry


def test_memory_does_not_leak_other_users_entries(client):
    headers_a = _login(client, "koffi")
    _make_memory(client, headers_a)

    headers_b = _login(client, "amina")
    response = client.get("/memory", headers=headers_b)
    assert response.status_code == 200
    assert response.json() == []


def test_memory_requires_auth(client):
    response = client.get("/memory")
    assert response.status_code in (401, 403)
