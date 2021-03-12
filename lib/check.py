#!/usr/bin/env python3


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


def is_int(var):
    if not var is None and isinstance(var, int):
        return True
    return False


def is_int_min(var, min):
    if is_int(min) and is_int(var) and var >= min:
        return True
    return False


def is_int_max(var, max):
    if is_int(max) and is_int(var) and var <= max:
        return True
    return False


def is_int_range(var, min, max):
    if is_int(min) and is_int(max) and is_int(var) and min <= var <= max:
        return True
    return False


def is_str(var):
    if not var is None and isinstance(var, str):
        return True
    return False


def is_str_no_empty(var):
    if is_str(var) and var:
        return True
    return False


def is_str_empty(var):
    if is_str(var) and not var:
        return True
    return False


def is_bool(var):
    if not var is None and isinstance(var, bool):
        return True
    return False


def is_list(var):
    if not var is None and isinstance(var, list):
        return True
    return False


def is_list_no_empty(var):
    if is_list(var) and var:
        return True
    return False


def is_list_empty(var):
    if is_list(var) and not var:
        return True
    return False
