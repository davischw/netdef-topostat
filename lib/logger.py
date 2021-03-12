#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool Logging Facilities"""


#
# NetDEF FRR Topotest Results Statistics Tool Logging Facilities
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
import sys
import os
from threading import Thread
from queue import Queue
from datetime import datetime


# constant definitions
TOPOSTAT_LOGGER_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S.%f"
TOPOSTAT_LOGGER_QUEUE_SIZE_MAX = 256
TOPOSTAT_LOGGER_MSG_TYPE_LOG = "log"
TOPOSTAT_LOGGER_MSG_TYPE_DEBUG = "debug"


class Logger:
    """
    Logging facility which allows asynchronous buffered logging to both standard
    output and a log file
    """

    def __init__(self, conf):
        self.run = True
        self.conf = conf
        self.buffer = Queue(maxsize=TOPOSTAT_LOGGER_QUEUE_SIZE_MAX)
        self.worker = Thread(target=self.worker_thread)

    def worker_thread(self):
        """
        log worker thread to read messages from log buffer and write to stdout
        and log file
        """

        try:
            log_file = open(self.conf.log_file, "a+")
        except Exception:
            pass
        while self.run:
            try:
                msg = self.buffer.get(timeout=1)
                if msg[0] == TOPOSTAT_LOGGER_MSG_TYPE_LOG:
                    if self.conf.verbose or self.conf.debug:
                        print(msg[1], flush=True)
                    try:
                        print(msg[1], file=log_file, flush=True)
                    except Exception:
                        pass
                elif msg[0] == TOPOSTAT_LOGGER_MSG_TYPE_DEBUG:
                    if self.conf.debug:
                        print(msg[1], flush=True)
                        try:
                            print(msg[1], file=log_file, flush=True)
                        except Exception:
                            pass
                self.buffer.task_done()
            except Exception:
                pass
        try:
            log_file.close()
        except Exception:
            pass

    def start(self):
        """start the log worker thread"""

        try:
            self.run = True
            self.worker.start()
        except Exception:
            pass

    def stop(self):
        """stop the log worker thread"""

        self.start()
        self.buffer.join()
        self.run = False
        self.worker.join()

    def log(self, msg):
        """print a log message"""

        timestamp = datetime.now().strftime(TOPOSTAT_LOGGER_TIMESTAMP_FMT)
        try:
            self.buffer.put(
                [
                    TOPOSTAT_LOGGER_MSG_TYPE_LOG,
                    timestamp + " " + self.conf.progname + " " + str(msg),
                ]
            )
        except Exception:
            pass

    def info(self, msg):
        """print an informational log message"""

        self.log("INFO: " + str(msg))

    def warn(self, msg):
        """print a warning log message"""

        self.log("WARN: " + str(msg))

    def err(self, msg):
        """print an error log message"""

        self.log("ERR:  " + str(msg))

    def abort(self, msg):
        """print an error log message and exit"""

        self.err(str(msg))
        self.err("aborting")
        self.stop()
        sys.exit(1)

    def kill(self, msg):
        """print an error log message and kill process"""

        self.err(str(msg))
        self.err("killing process")
        self.stop()
        os.kill(os.getpid(), 9)

    def success(self, msg):
        """print a success log message"""

        self.log("OK:   " + str(msg))

    def debug(self, msg):
        """print a debug message"""

        try:
            self.buffer.put([TOPOSTAT_LOGGER_MSG_TYPE_DEBUG, "DEBUG: " + msg])
        except Exception:
            pass
