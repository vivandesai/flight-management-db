from datetime import date, datetime
from decimal import Decimal
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect, CSRFError
import mysql.connector

from .catalogue import ROOT, REPORTS, TRANSACTIONS, TRIGGERS, CATEGORIES
from .db import connection, query, run_report, setup_status, init_db_command, install_views_command, TABLES
from .admin_routes import admin
from .demos import run_transaction, run_trigger, TRIGGER_LABELS
from .workflows import ACTIONS, STATUSES, field, validate, execute_action


def create_app(test_config=None):
    load_dotenv(ROOT / ".env")
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
        MYSQL_HOST=os.getenv("MYSQL_HOST", "127.0.0.1"), MYSQL_PORT=os.getenv("MYSQL_PORT", "3306"),
        MYSQL_USER=os.getenv("MYSQL_USER", "root"), MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD", ""),
        MYSQL_DATABASE=os.getenv("MYSQL_DATABASE", "FlightManagement"),
        MAX_CONTENT_LENGTH=64 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    CSRFProtect(app)
    app.cli.add_command(init_db_command)
    app.cli.add_command(install_views_command)
    app.register_blueprint(admin)

    @app.template_filter("cell")
    def cell(value, column=""):
        if value is None:
            return "—"
        if isinstance(value, datetime):
            return value.strftime("%d %b %Y, %H:%M")
        if isinstance(value, date):
            return value.strftime("%d %b %Y")
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        if isinstance(value, int):
            return f"{value:,}"
        return str(value)

    @app.template_filter("heading")
    def heading(value):
        return value.replace("_", " ").capitalize()

    @app.context_processor
    def shared():
        return dict(categories=CATEGORIES, actions=ACTIONS, reports=REPORTS, statuses=STATUSES)

    @app.errorhandler(mysql.connector.Error)
    def database_error(exc):
        app.logger.warning("Database request failed: %s (%s)", exc.errno, exc.sqlstate)
        return render_template("setup.html", title="Database connection", error=f"MySQL {exc.errno}: {exc.msg}"), 503

    @app.errorhandler(CSRFError)
    def csrf_error(exc):
        return render_template("error.html", title="Please reload this form", error="The form expired or has no valid security token. Reload the page and try again."), 400

    @app.errorhandler(404)
    def not_found(exc):
        return render_template("error.html", title="Page not found", error="This page or report does not exist."), 404

    @app.before_request
    def check_setup():
        if request.endpoint is None or request.endpoint == "static":
            return None
        with connection() as conn:
            missing = setup_status(conn)
        if missing:
            return render_template("setup.html", title="Database setup", missing=missing), 503

    def options(conn):
        return {
            "passenger": [(r["passenger_id"], f"{r['passenger_name']} · #{r['passenger_id']}") for r in query(conn, "SELECT passenger_id,passenger_name FROM Passenger ORDER BY passenger_name")],
            "flight": [(r["flight_id"], f"#{r['flight_id']} · {r['departure_airport']} → {r['arrival_airport']} · {r['departure_time']:%d %b %Y %H:%M} · {r['flight_status']}") for r in run_report(conn, REPORTS["J4"], {})],
            "booking": [(r["booking_id"], f"#{r['booking_id']} · {r['passenger_name']} · Flight {r['flight_id']} · {r['seat_number']}") for r in query(conn, "SELECT b.booking_id,p.passenger_name,b.flight_id,b.seat_number FROM Booking b JOIN Passenger p ON p.passenger_id=b.passenger_id ORDER BY b.booking_id")],
            "airline": [(r["airline_id"], f"{r['airline_name']} ({r['code']})") for r in query(conn, "SELECT * FROM Airline ORDER BY airline_name")],
            "airline_code": [(r["code"], f"{r['airline_name']} ({r['code']})") for r in query(conn, "SELECT * FROM Airline ORDER BY airline_name")],
            "aircraft": [(r["aircraft_id"], f"{r['registration_no']} · {r['airline_name']}") for r in run_report(conn, REPORTS["J2"], {})],
            "airport": [(r["airport_id"], f"{r['airport_code']} · {r['city']}") for r in query(conn, "SELECT * FROM Airport ORDER BY city")],
            "city": [(r["city"], r["city"]) for r in query(conn, "SELECT DISTINCT city FROM Airport ORDER BY city")],
            "status": [(s, s) for s in STATUSES],
        }

    @app.get("/")
    def overview():
        with connection() as conn:
            counts = run_report(conn, REPORTS["A1"], {})[0]
            revenue = run_report(conn, REPORTS["A2"], {})[0]["total_revenue"]
            popular = run_report(conn, REPORTS["A13"], {})
            occupancy = run_report(conn, REPORTS["A5"], {})
            schedule = run_report(conn, REPORTS["J4"], {})
        return render_template("overview.html", title="Operations overview", counts=counts,
                               revenue=revenue, popular=popular, occupancy=occupancy, schedule=schedule)

    @app.get("/reports")
    def report_list():
        search = request.args.get("q", "").strip().lower()
        category = request.args.get("category", "")
        selected = [r for r in REPORTS.values() if (not category or r.category == category)
                    and (not search or search in f"{r.id} {r.title} {r.description} {r.technique}".lower())]
        return render_template("reports.html", title=category or "All reports", selected=selected,
                               search=request.args.get("q", ""), category=category)

    @app.get("/reports/<report_id>")
    def report_detail(report_id):
        report = REPORTS.get(report_id)
        if not report:
            abort(404)
        specs = [field(name, {"from_city": "Departure city", "to_city": "Arrival city", "travel_date": "Travel date",
                              "airline_code": "Airline", "passenger_id": "Passenger", "flight_id": "Flight"}[name],
                       {"from_city": "city", "to_city": "city", "travel_date": "date", "airline_code": "airline_code",
                        "passenger_id": "passenger", "flight_id": "flight"}[name]) for name in report.inputs]
        rows, error = None, None
        values = request.args.to_dict()
        with connection() as conn:
            choices = options(conn) if specs else {}
            if not specs or "run" in request.args:
                try:
                    bound = validate(specs, request.args)
                    rows = run_report(conn, report, bound)
                except ValueError as exc:
                    error = str(exc)
                except mysql.connector.Error as exc:
                    error = f"MySQL {exc.errno} / SQLSTATE {exc.sqlstate}: {exc.msg}"
        return render_template("report.html", title=report.title, report=report, fields=specs,
                               choices=choices, values=values, rows=rows, error=error)

    @app.get("/records/<entity>")
    def records(entity):
        if entity not in TABLES:
            abort(404)
        with connection() as conn:
            rows = query(conn, f"SELECT * FROM `{entity}` ORDER BY 1, 2")
        return render_template("records.html", title=entity.replace("_", " ").capitalize(), rows=rows,
                               entity=entity, entities=TABLES)

    @app.get("/actions")
    def action_list():
        return render_template("actions.html", title="Management actions")

    @app.route("/actions/<action_id>", methods=["GET", "POST"])
    def action_detail(action_id):
        action = ACTIONS.get(action_id)
        if not action:
            abort(404)
        error, values = None, request.form.to_dict() if request.method == "POST" else {}
        with connection() as conn:
            choices = options(conn)
            if request.method == "POST":
                try:
                    v = validate(action["fields"], request.form)
                    if action_id == "cancel" and request.form.get("confirmed") != "yes":
                        impact = query(conn, "SELECT f.flight_id,f.flight_status,COUNT(b.booking_id) AS bookings FROM Flight f LEFT JOIN Booking b ON b.flight_id=f.flight_id WHERE f.flight_id=%s GROUP BY f.flight_id,f.flight_status", (v["flight_id"],))
                        return render_template("confirm.html", title="Confirm flight cancellation", action=action,
                                               values=values, impact=impact)
                    message = execute_action(conn, action_id, v)
                    flash(message, "success")
                    return redirect(url_for("action_detail", action_id=action_id))
                except ValueError as exc:
                    error = str(exc)
                except mysql.connector.Error as exc:
                    error = f"MySQL {exc.errno} / SQLSTATE {exc.sqlstate}: {exc.msg}. The management transaction was rolled back."
        return render_template("action.html", title=action["title"], action=action, action_id=action_id,
                               fields=action["fields"], choices=choices, values=values, error=error)

    @app.get("/database")
    def database_demos():
        return render_template("database.html", title="Database demonstrations", transactions=TRANSACTIONS,
                               triggers=TRIGGERS, trigger_labels=TRIGGER_LABELS)

    @app.route("/database/transactions/<int:demo_id>", methods=["GET", "POST"])
    def transaction_demo(demo_id):
        demo = TRANSACTIONS.get(demo_id)
        if not demo:
            abort(404)
        result = None
        if request.method == "POST":
            if request.form.get("confirmed") != "yes":
                abort(400, "Confirm the effects before running the original transaction.")
            with connection() as conn:
                result = run_transaction(conn, demo)
        return render_template("transaction.html", title=f"Transaction {demo_id}", demo=demo, result=result)

    @app.route("/database/triggers/<name>", methods=["GET", "POST"])
    def trigger_demo(name):
        trigger = next((t for t in TRIGGERS if t["name"] == name), None)
        if not trigger:
            abort(404)
        result = None
        if request.method == "POST":
            with connection() as conn:
                result = run_trigger(conn, name)
        return render_template("trigger.html", title=TRIGGER_LABELS[name][0], trigger=trigger,
                               description=TRIGGER_LABELS[name][1], result=result)

    return app
