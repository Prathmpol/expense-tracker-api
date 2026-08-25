"""
Pydantic schemas used for request validation and response serialization.
"""
from datetime import date as date_type, datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import ExpenseCategory


# ---------- Auth / User ----------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ---------- Expense ----------

class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="Expense amount, must be positive")
    category: ExpenseCategory = ExpenseCategory.OTHER
    description: Optional[str] = Field(None, max_length=1000)
    date: date_type = Field(default_factory=date_type.today)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = Field(None, max_length=1000)
    date: Optional[date_type] = None


class ExpenseOut(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ---------- Income ----------

class IncomeBase(BaseModel):
    amount: float = Field(..., gt=0, description="Income amount, must be positive")
    source: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    date: date_type = Field(default_factory=date_type.today)


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    source: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    date: Optional[date_type] = None


class IncomeOut(IncomeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ---------- Analytics ----------

class SummaryOut(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    savings_rate: float
    highest_spending_category: Optional[str] = None
    average_daily_spending: float


class MonthlyBreakdown(BaseModel):
    month: str  # "YYYY-MM"
    total_income: float
    total_expenses: float
    balance: float


class MonthlyAnalyticsOut(BaseModel):
    months: List[MonthlyBreakdown]


class CategoryBreakdown(BaseModel):
    category: str
    total: float
    percentage: float
    transaction_count: int


class CategoryAnalyticsOut(BaseModel):
    categories: List[CategoryBreakdown]
    highest_spending_category: Optional[str] = None
    total_expenses: float


class SavingsAnalyticsOut(BaseModel):
    total_income: float
    total_expenses: float
    total_savings: float
    savings_rate: float
    average_daily_spending: float
