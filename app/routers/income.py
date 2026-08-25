"""
/income routes: add, view (with optional date filters), update, delete.
All routes are scoped to the authenticated user.
"""
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Income, User
from app.schemas import IncomeCreate, IncomeUpdate, IncomeOut

router = APIRouter(prefix="/income", tags=["Income"])


@router.post("", response_model=IncomeOut, status_code=status.HTTP_201_CREATED)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income = Income(user_id=current_user.id, **payload.model_dump())
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


@router.get("", response_model=List[IncomeOut])
def list_income(
    start_date: Optional[date] = Query(None, description="Filter: income on/after this date"),
    end_date: Optional[date] = Query(None, description="Filter: income on/before this date"),
    source: Optional[str] = Query(None, description="Filter by source (exact match)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Income).filter(Income.user_id == current_user.id)

    if start_date:
        query = query.filter(Income.date >= start_date)
    if end_date:
        query = query.filter(Income.date <= end_date)
    if source:
        query = query.filter(Income.source == source)

    return (
        query.order_by(Income.date.desc(), Income.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{income_id}", response_model=IncomeOut)
def get_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_income(db, income_id, current_user.id)


@router.put("/{income_id}", response_model=IncomeOut)
def update_income(
    income_id: int,
    payload: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income = _get_owned_income(db, income_id, current_user.id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(income, field, value)

    db.commit()
    db.refresh(income)
    return income


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income = _get_owned_income(db, income_id, current_user.id)
    db.delete(income)
    db.commit()
    return None


def _get_owned_income(db: Session, income_id: int, user_id: int) -> Income:
    income = (
        db.query(Income)
        .filter(Income.id == income_id, Income.user_id == user_id)
        .first()
    )
    if not income:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")
    return income
