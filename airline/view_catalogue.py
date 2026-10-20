"""Metadata and original definitions for seven separately installed SQL views."""
import re

from .catalogue import ROOT

SOURCE = "sql/views/01_management_views.sql"
LABELS = {
    "vw_flight_operations": ("Flight operations", "Airlines, aircraft, routes and schedules together. Based on J4.", "Flights"),
    "vw_flight_occupancy": ("Flight occupancy", "Booked seats, remaining capacity and occupancy for every flight. Based on A5.", "Flights"),
    "vw_airline_performance": ("Airline performance", "Fleet size, flight activity, bookings and recorded fare revenue.", "Revenue"),
    "vw_passenger_activity": ("Passenger activity", "Contacts, booking counts, spending and the latest booking date.", "Passengers"),
    "vw_booking_manifest": ("Booking manifest", "Passenger and seat assignments with flight, airline and route details.", "Bookings"),
    "vw_booking_baggage": ("Booking baggage", "Bag counts and total weight, including bookings without bags.", "Baggage"),
    "vw_airport_traffic": ("Airport traffic", "Departures and arrivals at each airport, including unused airports.", "Fleet & airports"),
}


def load_views():
    source = (ROOT / SOURCE).read_text(encoding="utf-8")
    definitions = list(re.finditer(r"CREATE OR REPLACE SQL SECURITY INVOKER VIEW (\w+)\s*\([^;]+;", source))
    if {m[1] for m in definitions} != set(LABELS) or len(definitions) != 7:
        raise ValueError("Expected exactly seven named view definitions.")
    return {m[1]: dict(name=m[1], id=f"V{i}", title=LABELS[m[1]][0], description=LABELS[m[1]][1], category=LABELS[m[1]][2],
                        sql=m[0], source=SOURCE, line=source.count("\n", 0, m.start()) + 1)
            for i, m in enumerate(definitions, 1)}


VIEWS = load_views()


def select_views(category="", search=""):
    search = search.strip().lower()
    return [v for v in VIEWS.values() if (not category or v["category"] == category)
            and (not search or search in f"{v['id']} {v['name']} {v['title']} {v['description']} SQL view".lower())]
