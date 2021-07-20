#!/usr/bin/env python3
"""NetDEF FRR Topotest Results Statistics Tool ORM Database"""


#
# NetDEF FRR Topotest Results Statistics Tool ORM Database
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
import urllib.parse

# third party library imports
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import relationship, sessionmaker

# proprietary library imports
from lib.check import is_str_no_empty, is_int_min, is_bool, is_float_min, is_datetime
from lib.config import DatabaseConfig


# database timestamp string format (SQL DATETIME)
TOPOSTAT_DB_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S.%f"

# database type strings
TOPOSTAT_DB_TYPE_SQLITE3 = "sqlite3"
TOPOSTAT_DB_TYPE_MYSQL = "mysql"
TOPOSTAT_DB_TYPE_POSTGRESQL = "postgresql"

# database table names
TOPOSTAT_DIRECTORY_TABLE_NAME = "directories"
TOPOSTAT_MODULE_TABLE_NAME = "modules"
TOPOSTAT_TEST_TABLE_NAME = "tests"
TOPOSTAT_AGENT_TABLE_NAME = "agents"
TOPOSTAT_PLAN_TABLE_NAME = "plans"
TOPOSTAT_BUILD_TABLE_NAME = "builds"
TOPOSTAT_JOB_TABLE_NAME = "jobs"
TOPOSTAT_RESULT_TABLE_NAME = "results"
TOPOSTAT_ARCH_TABLE_NAME = "architectures"
TOPOSTAT_DIST_TABLE_NAME = "distributions"
TOPOSTAT_KVERS_TABLE_NAME = "kernelversions"


# TODO: [code]
"""
find some way to keep relationship between test and (directory, module) which
lets us differentiate between tests of different (directories, modules) with the
same names.

find some way to keep relationship between job and plan which
lets us differentiate between jobs of different plans with the same names.
"""


# sqlalchemy declarative base class
Base = declarative_base()


class Database:
    """ORM database"""

    def __init__(self):
        """initialize default set of variables"""

        self.conf = None
        self.engine = None
        self.session = None

    def apply_config(self, conf):
        """apply a database configuration"""

        if isinstance(conf, DatabaseConfig) and conf.check():
            self.conf = conf
            return True
        return False

    def connect(self):
        """connect to the database"""

        if self.compose_database_connection_str():
            try:
                self.engine = create_engine(
                    self.conf.database_connection_str, echo=False
                )
            except Exception:
                # One reason why an exception would occur could be a missing
                # database driver module (pysqlite3, pymysql or psycopg2) for
                # the configured database type.
                return False
            try:
                Base.metadata.create_all(self.engine)
                session_class = sessionmaker(bind=self.engine)
                self.session = session_class()
                return True
            except Exception:
                # We could run into an exception here if the database connection
                # fails, the database does not exist or our ORM Base got messed
                # up somehow.
                pass
        return False

    # TODO: [code] implement
    def close(self):
        """disconnect from the database"""

        return False

    def compose_database_connection_str(self):
        if self.conf.check():
            if self.conf.database_type == TOPOSTAT_DB_TYPE_SQLITE3:
                if is_str_no_empty(self.conf.sqlite3_database_file):
                    self.conf.database_connection_str = (
                        "sqlite:///" + self.conf.sqlite3_database_file
                    )
                    self.conf.database_str = (
                        "sqlite3:///" + self.conf.sqlite3_database_file
                    )
                    return True
            elif self.conf.database_type == TOPOSTAT_DB_TYPE_MYSQL:
                if (
                    is_str_no_empty(self.conf.mysql_username)
                    and is_str_no_empty(self.conf.mysql_password)
                    and is_str_no_empty(self.conf.mysql_server_address)
                    and is_int_min(self.conf.mysql_server_port, 1)
                    and is_str_no_empty(self.conf.mysql_database)
                ):
                    self.conf.database_connection_str = (
                        "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4".format(
                            self.conf.mysql_username,
                            urllib.parse.quote_plus(self.conf.mysql_password),
                            self.conf.mysql_server_address,
                            self.conf.mysql_server_port,
                            self.conf.mysql_database,
                        )
                    )
                    self.conf.database_str = "mysql://{}:{}/{}".format(
                        self.conf.mysql_server_address,
                        self.conf.mysql_server_port,
                        self.conf.mysql_database,
                    )
                    return True
            elif self.conf.database_type == TOPOSTAT_DB_TYPE_POSTGRESQL:
                # TODO: [test] postgresql database connection
                if (
                    is_str_no_empty(self.conf.postgresql_username)
                    and is_str_no_empty(self.conf.postgresql_password)
                    and is_str_no_empty(self.conf.postgresql_server_address)
                    and is_int_min(self.conf.postgresql_server_port, 1)
                    and is_str_no_empty(self.conf.postgresql_database)
                ):
                    self.conf.database_connection_str = (
                        "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
                            self.conf.postgresql_username,
                            urllib.parse.quote_plus(self.conf.postgresql_password),
                            self.conf.postgresql_server_address,
                            self.conf.postgresql_server_port,
                            self.conf.postgresql_database,
                        )
                    )
                    self.conf.database_str = "postgresql://{}:{}/{}".format(
                        self.conf.postgresql_server_address,
                        self.conf.postgresql_server_port,
                        self.conf.postgresql_database,
                    )
                    return True
            else:
                return False
        return False

    # TODO: [code] implement / find a way to check for errors on established
    # connection
    def check(self):
        return True


