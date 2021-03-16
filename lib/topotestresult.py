#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool TopotestResult"""


#
# NetDEF FRR Topotest Results Statistics Tool TopotestResult
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


from datetime import datetime

# third party library imports
from junitparser import Failure, Skipped, TestCase


from lib.check import is_int_min, is_str_no_empty, is_float_min


TOPOSTAT_TTR_VERSION_1 = 1
# TODO: bump up version number to '2' as soon as server is capable of handling it
TOPOSTAT_TTR_VERSION_2 = 1
TOPOSTAT_TTR_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S.%f"
TOPOSTAT_TTR_PASSED = "passed"
TOPOSTAT_TTR_SKIPPED = "skipped"
TOPOSTAT_TTR_FAILED = "failed"


class TopotestResult:
    def __init__(
        self,
        name=None,
        result=None,
        time=None,
        host=None,
        timestamp=None,  # python datetime UTC timestamp
        plan=None,
        build=None,
        job=None,
        version=None,  # keep version number at end of argument list
    ):
        if version is None or not isinstance(version, int):
            self.version = TOPOSTAT_TTR_VERSION_1
        else:
            self.version = version
        self.name = name
        self.result = result
        self.time = time
        self.host = host
        self.timestamp = timestamp  # python datetime UTC timestamp
        self.plan = plan
        self.build = build
        self.job = job

    def json(self) -> dict:
        """returns a JSON object representation of the instance"""

        if self.check():
            return {
                "version": self.version,
                "name": self.name,
                "result": self.result,
                "time": str(self.time),
                "host": self.host,
                "timestamp": self.timestamp.strftime(TOPOSTAT_TTR_TIMESTAMP_FMT),
                "plan": self.plan,
                "build": str(self.build),
                "job": self.job,
            }
        return None

    def from_json(self, json_dict: dict):
        try:
            if json_dict["version"] != TOPOSTAT_TTR_VERSION_1:
                return None
            self.name = json_dict["name"]
            self.result = json_dict["result"]
            self.time = float(json_dict["time"])
            self.host = json_dict["host"]
            self.timestamp = datetime.strptime(
                str(json_dict["timestamp"]), TOPOSTAT_TTR_TIMESTAMP_FMT
            )
            self.plan = json_dict["plan"]
            self.build = int(json_dict["build"])
            self.job = json_dict["job"]
        except Exception:
            return None
        if not self.check():
            return None
        return self

    def from_case(self, case, host, plan, build, job):
        if (
            isinstance(case, TestCase)
            and is_str_no_empty(host)
            and is_str_no_empty(plan)
            and is_int_min(build, 1)
            and is_str_no_empty(job)
        ):
            self.version = TOPOSTAT_TTR_VERSION_1
            self.name = str(case.classname) + "." + str(case.name)
            if case.result:
                # junit parser version switch
                if isinstance(case.result, list):
                    # junitparser v2.X
                    if isinstance(case.result[0], Failure):
                        self.result = TOPOSTAT_TTR_FAILED
                    elif isinstance(case.result[0], Skipped):
                        self.result = TOPOSTAT_TTR_SKIPPED
                else:
                    # junitparser v1.X
                    if isinstance(case.result, Failure):
                        self.result = TOPOSTAT_TTR_FAILED
                    elif isinstance(case.result, Skipped):
                        self.result = TOPOSTAT_TTR_SKIPPED
            else:
                self.result = TOPOSTAT_TTR_PASSED
            self.time = float(case.time)
            self.host = host
            self.timestamp = datetime.utcnow()  # UTC timestamp
            self.plan = plan
            self.build = build
            self.job = job
            return self
        return None

    def check(self) -> bool:
        if (
            is_str_no_empty(self.name)
            # this fixes the client sending skipped bamboo build jobs
            and self.name.strip() != "skipped.skipped"
            and is_str_no_empty(self.result)
            and self.result
            in [TOPOSTAT_TTR_PASSED, TOPOSTAT_TTR_FAILED, TOPOSTAT_TTR_SKIPPED]
            and is_float_min(self.time, 0.0)
        ):
            if (
                is_str_no_empty(self.host)
                and isinstance(self.timestamp, datetime)
                and is_str_no_empty(self.plan)
                and is_int_min(self.build, 1)
                and is_str_no_empty(self.job)
            ):
                if (
                    is_int_min(self.version, 1)
                    and self.version == TOPOSTAT_TTR_VERSION_1
                ):
                    return True
        return False

    def passed(self) -> bool:
        if is_str_no_empty(self.result) and self.result == TOPOSTAT_TTR_PASSED:
            return True
        return False

    def failed(self) -> bool:
        if is_str_no_empty(self.result) and self.result == TOPOSTAT_TTR_FAILED:
            return True
        return False

    def skipped(self) -> bool:
        if is_str_no_empty(self.result) and self.result == TOPOSTAT_TTR_SKIPPED:
            return True
        return False


