#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool ZeroMQ Utility Functions"""


#
# NetDEF FRR Topotest Results Statistics Tool ZeroMQ Utility Functions
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
import re
import socket

# proprietary library imports
from lib.check import is_str_no_empty
from lib.config import ClientConfig
from lib.logger import Logger


def compose_zmq_client_address_str(conf: ClientConfig, log: Logger) -> str:
    """
    composes a ZeroMQ socket address string from information retrieved from the
    specified ClientConfig object
    """

    server_address_types = ["IPV4", "IPV6", "DNS"]

    if not isinstance(conf, ClientConfig) or not isinstance(log, Logger):
        return None

    if not is_str_no_empty(conf.server_address_type):
        if ":" in conf.server_address:
            conf.server_address_type = "IPV6"
        elif re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", conf.server_address):
            conf.server_address_type = "IPV4"
        else:
            conf.server_address_type = "DNS"
    log.debug("conf.server_address_type = {}".format(conf.server_address_type))

    if conf.server_address_type in server_address_types:
        if conf.server_address_type == "IPV6":
            conf.socket_address_str = "tcp://[{}]:{}".format(
                conf.server_address, conf.server_port
            )
        elif conf.server_address_type == "IPV4":
            conf.socket_address_str = "tcp://{}:{}".format(
                conf.server_address, conf.server_port
            )
        else:
            dns_addr = conf.server_address
            try:
                conf.server_address = socket.gethostbyname(dns_addr)
            except OSError:
                log.err("failed to resolve DNS server address {}".format(dns_addr))
                return None
            log.debug(
                "conf.server_address = {} (DNS resolved {})".format(
                    conf.server_address, dns_addr
                )
            )
            conf.server_address_type = None
            log.debug("conf.server_address_type = None")
            log.info(
                "resolved DNS server address {} to ip address {}".format(
                    dns_addr, conf.server_address
                )
            )
            return compose_zmq_client_address_str(conf, log)
    else:
        log.err("invalid server address type {}".format(conf.server_address_type))
        return None

    log.debug("conf.socket_address_str = {}".format(conf.socket_address_str))
    return conf.socket_address_str
