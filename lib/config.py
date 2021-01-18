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
import lib.check as check


class Config:
    def __init__(self):
        self.default_variables()

    def default_variables(self):
        self.config_section = None
        self.progname = None
        self.progname_long = None
        self.config_lists = [
            "config_lists",
            "config_bools",
            "config_ints",
            "config_no_show",
            "config_no_overwrite",
        ]
        self.config_bools = []
        self.config_ints = []
        self.config_no_overwrite = [
            "config_section" "config_bools",
            "config_ints",
            "config_no_show",
            "config_no_overwrite",
            "progname",
            "progname_long",
        ]
        self.config_no_show = []

    def append_var_list(self, list, vars):
        if check.is_list(list):
            if check.is_list_no_empty(vars):
                no_errs = True
                for var in vars:
                    if not check.is_str_no_empty(var):
                        no_errs = False
                if no_errs:
                    list += vars
                    return True
        return False

    def check(self):
        return self.default_check()

    def default_check(self):
        if (
            check.is_list(self.config_bools)
            and check.is_list(self.config_ints)
            and check.is_list_no_empty(self.config_lists)
            and check.is_list_no_empty(self.config_no_overwrite)
            and check.is_list(self.config_no_show)
        ):
            for var in self.__dict__:
                if var in self.config_lists:
                    if not check.is_list(self.__dict__[var]):
                        return False
                    for listvar in self.__dict__[var]:
                        if not check.is_str_no_empty(listvar):
                            return False
                elif var in self.config_bools:
                    if not check.is_bool(self.__dict__[var]):
                        return False
                elif var in self.config_ints:
                    if not check.is_int(self.__dict__[var]):
                        return False
                elif check.is_str(self.__dict__[var]):
                    continue
                else:
                    return False
            return True
        return False

    def no_show_vars(self, vars):
        return self.append_var_list(self.config_no_show, vars)

    def no_overwrite_vars(self, vars):
        return self.append_var_list(self.config_no_overwrite, vars)

    def bool_vars(self, vars):
        return self.append_var_list(self.config_bools, vars)

    def int_vars(self, vars):
        return self.append_var_list(self.config_ints, vars)


class ServerConfig(Config):
    def __init__(self):
        self.default_variables()
        self.bool_vars(["run", "verbose", "debug", "server_no_ipv6", "server_no_ipv4"])
        self.int_vars(
            ["server_port_ipv6", "server_port_ipv4", "socket_recv_timeout_ms"]
        )
        self.no_overwrite_vars(["run", "default_config_file"])
        self.no_show_vars(["auth_key"])

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
        self.config_file = ""

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


class ClientConfig(Config):
    def __init__(self):
        self.default_variables()
        self.bool_vars(["verbose", "debug"])
        self.int_vars(["server_port", "connection_timeout"])
        self.no_overwrite_vars(["default_config_file", "server_address_type"])
        self.no_show_vars(["auth_key"])

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
        self.config_file = ""

        # server connection
        self.server_address_type = ""
        self.server_address = "127.0.0.1"
        self.server_port = 5678
        self.socket_address_str = ""
        self.connection_timeout = 15

        # authentication
        self.auth_key = ""

        # junit xml
        self.junit_xml = ""


def read_config_file(config_file, conf, log):
    last_var = None
    cp = ConfigParser()
    try:
        cp.read(config_file)
        for var, val in cp[conf.config_section].items():
            if var in conf.__dict__:
                if not var in conf.config_no_overwrite:
                    if not val is None:
                        if var in conf.config_lists:
                            log.debug("configure list attempt conf.{}".format(var))

                        elif var in conf.config_bools:
                            conf.__dict__[var] = cp[conf.config_section].getboolean(var)
                            if var in conf.config_no_show:
                                log.debug(
                                    "conf.{} = cfg[{}][{}] = *** (bool)".format(
                                        var, conf.config_section, var
                                    )
                                )
                            else:
                                log.debug(
                                    "conf.{} = cfg[{}][{}] = {} (bool)".format(
                                        var,
                                        conf.config_section,
                                        var,
                                        cp[conf.config_section].getboolean(var),
                                    )
                                )

                        elif var in conf.config_ints:
                            conf.__dict__[var] = cp[conf.config_section].getint(var)
                            if var in conf.config_no_show:
                                log.debug(
                                    "conf.{} = cfg[{}][{}] = *** (int)".format(
                                        var, conf.config_section, var
                                    )
                                )
                            else:
                                log.debug(
                                    "conf.{} = cfg[{}][{}] = {} (int)".format(
                                        var,
                                        conf.config_section,
                                        var,
                                        cp[conf.config_section].getint(var),
                                    )
                                )

                        elif check.is_str_no_empty(var):
                            conf.__dict__[var] = val
                            if var in conf.config_no_show:
                                log.debug(
                                    "conf.{} = cfg[{}][{}] = *** (str)".format(
                                        var, conf.config_section, var, val
                                    )
                                )
                            else:
                                log.debug(
                                    "conf.{} = cfg[{}][{}] = {} (str)".format(
                                        var, conf.config_section, var, val
                                    )
                                )
                        else:
                            log.debug(
                                "cfg[{}] type invalid {}".format(
                                    var, type(cp[conf.config_section][var])
                                )
                            )
                    last_var = var
                else:
                    log.debug("overwrite attempt conf.{}".format(var))
            else:
                log.debug("no such config var {}".format(var))
        log.info("read configuration file {}".format(config_file))
    except:
        if check.is_str_no_empty(last_var):
            log.err(
                "last successfully parsed variable was cfg[{}][{}]".format(
                    conf.config_section, last_var
                )
            )
        log.abort("failed to read config file {}".format(config_file))
    if not conf.check():
        log.debug("config check failed")
        return False
    return True
