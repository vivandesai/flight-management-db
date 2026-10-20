"""Allowlisted DBA operations; all SQL templates live in the new DBA script."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
import re

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData

from .catalogue import ROOT
from .db import query
from .workflows import field, PASSENGER_FIELDS, validate

SOURCE = "sql/dba/01_entity_operations.sql"


@dataclass(frozen=True)
class Entity:
    name: str
    keys: tuple
    fields: list


ENTITIES = {e.name: e for e in [
    Entity("Airline", ("airline_id",), [field("code", "Airline code", limit=10), field("airline_name", "Airline name", limit=100)]),
    Entity("Aircraft", ("aircraft_id",), [field("registration_no", "Registration", limit=20), field("model", "Model", limit=50), field("capacity", "Seat capacity", "integer")]),
    Entity("Airport", ("airport_id",), [field("airport_code", "Airport code", limit=10), field("airport_name", "Airport name", limit=100), field("city", "City", limit=100)]),
    Entity("Passenger", ("passenger_id",), PASSENGER_FIELDS),
    Entity("Flight", ("flight_id",), [field("departure_time", "Departure", "datetime-local"), field("arrival_time", "Arrival", "datetime-local"), field("flight_status", "Status", "status")]),
    Entity("Booking", ("booking_id",), [field("seat_number", "Seat number", limit=10), field("fare", "Fare", "money")]),
    Entity("Baggage", ("booking_id", "baggage_no"), [field("baggage_weight", "Weight (kg)", "weight")]),
]}


def load_statements():
    text = (ROOT / SOURCE).read_text(encoding="utf-8")
    markers = list(re.finditer(r"(?m)^-- name: ([\w.]+)\s*$", text))
    return {m[1]: dict(sql=text[m.end():markers[i+1].start() if i+1 < len(markers) else len(text)].strip(),
                       source=SOURCE, line=text.count("\n", 0, m.end()) + 2)
            for i, m in enumerate(markers)}


STATEMENTS = load_statements()


def run(conn, name, values=None):
    return query(conn, STATEMENTS[name]["sql"], values or {})


def key_values(entity, key):
    parts = key.split("-")
    if len(parts) != len(entity.keys) or any(not re.fullmatch(r"[1-9][0-9]{0,9}", p) or int(p) > 2147483647 for p in parts):
        raise ValueError("Invalid record key.")
    return {"key_" + name: int(value) for name, value in zip(entity.keys, parts)}


def record_key(entity, row):
    return "-".join(str(row[k]) for k in entity.keys)


def get_record(conn, entity, key, lock=False):
    rows = run(conn, entity.name + (".lock" if lock else ".get"), key_values(entity, key))
    if not rows:
        raise LookupError("This record no longer exists.")
    return rows[0]


def fingerprint(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()


def serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt="dba-row-v1")


def row_token(entity, row, operation):
    return serializer().dumps([entity.name, record_key(entity, row), operation, fingerprint(row)])


def check_token(entity, key, row, operation, token):
    try:
        expected = serializer().loads(token, max_age=3600)
    except BadData as exc:
        raise ValueError("This form expired or was changed. Reload the record and try again.") from exc
    if expected != [entity.name, key, operation, fingerprint(row)]:
        raise ValueError("This record changed since you opened it. Reload it before saving or deleting.")


def form_values(row):
    return {key: (value.isoformat() if isinstance(value, (date, datetime)) else "" if value is None else str(value))
            for key, value in row.items()}


def dependencies(conn, entity, key):
    return run(conn, entity.name + ".dependencies", key_values(entity, key))


def lock_parents(conn, entity, row):
    # Same parent-before-child order as booking, baggage, transfer and scheduling workflows.
    if entity.name == "Flight":
        get_record(conn, ENTITIES["Aircraft"], str(row["aircraft_id"]), lock=True)
    elif entity.name == "Booking":
        get_record(conn, ENTITIES["Flight"], str(row["flight_id"]), lock=True)
    elif entity.name == "Baggage":
        get_record(conn, ENTITIES["Booking"], str(row["booking_id"]), lock=True)


def validate_rules(conn, entity, old, values):
    name = entity.name
    clock = run(conn, "rule.clock")[0]
    if name == "Passenger":
        if values["dob"] >= clock["today"]:
            raise ValueError("Date of birth must be in the past.")
        if values["email"] is not None and not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", values["email"]):
            raise ValueError("Invalid email format.")
    elif name == "Booking" and values["fare"] <= 0:
        raise ValueError("Fare must be greater than zero.")
    elif name == "Baggage":
        if not 0 < values["baggage_weight"] <= 50:
            raise ValueError("Baggage weight must be between 0 and 50 kg.")
        total = run(conn, "rule.baggage_total", old)[0]["total"]
        if total + values["baggage_weight"] > Decimal("80"):
            raise ValueError("Total baggage weight for this booking cannot exceed 80kg.")
    elif name == "Aircraft":
        flights = run(conn, "rule.aircraft_flights", old)
        for flight in flights:
            if run(conn, "rule.booked_seats", flight)[0]["booked"] > values["capacity"]:
                raise ValueError(f"Capacity is below the booked seat count on Flight {flight['flight_id']}.")
    elif name == "Flight":
        changed_times = any(values[k] != old[k] for k in ("departure_time", "arrival_time"))
        reactivating = old["flight_status"] == "Cancelled" and values["flight_status"] != "Cancelled"
        if changed_times and values["departure_time"] <= clock["now"]:
            raise ValueError("Changed departure time must be in the future.")
        if values["arrival_time"] <= values["departure_time"]:
            raise ValueError("Arrival time must be after departure time.")
        if values["flight_status"] != "Cancelled" and (changed_times or reactivating):
            if run(conn, "rule.overlap", {**old, **values}):
                raise ValueError("Aircraft is already scheduled for another flight during this time.")


def mutate(conn, entity, key, operation, token, data=None):
    if operation not in ("update", "delete"):
        raise ValueError("Unknown DBA operation.")
    values = validate(entity.fields, data or {}) if operation == "update" else {}
    conn.start_transaction(isolation_level="READ COMMITTED")
    try:
        preview = get_record(conn, entity, key)
        lock_parents(conn, entity, preview)
        old = get_record(conn, entity, key, lock=True)
        check_token(entity, key, old, operation, token)
        if operation == "delete":
            blocked = [r for r in dependencies(conn, entity, key) if r["row_count"]]
            if blocked:
                raise ValueError("Deletion blocked by dependent records: " + ", ".join(f"{r['entity']} ({r['row_count']})" for r in blocked))
        else:
            validate_rules(conn, entity, old, values)
        run(conn, entity.name + "." + operation, {**key_values(entity, key), **values})
        conn.commit()
    except Exception:
        conn.rollback()
        raise
