#!/usr/bin/env python3

import os
import sys
from datetime import datetime
import sqlite3
import argparse
import traceback

TOPOSTAT_DB_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S.%f"
def topostat_db_timestamp_parse(raw):
    return datetime.strptime(str(raw), TOPOSTAT_DB_TIMESTAMP_FMT)

fields = [
    ("name", str),
    ("result", str),
    ("time", float),
    ("host", str),
    ("timestamp", topostat_db_timestamp_parse),
    ("plan", str),
    ("build", int),
    ("job", str),
]

def merge(conn_dst: sqlite3.Connection, db_src: sqlite3.Cursor) -> None:
    sql = f"SELECT {', '.join(field[0] for field in fields)} FROM testresults"
    # iteratively fetch topotest results from source database
    try:
        db_src.execute(sql)
    except Exception as e:
        raise EnvironmentError("failed to query source") from e

    sql = f"INSERT INTO testresults ({', '.join(field[0] for field in fields)}) " + \
        f"VALUES ({', '.join('?' for field in fields)})"
    db_dst = conn_dst.cursor()
    queue = []
    done = 0

    for row in db_src:
        row_parsed = tuple(field[1](item) for field, item in zip(fields, row))
        queue.append(row_parsed)
        if len(queue) >= 10000:
            db_dst.executemany(sql, queue)
            conn_dst.commit()

            done += len(queue)
            queue = []
            sys.stderr.write("\033[K> %d\r" % (done))
            sys.stdout.flush()

    if queue:
        db_dst.executemany(sql, queue)
        conn_dst.commit()

    sys.stderr.write("\033[K")
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--database", help="sqlite3 database file to update")
    ap.add_argument("INPUT_DB", nargs="+", help="database files to merge")

    args = ap.parse_args()

    # connect to destination database file
    try:
        conn_dst = sqlite3.connect(args.database)
    except Exception as e:
        print(f"failed to connect to database {args.database!r}: {e}")
        sys.exit(1)

    db_dst = conn_dst.cursor()


    # create results table if it does not exist
    db_dst.execute(
        "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='testresults'"
    )

    if db_dst.fetchone()[0] == 0:
        conn_dst.cursor().execute(
            "CREATE TABLE testresults ("
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
        conn_dst.commit()

        print(f"created table testresults in database {args.database!r}")

    failures = 0

    for input_db in args.INPUT_DB:
        print(f"merging {input_db!r}...")
        try:
            conn_src = sqlite3.connect(input_db)
        except Exception as e:
            print(f"failed to connect to database {input_db!r}: {e}")
            failures += 1
        try:
            db_src = conn_src.cursor()
            merge(conn_dst, db_src)
        except:
            traceback.print_exc()
            failures += 1

    if failures:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
