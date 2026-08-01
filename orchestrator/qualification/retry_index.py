# -*- coding: utf-8 -*-
"""One exact JSON retry-index scalar contract shared by T-126 consumers."""
from __future__ import annotations


class RetryIndexError(ValueError):
    """A retry index is not the exact JSON integer 0 or 1."""


def validate_retry_index(value: object) -> int:
    """Return an exact retry index without accepting JSON booleans as ints."""
    if type(value) is not int or value not in (0, 1):
        raise RetryIndexError("retry index must be exact integer 0 or 1")
    return value
