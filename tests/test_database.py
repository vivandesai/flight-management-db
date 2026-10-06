from datetime import datetime, timedelta
from decimal import Decimal
import re

import mysql.connector
import pytest

from airline.catalogue import REPORTS, TRANSACTIONS, TRIGGERS
from airline.db import initialize, query, run_report, setup_status
from airline.demos import run_transaction, run_trigger, snapshot
from airline.workflows import ACTIONS, execute_action, validate

pytestmark = pytest.mark.integration
INPUTS = dict(from_city="Mumbai", to_city="Delhi", travel_date="2026-10-05", airline_code="AI", passenger_id=1, flight_id=1)


@pytest.mark.parametrize("report_id", list(REPORTS))
def test_every_original_report(database, app, report_id):
    rows = run_report(database, REPORTS[report_id], INPUTS)
    assert isinstance(rows, list)
    response = app.test_client().get(f"/reports/{report_id}", query_string={**INPUTS, "run": "1"})
    assert response.status_code == 200
    assert b"View SQL" in response.data
    assert b"MySQL 1064" not in response.data


def test_seed_counts_and_revenue(database):
    assert not setup_status(database)
    assert run_report(database, REPORTS["A1"], {}) == [dict(total_airlines=5, total_aircraft=7, total_airports=10, total_passengers=15, total_flights=12, total_bookings=29, total_baggage=20)]
    assert run_report(database, REPORTS["A2"], {})[0]["total_revenue"] == Decimal("271300.00")
    assert run_report(database, REPORTS["U3"], INPUTS)[0]["available_seats"] == 177
    assert run_report(database, REPORTS["U1"], INPUTS)[0]["flight_id"] == 1
    assert run_report(database, REPORTS["U1"], {**INPUTS, "travel_date": "2026-10-01"}) == []
    assert run_report(database, REPORTS["U8"], INPUTS)[0]["booking_id"] == 16


def test_bindings_do_not_leak_or_inject(database):
    assert run_report(database, REPORTS["U1"], {**INPUTS, "from_city": "Mumbai' OR 1=1 --"}) == []
    assert len(run_report(database, REPORTS["U1"], INPUTS)) == 1
    assert run_report(database, REPORTS["U5"], {**INPUTS, "passenger_id": 999999}) == []
    assert len(run_report(database, REPORTS["U5"], INPUTS)) == 2


@pytest.mark.parametrize("demo_id", list(TRANSACTIONS))
def test_all_original_transactions(database, demo_id):
    before = snapshot(database)
    result = run_transaction(database, TRANSACTIONS[demo_id])
    if demo_id == 3:
        assert "Cannot book a cancelled flight" in result["error"]
        assert query(database, "SELECT flight_status FROM Flight WHERE flight_id=11")[0]["flight_status"] == "Cancelled"
        assert len(query(database, "SELECT * FROM flight_status_log WHERE flight_id=11")) == 1
        assert not query(database, "SELECT * FROM Booking WHERE flight_id=11 AND seat_number='25A'")
    elif demo_id == 7 and datetime.now() >= datetime(2026, 11, 1, 10):
        assert "Departure time must be in the future" in result["error"]
        assert not query(database, "SELECT * FROM Airline WHERE code='QR'")
    else:
        assert result["error"] is None, result["error"]
        if demo_id == 1:
            assert len(query(database, "SELECT * FROM Passenger WHERE passport_no='P100016'")) == 1
            assert len(query(database, "SELECT * FROM booking_creation_log")) == 1
        elif demo_id == 2:
            assert not query(database, "SELECT * FROM Booking WHERE passenger_id=1 AND flight_id=1")
            booking = query(database, "SELECT * FROM Booking WHERE passenger_id=1 AND flight_id=10")[0]
            assert [b["baggage_weight"] for b in query(database, "SELECT * FROM Baggage WHERE booking_id=%s ORDER BY baggage_no", (booking["booking_id"],))] == [Decimal("18.50"), Decimal("7.20")]
        elif demo_id == 4:
            assert [b["seat_number"] for b in query(database, "SELECT * FROM Booking WHERE flight_id=2 ORDER BY booking_id")][-2:] == ["18A", "18B"]
            assert len(query(database, "SELECT * FROM booking_creation_log")) == 2
        elif demo_id == 5:
            assert [f["flight_status"] for f in query(database, "SELECT flight_status FROM Flight WHERE flight_id IN (3,4,7) ORDER BY flight_id")] == ["Boarding", "Scheduled", "Boarding"]
            assert len(query(database, "SELECT * FROM flight_status_log")) == 2
        elif demo_id == 6:
            assert not query(database, "SELECT * FROM Booking WHERE flight_id=9")
            assert len(query(database, "SELECT * FROM booking_cancellation_log")) == 2
        elif demo_id == 7:
            assert query(database, "SELECT * FROM Airline WHERE code='QR'")
            assert len(query(database, "SELECT * FROM Flight")) == 13
        elif demo_id == 8:
            assert snapshot(database) == before
        elif demo_id == 9:
            assert query(database, "SELECT email FROM Passenger WHERE passenger_id=4")[0]["email"] == "isha.new@email.com"
        elif demo_id == 10:
            assert [r["baggage_no"] for r in query(database, "SELECT * FROM Baggage WHERE booking_id=5 ORDER BY baggage_no")] == [1, 2, 3]


