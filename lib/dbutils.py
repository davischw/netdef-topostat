#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool ORM Database Utility Functions"""


#
# NetDEF FRR Topotest Results Statistics Tool ORM Database Utility Functions
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


# third party imports
from sqlalchemy.exc import SQLAlchemyError

# proprietary library imports
from lib.database import (
    Base,
    Database,
    Directory,
    Module,
    Test,
    Agent,
    Plan,
    Build,
    Job,
    Result,
    TOPOSTAT_DB_TYPES,
)
from lib.topotestresult import (
    TopotestResult,
    TOPOSTAT_TTR_PASSED,
    TOPOSTAT_TTR_FAILED,
)
from lib.check import is_str_no_empty, is_int_min, is_list_no_empty


# TODO: [code] move to generic combinatory retrieval and/or deprecate
def generic_get_by_name(name, generic_type, database):
    if is_str_no_empty(name) and isinstance(database, Database):
        try:
            return (
                database.session.query(generic_type)
                .filter_by(name=name.strip())
                .first()
            )
        except SQLAlchemyError:
            pass
    return None


# TODO: [code] implement
def generic_get_by_combination(combination: list, database: Database) -> Base:
    """
    retrieves an ORM database object from a database based on a combination of
    conditions
    """

    assert False
    """
    if is_list_no_empty(combination) and isinstance(database, Database):
        for condition in combination:
            if not isinstance(condition, dict):
                return None
            if (
                not "type" in condition.__dict__
                or not type(condition["type"]) in TOPOSTAT_DB_TYPES
            ):
                return None
    """
    return None


def get_directory_by_name(name, database):
    """retrieves a Directory ORM database object from a database by its name"""

    return generic_get_by_name(name, Directory, database)


# TODO: [code] deprecate
def get_module_by_name(name, database):
    """retrieves a Module ORM database object from a database by its name"""

    return generic_get_by_name(name, Module, database)


def get_module_by_name_and_directory(name, directory, database):
    """
    retrieves a Module ORM database object from a database by its name and
    related directory
    """

    # TODO: [code] either go with combinatory retrieval or deprecate
    """
    combination = [
        { "key": "name", "value": name, "type": Module },
        { "key": "name", "value": directory, "type": Directory }
    ]
    return generic_get_by_combination(combination, database)
    """

    if is_str_no_empty(name) and isinstance(database, Database):
        directory_obj = get_directory_by_name(directory, database)
        if directory_obj:
            try:
                return (
                    database.session.query(Module)
                    .filter_by(name=name.strip(), directory=directory_obj)
                    .first()
                )
            except SQLAlchemyError:
                pass
    return None


# TODO: [code] deprecate
def get_test_by_name(name, database):
    """retrieves a Test ORM database object from a database by its name"""

    return generic_get_by_name(name, Test, database)


def get_test_by_name_and_module_and_directory(name, module, directory, database):
    """
    retrieves a Test ORM database object from a database by its name and related
    module and directory
    """

    if is_str_no_empty(name) and is_str_no_empty(module) and is_str_no_empty(directory):
        combination = [
            {"key": "name", "value": name, "type": Test},
            {"key": "name", "value": module, "type": Module},
            {"key": "name", "value": directory, "type": Directory},
        ]
        return generic_get_by_combination(combination, database)
    return None


def get_agent_by_name(name, database):
    """retrieves an Agent ORM database object from a database by its name"""

    return generic_get_by_name(name, Agent, database)


def get_plan_by_name(name, database):
    """retrieves a Plan ORM database object from a database by its name"""

    return generic_get_by_name(name, Plan, database)


# TODO: [code] deprecate
def get_job_by_name(name, database):
    """retrieves a Job ORM database object from a database by its name"""

    return generic_get_by_name(name, Job, database)


def get_job_by_name_and_plan(name, plan, database):
    """
    retrieves a Job ORM database object from a database by its name and related
    plan
    """

    if is_str_no_empty(name) and is_str_no_empty(plan):
        combination = [
            {"key": "name", "value": name, "type": Job},
            {"key": "name", "value": name, "type": Plan},
        ]
        return generic_get_by_combination(combination, database)
    return None


def get_build_by_number(number, database):
    """retrieves a Build ORM database object from a database by its number"""

    if is_int_min(number, 1) and isinstance(database, Database):
        try:
            return database.session.query(Build).filter_by(number=number).first()
        except SQLAlchemyError:
            pass
    return None


# TODO: [test]
# TODO: [code] deprecate after database migration
def result_to_topotestresult(result: Result, database: Database) -> TopotestResult:
    """converts a Result ORM database object to TopotestResult object"""

    if isinstance(result, Result):
        if isinstance(database, Database) and database.check():
            ttr_name = (
                result.directory.name
                + "."
                + result.module.name
                + "."
                + result.test.name
            )

            if result.passed:
                ttr_result = TOPOSTAT_TTR_PASSED
            else:
                ttr_result = TOPOSTAT_TTR_FAILED

            ttr = TopotestResult(
                name=ttr_name,
                result=ttr_result,
                time=result.time,
                host=result.agent.name,
                timestamp=result.timestamp,
                plan=result.plan.name,
                build=result.build.number,
                job=result.job.name,
            )

            if ttr.check():
                return ttr
    return None


def topotestresult_to_result(ttr: TopotestResult, database: Database) -> Result:
    """converts a TopotestResult object to a Result ORM database object"""

    if isinstance(ttr, TopotestResult) and ttr.check():
        print("debug_1350")
        if isinstance(database, Database) and database.check():
            print("debug_1351")
            if is_str_no_empty(ttr.name) and len(ttr.name.split(".")) == 3:
                print("debug_1352")
                directory_name = ttr.name.split(".")[0]
                module_name = ttr.name.split(".")[1]
                test_name = ttr.name.split(".")[2]

                directory = get_directory_by_name(directory_name, database)
                if not directory:
                    directory = Directory(name=directory_name.strip())

                module = get_module_by_name(module_name, database)
                if not module:
                    module = Module(name=module_name.strip(), directory=directory)

                test = get_test_by_name(test_name, database)
                if not test:
                    test = Test(
                        name=test_name.strip(), module=module, directory=directory
                    )

                agent = get_agent_by_name(ttr.host, database)
                if not agent:
                    agent = Agent(name=ttr.host.strip())

                plan = get_plan_by_name(ttr.plan, database)
                if not plan:
                    plan = Plan(name=ttr.plan.strip())

                build = get_build_by_number(ttr.build, database)
                if not build:
                    build = Build(number=ttr.build, plan=plan)

                job = get_job_by_name(ttr.job, database)
                if not job:
                    job = Job(name=ttr.job.strip(), plan=plan)

                if (
                    directory.check()
                    and module.check()
                    and test.check()
                    and agent.check()
                    and plan.check()
                ):
                    if build.check() and job.check():
                        return Result(
                            directory=directory,
                            module=module,
                            test=test,
                            passed=ttr.passed(),
                            time=ttr.time,
                            agent=agent,
                            timestamp=ttr.timestamp,
                            plan=plan,
                            build=build,
                            job=job,
                        )
    return None
