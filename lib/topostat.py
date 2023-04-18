#!/usr/bin/env python3


#
# NetDEF FRR Topotest Results Statistics Tool Library
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


import sys
import os
from datetime import datetime
import json
import hashlib
import threading
import re
from queue import Queue
import socket

from junitparser import Failure, Skipped, Element, TestSuite, TestCase

from lib.config import ServerConfig, ClientConfig
import lib.check as check


TOPOSTAT_MESSAGE_VERSION = 1
TOPOSTAT_TTR_VERSION = 1


class Message:
    def __init__(self, version=None, auth=None, timestamp=None, payload=None):
        if version is None or not isinstance(version, int):
            self.version = TOPOSTAT_MESSAGE_VERSION
        else:
            self.version = version
        self.auth = auth
        self.timestamp = timestamp
        self.payload = payload

    def from_json(self, json_obj):
        self.version = json_obj["version"]
        self.auth = json_obj["auth"]
        self.timestamp = json_obj["timestamp"]
        self.payload = json_obj["payload"]

    def to_json(self):
        if not self.check():
            return None
        return json.loads(json.dumps(self.__dict__))

    def gen_auth(self, auth_key):
        if auth_key is None or not isinstance(auth_key, str):
            return False
        self.timestamp = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )  # UTC timestamp
        self.auth = hashlib.sha512((self.timestamp + auth_key).encode()).hexdigest()
        return True

    def check_auth(self, auth_key):
        if auth_key is None or not isinstance(auth_key, str):
            return False
        if not self.check():
            return False
        if not isinstance(self.auth, str):
            return False
        auth = hashlib.sha512((self.timestamp + auth_key).encode()).hexdigest()
        if self.auth == auth:
            return True
        return False

    def check(self):
        for var in self.__dict__.values():
            if var is None:
                return False
        if (
            not isinstance(self.version, int)
            or self.version != TOPOSTAT_MESSAGE_VERSION
        ):
            return False
        return True

    # add a json payload
    def add_payload(self, payload):
        if payload is None:
            return False
        self.payload = json.loads(json.dumps(payload))
        return True


class TopotestResult:
    def __init__(
        self,
        name=None,
        result=None,
        time=None,
        host=None,
        timestamp=None,
        plan=None,
        build=None,
        job=None,
        pr=None,
        version=None,  # keep version number at end of argument list
    ):
        if version is None or not isinstance(version, int):
            self.version = TOPOSTAT_TTR_VERSION
        else:
            self.version = version
        self.name = name
        self.result = result
        self.time = time
        self.host = host
        self.timestamp = timestamp
        self.plan = plan
        self.build = build
        self.job = job
        self.pr = pr

    def create_table(self, conn, table):
        conn.cursor().execute(
            "CREATE TABLE {} (".format(table)
            + "id INTEGER PRIMARY KEY AUTOINCREMENT"
            + ", name text"
            + ", result text"
            + ", time text"
            + ", host text"
            + ", timestamp text"
            + ", plan text"
            + ", build text"
            + ", job text"
            + ", pr text"
            + ")"
        )
        conn.commit()

    def insert_into(self, conn, table):
        conn.cursor().execute(
            "INSERT INTO {} (".format(table)
            + "name, result, time, host, timestamp, plan, build, job, pr"
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(self.name),
                str(self.result),
                str(self.time),
                str(self.host),
                str(self.timestamp),
                str(self.plan),
                str(self.build),
                str(self.job),
                self.pr if check.is_str_no_empty(self.pr) else "NULL",
            ),
        )
        conn.commit()

    def to_json(self):
        json_dict = {
            "name": str(self.name),
            "result": str(self.result),
            "time": str(self.time),
            "host": str(self.host),
            "timestamp": str(self.timestamp),
            "plan": str(self.plan),
            "build": str(self.build),
            "job": str(self.job),
        }

        if check.is_str_no_empty(self.pr):
            json_dict["pr"] = self.pr

        if not self.check():
            return None
        return json.loads(json.dumps(json_dict))

    def from_json(self, json_dict):
        try:
            if json_dict["version"] != TOPOSTAT_TTR_VERSION:
                return None
            self.name = json_dict["name"]
            self.result = json_dict["result"]
            self.time = json_dict["time"]
            self.host = json_dict["host"]
            self.timestamp = json_dict["timestamp"]
            self.plan = json_dict["plan"]
            self.build = json_dict["build"]
            self.job = json_dict["job"]
            if "pr" in json_dict:
                self.pr = json_dict["pr"]
            else:
                self.pr = None
        except:
            return None
        if not self.check():
            return None
        return self

    def from_case(self, case, host, plan, build, job, pr=None):
        if case is None or not isinstance(case, TestCase):
            assert False, "from_case case check failed"
            return None
        if not (
            check.is_str_no_empty(host)
            and check.is_str_no_empty(plan)
            and check.is_str_no_empty(build)
            and check.is_str_no_empty(job)
        ):
            assert False, "from_case arg check failed"
            return None
        self.version = TOPOSTAT_TTR_VERSION
        self.name = str(case.classname) + "." + str(case.name)
        if case.result:
            # junit parser version switch
            if isinstance(case.result, list):
                # junitparser v2.X
                if isinstance(case.result[0], Failure):
                    self.result = "failed"
                elif isinstance(case.result[0], Skipped):
                    self.result = "skipped"
            else:
                # junitparser v1.X
                if isinstance(case.result, Failure):
                    self.result = "failed"
                elif isinstance(case.result, Skipped):
                    self.result = "skipped"
        else:
            self.result = "passed"
        self.time = str(case.time)
        self.host = host
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.plan = plan
        self.build = build
        self.job = job
        if check.is_str_no_empty(pr):
            self.pr = pr
        else:
            self.pr = None
        return self

    def check(self):
        for key, value in self.__dict__.items():
            print("===== DEBUG key = {}".format(key))
            print("===== DEBUG value = {}".format(value))
            if key == "pr":
                if not (check.is_str_no_empty(value) or value == None):
                    return False
                continue
            elif value is None:
                return False
            elif isinstance(value, int):
                continue
            elif isinstance(value, str):
                if value == "" or value == "None":
                    return False
                continue
            else:
                return False
        if not isinstance(self.version, int):
            return False
        if self.version != TOPOSTAT_TTR_VERSION:
            return False
        return True

    def passed(self):
        if (
            self.result is None
            or not isinstance(self.result, str)
            or self.result != "passed"
        ):
            return False
        else:
            return True

    def failed(self):
        if (
            self.result is None
            or not isinstance(self.result, str)
            or self.result != "failed"
        ):
            return False
        else:
            return True

    def skipped(self):
        if (
            self.result is None
            or not isinstance(self.result, str)
            or self.result != "skipped"
        ):
            return False
        else:
            return True


