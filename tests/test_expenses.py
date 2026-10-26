def test_create_and_list_expense(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={
            "amount": 250.5,
            "category": "Food",
            "description": "Groceries",
            "date": "2026-08-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == 250.5
    assert body["category"] == "Food"

    resp = client.get("/expenses", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_expense(client, auth_headers):
    create = client.post(
        "/expenses",
        json={"amount": 100, "category": "Travel", "date": "2026-08-02"},
        headers=auth_headers,
    )
    expense_id = create.json()["id"]

    resp = client.put(
        f"/expenses/{expense_id}",
        json={"amount": 150},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 150


def test_delete_expense(client, auth_headers):
    create = client.post(
        "/expenses",
        json={"amount": 75, "category": "Bills", "date": "2026-08-03"},
        headers=auth_headers,
    )
    expense_id = create.json()["id"]

    resp = client.delete(f"/expenses/{expense_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/expenses/{expense_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_expenses_by_category(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Food", "date": "2026-08-01"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 30, "category": "Travel", "date": "2026-08-02"},
        headers=auth_headers,
    )

    resp = client.get("/expenses?category=Food", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["category"] == "Food"


def test_filter_expenses_by_date_range(client, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 20, "category": "Food", "date": "2026-07-01"},
        headers=auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 30, "category": "Food", "date": "2026-08-15"},
        headers=auth_headers,
    )

    resp = client.get(
        "/expenses?start_date=2026-08-01&end_date=2026-08-31",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["amount"] == 30


def test_expense_isolated_per_user(client):
    # User A
    client.post(
        "/auth/register",
        json={
            "name": "A",
            "email": "a@example.com",
            "password": "password123",
        },
    )
    login_a = client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "password123"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    # User B
    client.post(
        "/auth/register",
        json={
            "name": "B",
            "email": "b@example.com",
            "password": "password123",
        },
    )
    login_b = client.post(
        "/auth/login",
        json={"email": "b@example.com", "password": "password123"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    client.post(
        "/expenses",
        json={"amount": 10, "category": "Food", "date": "2026-08-01"},
        headers=headers_a,
    )

    resp = client.get("/expenses", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_expense_rejects_zero_amount(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={"amount": 0, "category": "Food", "date": "2026-08-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_expense_rejects_invalid_category(client, auth_headers):
    resp = client.post(
        "/expenses",
        json={
            "amount": 100,
            "category": "InvalidCategory",
            "date": "2026-08-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_list_expenses_rejects_invalid_limit(client, auth_headers):
    resp = client.get("/expenses?limit=0", headers=auth_headers)
    assert resp.status_code == 422