def test_repeated_transaction_exposes_actual_failure(database):
    assert run_transaction(database, TRANSACTIONS[1])["error"] is None
    before = snapshot(database)
    assert "Duplicate entry" in run_transaction(database, TRANSACTIONS[1])["error"]
    assert snapshot(database) == before


@pytest.mark.parametrize("name", [t["name"] for t in TRIGGERS])
def test_all_trigger_demos_restore_rows(database, name):
    before = snapshot(database)
    result = run_trigger(database, name)
    assert result["restored"]
    assert snapshot(database) == before
    if name in ("trg_flight_after_update", "trg_booking_after_insert", "trg_booking_after_delete"):
        assert result["error"] is None
        assert result["steps"][-1]["rows"]
    else:
        assert "SQLSTATE 45000" in result["error"]
        assert result["steps"][-1]["state"] == "Rejected by MySQL"


def action(conn, name, **values):
    return execute_action(conn, name, validate(ACTIONS[name]["fields"], {k: str(v) for k, v in values.items()}))


def test_management_workflows(database):
    action(database, "register", passenger_name="New customer", dob="2000-02-01", passport_no="NEWDOC")
    pid = query(database, "SELECT passenger_id FROM Passenger WHERE passport_no='NEWDOC'")[0]["passenger_id"]
    action(database, "book", passenger_id=pid, flight_id=1, seat_number="44A", fare="1000", baggage_weight="14.75")
    bid = query(database, "SELECT booking_id FROM Booking WHERE passenger_id=%s", (pid,))[0]["booking_id"]
    action(database, "baggage", booking_id=bid, baggage_no=2, baggage_weight="7.25")
    action(database, "transfer", booking_id=bid, flight_id=2, seat_number="44B", fare="2000")
    new_bid = query(database, "SELECT booking_id FROM Booking WHERE passenger_id=%s", (pid,))[0]["booking_id"]
    assert [r["baggage_weight"] for r in query(database, "SELECT * FROM Baggage WHERE booking_id=%s ORDER BY baggage_no", (new_bid,))] == [Decimal("14.75"), Decimal("7.25")]
    action(database, "contact", passenger_id=pid, phone="1234567890", email="new@example.com")
    action(database, "status", flight_id=2, flight_status="Boarding")
    action(database, "cancel", flight_id=2)
    assert not query(database, "SELECT * FROM Booking WHERE flight_id=2")
    assert not query(database, "SELECT * FROM Baggage WHERE booking_id=%s", (new_bid,))
    assert len(query(database, "SELECT * FROM booking_cancellation_log WHERE passenger_id=%s", (pid,))) == 2
    future = datetime.now() + timedelta(days=60)
    schedule = dict(departure_time=future.isoformat(timespec="minutes"), arrival_time=(future + timedelta(hours=2)).isoformat(timespec="minutes"), departure_airport_id=1, arrival_airport_id=2)
    action(database, "schedule", airline_id=1, aircraft_id=1, **schedule)
    action(database, "onboard", code="ZZ", airline_name="New airline", registration_no="ZZ-AIR", model="Airbus A320", capacity=180, **schedule)
    assert query(database, "SELECT * FROM Airline WHERE code='ZZ'")


