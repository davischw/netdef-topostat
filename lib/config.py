#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool Configurations"""


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


# third party library imports
from configparser import ConfigParser

# proprietary library imports
from lib.check import (
    is_int,
    is_bool,
    is_str,
    is_str_no_empty,
    is_list,
    is_list_no_empty,
)
from lib.logger import Logger


class Config:
    """generic configuration base class"""

    def __init__(self):
        self.config_section = None
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
            "config_section",
            "config_bools",
            "config_ints",
            "config_no_show",
            "config_no_overwrite",
        ]
        self.config_no_show = []

    def append_var_list(self, config_list, variables):
        if is_str_no_empty(config_list) and config_list in self.__dict__:
            if is_list(self.__dict__[config_list]):
                if is_list_no_empty(variables):
                    no_errs = True
                    for var in variables:
                        if not is_str_no_empty(var):
                            no_errs = False
                    if no_errs:
                        self.__dict__[config_list] += variables
                        return True
        return False

    def check(self):
        return self.default_check()

    def default_check(self):
        if (
            is_list(self.config_bools)
            and is_list(self.config_ints)
            and is_list_no_empty(self.config_lists)
            and is_list_no_empty(self.config_no_overwrite)
            and is_list(self.config_no_show)
        ):
            for var in self.__dict__:
                if var in self.config_lists:
                    if not is_list(self.__dict__[var]):
                        return False
                    for listvar in self.__dict__[var]:
                        if not is_str_no_empty(listvar):
                            return False
                elif var in self.config_bools:
                    if not is_bool(self.__dict__[var]):
                        return False
                elif var in self.config_ints:
                    if not is_int(self.__dict__[var]):
                        return False
                elif is_str(self.__dict__[var]):
                    continue
                else:
                    return False
            return True
        return False

    def no_show_vars(self, variables):
        return self.append_var_list("config_no_show", variables)

    def no_overwrite_vars(self, variables):
        return self.append_var_list("config_no_overwrite", variables)

    def bool_vars(self, variables):
        return self.append_var_list("config_bools", variables)

    def int_vars(self, variables):
        return self.append_var_list("config_ints", variables)


class ServerConfig(Config):
    """server configuration type"""

    def __init__(self):
        super().__init__()
        self.bool_vars(["run", "verbose", "debug", "server_no_ipv6", "server_no_ipv4"])
        self.int_vars(
            ["server_port_ipv6", "server_port_ipv4", "socket_recv_timeout_ms"]
        )
        self.no_overwrite_vars(
            ["progname", "progname_long", "run", "default_config_file"]
        )
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


class ClientConfig(Config):
    """client configuration type"""

    def __init__(self):
        super().__init__()
        self.bool_vars(["verbose", "debug"])
        self.int_vars(["server_port", "connection_timeout"])
        self.no_overwrite_vars(
            ["progname", "progname_long", "default_config_file", "server_address_type"]
        )
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
        self.sender_id = ""

        # authentication
        self.auth_key = ""

        # junit xml
        self.junit_xml = ""


class StatsConfig(Config):
    """statistics tool configuration type"""

    def __init__(self):
        super().__init__()
        self.bool_vars(["verbose", "debug", "no_txt_report", "no_html_report"])
        self.no_overwrite_vars(["progname", "progname_long", "default_config_file"])

        # config file section
        self.config_section = "stats"

        # program name
        self.progname = "topostat-stats"
        self.progname_long = (
            "NetDEF FRR Topotest Results Statistics Tool Statistics Grabber"
        )

        # verbosity
        self.verbose = True
        self.debug = True

        # log
        self.log_file = "/var/log/topostat/stats.log"

        # config file
        self.default_config_file = "/etc/topostat.conf"
        self.config_file = ""

        # sqlite3 database
        self.sqlite3_db = "/home/topostat/topotests.db"
        self.results_table = "testresults"

        # txt report
        self.no_txt_report = False
        self.txt_report_file = "/home/topostat/report.txt"

        # html report
        self.no_html_report = True
        self.html_report_file = "/home/topostat/report.html"


class DatabaseConfig(Config):
    """database configuration type"""

    def __init__(self):
        super().__init__()
        self.int_vars(["mysql_server_port", "postgresql_server_port"])
        self.no_show_vars(
            ["database_connection_str", "mysql_password", "postgresql_password"]
        )

        # config file section
        self.config_section = "database"

        # database type
        self.database_type = ""

        # database string
        self.database_str = ""
        self.database_connection_str = ""

        # sqlite3
        self.sqlite3_database_file = "/home/topostat/topotests.db"

        # mysql
        self.mysql_username = "topostat"
        self.mysql_password = ""
        self.mysql_server_address = "127.0.0.1"
        self.mysql_server_port = 3306
        self.mysql_database = "topostat"

        # postgresql
        self.postgresql_username = "topostat"
        self.postgresql_password = ""
        self.postgresql_server_address = "127.0.0.1"
        self.postgresql_server_port = 5432
        self.postgresql_database = "topostat"


