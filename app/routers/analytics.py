"""
/analytics routes: financial analytics computed with pandas over the
authenticated user's expenses and income.
"""
from datetime import date, timedelta
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Expense, Income, User
from app.schemas import (
    SummaryOut,
    MonthlyAnalyticsOut,
    MonthlyBreakdown,
    CategoryAnalyticsOut,
    CategoryBreakdown,
    SavingsAnalyticsOut,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _expenses_df(db: Session, user_id: int, start_date: Optional[date], end_date: Optional[date]) -> pd.DataFrame:
    query = db.query(Expense).filter(Expense.user_id == user_id)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    rows = query.all()

    if not rows:
        return pd.DataFrame(columns=["amount", "category", "date"])

    return pd.DataFrame(
        [{"amount": r.amount, "category": r.category.value, "date": r.date} for r in rows]
    )


def _income_df(db: Session, user_id: int, start_date: Optional[date], end_date: Optional[date]) -> pd.DataFrame:
    query = db.query(Income).filter(Income.user_id == user_id)
    if start_date:
        query = query.filter(Income.date >= start_date)
    if end_date:
        query = query.filter(Income.date <= end_date)
    rows = query.all()

    if not rows:
        return pd.DataFrame(columns=["amount", "source", "date"])

    return pd.DataFrame([{"amount": r.amount, "source": r.source, "date": r.date} for r in rows])


def _average_daily_spending(expenses_df: pd.DataFrame) -> float:
    if expenses_df.empty:
        return 0.0
    day_span = (expenses_df["date"].max() - expenses_df["date"].min()).days + 1
    day_span = max(day_span, 1)
    return round(float(expenses_df["amount"].sum()) / day_span, 2)


@router.get("/summary", response_model=SummaryOut)
def get_summary(
    start_date: Optional[date] = Query(None, description="Restrict analytics to this range"),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expenses_df = _expenses_df(db, current_user.id, start_date, end_date)
    income_df = _income_df(db, current_user.id, start_date, end_date)

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0
    total_expenses = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
    balance = round(total_income - total_expenses, 2)
    savings_rate = round((balance / total_income) * 100, 2) if total_income > 0 else 0.0

    highest_category = None
    if not expenses_df.empty:
        by_category = expenses_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        if not by_category.empty:
            highest_category = str(by_category.index[0])

    return SummaryOut(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        balance=balance,
        savings_rate=savings_rate,
        highest_spending_category=highest_category,
        average_daily_spending=_average_daily_spending(expenses_df),
    )


@router.get("/monthly", response_model=MonthlyAnalyticsOut)
def get_monthly_analytics(
    year: Optional[int] = Query(None, description="Restrict to a specific year, e.g. 2026"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expenses_df = _expenses_df(db, current_user.id, None, None)
    income_df = _income_df(db, current_user.id, None, None)

    if not expenses_df.empty:
        expenses_df["month"] = pd.to_datetime(expenses_df["date"]).dt.strftime("%Y-%m")
        if year:
            expenses_df = expenses_df[expenses_df["month"].str.startswith(str(year))]
    if not income_df.empty:
        income_df["month"] = pd.to_datetime(income_df["date"]).dt.strftime("%Y-%m")
        if year:
            income_df = income_df[income_df["month"].str.startswith(str(year))]

    expense_by_month = (
        expenses_df.groupby("month")["amount"].sum() if not expenses_df.empty else pd.Series(dtype=float)
    )
    income_by_month = (
        income_df.groupby("month")["amount"].sum() if not income_df.empty else pd.Series(dtype=float)
    )

    all_months = sorted(set(expense_by_month.index) | set(income_by_month.index))

    months = [
        MonthlyBreakdown(
            month=m,
            total_income=round(float(income_by_month.get(m, 0.0)), 2),
            total_expenses=round(float(expense_by_month.get(m, 0.0)), 2),
            balance=round(float(income_by_month.get(m, 0.0)) - float(expense_by_month.get(m, 0.0)), 2),
        )
        for m in all_months
    ]

    return MonthlyAnalyticsOut(months=months)


@router.get("/category", response_model=CategoryAnalyticsOut)
def get_category_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expenses_df = _expenses_df(db, current_user.id, start_date, end_date)

    if expenses_df.empty:
        return CategoryAnalyticsOut(categories=[], highest_spending_category=None, total_expenses=0.0)

    total_expenses = float(expenses_df["amount"].sum())

    grouped = (
        expenses_df.groupby("category")["amount"]
        .agg(total="sum", transaction_count="count")
        .sort_values("total", ascending=False)
    )

    categories = [
        CategoryBreakdown(
            category=str(cat),
            total=round(float(row["total"]), 2),
            percentage=round((float(row["total"]) / total_expenses) * 100, 2) if total_expenses else 0.0,
            transaction_count=int(row["transaction_count"]),
        )
        for cat, row in grouped.iterrows()
    ]

    return CategoryAnalyticsOut(
        categories=categories,
        highest_spending_category=categories[0].category if categories else None,
        total_expenses=round(total_expenses, 2),
    )


@router.get("/savings", response_model=SavingsAnalyticsOut)
def get_savings_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expenses_df = _expenses_df(db, current_user.id, start_date, end_date)
    income_df = _income_df(db, current_user.id, start_date, end_date)

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0
    total_expenses = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
    total_savings = round(total_income - total_expenses, 2)
    savings_rate = round((total_savings / total_income) * 100, 2) if total_income > 0 else 0.0

    return SavingsAnalyticsOut(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        total_savings=total_savings,
        savings_rate=savings_rate,
        average_daily_spending=_average_daily_spending(expenses_df),
    )
