def test_create_and_list_income(client, auth_headers):
    resp = client.post(
        "/income",
        json={"amount": 50000, "source": "Salary", "date": "2026-08-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["source"] == "Salary"

    resp = client.get("/income", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_income(client, auth_headers):
    create = client.post(
        "/income", json={"amount": 1000, "source": "Freelance", "date": "2026-08-01"}, headers=auth_headers
    )
    income_id = create.json()["id"]

    resp = client.put(f"/income/{income_id}", json={"amount": 1200}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["amount"] == 1200


def test_delete_income(client, auth_headers):
    create = client.post(
        "/income", json={"amount": 500, "source": "Gift", "date": "2026-08-01"}, headers=auth_headers
    )
    income_id = create.json()["id"]

    resp = client.delete(f"/income/{income_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/income/{income_id}", headers=auth_headers)
    assert resp.status_code == 404

def test_create_income_rejects_zero_amount(client, auth_headers):
    resp = client.post(
        "/income",
        json={
            "amount": 0,
            "source": "Salary",
            "date": "2026-08-01",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 422


def test_create_income_rejects_missing_source(client, auth_headers):
    resp = client.post(
        "/income",
        json={
            "amount": 1000,
            "date": "2026-08-01",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 422
