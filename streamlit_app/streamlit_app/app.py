"""Ledger – Streamlit frontend for the Expense Tracker API.
Run:  streamlit run streamlit_app/app.py   (API must be running on :8000)
"""
import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API = os.getenv("API_BASE", "http://127.0.0.1:8000")
CATS = ["Food", "Travel", "Shopping", "Bills", "Education", "Entertainment", "Healthcare", "Other"]
PALETTE = ["#6C63FF", "#00C9A7", "#FF6B8A", "#FFB454", "#4FACFE", "#B66DFF", "#2ED47A", "#8892B0"]

st.set_page_config(page_title="Ledger · Expense Tracker", page_icon="💸", layout="wide")

st.markdown("""
<style>
.stApp{background:radial-gradient(1200px 600px at 10% -10%,#1d1b4b 0%,#0e1117 55%)}
section[data-testid="stSidebar"]{background:#11141d;border-right:1px solid #232838}
.hero{padding:1.2rem 1.6rem;border-radius:18px;margin-bottom:1rem;
 background:linear-gradient(120deg,#6C63FF 0%,#00C9A7 100%);color:#fff}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.2rem 0 0;opacity:.9}
.kpi{padding:1.1rem 1.2rem;border-radius:16px;background:rgba(255,255,255,.04);
 border:1px solid rgba(255,255,255,.08);backdrop-filter:blur(6px);transition:.2s}
.kpi:hover{transform:translateY(-3px);border-color:#6C63FF}
.kpi .l{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:#9aa4bf}
.kpi .v{font-size:1.7rem;font-weight:700;margin-top:.2rem}
.kpi .s{font-size:.8rem;color:#9aa4bf}
.pos{color:#2ED47A}.neg{color:#FF6B8A}
.stButton>button,.stFormSubmitButton>button{border-radius:12px;font-weight:600;
 background:linear-gradient(120deg,#6C63FF,#8b5cf6);color:#fff;border:0}
.stTabs [data-baseweb="tab"]{font-weight:600}
#MainMenu,footer{visibility:hidden}
</style>""", unsafe_allow_html=True)


# ---------------- API helpers ----------------
def call(method, path, **kw):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.get("token") else {}
    try:
        r = requests.request(method, f"{API}{path}", headers=headers, timeout=10, **kw)
    except requests.ConnectionError:
        st.error(f"Cannot reach API at {API}. Start it with `uvicorn app.main:app --reload`.")
        st.stop()
    if r.status_code == 401 and st.session_state.get("token"):
        st.session_state.token = None
        st.rerun()
    if not r.ok:
        d = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
        raise ValueError(d if isinstance(d, str) else d[0].get("msg", str(d)))
    return None if r.status_code == 204 else r.json()


def kpi(label, value, sub="", cls=""):
    st.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v {cls}">{value}</div>'
                f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def inr(x):
    return f"₹{x:,.0f}"


def style(fig, h=340):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#cfd6ea", legend_orientation="h",
                      legend_y=-0.15)
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)")
    return fig


# ---------------- Auth screen ----------------
if "token" not in st.session_state:
    st.session_state.token = None

