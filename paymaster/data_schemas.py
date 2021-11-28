"""Responses and requests data schemas."""
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Tuple

from fastapi import status
from paymaster.currencies import BASE_CURRENCY
from pydantic import BaseModel, Field, PositiveInt, condecimal


class OperationType(str, Enum):
    credit: str = 'credit'
    debit: str = 'debit'


class Balance(BaseModel):
    status_code: int = Field(status.HTTP_200_OK, ge=100, lt=600)
    user_id: PositiveInt
    balance: condecimal(decimal_places=2)
    currency: str = Field(BASE_CURRENCY, min_length=3, max_length=3, description='')


class Operation(BaseModel):
    operation: OperationType
    user_id: PositiveInt
    total: condecimal(gt=Decimal(0), decimal_places=2)
    description: str = None


class Transaction(BaseModel):
    sender_id: PositiveInt
    recipient_id: PositiveInt
    total: condecimal(gt=Decimal(0), decimal_places=2)
    description: str


class PageOut(BaseModel):
    status_code: int = Field(status.HTTP_200_OK, ge=100, lt=600)
    page_number: PositiveInt
    content: Tuple[Dict]
