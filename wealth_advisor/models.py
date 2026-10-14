"""Structured data models shared across the system."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: str
    date: str
    description: str
    category: str
    amount: float
    account_id: str


class Account(BaseModel):
    id: str
    type: str
    balance: float
    currency: str = "USD"


class ClientProfile(BaseModel):
    client_id: str
    name: str
    email: Optional[str] = None
    risk_profile: str = "moderate"
    goals: list[str] = Field(default_factory=list)


class ClientFinancialData(BaseModel):
    client: ClientProfile
    accounts: list[Account] = Field(default_factory=list)
    transactions: list[Transaction] = Field(default_factory=list)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Anomaly(BaseModel):
    category: str
    severity: Severity
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    top_spending_categories: list[dict[str, Any]]
    anomalies: list[Anomaly]


class AdvisoryOutput(BaseModel):
    client_id: str
    summary: str
    insights: list[str]
    anomalies: list[Anomaly]
    recommendations: list[str]