if not st.session_state.token:
    st.markdown('<div class="hero"><h1>💸 Ledger</h1><p>Track every rupee. Understand your money.</p></div>',
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        t1, t2 = st.tabs(["🔐 Sign in", "✨ Create account"])
        with t1:
            with st.form("login"):
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in", use_container_width=True):
                    try:
                        st.session_state.token = call("POST", "/auth/login", json={"email": e, "password": p})["access_token"]
                        st.session_state.email = e
                        st.rerun()
                    except ValueError as ex:
                        st.error(ex)
        with t2:
            with st.form("reg"):
                n = st.text_input("Name")
                e2 = st.text_input("Email ")
                p2 = st.text_input("Password (min 6 chars)", type="password")
                if st.form_submit_button("Create account", use_container_width=True):
                    try:
                        call("POST", "/auth/register", json={"name": n, "email": e2, "password": p2})
                        st.success("Account created — sign in from the other tab.")
                    except ValueError as ex:
                        st.error(ex)
    st.stop()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("## 💸 Ledger")
    st.caption(st.session_state.get("email", ""))
    rng = st.selectbox("Period", ["This month", "Last 30 days", "Last 90 days", "This year", "All time", "Custom"], index=1)
    today = date.today()
    start, end = {
        "This month": (today.replace(day=1), today),
        "Last 30 days": (today - timedelta(days=30), today),
        "Last 90 days": (today - timedelta(days=90), today),
        "This year": (today.replace(month=1, day=1), today),
        "All time": (None, None),
        "Custom": (None, None),
    }[rng]
    if rng == "Custom":
        picked = st.date_input("Range", (today - timedelta(days=30), today))
        if len(picked) == 2:
            start, end = picked
    st.divider()
    if st.button("Log out", use_container_width=True):
        st.session_state.token = None
        st.rerun()

params = {k: v.isoformat() for k, v in {"start_date": start, "end_date": end}.items() if v}

st.markdown('<div class="hero"><h1>Financial Overview</h1><p>Your income, spending and savings at a glance.</p></div>',
            unsafe_allow_html=True)

tab_dash, tab_exp, tab_inc = st.tabs(["📊 Dashboard", "🧾 Expenses", "💰 Income"])

# ---------------- Dashboard ----------------
with tab_dash:
    s = call("GET", "/analytics/summary", params=params)
    c = st.columns(4)
    with c[0]: kpi("Income", inr(s["total_income"]), "money in", "pos")
    with c[1]: kpi("Expenses", inr(s["total_expenses"]), f"avg {inr(s['average_daily_spending'])}/day", "neg")
    with c[2]: kpi("Balance", inr(s["balance"]), "income − expenses", "pos" if s["balance"] >= 0 else "neg")
    with c[3]: kpi("Savings rate", f"{s['savings_rate']:.1f}%", f"top: {s['highest_spending_category'] or '—'}")
    st.write("")
    g1, g2 = st.columns([1.1, 1])
    cat = call("GET", "/analytics/category", params=params)["categories"]
    with g1:
        if cat:
            df = pd.DataFrame(cat)
            f = px.pie(df, names="category", values="total", hole=.6, color_discrete_sequence=PALETTE,
                       title="Spending by category")
            f.update_traces(textinfo="percent", marker_line_width=0)
            st.plotly_chart(style(f), use_container_width=True)
        else:
            st.info("No expenses in this period.")
    with g2:
        if cat:
            f = px.bar(df.sort_values("total"), x="total", y="category", orientation="h",
                       color="category", color_discrete_sequence=PALETTE, title="Category ranking",
                       text=df.sort_values("total")["total"].map(inr))
            f.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(style(f), use_container_width=True)
    months = call("GET", "/analytics/monthly", params=params)["months"]
    if months:
        m = pd.DataFrame(months)
        f = go.Figure()
        f.add_bar(x=m.month, y=m.total_income, name="Income", marker_color="#00C9A7")
        f.add_bar(x=m.month, y=m.total_expenses, name="Expenses", marker_color="#FF6B8A")
        f.add_scatter(x=m.month, y=m.balance, name="Balance", mode="lines+markers",
                      line=dict(color="#6C63FF", width=3))
        f.update_layout(barmode="group", title="Monthly trend")
        st.plotly_chart(style(f, 380), use_container_width=True)


# ---------------- Generic transactions tab ----------------
def ledger_tab(kind):
    is_exp = kind == "expenses"
    path = "/expenses" if is_exp else "/income"
    label = "expense" if is_exp else "income"
    left, right = st.columns([1, 2.2])

    with left:
        st.subheader(f"➕ Add {label}")
        with st.form(f"add_{kind}", clear_on_submit=True):
            amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            if is_exp:
                tag = st.selectbox("Category", CATS)
            else:
                tag = st.text_input("Source", placeholder="Salary, Freelance…")
            desc = st.text_input("Description (optional)")
            d = st.date_input("Date", date.today())
            if st.form_submit_button(f"Save {label}", use_container_width=True):
                body = {"amount": amt, ("category" if is_exp else "source"): tag,
                        "description": desc or None, "date": d.isoformat()}
                try:
                    call("POST", path, json=body)
                    st.toast(f"{label.title()} added", icon="✅")
                    st.rerun()
                except ValueError as ex:
                    st.error(ex)

    with right:
        q = dict(params, limit=500)
        cat_f = None
        if is_exp:
            cat_f = st.multiselect("Filter categories", CATS, key=f"f_{kind}")
        rows = call("GET", path, params=q)
        if cat_f:
            rows = [r for r in rows if r["category"] in cat_f]
        if not rows:
            st.info(f"No {kind} found for this period.")
            return
        df = pd.DataFrame(rows)
        tagcol = "category" if is_exp else "source"
        st.caption(f"{len(df)} records · total **{inr(df.amount.sum())}**")
        st.dataframe(
            df[["id", "date", tagcol, "description", "amount"]],
            hide_index=True, use_container_width=True, height=330,
            column_config={"amount": st.column_config.NumberColumn("Amount", format="₹%.0f"),
                           "date": st.column_config.DateColumn("Date")})
        c1, c2 = st.columns([3, 1])
        with c1:
            pick = st.selectbox("Delete a record", df.id,
                                format_func=lambda i: f"#{i} · {df.loc[df.id == i, tagcol].iat[0]} · {inr(df.loc[df.id == i, 'amount'].iat[0])}",
                                key=f"del_{kind}")
        with c2:
            st.write("")
            st.write("")
            if st.button("🗑 Delete", key=f"delb_{kind}", use_container_width=True):
                call("DELETE", f"{path}/{pick}")
                st.toast("Deleted", icon="🗑")
                st.rerun()
        st.download_button("⬇ Export CSV", df.to_csv(index=False), f"{kind}.csv", "text/csv")


with tab_exp:
    ledger_tab("expenses")
with tab_inc:
    ledger_tab("income")
