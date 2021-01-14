#!/usr/bin/env python3


#
# NetDEF FRR Topotest Results Statistics Tool Client
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
import argparse
from threading import Timer

from configparser import ConfigParser
from junitparser import JUnitXml, TestSuite, TestCase
import zmq

from lib.topostat import Logger, Message, TopotestResult, compose_zmq_client_address_str
from lib.config import ClientConfig, read_config_file


# Upload watchdog handler to terminate non-responsive ZeroMQ connect and send threads
def watchdog_handler(log):
    log.kill("upload watchdog timer expired")


# parse cli arguments
def parse_cli_arguments(conf, log):
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", help="verbosity", action="store_true")
    ap.add_argument("-d", "--debug", help="debug messages", action="store_true")
    ap.add_argument("-c", "--config", help="configuration file")
    ap.add_argument("-a", "--address", help="server address")
    ap.add_argument("-p", "--port", help="server tcp port")
    ap.add_argument("-k", "--key", help="authentication key")
    ap.add_argument("-f", "--file", help="junit xml file")
    ap.add_argument("-l", "--log", help="log file")
    try:
        args = vars(ap.parse_args())
        conf_to_args = {
            "verbose": "verbose",
            "debug": "debug",
            "server_address": "address",
            "server_port": "port",
            "auth_key": "key",
            "junit_xml": "file",
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
                elif conf_var == "auth_key":
                    conf.__dict__[conf_var] = args[arg_val]
                    log.debug(
                        "conf.{} = args[{}] = ***auth_key***".format(conf_var, arg_val)
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
    conf = ClientConfig()

    # initialize logger
    log = Logger(conf)

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

    # compose ZeroMQ server address string
    try:
        compose_zmq_client_address_str(conf, log)
    except:
        log.abort("failed to compose ZeroMQ server address string")

    # get bamboo environment variables
    try:
        plan = os.environ["bamboo_planKey"]
    except:
        log.abort("failed to get environment variable bamboo_planKey")
    try:
        build = os.environ["bamboo_buildNumber"]
    except:
        log.abort("failed to get environment variable bamboo_buildNumber")
    try:
        job = os.environ["bamboo_shortJobName"]
    except:
        log.abort("failed to get environment variable bamboo_shortJobName")

    # parse junit xml file
    try:
        xml = JUnitXml.fromfile(conf.junit_xml)
        log.info("parsed junit xml file {}".format(conf.junit_xml))
    except:
        log.abort("failed to parse junit xml file {}".format(conf.junit_xml))

    # gather test results
    results_valid = 0
    results_invalid = 0
    results_skipped = 0
    results_total = 0
    results = []
    for suite in xml:
        if isinstance(suite, TestSuite):
            for case in suite:
                results_total += 1
                result = TopotestResult().from_case(case, suite, plan, build, job)
                # check result
                if not result.check():
                    results_invalid += 1
                    continue
                # do not report if test was skipped
                if result.skipped():
                    results_skipped += 1
                    continue
                # append to results list
                results.append(result.to_json())
                results_valid += 1
        elif isinstance(suite, TestCase):
            results_total += 1
            result = TopotestResult().from_case(suite, None, plan, build, job)
            # check result
            if not result.check():
                results_invalid += 1
                continue
            # do not report if test was skipped
            if result.skipped():
                results_skipped += 1
                continue
            # append to results list
            results.append(result.to_json())
            results_valid += 1

    log.info(
        "gathered {} test results ({} valid, {} skipped, {} invalid)".format(
            results_total, results_valid, results_skipped, results_invalid
        )
    )

    # send valid results to collection server
    if results:

        # compose topostat message
        msg = Message()
        try:
            msg.add_payload(results)
            msg.gen_auth(conf.auth_key)
        except:
            log.abort("failed to compose topostat message")
        if not msg.check():
            log.abort("check of composed topostat message failed")
        log.info("composed topostat message")

        # create ZeroMQ context and socket
        context = zmq.Context()
        sock = context.socket(zmq.PUSH)
        if conf.server_address_type in ["IPV6", "DNS"]:
            sock.setsockopt(zmq.IPV6, True)

        # start upload watchdog timer
        watchdog = Timer(conf.connection_timeout, watchdog_handler, [log])
        watchdog.start()
        log.info(
            "started upload watchdog timer with interval of {}s".format(
                conf.connection_timeout
            )
        )

        # establish connection to ZeroMQ server
        try:
            sock.connect(conf.socket_address_str)
            log.info(
                "connected ZeroMQ PUSH socket to address {}".format(
                    conf.socket_address_str
                )
            )
        except:
            watchdog.cancel()
            sock.close()
            context.term()
            log.abort(
                "failed to connect ZeroMQ PUSH socket to address {}".format(
                    conf.socket_address_str
                )
            )

        # send test results JSON data to server
        try:
            sock.send_json(msg.to_json())
            sock.close()
            context.term()
            log.info("sent {} topotest results to server".format(results_valid))
            log.info(
                "closed ZeroMQ PUSH socket connected to address {}".format(
                    conf.socket_address_str
                )
            )
        except:
            watchdog.cancel()
            sock.close()
            context.term()
            log.err("failed to send topotest results to server")

        # stop upload watchdog timer
        watchdog.cancel()
        log.info("stopped upload watchdog timer")

    else:
        # nothing to do if no valid results
        log.info("no results to send")

    # exit
    log.ok("terminating")
    log.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
