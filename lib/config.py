#!/usr/bin/env python3


#
# NetDEF FRR Topotest Results Statistics Tool Configurations
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


from configparser import ConfigParser


class ServerConfig:
    def __init__(self):
        # config file section
        self.config_section = "server"

        # program name
        self.progname = "topostat-server"
        self.progname_long = "NetDEF FRR Topotest Results Statistics Tool Server"

        # main loop condition
        self.run = True

        # verbosity
        self.verbose = True
        self.debug = False

        # log file
        self.log_file = "/var/log/topostat/server.log"

        # config file
        self.default_config_file = "/etc/topostat.conf"
        self.config_file = None

        # server ipv6 socket
        self.server_no_ipv6 = False
        self.server_address_ipv6 = "::1"
        self.server_port_ipv6 = 5678
        self.socket_address_ipv6_str = ""

        # server ipv4 socket
        self.server_no_ipv4 = False
        self.server_address_ipv4 = "127.0.0.1"
        self.server_port_ipv4 = 5678
        self.socket_address_ipv4_str = ""

        # sockets receive timeout in milliseconds
        self.socket_recv_timeout_ms = 100

        # authentication
        self.auth_key = ""

        # sqlite3 database
        self.sqlite3_db = "/home/topostat/topotests.db"
        self.results_table = "testresults"

    # returns list of boolean config values
    def bools(self):
        return ["verbose", "debug", "server_no_ipv4", "server_no_ipv6"]


class ClientConfig:
    def __init__(self):
        # config file section
        self.config_section = "client"

        # program name
        self.progname = "topostat-client"
        self.progname_long = "NetDEF FRR Topotest Results Statistics Tool Client"

        # verbosity
        self.verbose = False
        self.debug = False

        # log
        self.log_file = "/var/log/topostat/client.log"

        # config file
        self.default_config_file = "/etc/topostat.conf"
        self.config_file = None

        # server connection
        self.server_address_type = None
        self.server_address = "127.0.0.1"
        self.server_port = 5678
        self.socket_address_str = ""
        self.connection_timeout = 15

        # authentication
        self.auth_key = ""

        # junit xml
        self.junit_xml = ""

    # returns list of boolean config values
    def bools(self):
        return ["verbose", "debug"]


def read_config_file(config_file, conf, log):
    cp = ConfigParser()
    try:
        cp.read(config_file)
        for var, val in cp[conf.config_section].items():
            if var in conf.__dict__:
                if var in conf.bools():
                    conf.__dict__[var] = cp[conf.config_section].getboolean(var)
                    log.debug(
                        "conf.{} = cfg[{}][{}] = {} (boolean)".format(
                            var,
                            conf.config_section,
                            var,
                            cp[conf.config_section].getboolean(var),
                        )
                    )
                elif var == "auth_key":
                    conf.__dict__[var] = val
                    log.debug(
                        "conf.{} = cfg[{}][{}] = ***auth_key***".format(
                            var, conf.config_section, var
                        )
                    )
                else:
                    conf.__dict__[var] = val
                    log.debug(
                        "conf.{} = cfg[{}][{}] = {}".format(
                            var, conf.config_section, var, val
                        )
                    )
        log.info("read configuration file {}".format(config_file))
    except:
        log.abort("failed to read config file {}".format(config_file))
