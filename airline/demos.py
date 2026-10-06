"""Original transaction execution and reversible demonstrations of all triggers."""
from datetime import datetime, timedelta
from uuid import uuid4

import mysql.connector
import sqlparse

from .db import query, TABLES

TRIGGER_LABELS = {
    "trg_flight_before_insert": ("Validate a new flight", "Try an invalid arrival time on a temporary future flight."),
    "trg_flight_before_update": ("Validate changed flight times", "Try moving an arrival before its departure."),
    "trg_booking_before_insert": ("Prevent invalid bookings", "Try booking a cancelled flight."),
    "trg_baggage_before_insert": ("Limit individual bag weight", "Try registering a 51 kg bag."),
    "trg_passenger_before_insert": ("Validate passenger details", "Try registering a passenger born tomorrow."),
    "trg_flight_after_update": ("Audit flight status changes", "Change a temporary flight status and inspect the audit row."),
    "trg_booking_after_delete": ("Audit booking cancellations", "Delete a temporary booking and inspect the cancellation log."),
    "trg_booking_after_insert": ("Audit new bookings", "Insert a temporary booking and inspect its creation log."),
    "trg_flight_before_delete": ("Protect booked flights", "Try deleting a flight which still has a booking."),
    "trg_airline_before_delete": ("Protect active airlines", "Try deleting an airline which operates a flight."),
    "trg_flight_status_lock": ("Lock arrived flights", "Mark a temporary flight Arrived, then try changing its status."),
    "trg_baggage_total_limit": ("Limit total baggage", "Add two 40 kg bags, then try adding another 1 kg."),
}


def snapshot(conn):
    # Table names are a static allowlist, never request values.
    return {name: query(conn, f"SELECT * FROM `{name}` ORDER BY 1, 2") for name in TABLES}


def run_transaction(conn, demo):
    result = dict(steps=[], error=None, outcome="", before=snapshot(conn))
    conn.autocommit = True  # Preserves statements outside explicit transactions.
    committed = False
    for statement in sqlparse.split(demo["sql"]):
        clean = sqlparse.format(statement, strip_comments=True).strip()
        if not clean:
            continue
        step = dict(sql=statement, rows=[], affected=0, state="Executed")
        result["steps"].append(step)
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(statement)
                step["rows"] = cur.fetchall() if cur.with_rows else []
                step["affected"] = max(0, cur.rowcount)
            if clean.upper().startswith("COMMIT"):
                committed = True
            if clean.upper().startswith("ROLLBACK"):
                step["state"] = "Rolled back to savepoint" if "SAVEPOINT" in clean.upper() else "Rolled back"
        except mysql.connector.Error as exc:
            conn.rollback()  # A SIGNAL does not automatically roll back the entire transaction.
            result["error"] = f"MySQL {exc.errno} / SQLSTATE {exc.sqlstate}: {exc.msg}"
            step["state"] = "Rejected by MySQL"
            result["outcome"] = "Execution stopped; active transaction explicitly rolled back. Earlier committed or autocommitted changes remain."
            break
    if not result["error"]:
        result["outcome"] = "Committed as written." if committed else "Rolled back as written."
    if conn.in_transaction:
        conn.rollback()
    result["after"] = snapshot(conn)
    result["changes"] = changes(result["before"], result["after"])
    return result


def changes(before, after):
    return [{"table": table, "before": before[table], "after": after[table]}
            for table in before if before[table] != after[table]]


