#!/usr/bin/env python3

import sys
import sqlite3


def main():

    file_src = "/tmp/src"
    file_dst = "/tmp/dst"

    # connect to source database file
    try:
        conn_src = sqlite3.connect(file_src)
        db_src = conn_src.cursor()
    except:
        print("failed to connect to database {}".format(file_src))
        sys.exit(1)

    # connect to destination database file
    try:
        conn_dst = sqlite3.connect(file_dst)
        db_dst = conn_dst.cursor()

        # TODO: create tabe if not exists


    # create results table if it does not exist
        db_dst.execute(
            "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='testresults'"
        )

        if db_dst.fetchone()[0] == 0:
            TopotestResult().create_table(conn, )

            
            print("created table testresults in database {}".format(file_dst))

    except:
        print("failed to connect to database {}".format(file_dst))
        sys.exit(1)


    # iteratively fetch topotest results from source database
    try:
        db_src.execute("SELECT * FROM testresults")
    except:
        print(
            "unable to query topotest results from table testresults in database {}".format(
                file_src
            )
        )
        sys.exit(1)

    results = []
    total_results = 0
    # TODO: [code] remove debug vars
    # try:
    log.info("selecting results of CI plan {}".format(conf.ci_plan))
    for row in db_src:
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


def topotestresult_from_sql_tuple(sql_tuple: tuple) -> TopotestResult:
    """creates a TopotestResult object from an sql tuple"""

    if isinstance(sql_tuple, tuple):
        ttr = TopotestResult()
        if len(sql_tuple) == (len(ttr.__dict__)):
            ttr.name = str(sql_tuple[1])
            ttr.result = str(sql_tuple[2])
            ttr.time = float(sql_tuple[3])
            ttr.host = str(sql_tuple[4])
            ttr.timestamp = datetime.strptime(
                str(sql_tuple[5]), TOPOSTAT_DB_TIMESTAMP_FMT
            )
            ttr.plan = str(sql_tuple[6])
            ttr.build = int(sql_tuple[7])
            ttr.job = str(sql_tuple[8])
            ttr.version = TOPOSTAT_TTR_VERSION_1
            if ttr.check():
                return ttr
    return None

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
            + ")"
        )
        conn.commit()





    def insert_into(self, conn, table):
        conn.cursor().execute(
            "INSERT INTO {} (".format(table)
            + "name, result, time, host, timestamp, plan, build, job"
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
            ),
        )
        conn.commit()
