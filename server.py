#!/usr/bin/env python3


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


import os
import sys
import signal
import argparse
import sqlite3

import zmq

from lib.topostat import Logger, Message, TopotestResult, compose_zmq_address_str
from lib.config import ServerConfig, read_config_file


# process received results and store results in database
def process_received_results(results, conn, conf, log):

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

        # convert to TopotestResult object
        try:
            result = TopotestResult().from_json(json_obj)
        except:
            results_invalid += 1
            continue
        if result is None:
            results_invalid += 1
            continue

        # check integrity of converted object
        if result.check():
            results_valid += 1
            agent = result.host

            # insert result into database
            try:
                result.insert_into(conn, conf.results_table)
            except:
                log.err(
                    "failed to insert results into table {} in database {}".format(
                        conf.results_table, conf.sqlite3_db
                    )
                )
        else:
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
    ap.add_argument("-v", "--verbose", help="verbosity", action="store_true")
    ap.add_argument("-d", "--debug", help="debug messages", action="store_true")
    ap.add_argument("-c", "--config", help="configuration file")
    ap.add_argument("-a", "--address", help="server address")
    ap.add_argument("-p", "--port", help="server tcp port")
    ap.add_argument("-k", "--key", help="authentication key")
    ap.add_argument("-b", "--database", help="sqlite3 database file")
    ap.add_argument("-l", "--log", help="log file")
    try:
        args = vars(ap.parse_args())
        conf_to_args = {
            "verbose": "verbose",
            "debug": "debug",
            "config_file": "config",
            "server_address": "address",
            "server_port": "port",
            "auth_key": "key",
            "sqlite3_db": "database",
            "log_file": "log",
        }
        for conf_var, arg_val in conf_to_args.items():
            if args[arg_val] is not None:
                if conf_var in conf.bools():
                    if args[arg_val]:
                        conf.__dict__[conf_var] = True
                        log.debug(
                            "conf.{} = args[{}] = True (boolean)".format(
                                conf_var, arg_val
                            )
                        )
                else:
                    conf.__dict__[conf_var] = args[arg_val]
                    log.debug(
                        "conf.{} = args[{}] = {}".format(
                            conf_var, arg_val, args[arg_val]
                        )
                    )
    except:
        log.abort("failed to parse arguments")


def main():
    # initialize config
    conf = ServerConfig()

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
    if conf.config_file is not None:
        read_config_file(conf.config_file, conf, log)
    elif os.path.isfile(conf.default_config_file):
        read_config_file(conf.default_config_file, conf, log)
    else:
        log.warn("running with potentially unsafe default configuration")

    # parse cli arguments
    parse_cli_arguments(conf, log)

    # start log buffer output
    log.info("writing to log file {}".format(conf.log_file))
    log.start()

    # compose ZeroMQ server socket address string
    try:
        compose_zmq_address_str(conf, log)
    except:
        log.abort("failed to compose ZeroMQ server socket address string")

    if conf.server_address_type == "DNS":
        log.abort("ZeroMQ does not allow to bind server socket to a DNS addresses")

    # connect to sqlite3 db
    try:
        conn = sqlite3.connect(conf.sqlite3_db)
        db = conn.cursor()
    except:
        log.abort("failed to connect to database {}".format(conf.sqlite3_db))

    # create results table if it does not exist
    try:
        db.execute(
            "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}'".format(
                conf.results_table
            )
        )
    except:
        log.abort(
            "unable to query if table {} exists in database {}".format(
                conf.results_table, conf.sqlite3_db
            )
        )
    if db.fetchone()[0] == 0:
        try:
            TopotestResult().create_table(conn, conf.results_table)
            log.info(
                "created table {} in database {}".format(
                    conf.results_table, conf.sqlite3_db
                )
            )
        except:
            conn.close()
            log.abort(
                "failed to create table {} in database {}".format(
                    conf.results_table, conf.sqlite3_db
                )
            )
    log.info(
        "using table {} in database {}".format(conf.results_table, conf.sqlite3_db)
    )

    # create ZeroMQ context and bind to socket
    context = zmq.Context()
    sock = context.socket(zmq.PULL)
    if conf.server_address_type == "IPV6":
        sock.setsockopt(zmq.IPV6, True)
    try:
        sock.bind(conf.socket_address_str)
        log.info(
            "bound ZeroMQ PULL socket to address {}".format(conf.socket_address_str)
        )
    except:
        conn.close()
        log.abort(
            "failed to bind ZeroMQ PULL socket to address {}".format(
                conf.socket_address_str
            )
        )

    # signal handling
    signal.signal(signal.SIGINT, signal_handler_sigint)
    signal.signal(signal.SIGTERM, signal_handler_sigterm)

    # main loop, process incoming topotest results
    while conf.run:
        # receive json object with test results
        try:
            json_msg = sock.recv_json()
        except TerminationSignalReceived:
            continue
        except:
            log.warn("failed to receive ZeroMQ message")
            continue

        # parse received message
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
        process_received_results(msg.payload, conn, conf, log)

    # closing socket and terminating ZeroMQ context
    sock.close()
    context.term()
    log.info(
        "closed ZeroMQ PULL socket bound to address {}".format(conf.socket_address_str)
    )

    # closing database connection
    conn.close()
    log.info("closed connection to database {}".format(conf.sqlite3_db))

    # exit
    log.ok("terminating")
    log.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
