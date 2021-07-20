#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool Client"""


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


# standard library imports
import os
import sys
import argparse
from threading import Timer
import socket

# third party library imports
from junitparser import JUnitXml, TestSuite, TestCase
import zmq

# proprietary library imports
from lib.logger import Logger
from lib.message import Message
from lib.topotestresult import TopotestResult_v2
from lib.zmqutils import compose_zmq_client_address_str
from lib.config import ClientConfig, read_config_file, read_config_from_cli_args
from lib.check import is_int_min, is_str_no_empty, is_str_empty
from lib.sysinfo import (
    linux_kernel_version_str,
    linux_architecture_str,
    linux_distribution_version_str,
)


def watchdog_handler(log):
    """
    upload watchdog handler to terminate non-responsive ZeroMQ connect and send
    threads
    """

    log.kill("upload watchdog timer expired")


def parse_cli_arguments(conf, log):
    """parses cli arguments"""

    arg_parse = argparse.ArgumentParser()
    arg_parse.add_argument(
        "-v", "--verbose", help="verbose output", action="store_true"
    )
    arg_parse.add_argument("-d", "--debug", help="debug messages", action="store_true")
    arg_parse.add_argument("-c", "--config", help="configuration file")
    arg_parse.add_argument("-a", "--address", help="server address")
    arg_parse.add_argument("-p", "--port", type=int, help="server tcp port")
    arg_parse.add_argument("-s", "--sender", help="sender identification")
    arg_parse.add_argument("-k", "--key", help="authentication key")
    arg_parse.add_argument("-f", "--file", help="junit xml file")
    arg_parse.add_argument("-l", "--log", help="log file")

    conf_to_args_map = {
        "verbose": "verbose",
        "debug": "debug",
        "server_address": "address",
        "server_port": "port",
        "sender_id": "sender",
        "auth_key": "key",
        "junit_xml": "file",
        "log_file": "log",
    }

    try:
        args = vars(arg_parse.parse_args())
    except Exception:
        log.abort("failed to parse arguments")

    try:
        lcfca_ret = read_config_from_cli_args(args, conf, conf_to_args_map, log)
    except Exception:
        lcfca_ret = False

    if lcfca_ret:
        return True

    log.abort("failed to write cli argument values to config variables")
    return False  # abort is async!


def determine_client_sender_id(conf):
    """
    Determine sender identification from either configured values or by
    attempting to get the machines hostname. This process can fail due to weird
    behaviour of python socket wrapper functions in connection with exotic
    network stack configurations (LCX, Jails, etc.).
    """

    # check if sender identification is already configured
    if is_str_no_empty(conf.sender_id) and conf.sender_id != "None":
        return True

    # otherwise use hostname
    conf.sender_id = socket.gethostname()
    if is_str_no_empty(conf.sender_id):
        return True

    # or cause the configuration check to abort the program, if
    # socket.gethostname() fails
    conf.sender_id = None
    return False


def main():
    """client main function"""

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
    if is_str_no_empty(conf.config_file):
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

    # start log buffer output (now we now which log file to write to)
    log.info("writing to log file {}".format(conf.log_file))
    log.start()

    # do a configuration check
    if not conf.check():
        log.abort("configuration check failed")
    else:
        log.info("passed configuration check")

    # make sure watchdog timeout is positive non-zero value
    if not is_int_min(conf.connection_timeout, 1):
        log.debug("conf.connection_timeout = {}".format(conf.connection_timeout))
        log.abort("upload watchdog timeout value is invalid")

    # get bamboo environment variables
    try:
        plan = str(os.environ["bamboo_planKey"])
        if is_str_empty(plan):
            raise KeyError
        log.debug("env[bamboo_planKey] = {} (str)".format(plan))
    except KeyError:
        log.abort("failed to get environment variable bamboo_planKey")
    try:
        build = int(os.environ["bamboo_buildNumber"])
        if not is_int_min(build, 1):
            raise ValueError
        log.debug("env[bamboo_buildNumber] = {} (int)".format(build))
    except (KeyError, ValueError):
        log.abort("failed to get environment variable bamboo_buildNumber")
    try:
        job = str(os.environ["bamboo_shortJobName"])
        if is_str_empty(job):
            raise KeyError
        log.debug("env[bamboo_shortJobName] = {} (str)".format(job))
    except KeyError:
        log.abort("failed to get environment variable bamboo_shortJobName")

    # get system information
    sys_dist = linux_distribution_version_str()
    if is_str_no_empty(sys_dist):
        log.debug("sys_dist = {} (str)".format(sys_dist))
    else:
        log.abort("failed to get linux distribution name and release version")
    sys_arch = linux_architecture_str()
    if is_str_no_empty(sys_arch):
        log.debug("sys_arch = {} (str)".format(sys_arch))
    else:
        log.abort("failed to get system architecure information")
    sys_kvers = linux_kernel_version_str()
    if is_str_no_empty(sys_kvers):
        log.debug("sys_kvers = {} (str)".format(sys_kvers))
    else:
        log.abort("failed to get linux kernel version")

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
                result = TopotestResult_v2().from_case(
                    case,
                    conf.sender_id,
                    plan,
                    build,
                    job,
                    sys_dist,
                    sys_arch,
                    sys_kvers,
                )
                if result and result.check():
                    # do not report if test was skipped
                    if result.skipped():
                        results_skipped += 1
                        continue
                    # append to results list
                    results.append(result.json())
                    results_valid += 1
                else:
                    results_invalid += 1
        elif isinstance(suite, TestCase):
            results_total += 1
            result = TopotestResult_v2().from_case(
                suite, conf.sender_id, plan, build, job, sys_dist, sys_arch, sys_kvers
            )
            if result and result.check():
                # do not report if test was skipped
                if result.skipped():
                    results_skipped += 1
                    # TODO: [code] compatibility with server for recording
                    #              skipped tests results
                    #continue
                # append to results list
                results.append(result.json())
                results_valid += 1
            else:
                results_invalid += 1

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
        log.debug("msg = {}".format(msg.json()))

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
        except zmq.ZMQError:
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
            sock.send_json(msg.json())
            sock.close()
            context.term()
            log.info("sent {} topotest results to server".format(results_valid))
            log.info(
                "closed ZeroMQ PUSH socket connected to address {}".format(
                    conf.socket_address_str
                )
            )
        except zmq.ZMQError:
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
    log.success("terminating")
    log.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
