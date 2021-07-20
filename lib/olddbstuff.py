#!/usr/bin/env python3
"""collection of deprecated functions to use with sqlite3 database"""


# standard library imports
from sqlite3 import Connection, DatabaseError
from datetime import datetime

# proprietary library imports
from lib.topotestresult import TopotestResult, TOPOSTAT_TTR_VERSION_1
from lib.database import TOPOSTAT_DB_TIMESTAMP_FMT
from lib.check import is_str_no_empty


# TODO: [test]
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


# TODO: [test]
def sqlite3_create_table(conn: Connection, table: str) -> bool:
    """
    creates a table for TopotestResult object storage in a sqlite3 database
    """

    if isinstance(conn, Connection) and is_str_no_empty(table):
        sql_str = (
            "CREATE TABLE {} ("
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
        ).format(table)
        try:
            conn.cursor().execute(sql_str)
            conn.commit()
            return True
        except DatabaseError:
            pass
    return False


# TODO: [test]
def sqlite3_insert_topotestresult(
    ttr: TopotestResult, conn: Connection, table: str
) -> bool:
    """inserts a TopotestResult into a sqlite3 database"""

    if (
        isinstance(ttr, TopotestResult)
        and isinstance(conn, Connection)
        and is_str_no_empty(str)
    ):
        sql_str = (
            "INSERT INTO {} ("
            + "name, result, time, host, timestamp, plan, build, job"
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        ).format(table)
        try:
            conn.cursor().execute(
                sql_str,
                (
                    str(ttr.name),
                    str(ttr.result),
                    str(ttr.time),
                    str(ttr.host),
                    str(ttr.timestamp),
                    str(ttr.plan),
                    str(ttr.build),
                    str(ttr.job),
                ),
            )
            conn.commit()
            return True
        except DatabaseError:
            pass
    return False