def read_config_file(config_file: str, conf: Config, log: Logger) -> bool:
    """read in configuration values from a specified configuration file"""

    last_var = None
    confp = ConfigParser()
    try:
        confp.read(config_file)
        for var, val in confp[conf.config_section].items():
            if var in conf.__dict__:
                if not var in conf.config_no_overwrite:
                    if not val is None:
                        if var in conf.config_lists:
                            log.debug("configure list attempt conf.{}".format(var))

                        elif var in conf.config_bools:
                            conf.__dict__[var] = confp[conf.config_section].getboolean(
                                var
                            )
                            if var in conf.config_no_show:
                                log.debug(
                                    "conf.{var} = cfg[{}][{var}] = *** (bool)".format(
                                        conf.config_section, var=var
                                    )
                                )
                            else:
                                log.debug(
                                    "conf.{var} = cfg[{}][{var}] = {} (bool)".format(
                                        conf.config_section,
                                        confp[conf.config_section].getboolean(var),
                                        var=var,
                                    )
                                )

                        elif var in conf.config_ints:
                            conf.__dict__[var] = confp[conf.config_section].getint(var)
                            if var in conf.config_no_show:
                                log.debug(
                                    "conf.{var} = cfg[{}][{var}] = *** (int)".format(
                                        conf.config_section, var=var
                                    )
                                )
                            else:
                                log.debug(
                                    "conf.{var} = cfg[{}][{var}] = {} (int)".format(
                                        conf.config_section,
                                        confp[conf.config_section].getint(var),
                                        var=var,
                                    )
                                )

                        elif is_str_no_empty(var):
                            conf.__dict__[var] = val
                            if var in conf.config_no_show:
                                log.debug(
                                    "conf.{var} = cfg[{}][{var}] = *** (str)".format(
                                        conf.config_section, var=var
                                    )
                                )
                            else:
                                log.debug(
                                    "conf.{var} = cfg[{}][{var}] = {} (str)".format(
                                        conf.config_section, val, var=var
                                    )
                                )
                        else:
                            log.debug(
                                "cfg[{}] type invalid {}".format(
                                    var, type(confp[conf.config_section][var])
                                )
                            )
                    last_var = var
                else:
                    log.debug("overwrite attempt conf.{}".format(var))
            else:
                log.debug("no such config var {}".format(var))
        log.info("read configuration file {}".format(config_file))
    except Exception:
        if is_str_no_empty(last_var):
            log.err(
                "last successfully parsed variable was cfg[{}][{}]".format(
                    conf.config_section, last_var
                )
            )
        log.abort("failed to read config file {}".format(config_file))
        return False
    return True


def read_config_from_cli_args(
    args: dict, conf: Config, mapping: dict, log: Logger
) -> bool:
    """
    read in configuration values from command line arguments in accordance with
    the specified mapping
    """

    for conf_var, arg_val in mapping.items():
        if not conf_var in conf.config_no_overwrite:
            if not args[arg_val] is None:
                if conf_var in conf.config_lists:
                    log.debug("configure list attempt conf.{}".format(conf_var))
                    return False

                if conf_var in conf.config_bools:
                    if args[arg_val]:
                        conf.__dict__[conf_var] = True
                        if not conf_var in conf.config_no_show:
                            log.debug(
                                "conf.{} = args[{}] = True (bool)".format(
                                    conf_var, arg_val
                                )
                            )
                elif conf_var in conf.config_ints:
                    conf.__dict__[conf_var] = int(args[arg_val])
                    if conf_var in conf.config_no_show:
                        log.debug(
                            "conf.{} = args[{}] = *** (int)".format(conf_var, arg_val)
                        )
                    else:
                        log.debug(
                            "conf.{} = args[{}] = {} (int)".format(
                                conf_var, arg_val, int(args[arg_val])
                            )
                        )
                elif is_str_no_empty(args[arg_val]):
                    conf.__dict__[conf_var] = args[arg_val]
                    if conf_var in conf.config_no_show:
                        log.debug(
                            "conf.{} = args[{}] = *** (str)".format(conf_var, arg_val)
                        )
                    else:
                        log.debug(
                            "conf.{} = args[{}] = {} (str)".format(
                                conf_var, arg_val, args[arg_val]
                            )
                        )
                else:
                    log.debug(
                        "args[{}] type invalid {}".format(arg_val, type(args[arg_val]))
                    )
                    return False
        else:
            log.debug("overwrite attempt conf.{}".format(conf_var))
            return False
    return True
