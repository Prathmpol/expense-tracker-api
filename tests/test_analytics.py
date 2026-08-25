def _seed(client, auth_headers):
    client.post("/income", json={"amount": 50000, "source": "Salary", "date": "2026-08-01"}, headers=auth_headers)
    client.post("/expenses", json={"amount": 20000, "category": "Food", "date": "2026-08-01"}, headers=auth_headers)
    client.post("/expenses", json={"amount": 12000, "category": "Bills", "date": "2026-08-05"}, headers=auth_headers)


def test_summary_analytics(client, auth_headers):
    _seed(client, auth_headers)

    resp = client.get("/analytics/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_income"] == 50000
    assert body["total_expenses"] == 32000
    assert body["balance"] == 18000
    assert body["highest_spending_category"] == "Food"
    assert body["savings_rate"] == 36.0


def test_category_analytics(client, auth_headers):
    _seed(client, auth_headers)

    resp = client.get("/analytics/category", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["highest_spending_category"] == "Food"
    assert body["total_expenses"] == 32000
    categories = {c["category"]: c for c in body["categories"]}
    assert categories["Food"]["total"] == 20000
    assert categories["Bills"]["total"] == 12000


def test_monthly_analytics(client, auth_headers):
    _seed(client, auth_headers)

    resp = client.get("/analytics/monthly", headers=auth_headers)
    assert resp.status_code == 200
    months = resp.json()["months"]
    assert len(months) == 1
    assert months[0]["month"] == "2026-08"
    assert months[0]["total_income"] == 50000
    assert months[0]["total_expenses"] == 32000


def test_savings_analytics(client, auth_headers):
    _seed(client, auth_headers)

    resp = client.get("/analytics/savings", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_savings"] == 18000
    assert body["savings_rate"] == 36.0


def test_analytics_with_no_data(client, auth_headers):
    resp = client.get("/analytics/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_income"] == 0
    assert body["total_expenses"] == 0
    assert body["savings_rate"] == 0
    assert body["highest_spending_category"] is None
