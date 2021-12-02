"""Responses and requests data schemas."""
from decimal import Decimal
from enum import Enum
from typing import Dict, Tuple

from fastapi import status
from paymaster.currencies import BASE_CURRENCY
from pydantic import BaseModel, Field, PositiveInt, condecimal


class OperationType(str, Enum):  # noqa: WPS600
    """Operations types for transactions."""

    replenishment: str = 'replenishment'
    withdraw: str = 'withdraw'


class SortKey(str, Enum):  # noqa: WPS600
    """Sort order for sort keys."""

    desc: str = 'desc'
    asc: str = 'asc'


class Balance(BaseModel):
    """Response model for user balance."""

    status_code: int = Field(status.HTTP_200_OK, ge=100, lt=600)  # noqa: WPS432
    user_id: PositiveInt
    balance: condecimal(decimal_places=2)
    currency: str = Field(BASE_CURRENCY, min_length=3, max_length=3)


class Operation(BaseModel):
    """Request model for change user balance."""

    operation: OperationType
    user_id: PositiveInt
    total: condecimal(gt=Decimal(0), decimal_places=2)
    description: str = None


class Transaction(BaseModel):
    """Request model for transfer funds between user accounts."""

    sender_id: PositiveInt
    recipient_id: PositiveInt
    total: condecimal(gt=Decimal(0), decimal_places=2)
    description: str = Field(None)


class PageOut(BaseModel):
    """Response model for user account transactions history request."""

    status_code: int = Field(status.HTTP_200_OK, ge=100, lt=600)  # noqa: WPS432
    content: Tuple[Dict, ...]  # noqa: WPS110
