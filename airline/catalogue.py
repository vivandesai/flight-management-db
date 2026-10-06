"""Business labels around original SQL. Query text is read, never rewritten."""
from dataclasses import dataclass
from pathlib import Path
import re

import sqlparse

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Report:
    id: str
    title: str
    category: str
    description: str
    technique: str
    source: str
    line: int
    sql: str
    inputs: tuple[str, ...]


# Order follows the source files. Separate reports stay separate even when similar.
JOINS = [
    ("Flights by airline", "Flights", "Flight times alongside the operating airline."),
    ("Aircraft ownership", "Fleet & airports", "Aircraft registrations, models and capacities by airline."),
    ("Flight routes", "Flights", "Departure and arrival airports and cities for every flight."),
    ("Complete flight schedule", "Flights", "Airline, aircraft, route, times and flight status in one table."),
    ("Passenger bookings", "Passengers", "Booking dates, assigned seats and fares for each passenger."),
    ("Bookings with flight details", "Bookings", "Passenger bookings alongside flight times and operating airlines."),
    ("All passengers and bookings", "Passengers", "Includes passengers without bookings, using a left join."),
    ("Booking totals by flight", "Bookings", "Includes flights with zero bookings."),
]
AGGREGATES = [
    ("Flight counts by airline", "Flights", "How many flights each airline operates, including zero."),
    ("Average fare by flight", "Revenue", "Average of recorded booking fares; NULL means no bookings."),
    ("Airline revenue · aggregate", "Revenue", "Sum of booking fares by airline; NULL means no booking revenue."),
    ("Booking counts by passenger", "Passengers", "How many bookings each passenger has made."),
    ("Above-average airline activity · aggregate", "Flights", "Airlines whose flight count exceeds the average across all airlines."),
    ("Baggage totals · booked bags", "Baggage", "Total weight for bookings that have baggage."),
    ("Baggage totals by passenger", "Baggage", "Combined baggage weight across each passenger's bookings."),
]
USER = [
    ("Search flight routes", "Flights", "Search by departure city, arrival city and travel date."),
    ("Flights for an airline", "Flights", "All scheduled records for the selected airline, ordered by departure."),
    ("Available seats on a flight", "Flights", "Aircraft capacity minus the number of recorded bookings. No seat map is assumed."),
    ("Flights with available capacity", "Flights", "Flights with bookings below aircraft capacity. The original query does not exclude cancelled or past flights."),
    ("Passenger booking history", "Passengers", "Booking dates, seats and fares for the selected passenger."),
    ("Detailed passenger itinerary", "Passengers", "Routes, airlines, flight status and fares for a passenger's bookings."),
    ("Passenger with a booking", "Passengers", "Returns the selected passenger only if a booking exists."),
    ("Bags on the latest booking", "Baggage", "Baggage for the passenger's latest booking, with booking ID breaking date ties."),
    ("Passenger baggage by booking", "Baggage", "Total weight for each booking, including zero when there are no bags."),
    ("Passenger total spending", "Revenue", "Total recorded booking fares for one passenger."),
    ("Lowest recorded fares per flight", "Revenue", "Returns cheapest existing bookings, including ties; these are not ticket price offers."),
    ("Bookings above the overall average fare", "Revenue", "Existing bookings costing more than the average booking fare."),
    ("Passengers without bookings", "Passengers", "Contact information for passengers who have never booked."),
    ("Highest recorded fares per flight", "Revenue", "Most expensive existing bookings per flight, including ties."),
]
ADMIN = [
    ("Database overview counts", "Overview", "Record counts for all seven main entities."),
    ("Total booking revenue", "Revenue", "Total of all fares currently recorded in Booking."),
    ("Airline revenue · subquery", "Revenue", "Revenue by airline, highest first; airlines without revenue show zero."),
    ("Flight booking performance", "Bookings", "Flights ranked by their number of bookings."),
    ("Flight occupancy", "Flights", "Aircraft capacity, booked seats and remaining seats for every flight."),
    ("Flights at least 90% full", "Flights", "Flights with booked seats at or above 90% of capacity."),
    ("Flights without bookings", "Flights", "Scheduled flight records with no bookings."),
    ("Unused aircraft", "Fleet & airports", "Aircraft not assigned to any flight record."),
    ("Aircraft usage", "Fleet & airports", "Number of flights assigned to each aircraft."),
    ("Unused airports", "Fleet & airports", "Airports absent from both departure and arrival routes."),
    ("Customer spending", "Revenue", "Passengers ranked by total recorded spending, including zero."),
    ("Customers above average spending", "Revenue", "Passenger spending compared with the average among passengers who have bookings."),
    ("Most booked flights", "Bookings", "All flights tied for the largest booking count."),
    ("Above-average airline activity · subquery", "Flights", "Airlines exceeding the average flight count among airlines represented in Flight."),
    ("Bookings with baggage", "Baggage", "Bookings with at least one registered bag."),
    ("Bookings without baggage", "Baggage", "Bookings with no registered baggage."),
    ("Baggage totals · all bookings", "Baggage", "Total weight for every booking, including bookings with no bags."),
    ("Bags above average weight", "Baggage", "Individual bags heavier than the average bag."),
    ("Highest fare bookings overall", "Revenue", "All bookings tied for the highest fare."),
    ("Flights above average revenue", "Revenue", "Flight revenue compared with the average among flights that have bookings."),
    ("Aircraft above average capacity", "Fleet & airports", "Aircraft with more seats than the fleet average."),
    ("Airports serving both directions", "Fleet & airports", "Airports used as both a departure and an arrival location."),
    ("Frequent passengers", "Passengers", "Passengers exceeding the average booking count among passengers with bookings."),
    ("Bookings on high-demand flights", "Bookings", "Bookings on flights above the average booking count among booked flights."),
    ("Fares above their flight average", "Revenue", "Bookings costing more than the average fare on their own flight."),
]
INPUT_ORDER = ("from_city", "to_city", "travel_date", "airline_code", "passenger_id", "flight_id")


