def test_register_user(client):
    resp = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_fails(client):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login", json={"email": "bob@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login", json={"email": "bob@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/expenses")
    assert resp.status_code == 401
