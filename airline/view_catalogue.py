"""Metadata and original definitions for seven separately installed SQL views."""
import re

from .catalogue import ROOT

SOURCE = "sql/views/01_management_views.sql"
LABELS = {
    "vw_flight_operations": ("Flight operations", "Airlines, aircraft, routes and schedules together. Based on J4."),
    "vw_flight_occupancy": ("Flight occupancy", "Booked seats, remaining capacity and occupancy for every flight. Based on A5."),
    "vw_airline_performance": ("Airline performance", "Fleet size, flight activity, bookings and recorded fare revenue."),
    "vw_passenger_activity": ("Passenger activity", "Contacts, booking counts, spending and the latest booking date."),
    "vw_booking_manifest": ("Booking manifest", "Passenger and seat assignments with flight, airline and route details."),
    "vw_booking_baggage": ("Booking baggage", "Bag counts and total weight, including bookings without bags."),
    "vw_airport_traffic": ("Airport traffic", "Departures and arrivals at each airport, including unused airports."),
}


def load_views():
    source = (ROOT / SOURCE).read_text(encoding="utf-8")
    definitions = list(re.finditer(r"CREATE OR REPLACE SQL SECURITY INVOKER VIEW (\w+)\s*\([^;]+;", source))
    if {m[1] for m in definitions} != set(LABELS) or len(definitions) != 7:
        raise ValueError("Expected exactly seven named view definitions.")
    return {m[1]: dict(name=m[1], title=LABELS[m[1]][0], description=LABELS[m[1]][1],
                        sql=m[0], source=SOURCE, line=source.count("\n", 0, m.start()) + 1)
            for m in definitions}


VIEWS = load_views()
