#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool Server"""


#
# NetDEF FRR Topotest Results Statistics Tool Server
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
import sys
import signal
import argparse

# third party library imports
import zmq
from sqlalchemy.exc import SQLAlchemyError

# proprietary library imports
from lib.logger import Logger
from lib.message import Message
from lib.topotestresult import TopotestResult
from lib.config import (
    ServerConfig,
    DatabaseConfig,
    read_config_file,
    read_config_from_cli_args,
)
from lib.check import is_str_no_empty
from lib.database import Database
from lib.dbutils import topotestresult_to_result


# process received results and store results in database
# TODO: [code] remove print statments
def process_received_results(results: list, database: Database, log: Logger):

    # check if received json payload is a list
    if not isinstance(results, list):
        log.warn("received json payload does not contain a list")
        return

    # check if received results list is empty
    if not results:
        log.warn("received empty list of test results")
        return

    # go through received list, convert and validate results
    results_valid = 0
    results_invalid = 0
    results_total = 0
    for json_obj in results:
        results_total += 1

        # convert json to TopotestResult object
        try:
            ttr = TopotestResult().from_json(json_obj)
        except:
            print("debug_1337: ttr.from_json")
            results_invalid += 1
            continue

        # convert json to TopotestResult object to Result datasbe object
        # TODO: [code] wrap in try except
        result = topotestresult_to_result(ttr, database)

        if result is None:
            print("debug_1338: topotestresult_to_result")
            results_invalid += 1
            continue

        # check integrity of converted object
        if result.check():
            results_valid += 1
            agent = result.agent.name

            # insert result into database
            try:
                database.session.add(result)
                database.session.commit()
            except SQLAlchemyError:
                print("debug_1340: insertion")
                log.err(
                    "failed to insert results into database {}".format(
                        database.conf.database_str
                    )
                )
        else:
            print("debug_1339: result.check")
            results_invalid += 1

    if results_valid > 0:
        log.info(
            "received {} test results ({} valid, {} invalid) from agent {}".format(
                results_total, results_valid, results_invalid, agent
            )
        )
    else:
        log.info(
            "received {} test results ({} valid, {} invalid)".format(
                results_total, results_valid, results_invalid
            )
        )


def parse_cli_arguments(conf, log):
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    ap.add_argument("-d", "--debug", help="debug messages", action="store_true")
    ap.add_argument("-c", "--config", help="configuration file")
    ap.add_argument(
        "-n6", "--no-ipv6", help="no ipv6 listen address", action="store_true"
    )
    ap.add_argument("-a6", "--ipv6-address", help="server ipv6 address")
    ap.add_argument("-p6", "--ipv6-port", help="server ipv6 tcp port")
    ap.add_argument(
        "-n4", "--no-ipv4", help="no ipv4 listen address", action="store_true"
    )
    ap.add_argument("-a4", "--ipv4-address", help="server ipv4 address")
    ap.add_argument("-p4", "--ipv4-port", help="server ipv4 tcp port")
    ap.add_argument("-k", "--key", help="authentication key")
    ap.add_argument("-l", "--log", help="log file")

    conf_to_args_map = {
        "verbose": "verbose",
        "debug": "debug",
        "config_file": "config",
        "server_no_ipv6": "no_ipv6",
        "server_address_ipv6": "ipv6_address",
        "server_port_ipv6": "ipv6_port",
        "server_no_ipv4": "no_ipv4",
        "server_address_ipv4": "ipv4_address",
        "server_port_ipv4": "ipv4_port",
        "auth_key": "key",
        "log_file": "log",
    }

    try:
        args = vars(ap.parse_args())
    except:
        log.abort("failed to parse arguments")

    try:
        lcfca_ret = read_config_from_cli_args(args, conf, conf_to_args_map, log)
    except:
        lcfca_ret = False

    if lcfca_ret:
        return True

    log.abort("failed to write cli argument values to config variables")
    return False  # abort is async!


