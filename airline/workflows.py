"""Small parameterized adapters for management forms. Business rules live in MySQL."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def field(name, label, kind="text", required=True, limit=None):
    return dict(name=name, label=label, kind=kind, required=required, limit=limit)


PASSENGER_FIELDS = [field("passenger_name", "Passenger name", limit=100), field("dob", "Date of birth", "date"),
                    field("phone", "Phone", required=False, limit=20), field("email", "Email", required=False, limit=100),
                    field("passport_no", "Passport number", limit=20)]
SCHEDULE_FIELDS = [field("departure_time", "Departure", "datetime-local"), field("arrival_time", "Arrival", "datetime-local"),
                   field("departure_airport_id", "Departure airport", "airport"),
                   field("arrival_airport_id", "Arrival airport", "airport")]
ACTIONS = {
    "register": dict(title="Register passenger", description="Add a passenger. MySQL checks birth date, email and passport uniqueness.", fields=PASSENGER_FIELDS),
    "book": dict(title="Create booking", description="Book an existing passenger and optionally register their first bag in the same transaction.", fields=[
        field("passenger_id", "Passenger", "passenger"), field("flight_id", "Flight", "flight"),
        field("seat_number", "Seat number", limit=10), field("fare", "Fare", "money"),
        field("baggage_weight", "First bag weight (kg, optional)", "weight", False)]),
    "transfer": dict(title="Transfer booking", description="Move a booking to another flight and preserve its actual baggage weights and numbers. Any failure rolls back the whole transfer.", fields=[
        field("booking_id", "Booking to transfer", "booking"), field("flight_id", "New flight", "flight"),
        field("seat_number", "New seat number", limit=10), field("fare", "New fare", "money")]),
    "baggage": dict(title="Add baggage", description="Register a bag. MySQL checks the individual 50 kg limit and the 80 kg booking total.", fields=[
        field("booking_id", "Booking", "booking"), field("baggage_no", "Bag number", "integer"), field("baggage_weight", "Weight (kg)", "weight")]),
    "contact": dict(title="Update passenger contact", description="Update phone and email. Leave either field blank to clear it.", fields=[
        field("passenger_id", "Passenger", "passenger"), field("phone", "Phone", required=False, limit=20), field("email", "Email", required=False, limit=100)]),
    "status": dict(title="Update flight status", description="Change the flight status. MySQL locks arrived flights and records status changes in its audit table.", fields=[
        field("flight_id", "Flight", "flight"), field("flight_status", "New status", "status")]),
    "cancel": dict(title="Cancel flight and bookings", description="Set a flight to Cancelled, delete its baggage and bookings, and retain the trigger-generated cancellation audit. All steps commit together.", fields=[field("flight_id", "Flight", "flight")]),
    "schedule": dict(title="Schedule flight", description="Schedule an existing aircraft. MySQL checks future departure, valid times, distinct airports, aircraft ownership and scheduling conflicts.", fields=[
        field("airline_id", "Airline", "airline"), field("aircraft_id", "Aircraft", "aircraft"), *SCHEDULE_FIELDS]),
    "onboard": dict(title="Onboard airline", description="Create an airline, register its first aircraft and schedule its first flight in one transaction.", fields=[
        field("code", "Airline code", limit=10), field("airline_name", "Airline name", limit=100),
        field("registration_no", "Aircraft registration", limit=20), field("model", "Aircraft model", limit=50),
        field("capacity", "Seat capacity", "integer"), *SCHEDULE_FIELDS]),
}
STATUSES = ("Scheduled", "Boarding", "Departed", "Delayed", "Arrived", "Cancelled")


def validate(fields, data):
    values = {}
    for spec in fields:
        name = spec["name"]
        value = data.get(name, "").strip()
        if not value:
            if spec["required"]:
                raise ValueError(f'{spec["label"]} is required.')
            values[name] = None
            continue
        if spec.get("limit") and len(value) > spec["limit"]:
            raise ValueError(f'{spec["label"]} must be at most {spec["limit"]} characters.')
        try:
            if spec["kind"] in ("integer", "passenger", "flight", "booking", "airport", "airline", "aircraft"):
                value = int(value)
                if value < 1 or value > 2147483647:
                    raise ValueError()
            elif spec["kind"] in ("money", "weight"):
                value = Decimal(value)
                bound = Decimal("99999999.99") if spec["kind"] == "money" else Decimal("999.99")
                if not value.is_finite() or abs(value) > bound or value != value.quantize(Decimal("0.01")):
                    raise ValueError()
            elif spec["kind"] == "date":
                value = date.fromisoformat(value)
            elif spec["kind"] == "datetime-local":
                value = datetime.fromisoformat(value)
                if value.tzinfo is not None:
                    raise ValueError()
            elif spec["kind"] == "status" and value not in STATUSES:
                raise ValueError()
        except (ValueError, InvalidOperation, OverflowError) as exc:
            raise ValueError(f'{spec["label"]} has an invalid value.') from exc
        values[name] = value
    return values


def execute_action(conn, action, v):
    with conn.cursor(dictionary=True) as cur:
        def run(sql, params=()):
            cur.execute(sql, params)
            return cur.fetchall() if cur.with_rows else cur.lastrowid

        def lock_flight(flight_id):
            rows = run("SELECT flight_id FROM Flight WHERE flight_id = %s FOR UPDATE", (flight_id,))
            if not rows:
                raise ValueError("The selected flight no longer exists.")

        def flight(airline_id, aircraft_id):
            return run("INSERT INTO Flight (departure_time, arrival_time, flight_status, airline_id, aircraft_id, departure_airport_id, arrival_airport_id) VALUES (%s,%s,'Scheduled',%s,%s,%s,%s)",
                       (v["departure_time"], v["arrival_time"], airline_id, aircraft_id, v["departure_airport_id"], v["arrival_airport_id"]))

        conn.start_transaction()
        try:
            if action == "register":
                record_id = run("INSERT INTO Passenger (passenger_name,dob,phone,email,passport_no) VALUES (%s,%s,%s,%s,%s)", tuple(v[f["name"]] for f in PASSENGER_FIELDS))
                message = f"Passenger {record_id} registered."
            elif action == "book":
                lock_flight(v["flight_id"])
                record_id = run("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),%s,%s,%s,%s)",
                                (v["seat_number"], v["fare"], v["passenger_id"], v["flight_id"]))
                if v["baggage_weight"] is not None:
                    run("INSERT INTO Baggage (booking_id,baggage_no,baggage_weight) VALUES (%s,1,%s)", (record_id, v["baggage_weight"]))
                message = f"Booking {record_id} created. Booking and optional baggage committed together."
            elif action == "transfer":
                # Lock flight rows in stable order before the booking, shared with cancellation.
                old = run("SELECT flight_id FROM Booking WHERE booking_id=%s", (v["booking_id"],))
                if not old:
                    raise ValueError("The selected booking no longer exists.")
                for fid in sorted({old[0]["flight_id"], v["flight_id"]}):
                    lock_flight(fid)
                old = run("SELECT * FROM Booking WHERE booking_id=%s FOR UPDATE", (v["booking_id"],))
                if not old:
                    raise ValueError("The selected booking no longer exists.")
                if old[0]["flight_id"] == v["flight_id"]:
                    raise ValueError("Choose a different flight for a transfer.")
                bags = run("SELECT baggage_no,baggage_weight FROM Baggage WHERE booking_id=%s FOR UPDATE", (v["booking_id"],))
                run("DELETE FROM Baggage WHERE booking_id=%s", (v["booking_id"],))
                run("DELETE FROM Booking WHERE booking_id=%s", (v["booking_id"],))
                record_id = run("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),%s,%s,%s,%s)",
                                (v["seat_number"], v["fare"], old[0]["passenger_id"], v["flight_id"]))
                for bag in bags:
                    run("INSERT INTO Baggage (booking_id,baggage_no,baggage_weight) VALUES (%s,%s,%s)", (record_id, bag["baggage_no"], bag["baggage_weight"]))
                message = f"Transferred to booking {record_id}; preserved {len(bags)} bag(s)."
            elif action == "baggage":
                if not run("SELECT booking_id FROM Booking WHERE booking_id=%s FOR UPDATE", (v["booking_id"],)):
                    raise ValueError("The selected booking no longer exists.")
                run("INSERT INTO Baggage (booking_id,baggage_no,baggage_weight) VALUES (%s,%s,%s)", (v["booking_id"], v["baggage_no"], v["baggage_weight"]))
                message = "Baggage registered."
            elif action == "contact":
                if not run("SELECT passenger_id FROM Passenger WHERE passenger_id=%s FOR UPDATE", (v["passenger_id"],)):
                    raise ValueError("The selected passenger no longer exists.")
                run("UPDATE Passenger SET phone=%s,email=%s WHERE passenger_id=%s", (v["phone"], v["email"], v["passenger_id"]))
                message = "Passenger contact updated."
            elif action == "status":
                lock_flight(v["flight_id"])
                run("UPDATE Flight SET flight_status=%s WHERE flight_id=%s", (v["flight_status"], v["flight_id"]))
                message = "Flight status updated. Any change is recorded by the audit trigger."
            elif action == "cancel":
                lock_flight(v["flight_id"])
                run("UPDATE Flight SET flight_status='Cancelled' WHERE flight_id=%s", (v["flight_id"],))
                run("DELETE FROM Baggage WHERE booking_id IN (SELECT booking_id FROM Booking WHERE flight_id=%s)", (v["flight_id"],))
                run("DELETE FROM Booking WHERE flight_id=%s", (v["flight_id"],))
                message = f"Flight cancelled; {cur.rowcount} booking(s) removed. Cancellation audit retained."
            elif action == "schedule":
                # Serializes schedules for the same aircraft before MySQL's overlap check.
                run("SELECT aircraft_id FROM Aircraft WHERE aircraft_id=%s FOR UPDATE", (v["aircraft_id"],))
                message = f"Flight {flight(v['airline_id'], v['aircraft_id'])} scheduled."
            elif action == "onboard":
                airline_id = run("INSERT INTO Airline (code,airline_name) VALUES (%s,%s)", (v["code"], v["airline_name"]))
                aircraft_id = run("INSERT INTO Aircraft (registration_no,model,capacity,airline_id) VALUES (%s,%s,%s,%s)",
                                  (v["registration_no"], v["model"], v["capacity"], airline_id))
                message = f"Airline {airline_id}, aircraft {aircraft_id} and flight {flight(airline_id, aircraft_id)} created."
            else:
                raise ValueError("Unknown management action.")
            conn.commit()
            return message
        except Exception:
            conn.rollback()
            raise
