"""Database module."""
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from asyncpg import Connection, exceptions
from paymaster.data_schemas import OperationType, SortKey
from paymaster.exceptions import AccountError, BalanceValueError, CurrencyError

FRACTIONAL_VALUE = Decimal(100)


async def create_acc(user_id: int, db_con: Connection) -> None:
    """Create user account.

    Args:
        user_id: user id
        db_con: connection to database

    Raises:
        AccountError: conflict with existiong account
    """
    query = """ INSERT INTO accounts (user_id)
                VALUES ($1)
                ON CONFLICT (user_id)
                DO UPDATE SET status = 'active';"""
    if await _has_account(user_id, db_con):
        raise AccountError(f'Account with id <{user_id}> already exists')
    else:
        await db_con.execute(query, user_id)


async def delete_acc(user_id: int, db_con: Connection) -> None:
    """Delete user account.

    Args:
        user_id: user id
        db_con: connection to database

    Raises:
        AccountError: conflict with non existiong account
    """
    acc_query = """ UPDATE accounts
                    SET status = 'deleted'
                    WHERE user_id = ($1);"""
    if await _has_account(user_id, db_con):
        await db_con.execute(acc_query, user_id)
    else:
        raise AccountError(f"Account with id <{user_id}> don't exists")


async def change_balance(
    user_id: int,
    qty_value: Decimal,
    operation_type: str,
    db_con: Connection,
    description: Optional[str] = None,
):
    """Change user account balance.

    Args:
        user_id: user id
        qty_value: quantity of transaction value
        operation_type: type of transaction
        db_con: connection to database
        description: description of transaction aim
    """
    if operation_type == OperationType.replenishment:
        await _crediting_balance(
            user_id=user_id,
            qty_value=qty_value,
            db_con=db_con,
            description=description,
        )
    elif operation_type == OperationType.withdraw:
        await _debiting_balance(
            user_id=user_id,
            qty_value=qty_value,
            db_con=db_con,
            description=description,
        )


async def transfer_between_accs(
    sender_id: int,
    recipient_id: int,
    qty_value: Decimal,
    db_con: Connection,
    description: Optional[str] = None,
) -> None:
    """Send funds from one account to another.

    Args:
        sender_id: sender user id
        recipient_id: recipient user id
        qty_value: quantity of transaction value
        db_con: connection to database
        description: description of transaction aim
    """
    async with db_con.transaction():
        await _debiting_balance(
            user_id=sender_id,
            deal_with=recipient_id,
            qty_value=qty_value,
            description='outcoming payment' if description is None else description,  # noqa: E501
            db_con=db_con,
        )
        await _crediting_balance(
            user_id=recipient_id,
            deal_with=sender_id,
            qty_value=qty_value,
            description='incoming payment' if description is None else description,  # noqa: E501
            db_con=db_con,
        )


async def get_balance(
    user_id: int,
    db_con: Connection,
    convert_to: Optional[str] = None,
) -> Decimal:
    """Get user account balance.

    Args:
        user_id: user id
        db_con: database connection
        convert_to: currency for convertation

    Returns:
        balance value

    Raises:
        AccountError: user account isn't registered
    """
    if await _has_account(user_id, db_con):
        balance: Decimal = await _compute_balance(user_id, db_con) / FRACTIONAL_VALUE  # noqa: E501
        cur_rate: Decimal = Decimal(1) if convert_to is None else await _fetch_currency_rate(  # noqa: E501
            cur_name=convert_to,
            db_con=db_con,
        )
        return Decimal(round(balance * cur_rate, 2))
    raise AccountError(f'Has no registered account with id: {user_id}')


async def fetch_acc_history(  # noqa: WPS210 WPS211
    user_id: int,
    db_con: Connection,
    page_number: int = 1,
    page_size: int = 20,
    order_by_date: Optional[SortKey] = None,
    order_by_total: Optional[SortKey] = None,
) -> Tuple[Dict[str, str]]:
    """Fetch user account transactions history.

    Args:
        user_id: user id
        db_con: database connection
        page_number: nuber of neccessary page
        page_size: number of records per page
        order_by_date: sort order by transaction date
        order_by_total: sort order by transaction total value

    Returns:
        transactions history

    Raises:
        AccountError: user account isn't registered
    """
    offset = (page_number - 1) * page_size
    primary_key, additional_key, coma = await _get_sort_keys(order_by_date, order_by_total)  # noqa: E501
    query: str = f"""   SELECT DATE(created_at)
                            AS date, deal_with, description, qty_change as total
                            FROM transactions
                            WHERE account_id = (
                                SELECT id
                                FROM accounts
                                WHERE user_id = $1
                                AND status = 'active'
                            )
                            ORDER BY {primary_key}{coma} {additional_key}
                            OFFSET $2 LIMIT $3;"""
    history = await db_con.fetch(query, user_id, offset, page_size)

    if history:
        history = tuple(map(dict, history))
        return history  # noqa: WPS331
    raise AccountError(f'Has no registered account with id: {user_id}')