class Directory(Base):
    """Directory ORM database type"""

    __tablename__ = TOPOSTAT_DIRECTORY_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    def check(self):
        """performs an instance variable type and value check"""

        if is_str_no_empty(self.name):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name}
        return None


class Module(Base):
    """Module ORM database type"""

    __tablename__ = TOPOSTAT_MODULE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    directory_id = Column(
        Integer, ForeignKey(TOPOSTAT_DIRECTORY_TABLE_NAME + ".id"), nullable=False
    )
    directory = relationship("Directory")

    def check(self):
        """performs an instance variable type and value check"""

        if (
            is_str_no_empty(self.name)
            and isinstance(self.directory, Directory)
            and is_str_no_empty(self.directory.name)
        ):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name, "directory": self.directory.name}
        return None


class Test(Base):
    """Test ORM database type"""

    __tablename__ = TOPOSTAT_TEST_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    directory_id = Column(
        Integer, ForeignKey(TOPOSTAT_DIRECTORY_TABLE_NAME + ".id"), nullable=False
    )
    directory = relationship("Directory")

    module_id = Column(
        Integer, ForeignKey(TOPOSTAT_MODULE_TABLE_NAME + ".id"), nullable=False
    )
    module = relationship("Module")

    def check(self):
        """performs an instance variable type and value check"""

        if (
            is_str_no_empty(self.name)
            and isinstance(self.directory, Directory)
            and is_str_no_empty(self.directory.name)
            and isinstance(self.module, Module)
            and is_str_no_empty(self.module.name)
        ):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {
                "name": self.name,
                "directory": self.directory.name,
                "module": self.module.name,
            }
        return None


class Agent(Base):
    """Agent ORM database type"""

    __tablename__ = TOPOSTAT_AGENT_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    def check(self):
        """performs an instance variable type and value check"""

        if is_str_no_empty(self.name):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name}
        return None


class Plan(Base):
    """Plan ORM database type"""

    __tablename__ = TOPOSTAT_PLAN_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    def check(self):
        """performs an instance variable type and value check"""

        if is_str_no_empty(self.name):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name}
        return None


class Build(Base):
    """Build ORM database type"""

    __tablename__ = TOPOSTAT_BUILD_TABLE_NAME

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)

    plan_id = Column(
        Integer, ForeignKey(TOPOSTAT_PLAN_TABLE_NAME + ".id"), nullable=False
    )
    plan = relationship("Plan")

    def check(self):
        """performs an instance variable type and value check"""

        if (
            is_int_min(self.number, 1)
            and isinstance(self.plan, Plan)
            and is_str_no_empty(self.plan.name)
        ):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"number": self.number, "plan": self.plan.name}
        return None


class Job(Base):
    """Job ORM database type"""

    __tablename__ = TOPOSTAT_JOB_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    plan_id = Column(
        Integer, ForeignKey(TOPOSTAT_PLAN_TABLE_NAME + ".id"), nullable=False
    )
    plan = relationship("Plan")

    def check(self):
        """performs an instance variable type and value check"""

        if (
            is_str_no_empty(self.name)
            and isinstance(self.plan, Plan)
            and is_str_no_empty(self.plan.name)
        ):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name, "plan": self.plan.name}
        return None


class Architecture(Base):
    """Architecture ORM database type"""

    __tablename__ = TOPOSTAT_ARCH_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    def check(self):
        """performs an instance variable type and value check"""

        if is_str_no_empty(self.name):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name}
        return None


class Distribution(Base):
    """Distribution ORM database type"""

    __tablename__ = TOPOSTAT_DIST_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)

    def check(self):
        """performs an instance variable type and value check"""

        if is_str_no_empty(self.name):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"name": self.name}
        return None