def original_selects(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    offset = 0
    for part in sqlparse.split(text):
        start = text.find(part, offset)
        offset = start + len(part)
        # Find the actual SELECT token after comments, without formatting its text.
        clean = sqlparse.format(part, strip_comments=True).strip()
        if not clean.upper().startswith("SELECT"):
            continue
        match = re.search(r"(?m)^SELECT\b", part)
        if not match:
            raise ValueError(f"Cannot locate SELECT in {path}")
        select_start = start + match.start()
        yield text[select_start:offset], text.count("\n", 0, select_start) + 1


def load_reports():
    reports = {}
    groups = [
        ("sql/queries/01_joins.sql", "J", JOINS, "JOIN"),
        ("sql/queries/02_aggregates.sql", "G", AGGREGATES, "Aggregate"),
        ("sql/queries/03_subqueries.sql", "S", USER + ADMIN, "Subquery"),
    ]
    for source, prefix, labels, technique in groups:
        statements = list(original_selects(source))
        if len(statements) != len(labels):
            raise ValueError(f"Report catalogue needs updating: {source}")
        for i, ((sql, line), (title, category, description)) in enumerate(zip(statements, labels), 1):
            report_id = (f"U{i}" if i <= 14 else f"A{i - 14}") if prefix == "S" else f"{prefix}{i}"
            inputs = tuple(name for name in INPUT_ORDER if re.search(r"@" + name + r"\b", sql))
            reports[report_id] = Report(report_id, title, category, description, technique, source, line, sql, inputs)
    return reports


def load_transactions():
    source = "sql/transactions/01_transactions.sql"
    text = (ROOT / source).read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^-- TRANSACTION (\d+): (.+)$", text))
    return {int(h.group(1)): {
        "id": int(h.group(1)), "title": h.group(2), "source": source,
        "line": text.count("\n", 0, h.start()) + 1,
        "sql": text[h.start():headings[i + 1].start() if i + 1 < len(headings) else len(text)].strip(),
    } for i, h in enumerate(headings)}


def load_triggers():
    source = "sql/triggers/01_triggers.sql"
    text = (ROOT / source).read_text(encoding="utf-8")
    return [{"name": match.group(1), "source": source,
             "line": text.count("\n", 0, match.start()) + 1,
             "sql": match.group(0)}
            for match in re.finditer(r"CREATE TRIGGER (\w+).*?END\$\$", text, re.S)]


REPORTS = load_reports()
TRANSACTIONS = load_transactions()
TRIGGERS = load_triggers()
CATEGORIES = ("Overview", "Flights", "Fleet & airports", "Passengers", "Bookings", "Baggage", "Revenue")
