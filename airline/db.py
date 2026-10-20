"""Direct MySQL access and explicit initialization using unmodified scripts."""
from contextlib import contextmanager
import os

import click
from flask import current_app
import mysql.connector

from .catalogue import ROOT, TRIGGERS

TABLES = ("Airline", "Aircraft", "Airport", "Passenger", "Flight", "Booking", "Baggage",
          "flight_status_log", "booking_cancellation_log", "booking_creation_log")


def connect(server_only=False):
    config = current_app.config if current_app else os.environ
    args = dict(host=config.get("MYSQL_HOST", "127.0.0.1"),
                port=int(config.get("MYSQL_PORT", 3306)),
                user=config.get("MYSQL_USER", "root"),
                password=config.get("MYSQL_PASSWORD", ""),
                autocommit=True, connection_timeout=5,
                charset="utf8mb4", use_pure=True)
    if not server_only:
        args["database"] = config.get("MYSQL_DATABASE", "FlightManagement")
    return mysql.connector.connect(**args)


@contextmanager
def connection():
    conn = connect()
    try:
        yield conn
    finally:
        if conn.in_transaction:
            conn.rollback()
        conn.close()


def query(conn, sql, params=None):
    with conn.cursor(dictionary=True) as cur:
        cur.execute(sql, params)
        return cur.fetchall() if cur.with_rows else []


def run_report(conn, report, values):
    for name in report.inputs:
        # Variable identifiers come exclusively from the checked-in catalogue.
        query(conn, f"SET @{name} = %s", (values[name],))
    return query(conn, report.sql)


def setup_status(conn):
    tables = {row["TABLE_NAME"].lower() for row in query(conn,
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")}
    triggers = {row["TRIGGER_NAME"] for row in query(conn,
        "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE()")}
    missing = [name for name in TABLES if name.lower() not in tables]
    missing += [t["name"] for t in TRIGGERS if t["name"] not in triggers]
    return missing


def execute_script(conn, path):
    # Connector/Python supports MySQL DELIMITER directives, including trigger bodies.
    with conn.cursor() as cur:
        cur.execute((ROOT / path).read_text(encoding="utf-8"))
        while True:
            if cur.with_rows:
                cur.fetchall()
            if not cur.nextset():
                break


def initialize(conn):
    existing = query(conn, "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
                     ("FlightManagement",))
    if existing:
        raise ValueError("FlightManagement already exists. Initialization refuses to overwrite or reseed it.")
    for path in ("sql/01_create_database.sql", "sql/02_create_tables.sql", "sql/03_insert_data.sql",
                 "sql/triggers/01_triggers.sql"):
        execute_script(conn, path)
    install_views(conn)


def install_views(conn):
    missing = setup_status(conn)
    if missing:
        raise ValueError("Install the original tables and triggers first. Missing: " + ", ".join(missing))
    execute_script(conn, "sql/views/01_management_views.sql")


@click.command("install-views")
def install_views_command():
    """Install or replace only the seven management views in the configured database."""
    try:
        with connection() as conn:
            install_views(conn)
    except (ValueError, mysql.connector.Error) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo("Installed seven management views. Base tables and stored rows were not changed.")


@click.command("init-db")
@click.option("--fresh", is_flag=True, help="Explicitly initialize a new FlightManagement database.")
def init_db_command(fresh):
    if not fresh:
        raise click.ClickException("Use init-db --fresh only when FlightManagement does not exist.")
    if current_app.config["MYSQL_DATABASE"] != "FlightManagement":
        raise click.ClickException("The unchanged scripts create FlightManagement; set MYSQL_DATABASE accordingly.")
    conn = connect(server_only=True)
    try:
        initialize(conn)
    except (ValueError, mysql.connector.Error) as exc:
        raise click.ClickException(str(exc)) from exc
    finally:
        conn.close()
    click.echo("Created FlightManagement using the four original scripts, followed by seven views. Installed 12 triggers after seed data.")
