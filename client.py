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

from junitparser import JUnitXml, TestSuite, TestCase
import zmq

from lib.topostat import (
    Logger,
    Message,
    TopotestResult,
    compose_zmq_client_address_str,
    determine_client_sender_id,
)
from lib.config import ClientConfig, read_config_file
import lib.check as check


# Upload watchdog handler to terminate non-responsive ZeroMQ connect and send
# threads
def watchdog_handler(log):
    log.kill("upload watchdog timer expired")


# parse cli arguments
def parse_cli_arguments(conf, log):
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    ap.add_argument("-d", "--debug", help="debug messages", action="store_true")
    ap.add_argument("-c", "--config", help="configuration file")
    ap.add_argument("-a", "--address", help="server address")
    ap.add_argument("-p", "--port", help="server tcp port")
    ap.add_argument("-s", "--sender", help="sender identification")
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
            "sender_id": "sender",
            "auth_key": "key",
            "junit_xml": "file",
            "log_file": "log",
        }
        for conf_var, arg_val in conf_to_args.items():
            if not conf_var in conf.config_no_overwrite:
                if not args[arg_val] is None:
                    if conf_var in conf.config_lists:
                        log.debug("configure list attempt conf.{}".format(conf_var))
                    elif conf_var in conf.config_bools:
                        if args[arg_val]:
                            conf.__dict__[conf_var] = True
                            if not conf_var in conf.config_no_show:
                                log.debug(
                                    "conf.{} = args[{}] = True (bool)".format(
                                        conf_var, arg_val
                                    )
                                )
                    elif conf_var in conf.config_ints:
                        conf.__dict__[conf_var] = args[arg_val].getint()
                        if conf_var in conf.config_no_show:
                            log.debug(
                                "conf.{} = args[{}] = *** (int)".format(
                                    conf_var, arg_val
                                )
                            )
                        else:
                            log.debug(
                                "conf.{} = args[{}] = {} (int)".format(
                                    conf_var, arg_val, args[arg_val].getint()
                                )
                            )
                    elif check.is_str_no_empty(args[arg_val]):
                        conf.__dict__[conf_var] = args[arg_val]
                        if conf_var in conf.config_no_show:
                            log.debug(
                                "conf.{} = args[{}] = *** (str)".format(
                                    conf_var, arg_val
                                )
                            )
                        else:
                            log.debug(
                                "conf.{} = args[{}] = {} (str)".format(
                                    conf_var, arg_val, args[arg_val]
                                )
                            )
                    else:
                        log.debug(
                            "args[{}] type invalid {}".format(
                                arg_val, type(args[arg_val])
                            )
                        )
            else:
                log.debug("overwrite attempt conf.{}".format(conf_var))
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
    if check.is_str_no_empty(conf.config_file):
        read_config_file(conf.config_file, conf, log)
    elif os.path.isfile(conf.default_config_file):
        read_config_file(conf.default_config_file, conf, log)
    else:
        log.warn("running with potentially unsafe default configuration")

    # parse cli arguments
    parse_cli_arguments(conf, log)

    # determine sender identification
    determine_client_sender_id(conf)
    log.info("identifying as sender {}".format(conf.sender_id))

    # start log buffer output
    log.info("writing to log file {}".format(conf.log_file))
    log.start()

    # do a configuration check
    if not conf.check():
        log.abort("configuration check failed")
    else:
        log.info("passed configuration check")

    # make sure watchdog timeout is positive non-zero value
    if not check.is_int_min(conf.connection_timeout, 1):
        log.debug("conf.connection_timeout = {}".format(conf.connection_timeout))
        log.abort("upload watchdog timeout value is invalid")

    # get bamboo environment variables
    try:
        plan = str(os.environ["bamboo_planKey"])
        log.debug("env[bamboo_planKey] = {} (str)".format(plan))
    except:
        log.abort("failed to get environment variable bamboo_planKey")
    try:
        build = str(os.environ["bamboo_buildNumber"])
        log.debug("env[bamboo_buildNumber] = {} (str)".format(build))
    except:
        log.abort("failed to get environment variable bamboo_buildNumber")
    try:
        job = str(os.environ["bamboo_shortJobName"])
        log.debug("env[bamboo_shortJobName] = {} (str)".format(job))
    except:
        log.abort("failed to get environment variable bamboo_shortJobName")

    # compose ZeroMQ server address string (includes DNS resolve)
    if compose_zmq_client_address_str(conf, log) is None:
        log.abort("failed to compose ZeroMQ server address string")

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
                result = TopotestResult().from_case(
                    case, conf.sender_id, plan, build, job
                )
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
            result = TopotestResult().from_case(suite, conf.sender_id, plan, build, job)
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

    # give some indication it all worked
    if not conf.verbose and not conf.debug:
        print(
            "{}: sent {} valid results to server {}".format(
                conf.progname, results_valid, conf.server_address
            )
        )

    # exit
    log.ok("terminating")
    log.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