def main():
    """server main function"""

    # initialize configs
    conf = ServerConfig()
    db_conf = DatabaseConfig()

    # initialize logger
    log = Logger(conf)

    # Custom exception to terminate server
    class TerminationSignalReceived(Exception):
        def __init__(self, sig):
            self.sig = sig

        def __str__(self):
            return repr(self.sig)

    # SIGINT signal handler
    def signal_handler_sigint(sig, frame):
        log.info("received signal SIGINT")
        conf.run = False
        raise (TerminationSignalReceived("SIGINT"))

    # SIGTERM signal handler
    def signal_handler_sigterm(sig, frame):
        log.info("received signal SIGTERM")
        conf.run = False
        raise (TerminationSignalReceived("SIGTERM"))

    # log start entry
    log.info("started {}".format(conf.progname_long))

    # read config file
    for arg in sys.argv:
        if sys.argv.index(arg) + 1 == len(sys.argv):
            break
        if arg in ("-c", "--config"):
            conf.config_file = sys.argv[sys.argv.index(arg) + 1]
    if is_str_no_empty(conf.config_file):
        read_config_file(conf.config_file, conf, log)
        read_config_file(conf.config_file, db_conf, log)
    elif os.path.isfile(conf.default_config_file):
        read_config_file(conf.default_config_file, conf, log)
        read_config_file(conf.config_file, db_conf, log)
    else:
        log.warn("running with potentially unsafe default configuration")

    # parse cli arguments
    parse_cli_arguments(conf, log)

    # start log buffer output (now we now which log file to write to)
    log.info("writing to log file {}".format(conf.log_file))
    log.start()

    # do a configuration check
    if not conf.check():
        log.abort("configuration check failed")
    elif not db_conf.check():
        log.abort("database configuration check failed")
    else:
        log.info("passed configuration check")

    # compose ZeroMQ server socket address strings
    if conf.server_no_ipv4 and conf.server_no_ipv6:
        log.abort("neither using ipv4 or ipv6")
    else:
        if not conf.server_no_ipv4:
            conf.socket_address_ipv4_str = "tcp://{}:{}".format(
                conf.server_address_ipv4, conf.server_port_ipv4
            )
            log.debug(
                "conf.socket_address_ipv4_str = {}".format(conf.socket_address_ipv4_str)
            )
        if not conf.server_no_ipv6:
            conf.socket_address_ipv6_str = "tcp://[{}]:{}".format(
                conf.server_address_ipv6, conf.server_port_ipv6
            )
            log.debug(
                "conf.socket_address_ipv6_str = {}".format(conf.socket_address_ipv6_str)
            )

    # create database instance
    db = Database()

    # apply database configuration
    if db.apply_config(db_conf):
        log.info("applied database configuration")
    else:
        log.abort("failed to apply database configuration")

    # connect to database
    if db.connect():
        log.info("connected to database {}".format(db.conf.database_str))
    else:
        log.abort("failed to connect to database")

    # create ZeroMQ contexts and bind to sockets
    if not conf.server_no_ipv6:
        context_ipv6 = zmq.Context()
        sock_ipv6 = context_ipv6.socket(zmq.PULL)
        sock_ipv6.setsockopt(zmq.RCVTIMEO, conf.socket_recv_timeout_ms)
        sock_ipv6.setsockopt(zmq.IPV6, True)
        try:
            sock_ipv6.bind(conf.socket_address_ipv6_str)
            log.info(
                "bound ZeroMQ PULL ipv6 socket to address {}".format(
                    conf.socket_address_ipv6_str
                )
            )
        except:
            db.close()
            log.abort(
                "failed to bind ZeroMQ PULL ipv6 socket to address {}".format(
                    conf.socket_address_ipv6_str
                )
            )
    if not conf.server_no_ipv4:
        context_ipv4 = zmq.Context()
        sock_ipv4 = context_ipv4.socket(zmq.PULL)
        sock_ipv4.setsockopt(zmq.RCVTIMEO, conf.socket_recv_timeout_ms)
        try:
            sock_ipv4.bind(conf.socket_address_ipv4_str)
            log.info(
                "bound ZeroMQ PULL ipv4 socket to address {}".format(
                    conf.socket_address_ipv4_str
                )
            )
        except:
            db.close()
            log.abort(
                "failed to bind ZeroMQ PULL ipv4 socket to address {}".format(
                    conf.socket_address_ipv4_str
                )
            )

    # signal handling
    signal.signal(signal.SIGINT, signal_handler_sigint)
    signal.signal(signal.SIGTERM, signal_handler_sigterm)

    # main loop, process incoming topotest results
    while conf.run:
        # receive json object with test results
        while conf.run:
            if not conf.server_no_ipv6:
                json_msg = None
                try:
                    json_msg = sock_ipv6.recv_json()
                    break
                except TerminationSignalReceived:
                    break
                except Exception:
                    pass
            if not conf.server_no_ipv4:
                json_msg = None
                try:
                    json_msg = sock_ipv4.recv_json()
                    break
                except TerminationSignalReceived:
                    break
                except Exception:
                    pass

        if conf.run and json_msg is None:
            log.warn("failed to receive ZeroMQ message")
            continue

        # parse received message
        if conf.run:
            msg = Message()
            try:
                msg.from_json(json_msg)
                if not msg.check_auth(conf.auth_key):
                    log.warn("failed to authenticate ZeroMQ message")
                    continue
            except:
                log.warn("failed to parse ZeroMQ message")
                continue
            # process received test results
            process_received_results(msg.payload, db, log)

    # closing sockets and terminating ZeroMQ contexts
    if not conf.server_no_ipv6:
        sock_ipv6.close()
        context_ipv6.term()
        log.info(
            "closed ZeroMQ PULL ipv6 socket bound to address {}".format(
                conf.socket_address_ipv6_str
            )
        )
    if not conf.server_no_ipv4:
        sock_ipv4.close()
        context_ipv4.term()
        log.info(
            "closed ZeroMQ PULL ipv4 socket bound to address {}".format(
                conf.socket_address_ipv4_str
            )
        )

    # closing database connection
    db.close()
    log.info("closed connection to database {}".format(db.conf.database_str))

    # exit
    log.success("terminating")
    log.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
