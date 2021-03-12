#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool Message"""


#
# NetDEF FRR Topotest Results Statistics Tool Message
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
import json
import hashlib
from json import JSONDecodeError

# proprietary library imports
from lib.check import is_str_no_empty, is_int_min, is_datetime, is_list_no_empty


# message version number
TOPOSTAT_MESSAGE_VERSION = 1

# message timestamp format string
TOPOSTAT_MESSAGE_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S.%f"


class Message:
    """topostat Message type"""

    def __init__(self, version=None, auth=None, timestamp=None, payload=None):
        if is_int_min(version, 1):
            self.version = version
        else:
            self.version = TOPOSTAT_MESSAGE_VERSION
        self.auth = auth
        self.timestamp = timestamp  # python datetime UTC timestamp
        self.payload = payload

    def from_json(self, json_obj: dict):
        """creates an instance from a JSON dict"""

        try:
            self.version = int(json_obj["version"])
            self.auth = json_obj["auth"]
            self.timestamp = datetime.strptime(
                json_obj["timestamp"], TOPOSTAT_MESSAGE_TIMESTAMP_FMT
            )
            self.payload = json_obj["payload"]
            return self
        except (KeyError, ValueError):
            pass
        return None

    def json(self) -> dict:
        """returns a JSON object representation of the instance"""

        if self.check():
            return {
                "version": self.version,
                "auth": self.auth,
                "timestamp": self.timestamp.strftime(TOPOSTAT_MESSAGE_TIMESTAMP_FMT),
                "payload": self.payload,
            }
        return None

    def gen_auth(self, auth_key: str) -> bool:
        """
        generates the instances authentication string with the specified
        authentication key
        """

        if auth_key is None or not isinstance(auth_key, str):
            return False
        if not is_datetime(self.timestamp):
            self.timestamp = datetime.utcnow()
        salt = self.timestamp.strftime(TOPOSTAT_MESSAGE_TIMESTAMP_FMT)
        self.auth = hashlib.sha512((salt + auth_key).encode()).hexdigest()
        return True

    def check_auth(self, auth_key: str) -> bool:
        """
        validates the instances authentication string with the specified
        authentication key
        """

        if auth_key is None or not isinstance(auth_key, str):
            return False
        if not self.check():
            return False
        if not isinstance(self.auth, str):
            return False
        salt = self.timestamp.strftime(TOPOSTAT_MESSAGE_TIMESTAMP_FMT)
        auth = hashlib.sha512((salt + auth_key).encode()).hexdigest()
        if self.auth == auth:
            return True
        return False

    def check(self) -> bool:
        """performs an instance variable type and value check"""

        if (
            is_int_min(self.version, 1)
            and self.version == TOPOSTAT_MESSAGE_VERSION
            and is_str_no_empty(self.auth)
            and isinstance(self.timestamp, datetime)
            and isinstance(self.payload, list)
        ):
            return True
        return False

    # add a json payload
    def add_payload(self, payload: list) -> bool:
        """adds a payload to the instance"""

        if is_list_no_empty(payload):
            try:
                self.payload = json.loads(json.dumps(payload))
                return True
            except JSONDecodeError:
                pass
        return False
