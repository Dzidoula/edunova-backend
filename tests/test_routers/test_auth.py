def test_login_creates_user_on_first_call(client):
    response = client.post("/auth/login", json={"username": "koffi", "password": "secret123"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["username"] == "koffi"
    assert body["token"]

    # second call with the same username reuses the same user id
    response2 = client.post("/auth/login", json={"username": "koffi", "password": "secret123"})
    assert response2.json()["user"]["id"] == body["user"]["id"]


def test_login_rejects_blank_username(client):
    response = client.post("/auth/login", json={"username": "   ", "password": "secret123"})
    assert response.status_code == 422


def test_login_rejects_wrong_password(client):
    client.post("/auth/login", json={"username": "koffi", "password": "secret123"})
    response = client.post("/auth/login", json={"username": "koffi", "password": "wrong-pass"})
    assert response.status_code == 401


def test_login_rejects_short_password(client):
    response = client.post("/auth/login", json={"username": "koffi", "password": "123"})
    assert response.status_code == 422
