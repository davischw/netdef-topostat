#!/usr/bin/env python3


import os
import sys
import datetime
import sqlite3
import argparse

from lib.config import StatsConfig, read_config_file
from lib.check import (
    is_int_min,
    is_str_no_empty,
    is_datetime,
    is_list,
    is_float_min,
    is_bool,
    is_float_range,
    is_list_no_empty,
)
from lib.topotestresult import (
    TOPOSTAT_TTR_TIMESTAMP_FMT,
    TopotestResult,
)
from lib.logger import Logger
from lib.olddbstuff import topotestresult_from_sql_tuple


TOPOSTAT_DATABASE = "/home/davischw/topotests.db"
TOPOSTAT_TESTRESULTS_TABLE = "testresults"
CI_URL_BROWSE = "https://ci1.netdef.org/browse"


IDX_ID = 0
IDX_NAME = 1
IDX_RESULT = 2
IDX_TIME = 3
IDX_HOST = 4
IDX_TIMESTAMP = 5
IDX_PLAN = 6
IDX_BUILD = 7
IDX_JOB = 8


# use same for tests, agents, jobs
class Statistics:
    def __init__(self, name):
        self.name = name
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.quality = 0.0
        self.time_total = 0.0
        self.time_avg = 0.0

    def inc_passed(self):
        self.total += 1
        self.passed += 1

    def inc_failed(self):
        self.total += 1
        self.failed += 1

    def add_time(self, time):
        if is_float_min(time, 0.0):
            self.time_total += time
            return True
        return False

    def update_quality(self):
        if is_int_min(self.total, 1) and is_int_min(self.passed, 0):
            self.quality = float(self.passed / float(self.total))
            return True
        self.quality = 0.0
        return False

    def update_time(self):
        if is_int_min(self.passed, 1) and is_float_min(self.time_total, 0.0):
            self.time_avg = self.time_total / float(self.passed)
            return True
        self.time_avg = 0.0
        return False

    def check(self):
        if (
            is_str_no_empty(self.name)
            and is_int_min(self.total, 0)
            and is_int_min(self.passed, 0)
            and is_int_min(self.failed, 0)
            and is_float_range(self.quality, 0.0, 1.0)
            and is_float_min(self.time_total, 0.0)
            and is_float_min(self.time_avg, 0.0)
        ):
            return True
        return False


def sort_statistics_by_quality(stats_list, reverse_order=False):
    if is_list_no_empty(stats_list) and is_bool(reverse_order):
        no_err = True
        for stat in stats_list:
            if stat is None or not isinstance(stat, Statistics):
                no_err = False
        if no_err:
            stats_list.sort(key=lambda x: x.quality, reverse=reverse_order)
            return True
    return False


def sort_statistics_by_failures(stats_list, reverse_order=True):
    if is_list_no_empty(stats_list) and is_bool(reverse_order):
        no_err = True
        for stat in stats_list:
            if stat is None or not isinstance(stat, Statistics):
                no_err = False
        if no_err:
            stats_list.sort(key=lambda x: x.failed, reverse=reverse_order)
            return True
    return False


def sort_statistics_by_time_avg(stats_list, reverse_order=True):
    if is_list_no_empty(stats_list) and is_bool(reverse_order):
        no_err = True
        for stat in stats_list:
            if stat is None or not isinstance(stat, Statistics):
                no_err = False
        if no_err:
            stats_list.sort(key=lambda x: x.time_avg, reverse=reverse_order)
            return True
    return False


def date_str_between_dates(date_str, min_dt, max_dt):
    if is_str_no_empty(date_str) and is_datetime(min_dt) and is_datetime(max_dt):
        try:
            date_dt = datetime.datetime.strptime(date_str, TOPOSTAT_TTR_TIMESTAMP_FMT)
        except:
            return False
        else:
            if min_dt <= date_dt <= max_dt:
                return True
    return False


def result_process_and_append_to_stats_list(result, var, stats_list):
    if (
        isinstance(result, TopotestResult)
        and result.check()
        and is_str_no_empty(var)
        and is_list(stats_list)
    ):
        if var in result.__dict__:
            in_stats_list = False
            for stats in stats_list:
                if result.__dict__[var] == stats.name:
                    in_stats_list = True
                    if result.passed():
                        stats.inc_passed()
                        if var == "name" and is_float_min(result.time, 0.0):
                            stats.add_time(result.time)
                    elif result.failed():
                        stats.inc_failed()
                    continue
            if not in_stats_list:
                new_stats = Statistics(result.__dict__[var])
                if result.passed():
                    new_stats.inc_passed()
                    if var == "name" and is_float_min(result.time, 0.0):
                        new_stats.add_time(result.time)
                elif result.failed():
                    new_stats.inc_failed()
                stats_list.append(new_stats)