async def update_currencies(
    cur_rates: List[Tuple[str, float]],
    db_con: Connection,
) -> None:
    """Update currencies rates table.

    Args:
        cur_rates: rates of currencies
        db_con: darabase connection
    """
    query = """ INSERT INTO currencies (cur_name, rate_to_base)
                VALUES ($1, $2)
                ON CONFLICT (cur_name)
                DO UPDATE SET rate_to_base = $2
                WHERE currencies.cur_name = $1;"""
    await db_con.executemany(query, cur_rates)


async def _crediting_balance(
    user_id: int,
    qty_value: Decimal,
    db_con: Connection,
    deal_with: Optional[int] = None,
    description: Optional[str] = None,
) -> None:
    deal_with = user_id if deal_with is None else deal_with
    description = 'replenishment' if description is None else description
    fractional_qty_value = int(qty_value * FRACTIONAL_VALUE)
    query = """ INSERT INTO transactions (
                    account_id, deal_with, description, qty_change
                )
                VALUES (
                    (SELECT id
                    FROM accounts
                    WHERE user_id = $1
                    AND status = 'active'), $2, $3, $4
                );"""
    async with db_con.transaction():
        try:
            await db_con.execute(
                query,
                user_id,
                deal_with,
                description,
                fractional_qty_value,
            )
        except exceptions.NotNullViolationError as exc:
            raise AccountError(
                f'Has no registered account with id: {user_id}',
            ) from exc


async def _debiting_balance(
    user_id: int,
    qty_value: Decimal,
    db_con: Connection,
    deal_with: Optional[int] = None,
    description: Optional[str] = None,
) -> None:
    deal_with = user_id if deal_with is None else deal_with
    description = 'withdraw' if description is None else description
    fractional_qty_value = int(qty_value * FRACTIONAL_VALUE)
    query = """ INSERT INTO transactions (
                    account_id, deal_with, description, qty_change
                )
                VALUES (
                    (SELECT id
                    FROM accounts
                     WHERE user_id = $1
                     AND status = 'active'), $2, $3, $4
                );"""
    if not await _has_account(user_id, db_con):
        raise AccountError(f'Has no registered account with id: {user_id}')
    async with db_con.transaction():
        balance = await _compute_balance(user_id, db_con)
        if balance - abs(fractional_qty_value) >= 0:
            try:
                await db_con.execute(
                    query,
                    user_id,
                    deal_with,
                    description,
                    -fractional_qty_value,  # Make quantity value negative
                )
            except exceptions.ForeignKeyViolationError:
                raise AccountError(f'Has no registered account with id: {deal_with}')  # noqa: E501
        else:
            raise BalanceValueError(
                f'Insufficient funds on the account: {user_id}',
            )


async def _fetch_currency_rate(cur_name: str, db_con: Connection) -> Decimal:
    query = """ SELECT rate_to_base
                FROM currencies
                WHERE cur_name = $1;"""
    rate: float = await db_con.fetchval(query, cur_name)
    if rate is None:
        raise CurrencyError(f'Unsupported currency type: {cur_name}')
    return Decimal(rate)


async def _compute_balance(user_id: int, db_con: Connection) -> Decimal:
    balance_query = """ SELECT sum(qty_change)
                        FROM transactions
                        WHERE account_id = (
                            SELECT id
                            FROM accounts
                            WHERE user_id = $1
                            AND status = 'active'
                        );"""
    balance = await db_con.fetchval(balance_query, user_id)
    return Decimal(0) if balance is None else Decimal(balance)


async def _get_sort_keys(
    order_by_date: Optional[SortKey],
    order_by_total: Optional[SortKey],
):
    date_key: str = 'date'
    total_key: str = 'total'
    if order_by_date is None:
        date_sort_order: str = 'DESC'
    else:
        date_sort_order = 'DESC' if order_by_date == SortKey.desc else 'ASC'
    if order_by_total is not None:
        total_sort_order: str = 'DESC' if order_by_total == SortKey.desc else 'ASC'  # noqa: E501
    coma: str = '' if order_by_total is None else ','
    date_key = f'{date_key} {date_sort_order}'
    total_key = '' if order_by_total is None else f'{total_key} {total_sort_order}'  # noqa: E501
    return date_key, total_key, coma


async def _has_account(user_id: int, db_con: Connection):
    query = """ SELECT user_id
                FROM accounts
                WHERE user_id = $1
                AND status = 'active';"""
    return user_id == await db_con.fetchval(query, user_id)
