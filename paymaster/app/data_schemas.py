"""Responses and requests data schemas."""
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from fastapi import status
from paymaster.currencies import BASE_CURRENCY
from pydantic import BaseModel, ConstrainedDecimal, Field, PositiveInt


class TotalValue(ConstrainedDecimal):
    """Type for validate total value."""

    gt = Decimal(0)
    decimal_places = 2


class BalanceValue(ConstrainedDecimal):
    """Type for validate balance value."""

    decimal_places = 2


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
    balance: BalanceValue
    currency: str = Field(BASE_CURRENCY, min_length=3, max_length=3)


class Operation(BaseModel):
    """Request model for change user balance."""

    operation: OperationType
    user_id: PositiveInt
    total: TotalValue
    description: Optional[str] = Field(None)


class Transaction(BaseModel):
    """Request model for transfer funds between user accounts."""

    sender_id: PositiveInt
    recipient_id: PositiveInt
    total: TotalValue
    description: Optional[str] = Field(None)


class PageOut(BaseModel):
    """Response model for user account transactions history request."""

    content: Tuple[Dict[str, Any], ...]  # noqa: WPS110