class Logger:
    def __init__(self, conf):
        self.run = True
        self.conf = conf
        self.buffer = Queue(maxsize=128)
        self.worker = threading.Thread(target=self.worker_thread)

    def worker_thread(self):
        try:
            f = open(self.conf.log_file, "a+")
        except:
            pass
        while self.run:
            try:
                msg = self.buffer.get(timeout=1)
                if msg[0] == "log":
                    if self.conf.verbose or self.conf.debug:
                        print(msg[1], flush=True)
                    try:
                        print(msg[1], file=f, flush=True)
                    except:
                        pass
                elif msg[0] == "debug":
                    if self.conf.debug:
                        print(msg[1], flush=True)
                        try:
                            print(msg[1], file=f, flush=True)
                        except:
                            pass
                self.buffer.task_done()
            except:
                pass
        try:
            f.close()
        except:
            pass

    def start(self):
        try:
            self.run = True
            self.worker.start()
        except:
            pass

    def stop(self):
        self.start()
        self.buffer.join()
        self.run = False
        self.worker.join()

    # print a log message
    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        try:
            self.buffer.put(
                ["log", timestamp + " " + self.conf.progname + " " + str(msg)]
            )
        except:
            pass

    # print an informational log message
    def info(self, msg):
        self.log("INFO: " + str(msg))

    # print a warning log message
    def warn(self, msg):
        self.log("WARN: " + str(msg))

    # print an error log message
    def err(self, msg):
        self.log("ERR:  " + str(msg))

    # print an error log message and exit
    def abort(self, msg):
        self.err(str(msg))
        self.err("aborting")
        self.stop()
        sys.exit(1)

    # print an error log message and kill process
    def kill(self, msg):
        self.err(str(msg))
        self.err("killing process")
        self.stop()
        os.kill(os.getpid(), 9)

    # print a success log message
    def ok(self, msg):
        self.log("OK:   " + str(msg))

    def debug(self, msg):
        try:
            self.buffer.put(["debug", "DEBUG: " + msg])
        except:
            pass


def compose_zmq_client_address_str(conf, log):
    server_address_types = ["IPV4", "IPV6", "DNS"]

    if not check.is_str_no_empty(conf.server_address_type):
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
            except:
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


def determine_client_sender_id(conf):
    """
    Determine sender identification from either configured values or by
    attempting to get the machines hostname. This process can fail due to weird
    behaviour of python socket wrapper functions in connection with exotic
    network stack configurations (LCX, Jails, etc.).
    """

    # check if sender identification is already configured
    if check.is_str_no_empty(conf.sender_id) and conf.sender_id != "None":
        return True

    # otherwise use hostname
    conf.sender_id = socket.gethostname()
    if check.is_str_no_empty(conf.sender_id):
        return True

    # or cause the configuration check to abort the program, if
    # socket.gethostname() fails
    conf.sender_id = None
    return False