def result_process_module_and_append_to_stats_list(result, stats_list):
    if isinstance(result, TopotestResult) and result.check() and is_list(stats_list):
        in_stats_list = False
        for stats in stats_list:
            if result.name.split(".", 1)[0] == stats.name:
                in_stats_list = True
                if result.passed():
                    stats.inc_passed()
                    if is_float_min(result.time, 0.0):
                        stats.add_time(result.time)
                elif result.failed():
                    stats.inc_failed()
                continue
        if not in_stats_list:
            new_stats = Statistics(result.name.split(".", 1)[0])
            if result.passed():
                new_stats.inc_passed()
                if is_float_min(result.time, 0.0):
                    new_stats.add_time(result.time)
            elif result.failed():
                new_stats.inc_failed()
            stats_list.append(new_stats)


def generate_txt_report(
    conf,
    log,
    results,
    database_name,
    total_results,
    total_weekly,
    week_dt,
    now_dt,
    test_stats_failures,
    test_stats_quality,
    time_stats,
    agent_stats,
    job_stats,
):
    if (
        isinstance(conf, StatsConfig)
        and isinstance(log, Logger)
        and isinstance(results, list)
        and is_str_no_empty(database_name)
        and is_int_min(total_results, 0)
        and is_int_min(total_weekly, 0)
        and is_datetime(week_dt)
        and is_datetime(now_dt)
        and is_list(test_stats_failures)
        and is_list(test_stats_quality)
        and is_list(time_stats)
        and is_list(agent_stats)
        and is_list(job_stats)
    ):
        txt = "===== DATABASE {} ({}) =====\n".format(database_name, total_results)
        txt += "===== WEEK FROM {} TO {} ({}) {} =====\n".format(
            week_dt.strftime("%Y-%m-%d"), now_dt.strftime("%Y-%m-%d"), total_weekly, conf.ci_plan
        )

        txt += "\n===== TESTS BY FAILURES [rank: name (total, passed, failed, failure rate)] ({}) =====".format(
            len(test_stats_failures)
        )
        index = 0
        for test in test_stats_failures[:20]:
            if not test is None and isinstance(test, Statistics):
                index += 1
                txt += "\n{:2d}: {} ({}, {}, {}, {:5.2f}%)".format(
                    index,
                    test.name,
                    test.total,
                    test.passed,
                    test.failed,
                    (1.0 - test.quality) * 100.0,
                )

        txt += "\n\n===== TESTS BY FAILURE RATE [rank: name (total, passed, failed, failure rate)] ({}) =====".format(
            len(test_stats_quality)
        )
        index = 0
        for test in test_stats_quality[:100]:
            if not test is None and isinstance(test, Statistics):
                index += 1
                txt += "\n{:3d}: {} ({}, {}, {}, {:5.2f}%)".format(
                    index,
                    test.name,
                    test.total,
                    test.passed,
                    test.failed,
                    (1.0 - test.quality) * 100.0,
                )

                failed_tests = lookup_failed_tests_for_suite(log, results, conf.ci_plan, test.name)
                if isinstance(failed_tests, list) and failed_tests:
                    failed_tests_printable = []
                    failed_tests_suppress = dict()

                    for failed_test in reversed(failed_tests):
                        if isinstance(failed_test, TopotestResult):
                            failed_test_name = failed_test.name.split(".")[-1]
                            failed_test_count = 1

                            if failed_test_name in failed_tests_suppress:
                                failed_test_count = failed_tests_suppress[failed_test_name]
                                if isinstance(failed_test_count, int):
                                    failed_test_count += 1
                                else:
                                    failed_test_count = 1

                            failed_tests_suppress[failed_test_name] = failed_test_count

                            if failed_test_count <= 3:
                                failed_tests_printable.append(failed_test)

                    for name, count in reversed(failed_tests_suppress.items()):
                        if count > 3:
                            txt += "\n       [ {}: suppressed {} additional failures ]".format(
                                name, (count - 3)
                            )

                    for failed_test_printable in reversed(failed_tests_printable):
                        if isinstance(failed_test_printable, TopotestResult):
                            failed_test_printable_name = failed_test_printable.name.split(".")[-1]

                            txt += "\n     * {} ({}/{}-{})".format(
                                failed_test_printable_name,
                                CI_URL_BROWSE,
                                failed_test_printable.plan,
                                failed_test_printable.build
                            )

        txt += "\n\n===== WORST TEST TIMES [rank: name (total-time, passed, avg-time)] ({}) =====".format(
            len(time_stats)
        )
        index = 0
        for time in time_stats[:10]:
            if not time is None and isinstance(time, Statistics):
                index += 1
                txt += "\n{:2d}: {} ({:.3f}, {}, {:.3f})".format(
                    index, time.name, time.time_total, time.passed, time.time_avg
                )

        index = 0
        txt += "\n\n===== WORST AGENTS [rank: name (total, passed, failed, quality)] ({}) =====".format(
            len(agent_stats)
        )
        for agent in agent_stats[:10]:
            if not agent is None and isinstance(agent, Statistics):
                index += 1
                txt += "\n{:2d}: {} ({}, {}, {}, {:5.3f})".format(
                    index,
                    agent.name,
                    agent.total,
                    agent.passed,
                    agent.failed,
                    agent.quality,
                )

        index = 0
        txt += "\n\n===== WORST JOBS [rank: name (total, passed, failed, quality)] ({}) =====".format(
            len(job_stats)
        )
        for job in job_stats[:10]:
            if not job is None and isinstance(job, Statistics):
                index += 1
                txt += "\n{:2d}: {} ({}, {}, {}, {:5.3f})".format(
                    index, job.name, job.total, job.passed, job.failed, job.quality
                )
        return txt
    return None