# TODO: bump up version number as soon as server is ready
class TopotestResult_v2:
    def __init__(
        self,
        name=None,
        result=None,
        time=None,
        host=None,
        timestamp=None,  # python datetime UTC timestamp
        plan=None,
        build=None,
        job=None,
        os=None,
        arch=None,
        kvers=None,
        version=None,  # keep version number at end of argument list
    ):
        if version is None or not isinstance(version, int):
            self.version = TOPOSTAT_TTR_VERSION_2
        else:
            self.version = version
        self.name = name
        self.result = result
        self.time = time
        self.host = host
        self.timestamp = timestamp  # python datetime UTC timestamp
        self.plan = plan
        self.build = build
        self.job = job
        self.os = os
        self.arch = arch
        self.kvers = kvers

    def json(self) -> dict:
        """returns a JSON object representation of the instance"""

        if self.check():
            return {
                "version": self.version,
                "name": self.name,
                "result": self.result,
                "time": str(self.time),
                "host": self.host,
                "timestamp": self.timestamp.strftime(TOPOSTAT_TTR_TIMESTAMP_FMT),
                "plan": self.plan,
                "build": str(self.build),
                "job": self.job,
                "os": self.os,
                "arch": self.arch,
                "kvers": self.kvers,
            }
        return None

    def from_json(self, json_dict: dict):
        try:
            if json_dict["version"] != TOPOSTAT_TTR_VERSION_2:
                return None
            self.name = json_dict["name"]
            self.result = json_dict["result"]
            self.time = float(json_dict["time"])
            self.host = json_dict["host"]
            self.timestamp = datetime.strptime(
                str(json_dict["timestamp"]), TOPOSTAT_TTR_TIMESTAMP_FMT
            )
            self.plan = json_dict["plan"]
            self.build = int(json_dict["build"])
            self.job = json_dict["job"]
            self.os = json_dict["os"]
            self.arch = json_dict["arch"]
            self.kvers = json_dict["kvers"]
        except Exception:
            return None
        if not self.check():
            return None
        return self

    def from_case(self, case, host, plan, build, job, os, arch, kvers):
        if (
            isinstance(case, TestCase)
            and is_str_no_empty(host)
            and is_str_no_empty(plan)
            and is_int_min(build, 1)
            and is_str_no_empty(job)
        ):
            if is_str_no_empty(os) and is_str_no_empty(arch) and is_str_no_empty(kvers):
                self.version = TOPOSTAT_TTR_VERSION_2
                self.name = str(case.classname) + "." + str(case.name)
                if case.result:
                    # junit parser version switch
                    if isinstance(case.result, list):
                        # junitparser v2.X
                        if isinstance(case.result[0], Failure):
                            self.result = TOPOSTAT_TTR_FAILED
                        elif isinstance(case.result[0], Skipped):
                            self.result = TOPOSTAT_TTR_SKIPPED
                    else:
                        # junitparser v1.X
                        if isinstance(case.result, Failure):
                            self.result = TOPOSTAT_TTR_FAILED
                        elif isinstance(case.result, Skipped):
                            self.result = TOPOSTAT_TTR_SKIPPED
                else:
                    self.result = TOPOSTAT_TTR_PASSED
                self.time = float(case.time)
                self.host = host
                self.timestamp = datetime.utcnow()  # UTC timestamp
                self.plan = plan
                self.build = build
                self.job = job
                self.os = os
                self.arch = arch
                self.kvers = kvers
                return self
        return None

    def check(self) -> bool:
        if (
            is_str_no_empty(self.name)
            # this fixes the client sending skipped bamboo build jobs
            and self.name.strip() != "skipped.skipped"
            and is_str_no_empty(self.result)
            and self.result
            in [TOPOSTAT_TTR_PASSED, TOPOSTAT_TTR_FAILED, TOPOSTAT_TTR_SKIPPED]
            and is_float_min(self.time, 0.0)
        ):
            if (
                is_str_no_empty(self.host)
                and isinstance(self.timestamp, datetime)
                and is_str_no_empty(self.plan)
                and is_int_min(self.build, 1)
                and is_str_no_empty(self.job)
            ):
                if (
                    is_str_no_empty(self.os)
                    and is_str_no_empty(self.arch)
                    and is_str_no_empty(self.kvers)
                    and is_int_min(self.version, 1)
                    and self.version == TOPOSTAT_TTR_VERSION_2
                ):
                    return True
        return False

    def passed(self) -> bool:
        if is_str_no_empty(self.result) and self.result == TOPOSTAT_TTR_PASSED:
            return True
        return False

    def failed(self) -> bool:
        if is_str_no_empty(self.result) and self.result == TOPOSTAT_TTR_FAILED:
            return True
        return False

    def skipped(self) -> bool:
        if is_str_no_empty(self.result) and self.result == TOPOSTAT_TTR_SKIPPED:
            return True
        return False
