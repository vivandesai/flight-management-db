# ✈️ Flight Management System

## Run the airline management interface

The repository now includes a simple **Flask + Jinja + Bootstrap** interface for airline staff: all 54 original report queries, management forms, 10 transaction examples, 12 trigger demonstrations and the database audit logs. The original files in `sql/` are unchanged.

See **[setup and presentation walkthrough](docs/interface.md)** for Windows installation, MySQL connection settings and startup instructions. See **[query coverage](docs/query-coverage.md)** for the mapping from every original query to its screen.

Quick start after installing Python 3.10+ and MySQL 8.4:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your own MySQL credentials.
# For a NEW database only (skip if FlightManagement already exists):
.\.venv\Scripts\python.exe -m flask --app run init-db --fresh
.\.venv\Scripts\python.exe run.py
```

Open **http://127.0.0.1:5000**. The interface runs locally without Node.js, a frontend build, or internet access after installation. No database setup runs automatically.

---

A Database Management System (DBMS) mini-project for managing airlines, aircraft, airports, flights, passengers, bookings, and baggage using MySQL.

The project demonstrates the design and implementation of a relational database along with SQL queries, transactions, triggers, and database constraints.

---

## 📌 Project Overview

The Flight Management System is designed to store and manage information related to airline operations and passenger bookings.

The system maintains relationships between:

- Airlines and their aircraft
- Airlines and flights
- Aircraft assigned to flights
- Airports used for flight departures and arrivals
- Passengers and their bookings
- Flights and their bookings
- Bookings and associated baggage

The database is designed using an Entity-Relationship (ER) model and converted into a normalized relational schema.

---

## 🎯 Objectives

The main objectives of this project are:

- Design an ER model for a Flight Management System.
- Convert the ER model into a relational schema.
- Normalize the database to reduce redundancy and maintain data integrity.
- Implement the database using MySQL.
- Insert and manage realistic sample data.
- Perform SQL queries using:
  - JOINs
  - Aggregate functions
  - GROUP BY and HAVING
  - Subqueries
- Implement database triggers.
- Demonstrate SQL transactions using `COMMIT`, `ROLLBACK`, and related transaction operations.

---

## 🗂️ Database Entities

The database consists of the following entities:

### Airline

Stores information about airlines.

**Attributes:**
- `airline_id` – Primary Key
- `code`
- `airline_name`

### Aircraft

Stores information about aircraft operated by airlines.

**Attributes:**
- `aircraft_id` – Primary Key
- `registration_no`
- `model`
- `capacity`
- `airline_id` – Foreign Key

### Airport

Stores information about airports.

**Attributes:**
- `airport_id` – Primary Key
- `airport_code`
- `airport_name`
- `city`

### Passenger

Stores passenger information.

**Attributes:**
- `passenger_id` – Primary Key
- `passenger_name`
- `dob`
- `phone`
- `email`
- `passport_no`

### Flight

Stores scheduled flight information.

**Attributes:**
- `flight_id` – Primary Key
- `departure_time`
- `arrival_time`
- `flight_status`
- `airline_id` – Foreign Key
- `aircraft_id` – Foreign Key
- `departure_airport_id` – Foreign Key
- `arrival_airport_id` – Foreign Key

### Booking

Stores passenger flight bookings.

**Attributes:**
- `booking_id` – Primary Key
- `booking_date`
- `seat_number`
- `fare`
- `passenger_id` – Foreign Key
- `flight_id` – Foreign Key

A unique constraint on `(flight_id, seat_number)` prevents the same seat from being booked more than once on a flight.

### Baggage

Baggage is modeled as a **weak entity** dependent on Booking.

**Attributes:**
- `booking_id` – Foreign Key
- `baggage_no` – Partial Key
- `baggage_weight`

The primary key is:

```text
(booking_id, baggage_no)
```