def generate_html_report(
    database_name,
    total_results,
    total_weekly,
    week_dt,
    now_dt,
    test_stats,
    time_stats,
    agent_stats,
    job_stats,
):
    if (
        is_str_no_empty(database_name)
        and is_int_min(total_results, 0)
        and is_int_min(total_weekly, 0)
        and is_datetime(week_dt)
        and is_datetime(now_dt)
        and is_list(test_stats)
        and is_list(time_stats)
        and is_list(agent_stats)
        and is_list(job_stats)
    ):
        html = '<!DOCTYPE HTML><html><head><meta charset="utf-8" />'
        html += "<title>NetDEF Topostat Statistics Report</title>"
        html += "</head><body>"

        html += "<table>"
        html += "<tr><th>#</th><th>name</th><th>total</th><th>passed</th>"
        html += "<th>failed</th><th>quality</th></tr>"
        index = 0
        for time in time_stats[:10]:
            if not time is None and isinstance(time, Statistics):
                index += 1
                html += "<tr><td>{:2d}</td><td>{}</td><td>{:.3f}</td><td>{}</td><td>{:.3f}</td></tr>".format(
                    index, time.name, time.time_total, time.passed, time.time_avg
                )
        html += "</table>"

        html += "</body>"

    return None


# parse cli arguments
def parse_cli_arguments(conf, log):
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    ap.add_argument("-d", "--debug", help="debug messages", action="store_true")
    ap.add_argument("-c", "--config", help="configuration file")
    ap.add_argument("-b", "--database", help="sqlite3 database file")
    ap.add_argument(
        "-nt", "--no-txt-report", help="omit text report", action="store_true"
    )
    ap.add_argument("-tr", "--txt-report", help="text report file")
    ap.add_argument(
        "-nh", "--no-html-report", help="omit html report", action="store_true"
    )
    ap.add_argument("-hr", "--html-report", help="html report file")
    ap.add_argument("-l", "--log", help="log file")
    ap.add_argument("-p", "--plan", help="CI plan")

    try:
        args = vars(ap.parse_args())
        conf_to_args = {
            "verbose": "verbose",
            "debug": "debug",
            "config_file": "config",
            "sqlite3_db": "database",
            "no_txt_report": "no_txt_report",
            "txt_report_file": "txt_report",
            "no_html_report": "no_html_report",
            "html_report_file": "html_report",
            "log_file": "log",
            "ci_plan": "plan",
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
                    elif is_str_no_empty(args[arg_val]):
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


def lookup_failed_tests_for_suite(log, results, plan_name, suite_name):
    """ Lookup all failed tests for a specific suite """

    failed_tests = []

    if (
        isinstance(log, Logger)
        and isinstance(results, list)
        and isinstance(plan_name, str)
        and plan_name
        and isinstance(suite_name, str)
        and suite_name
    ):
        try:
            for result in results:
                if isinstance(result, TopotestResult):
                    if (
                        result.failed()
                        and result.plan == plan_name
                        and result.name.split(".", 1)[0] == suite_name
                    ):
                        failed_tests.append(result)

        except Exception:
            failed_tests = []

            log.warn("encountered exception looking up failed tests for suit '{}'".format(suite_name))

    return failed_tests


def main():
    # initialize config
    conf = StatsConfig()

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

    # start log buffer output
    log.info("writing to log file {}".format(conf.log_file))
    log.start()

    # do a configuration check
    if not conf.check():
        log.abort("configuration check failed")
    else:
        log.info("passed configuration check")

    # create datetime references
    now_dt = datetime.datetime.now()
    week_dt = now_dt - datetime.timedelta(
        days=7
    )  # TODO: cli switch for weekly/fortnightly

    # connect to sqlite3 db
    try:
        conn = sqlite3.connect(conf.sqlite3_db)
        db = conn.cursor()
    except:
        log.abort("failed to connect to database {}".format(conf.sqlite3_db))

    # check for existence of results table in database
    try:
        db.execute(
            "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}'".format(
                conf.results_table
            )
        )
    except:
        log.abort(
            "unable to confirm existence of table {} in database {}".format(
                conf.results_table, conf.sqlite3_db
            )
        )
    log.info(
        "using table {} in database {}".format(conf.results_table, conf.sqlite3_db)
    )

    # iteratively fetch topotest results from database
    try:
        db.execute("SELECT * FROM {}".format(TOPOSTAT_TESTRESULTS_TABLE))
    except:
        log.abort(
            "unable to query topotest results from table {} in database {}".format(
                conf.results_table, conf.sqlite3_db
            )
        )
    results = []
    total_results = 0
    # TODO: [code] remove debug vars
    # try:
    log.info("selecting results of CI plan {}".format(conf.ci_plan))
    for row in db:
        total_results += 1
        ttr = topotestresult_from_sql_tuple(row)
        if not ttr is None:
            if ttr.plan == conf.ci_plan:
                if date_str_between_dates(
                    ttr.timestamp.strftime(TOPOSTAT_TTR_TIMESTAMP_FMT),
                    week_dt,
                    now_dt,
                ):
                    results.append(ttr)
    """
    except:
    conn.close()
    log.abort(
        "failed to iteratively fetch topotest results from table {} in database {}".format(
            conf.results_table, conf.sqlite3_db
        )
    )
    """

    # closing database connection
    conn.close()
    log.info("closed connection to database {}".format(conf.sqlite3_db))

    if results:
        log.info(
            "fetched {} topotest results from table {} in database {}".format(
                len(results), conf.results_table, conf.sqlite3_db
            )
        )
    else:
        log.abort(
            "fetched 0 topotest results from table {} in database {}, nothing to do".format(
                conf.results_table, conf.sqlite3_db
            )
        )

    # process results
    tests = []
    agents = []
    jobs = []
    for result in results:
        # result_process_and_append_to_stats_list(result, "name", tests)
        result_process_module_and_append_to_stats_list(result, tests)
        result_process_and_append_to_stats_list(result, "host", agents)
        result_process_and_append_to_stats_list(result, "job", jobs)

    # calculate quality
    for stat in tests:
        stat.update_quality()
        stat.update_time()
    for stat in agents:
        stat.update_quality()
    for stat in jobs:
        stat.update_quality()

    # copy statistics tests to times before sorting
    times = tests.copy()
    tests_by_failures = tests.copy()

    # sort lists
    sort_statistics_by_quality(tests)
    sort_statistics_by_time_avg(times)
    sort_statistics_by_quality(agents)
    sort_statistics_by_quality(jobs)
    sort_statistics_by_failures(tests_by_failures)

    # generate text report
    if not conf.no_txt_report:
        txt = generate_txt_report(
            conf,
            log,
            results,
            conf.sqlite3_db,
            total_results,
            len(results),
            week_dt,
            now_dt,
            tests_by_failures,
            tests,
            times,
            agents,
            jobs,
        )
        """
        if is_str_no_empty(txt):
            log.info("generated TXT report")
            try:
                txt_fd = open(conf.txt_report_file, "w+")
                txt_fd.write(txt)
            except:
                # TODO: switch to abort
                log.err(
                    "failed to write TXT report to file {}".format(conf.txt_report_file)
                )
            else:
                txt_fd.close()
                log.info("wrote TXT report to file {}".format(conf.txt_report_file))
        else:
            log.abort("failed to generate TXT report")
        """
        print(txt)

    # TODO: generate html report

    # exit
    log.success("terminating")
    log.stop()
    sys.exit(0)


if __name__ == "__main__":
    main()