def test_booking_with_invalid_baggage_rolls_back_audit(database):
    before = snapshot(database)
    with pytest.raises(mysql.connector.Error, match="Baggage weight"):
        action(database, "book", passenger_id=15, flight_id=1, seat_number="45A", fare="1000", baggage_weight="51")
    assert snapshot(database) == before


def test_failed_transfer_keeps_actual_baggage(database):
    before = snapshot(database)
    with pytest.raises(mysql.connector.Error, match="Seat is already taken"):
        action(database, "transfer", booking_id=1, flight_id=2, seat_number="10A", fare="1000")
    assert snapshot(database) == before


@pytest.mark.parametrize("sql,params,message", [
    ("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'99A',0,15,1)", (), "Fare must be greater"),
    ("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'99A',10,1,1)", (), "Passenger already"),
    ("INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'12A',10,15,1)", (), "Seat is already"),
    ("INSERT INTO Passenger (passenger_name,dob,email,passport_no) VALUES ('Bad email','2000-01-01','bad-email','BADMAIL')", (), "Invalid email"),
    ("UPDATE Flight SET arrival_time=departure_time WHERE flight_id=1", (), "Arrival time"),
    ("UPDATE Flight SET arrival_airport_id=departure_airport_id WHERE flight_id=1", (), "Departure and arrival airports"),
])
def test_additional_trigger_rules(database, sql, params, message):
    with pytest.raises(mysql.connector.Error, match=message):
        query(database, sql, params)


def test_capacity_rule(database):
    query(database, "UPDATE Aircraft SET capacity=3 WHERE aircraft_id=1")
    with pytest.raises(mysql.connector.Error, match="fully booked"):
        query(database, "INSERT INTO Booking (booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'99A',10,15,1)")


def test_new_flight_validation_rules(database):
    future = datetime.now() + timedelta(days=60)
    statement = "INSERT INTO Flight (departure_time,arrival_time,flight_status,airline_id,aircraft_id,departure_airport_id,arrival_airport_id) VALUES (%s,%s,'Scheduled',%s,%s,%s,%s)"
    scenarios = [
        ((datetime(2000, 1, 1), datetime(2000, 1, 2), 1, 1, 1, 2), "Departure time"),
        ((future, future + timedelta(hours=2), 1, 1, 1, 1), "Departure and arrival airports"),
        ((future, future + timedelta(hours=2), 2, 1, 1, 2), "Aircraft does not belong"),
    ]
    for params, message in scenarios:
        with pytest.raises(mysql.connector.Error, match=message):
            query(database, statement, params)
    query(database, statement, (future, future + timedelta(hours=2), 1, 1, 1, 2))
    with pytest.raises(mysql.connector.Error, match="already scheduled"):
        query(database, statement, (future, future + timedelta(hours=1), 1, 1, 1, 2))


def test_initializer_refuses_existing_database(database):
    before = snapshot(database)
    with pytest.raises(ValueError, match="already exists"):
        initialize(database)
    assert snapshot(database) == before


def token(client, path):
    response = client.get(path)
    assert response.status_code == 200
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)