def run_trigger(conn, name):
    result = dict(steps=[], error=None, outcome="", changes=[])
    initial = snapshot(conn)
    conn.start_transaction()
    with conn.cursor(dictionary=True) as cur:
        def run(sql, params=()):
            step = dict(sql=sql, params=params, rows=[], affected=0, state="Executed")
            result["steps"].append(step)
            try:
                cur.execute(sql, params)
                step["rows"] = cur.fetchall() if cur.with_rows else []
                step["affected"] = max(0, cur.rowcount)
                return cur.lastrowid
            except mysql.connector.Error:
                step["state"] = "Rejected by MySQL"
                raise

        try:
            # All fixtures are new rows inside this transaction; demo works after normal data edits.
            code = "D" + uuid4().hex[:8]
            aid = run("INSERT INTO Airline (code,airline_name) VALUES (%s,'Temporary demonstration airline')", (code,))
            acid = run("INSERT INTO Aircraft (registration_no,model,capacity,airline_id) VALUES (%s,'Demo aircraft',4,%s)", (code, aid))
            ap1 = run("INSERT INTO Airport (airport_code,airport_name,city) VALUES (%s,'Demo departure','Demo city A')", (code + "A",))
            ap2 = run("INSERT INTO Airport (airport_code,airport_name,city) VALUES (%s,'Demo arrival','Demo city B')", (code + "B",))
            pid = run("INSERT INTO Passenger (passenger_name,dob,passport_no) VALUES ('Demo passenger','2000-01-01',%s)", (code,))
            depart = datetime.now() + timedelta(days=30)
            arrive = depart + timedelta(hours=2)
            fid = run("INSERT INTO Flight (departure_time,arrival_time,flight_status,airline_id,aircraft_id,departure_airport_id,arrival_airport_id) VALUES (%s,%s,'Scheduled',%s,%s,%s,%s)", (depart, arrive, aid, acid, ap1, ap2))
            bid = run("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'1A',100,%s,%s)", (pid, fid))
            before = snapshot(conn)
            result["fixture_steps"] = result["steps"]
            result["steps"] = []
            if name == "trg_flight_before_insert":
                run("INSERT INTO Flight (departure_time,arrival_time,flight_status,airline_id,aircraft_id,departure_airport_id,arrival_airport_id) VALUES (%s,%s,'Scheduled',%s,%s,%s,%s)", (depart, depart, aid, acid, ap1, ap2))
            elif name == "trg_flight_before_update":
                run("UPDATE Flight SET arrival_time=departure_time WHERE flight_id=%s", (fid,))
            elif name == "trg_booking_before_insert":
                run("UPDATE Flight SET flight_status='Cancelled' WHERE flight_id=%s", (fid,))
                run("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'2A',100,%s,%s)", (pid, fid))
            elif name == "trg_baggage_before_insert":
                run("INSERT INTO Baggage (booking_id,baggage_no,baggage_weight) VALUES (%s,1,51)", (bid,))
            elif name == "trg_passenger_before_insert":
                run("INSERT INTO Passenger (passenger_name,dob,passport_no) VALUES ('Invalid demo',DATE_ADD(CURDATE(),INTERVAL 1 DAY),%s)", (code + "X",))
            elif name == "trg_flight_after_update":
                run("UPDATE Flight SET flight_status='Boarding' WHERE flight_id=%s", (fid,))
                run("SELECT * FROM flight_status_log WHERE flight_id=%s", (fid,))
            elif name == "trg_booking_after_delete":
                run("DELETE FROM Booking WHERE booking_id=%s", (bid,))
                run("SELECT * FROM booking_cancellation_log WHERE booking_id=%s", (bid,))
            elif name == "trg_booking_after_insert":
                run("DELETE FROM Booking WHERE booking_id=%s", (bid,))
                bid = run("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'2A',100,%s,%s)", (pid, fid))
                run("SELECT * FROM booking_creation_log WHERE booking_id=%s", (bid,))
            elif name == "trg_flight_before_delete":
                run("DELETE FROM Flight WHERE flight_id=%s", (fid,))
            elif name == "trg_airline_before_delete":
                run("DELETE FROM Airline WHERE airline_id=%s", (aid,))
            elif name == "trg_flight_status_lock":
                run("UPDATE Flight SET flight_status='Arrived' WHERE flight_id=%s", (fid,))
                run("UPDATE Flight SET flight_status='Boarding' WHERE flight_id=%s", (fid,))
            elif name == "trg_baggage_total_limit":
                for number, weight in ((1, 40), (2, 40), (3, 1)):
                    run("INSERT INTO Baggage (booking_id,baggage_no,baggage_weight) VALUES (%s,%s,%s)", (bid, number, weight))
            else:
                raise ValueError("Unknown trigger demonstration.")
        except mysql.connector.Error as exc:
            result["error"] = f"MySQL {exc.errno} / SQLSTATE {exc.sqlstate}: {exc.msg}"
        finally:
            try:
                after = snapshot(conn)
                result["changes"] = changes(locals().get("before", initial), after)
            finally:
                conn.rollback()
    result["restored"] = snapshot(conn) == initial
    result["outcome"] = "Demonstration rolled back; original rows and audit logs restored." if result["restored"] else "Rollback verification failed."
    return result
