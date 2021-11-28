"""Exceptions module."""


class PaymasterException(Exception):
    """Base app exception."""
    pass


class AccountError(PaymasterException):
    """Exception of no account in database."""
    pass


class CurrencyError(PaymasterException):
    """Exception of no currency in currencies table."""
    pass


class BalanceValueError(PaymasterException):
    """Exception of negative account balance."""
    pass
