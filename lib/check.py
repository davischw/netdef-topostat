#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool Type Checks"""


#
# NetDEF FRR Topotest Results Statistics Tool Type Checks
# Copyright (C) 2021 Network Device Education Foundation, Inc. ("NetDEF")
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


# standard library imports
from datetime import datetime


def is_int(var: int) -> bool:
    """checks if an object is an integer type"""

    if isinstance(var, int):
        return True
    return False


def is_int_min(var: int, minimum: int) -> bool:
    """checks if an object is an integer type with a minimum value"""

    if is_int(minimum) and is_int(var) and var >= minimum:
        return True
    return False


def is_int_max(var: int, maximum: int) -> bool:
    """checks if an object is an integer type with a maximum value"""

    if is_int(maximum) and is_int(var) and var <= maximum:
        return True
    return False


def is_int_range(var: int, minimum: int, maximum: int) -> bool:
    """
    checks if an object is an integer type with a value inside a specified range
    """

    if (
        is_int(minimum)
        and is_int(maximum)
        and is_int(var)
        and minimum <= var <= maximum
    ):
        return True
    return False


def is_float(var: float) -> bool:
    """checks if an object is a float type"""

    if isinstance(var, float):
        return True
    return False


def is_float_min(var: float, minimum: float) -> bool:
    """checks if an object is a float type with a minimum value"""

    if is_float(minimum) and is_float(var) and var >= minimum:
        return True
    return False


def is_float_max(var: float, maximum: float) -> bool:
    """checks if an object is a float type with a maximum value"""

    if is_float(maximum) and is_float(var) and var <= maximum:
        return True
    return False


def is_float_range(var: float, minimum: float, maximum: float) -> bool:
    """
    checks if an object is a float type with a value inside a specified range
    """

    if (
        is_float(var)
        and is_float(minimum)
        and is_float(maximum)
        and minimum <= var <= maximum
    ):
        return True
    return False


def is_str(var: str) -> bool:
    """checks if an object is a string type"""

    if isinstance(var, str):
        return True
    return False


def is_str_no_empty(var: str) -> bool:
    """checks if an object is a string type and is not an empty string"""

    if is_str(var) and var:
        return True
    return False


def is_str_empty(var: str) -> bool:
    """checks if an object is a string type and is an empty string"""

    if is_str(var) and not var:
        return True
    return False


def is_bool(var: bool) -> bool:
    """checks if an object is a boolean type"""

    if isinstance(var, bool):
        return True
    return False


def is_list(var: list) -> bool:
    """checks if an object is a list type"""

    if isinstance(var, list):
        return True
    return False


def is_list_no_empty(var: list) -> bool:
    """checks if an object is a list type and is not an empty list"""

    if is_list(var) and var:
        return True
    return False


def is_list_empty(var: list) -> bool:
    """checks if an object is a list type and is an empty list"""

    if is_list(var) and not var:
        return True
    return False


def is_datetime(var: datetime) -> bool:
    """checks if an object is a datetime type"""

    if isinstance(var, datetime):
        return True
    return False