def test_pages_forms_confirmation_and_csrf(database, app):
    client = app.test_client()
    for path in ["/", "/reports", "/reports?category=Flights", "/actions", "/database"]:
        assert client.get(path).status_code == 200
    for name in ACTIONS:
        assert client.get(f"/actions/{name}").status_code == 200
    for name in snapshot(database):
        assert client.get(f"/records/{name}").status_code == 200
    for i in TRANSACTIONS:
        assert client.get(f"/database/transactions/{i}").status_code == 200
    for t in TRIGGERS:
        assert client.get(f"/database/triggers/{t['name']}").status_code == 200
    assert client.post("/actions/book", data={}).status_code == 400
    csrf = token(client, "/actions/cancel")
    before = snapshot(database)
    review = client.post("/actions/cancel", data=dict(csrf_token=csrf, flight_id=9))
    assert review.status_code == 200 and b"Confirm cancellation" in review.data
    assert snapshot(database) == before
    done = client.post("/actions/cancel", data=dict(csrf_token=csrf, flight_id=9, confirmed="yes"))
    assert done.status_code == 302
    assert not query(database, "SELECT * FROM Booking WHERE flight_id=9")
    assert client.get("/reports/does-not-exist").status_code == 404
    assert client.get("/records/Passenger%3BDROP%20TABLE%20Passenger").status_code == 404
    assert client.get("/reports/U5?run=1&passenger_id=bad").status_code == 200
    assert client.post("/database/transactions/1", data=dict(csrf_token=csrf)).status_code == 400
    demo = client.post("/database/triggers/trg_flight_after_update", data=dict(csrf_token=csrf))
    assert demo.status_code == 200 and b"original rows and audit logs restored" in demo.data


def test_missing_triggers_actionable_without_auto_setup(database, app):
    query(database, "DROP TRIGGER trg_booking_before_insert")
    response = app.test_client().get("/")
    assert response.status_code == 503
    assert b"trg_booking_before_insert" in response.data
    assert b"never initializes" in response.data


def test_database_unavailable_page(app):
    app.config["MYSQL_PORT"] = "33319"
    response = app.test_client().get("/")
    assert response.status_code == 503
    assert b"Retry connection" in response.data


def test_management_http_forms(database, app):
    client = app.test_client()

    def submit(name, values):
        csrf = token(client, f"/actions/{name}")
        response = client.post(f"/actions/{name}", data={**values, "csrf_token": csrf})
        assert response.status_code == 302, response.text
        response = client.get(response.headers["Location"])
        assert response.status_code == 200 and b"alert-success" in response.data

    submit("register", dict(passenger_name="HTTP customer", dob="2000-01-01", passport_no="HTTPDOC"))
    pid = query(database, "SELECT passenger_id FROM Passenger WHERE passport_no='HTTPDOC'")[0]["passenger_id"]
    submit("book", dict(passenger_id=pid, flight_id=1, seat_number="77A", fare="9000", baggage_weight="12"))
    bid = query(database, "SELECT booking_id FROM Booking WHERE passenger_id=%s", (pid,))[0]["booking_id"]
    submit("baggage", dict(booking_id=bid, baggage_no=2, baggage_weight="7"))
    submit("transfer", dict(booking_id=bid, flight_id=2, seat_number="77B", fare="9500"))
    submit("contact", dict(passenger_id=pid, phone="1234567890", email="http@example.com"))
    submit("status", dict(flight_id=2, flight_status="Boarding"))
    future = datetime.now() + timedelta(days=60)
    times = dict(departure_time=future.isoformat(timespec="minutes"), arrival_time=(future + timedelta(hours=2)).isoformat(timespec="minutes"), departure_airport_id=1, arrival_airport_id=2)
    submit("schedule", dict(airline_id=1, aircraft_id=1, **times))
    submit("onboard", dict(code="HT", airline_name="HTTP airline", registration_no="HT-001", model="A320", capacity=180, **times))
    # Cancellation's two-stage HTTP path is covered separately above.


def test_transaction_http_evidence(database, app):
    client = app.test_client()
    csrf = token(client, "/database/transactions/4")
    response = client.post("/database/transactions/4", data=dict(csrf_token=csrf, confirmed="yes"))
    assert response.status_code == 200
    assert b"Committed as written" in response.data
    assert b"Rolled back to savepoint" in response.data
    assert b"Persistent database changes" in response.data
    assert len(query(database, "SELECT * FROM booking_creation_log")) == 2
