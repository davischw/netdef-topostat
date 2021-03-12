#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool System Information Utilities"""


#
# NetDEF FRR Topotest Results Statistics Tool System Information Utilities
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
import os

# proprietary library imports
from lib.check import is_str_no_empty


TOPOSTAT_SYSINFO_RELEASE_FILE = "/etc/os-release"


def is_linux():
    """
    parses unix name output to check if running on GNU/Linux. returns True if
    running on Linux, returns False otherwise.
    """

    try:
        if os.uname()[0] == "Linux":
            return True
    except Exception:
        pass
    return False


def linux_kernel_version_str():
    """parses uname output and returns the linux kernel version as a string"""

    if is_linux():
        try:
            lkv_str = os.uname()[2].split("-")[0]
            if is_str_no_empty(lkv_str):
                return lkv_str
        except Exception:
            pass
    return None


def linux_architecture_str():
    """parses uname output and returns a generalized architecure name string"""

    if is_linux():
        try:
            mach = os.uname().machine
            if is_str_no_empty(mach):
                if mach in ["amd64", "x86_64", "x86-64"]:
                    return "amd64"
                if mach in ["i386", "i486", "i586", "i686", "x86"]:
                    return "i386"
                if mach in ["aarch64", "aarch64_be", "armv8b", "armv8l"]:
                    return "arm8"
                if mach in ["arm", "armhf", "armv7l"]:
                    return "arm7"
        except Exception:
            pass
    return None


def linux_distribution_version_str():
    """
    parses the release file and returns a string containing the distribution
    name and version
    """

    distribution = None
    version = None
    try:
        if os.path.isfile(TOPOSTAT_SYSINFO_RELEASE_FILE):
            with open(TOPOSTAT_SYSINFO_RELEASE_FILE, "r") as release_file:
                release_info = release_file.readlines()
                release_file.close()
                for line in release_info:
                    line = line.strip("\n")
                    if "ID=debian" in line:
                        distribution = "Debian"
                        break
                    if "ID=ubuntu" in line:
                        distribution = "Ubuntu"
                        break
                for line in release_info:
                    line = line.strip("\n")
                    if "VERSION_ID=" in line:
                        version = line.split("=")[1].strip('"')
                        break
                if is_str_no_empty(distribution) and is_str_no_empty(version):
                    return distribution + " " + version
    except Exception:
        pass
    return None