# TODO: [check] if necessary, lots of things can go wrong.
class KernelVersion(Base):
    """KernelVersion ORM database type"""

    __tablename__ = TOPOSTAT_KVERS_TABLE_NAME

    id = Column(Integer, primary_key=True)
    major = Column(Integer, nullable=False)
    minor = Column(Integer, nullable=False)
    update = Column(Integer, nullable=False)

    def check(self):
        """performs an instance variable type and value check"""

        if (
            is_int_min(self.major, 1)
            and is_int_min(self.minor, 0)
            and is_int_min(self.update, 0)
        ):
            return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {"major": self.major, "minor": self.minor, "update": self.update}
        return None


class Result(Base):
    """Result ORM database type"""

    __tablename__ = TOPOSTAT_RESULT_TABLE_NAME

    id = Column(Integer, primary_key=True)

    directory_id = Column(
        Integer, ForeignKey(TOPOSTAT_DIRECTORY_TABLE_NAME + ".id"), nullable=False
    )
    directory = relationship("Directory")

    module_id = Column(
        Integer, ForeignKey(TOPOSTAT_MODULE_TABLE_NAME + ".id"), nullable=False
    )
    module = relationship("Module")

    test_id = Column(
        Integer, ForeignKey(TOPOSTAT_TEST_TABLE_NAME + ".id"), nullable=False
    )
    test = relationship("Test")

    passed = Column(Boolean, nullable=False)

    time = Column(Float, nullable=False)

    agent_id = Column(
        Integer, ForeignKey(TOPOSTAT_AGENT_TABLE_NAME + ".id"), nullable=False
    )
    agent = relationship("Agent")

    timestamp = Column(DateTime, nullable=False)

    plan_id = Column(
        Integer, ForeignKey(TOPOSTAT_PLAN_TABLE_NAME + ".id"), nullable=False
    )
    plan = relationship("Plan")

    build_id = Column(
        Integer, ForeignKey(TOPOSTAT_BUILD_TABLE_NAME + ".id"), nullable=False
    )
    build = relationship("Build")

    job_id = Column(
        Integer, ForeignKey(TOPOSTAT_JOB_TABLE_NAME + ".id"), nullable=False
    )
    job = relationship("Job")

    # TODO: [check] if necessary
    """
    architecture_id = Column(
        Integer, ForeignKey(TOPOSTAT_ARCH_TABLE_NAME + ".id"), nullable=False
    )
    architecture = relationship("Architecture")

    distribution_id = Column(
        Integer, ForeignKey(TOPOSTAT_DIST_TABLE_NAME + ".id"), nullable=False
    )
    distribution = relationship("Job")

    kernelversion_id = Column(
        Integer, ForeignKey(TOPOSTAT_KVERS_TABLE_NAME + ".id"), nullable=False
    )
    kernelversion = relationship("KernelVersion")
    """

    def check(self):
        """performs an instance variable type and value check"""

        if (
            isinstance(self.directory, Directory)
            and is_str_no_empty(self.directory.name)
            and isinstance(self.module, Module)
            and is_str_no_empty(self.module.name)
            and isinstance(self.test, Test)
        ):
            if (
                is_str_no_empty(self.test.name)
                and is_bool(self.passed)
                and is_float_min(self.time, 0.0)
                and isinstance(self.agent, Agent)
                and is_str_no_empty(self.agent.name)
            ):
                if (
                    is_datetime(self.timestamp)
                    and isinstance(self.plan, Plan)
                    and is_str_no_empty(self.plan.name)
                    and isinstance(self.build, Build)
                    and is_int_min(self.build.number, 1)
                ):
                    if is_str_no_empty(self.job.name):
                        # TODO: [code] add checks for arch, dist, kvers
                        return True
        return False

    def json(self):
        """returns a JSON object representation of the instance"""

        if self.check():
            return {
                "directory": self.directory.name,
                "module": self.module.name,
                "test": self.test.name,
                "passed": self.passed,
                "time": self.time,
                "agent": self.agent.name,
                "timestamp": self.timestamp,
                "plan": self.plan.name,
                "build": self.build.number,
                "job": self.job.name  # ,
                # "architecture": self.architecture.name,
                # "distribution": self.distribution.name,
                # "kernelversion": (
                #    self.kernelversion.major,
                #    self.kernelversion.minor,
                #    self.kernelversion.update
                # )
            }
        return None


# ORM database types list
TOPOSTAT_DB_TYPES = [Directory, Module, Test, Agent, Plan, Build, Job, Result]
