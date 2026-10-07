# ✈️ Flight Management System (DBMS Mini Project)

A complete **Database Management System (DBMS)** project modeling airline flight operations, passenger reservations, baggage handling, and flight scheduling using **MySQL** with a full-stack **Flask + Jinja2 + Bootstrap** management interface.

The project demonstrates production-grade relational database design, including **Entity-Relationship (ER) modeling**, **normalization up to BCNF**, comprehensive **CHECK/FOREIGN KEY constraints**, **12 stored triggers**, **10 transaction workflows (ACID & SAVEPOINTs)**, and **54 analytical and operational queries**.

---

## 📑 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [Key Features](#-key-features)
- [Database Schema & Entities](#-database-schema--entities)
  - [Core Relational Schema](#core-relational-schema)
  - [Audit Logging Tables](#audit-logging-tables)
- [Triggers, Transactions & SQL Queries](#-triggers-transactions--sql-queries)
  - [Database Triggers (12 Triggers)](#database-triggers-12-triggers)
  - [Transaction Demos (10 Workflows)](#transaction-demos-10-workflows)
  - [Analytical & Operational Queries (54 Queries)](#analytical--operational-queries-54-queries)
- [Web Management Interface](#-web-management-interface)
- [Project Structure](#-project-structure)
- [Setup & Installation Guide (Windows)](#-setup--installation-guide-windows)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone & Virtual Environment](#2-clone--virtual-environment)
  - [3. Configure Environment Variables](#3-configure-environment-variables)
  - [4. Database Initialization](#4-database-initialization)
  - [5. Run the Application](#5-run-the-application)
- [Testing & Verification](#-testing--verification)
- [Documentation Links](#-documentation-links)

---

## 📌 Overview & Architecture

The Flight Management System coordinates real-world commercial airline operations:
1. **Fleet & Hub Management**: Airlines, their operating aircraft fleet, and international/domestic airport hubs.
2. **Flight Scheduling & Routing**: Connecting origin and destination airports with scheduled departure and arrival timestamps, aircraft assignment, and lifecycle flight statuses (`Scheduled`, `Boarding`, `Departed`, `Delayed`, `Arrived`, `Cancelled`).
3. **Ticketing & Reservations**: Passenger demographic records, unique seat assignments per flight, and fare calculations.
4. **Baggage Allowance Tracking**: Weak-entity baggage tracking enforcing individual and cumulative per-booking weight limits.
5. **Auditing & Integrity**: Automatic audit capture for status modifications, booking creations, and cancellations via triggers.

```
+-------------------------------------------------------------+
|               Flask Web Application (Waitress)              |
|   Management Forms | 54 Reports | Demos | Audit Viewer      |
+-------------------------------------------------------------+
                              │
               (Direct SQL / mysql-connector)
                              ▼
+-------------------------------------------------------------+
|                 MySQL 8.0+ Database Server                  |
|  • 7 Core Normalized Tables                                 |
|  • 3 Trigger Audit Tables                                   |
|  • 12 Integrity Triggers (BEFORE/AFTER INSERT/UPDATE/DELETE)|
|  • ACID Transactions with SAVEPOINTs                        |
+-------------------------------------------------------------+
```

---

## ✨ Key Features

- **No ORM abstraction**: Employs pure, parameterized SQL queries using `mysql-connector-python` to showcase raw SQL proficiency.
- **Relational Integrity**: Enforces foreign keys (`ON DELETE/UPDATE RESTRICT`), check constraints (`arrival > departure`, `capacity > 0`), and unique composite keys.
- **Business Logic Enforced in Database**: Real-world constraints (e.g., preventing duplicate seat bookings, forbidding flights departing in the past, or prohibiting booking cancelled flights) are enforced natively via MySQL triggers using `SIGNAL SQLSTATE '45000'`.
- **Interactive Staff Portal**: Includes live query execution, multi-step transaction runners with before/after state diffs, reversible trigger test suites, and operational forms.
- **Zero Frontend Build Dependencies**: Uses locally bundled Bootstrap and icons; works completely offline without Node.js.

---

## 🗂️ Database Schema & Entities

### Core Relational Schema

| Entity / Table | Primary Key | Foreign Keys | Key Constraints & Rules |
| :--- | :--- | :--- | :--- |
| **`Airline`** | `airline_id` | *None* | `code` is UNIQUE (e.g., 'AI', '6E', 'EK'). |
| **`Aircraft`** | `aircraft_id` | `airline_id` → `Airline` | `registration_no` is UNIQUE; `capacity > 0`. |
| **`Airport`** | `airport_id` | *None* | `airport_code` is UNIQUE (IATA code, e.g., 'BOM', 'DEL'). |
| **`Passenger`** | `passenger_id` | *None* | `passport_no` is UNIQUE; DOB must be in the past. |
| **`Flight`** | `flight_id` | `airline_id` → `Airline`<br>`aircraft_id` → `Aircraft`<br>`departure_airport_id` → `Airport`<br>`arrival_airport_id` → `Airport` | `arrival_time > departure_time`; `departure_airport_id <> arrival_airport_id`. |
| **`Booking`** | `booking_id` | `passenger_id` → `Passenger`<br>`flight_id` → `Flight` | `UNIQUE(flight_id, seat_number)`; `fare >= 0`. |
| **`Baggage`** *(Weak Entity)* | `(booking_id, baggage_no)` | `booking_id` → `Booking` | `baggage_weight > 0`; max 50 kg per bag; max 80 kg total per booking. |

### Audit Logging Tables

Automatically populated via database triggers for system tracking and compliance:
- **`flight_status_log`**: Records `flight_id`, `old_status`, `new_status`, and `changed_at` timestamp whenever a flight's status transitions.
- **`booking_creation_log`**: Records newly issued reservations (`booking_id`, `flight_id`, `passenger_id`, `seat_no`, `fare`, `created_at`).
- **`booking_cancellation_log`**: Records deleted/cancelled bookings for refund reconciliation.

---

## ⚡ Triggers, Transactions & SQL Queries

### Database Triggers (12 Triggers)

The system includes 12 automated triggers defined in [`sql/triggers/01_triggers.sql`](sql/triggers/01_triggers.sql):

1. **`trg_flight_before_insert`**: Ensures departure is in the future, arrival is after departure, airports are distinct, aircraft belongs to specified airline, and no schedule overlap exists for the aircraft.
2. **`trg_flight_before_update`**: Validates updated flight times and ensures source/destination airports remain distinct.
3. **`trg_flight_status_lock`**: Prevents status mutation on flights that have already arrived (`Arrived` state lock).
4. **`trg_flight_after_update`**: Automatically writes status changes to `flight_status_log`.
5. **`trg_flight_before_delete`**: Blocks deletion of any flight that still has active passenger bookings.
6. **`trg_airline_before_delete`**: Blocks deletion of any airline that has scheduled or operated flights.
7. **`trg_booking_before_insert`**: Verifies that the flight is not cancelled, fare is positive, passenger does not already have a ticket on this flight, seat is unoccupied, and aircraft capacity has not been exceeded.
8. **`trg_booking_after_insert`**: Inserts booking details into `booking_creation_log`.
9. **`trg_booking_after_delete`**: Logs cancelled bookings into `booking_cancellation_log`.
10. **`trg_baggage_before_insert`**: Validates individual baggage weight (must be > 0 and ≤ 50 kg).
11. **`trg_baggage_total_limit`**: Enforces a cumulative maximum limit of 80 kg total baggage across all bags for a single booking.
12. **`trg_passenger_before_insert`**: Validates date of birth (`dob < CURDATE()`) and checks email format syntax regex.

### Transaction Demos (10 Workflows)

Defined in [`sql/transactions/01_transactions.sql`](sql/transactions/01_transactions.sql) and interactively executable via the web interface:
- **T1: New Passenger + Booking + Baggage**: Multi-table atomic insert demonstrating all-or-nothing guarantee.
- **T2: Flight Transfer (Rebooking)**: Atomic delete and re-insert across bookings and baggage tables.
- **T3: Forced ROLLBACK**: Demonstrates failure and safe state reversal when attempting to book a cancelled flight.
- **T4: SAVEPOINT with Partial Rollback**: Creates two bookings, attempts an invalid third booking, rolls back to savepoint while committing the valid two.
- **T5: Batch Flight Status Update**: Updates multiple flights with savepoints for error recovery.
- **T6: Flight Cancellation**: Atomic cascade cancelling a flight and wiping dependent reservations while triggering audit logs.
- **T7: Onboard New Airline**: Registers airline, assigns aircraft, and schedules inaugural flight in a single transaction.
- **T8: Batch Fare Modification Rollback**: Demonstrates reverting an accidental price adjustment across all flights.
- **T9: Safe Passenger Update with Savepoint**: Updates phone and email with rollback protection.
- **T10: Multi-stage Baggage Addition**: Utilizes nested savepoints to add baggage sequentially.

### Analytical & Operational Queries (54 Queries)

Organized into three files under [`sql/queries/`](sql/queries/):
- **Joins (8 Queries - `01_joins.sql`)**: INNER and LEFT JOINs demonstrating table associations (e.g. flight schedules, airline ownership, passenger manifests).
- **Aggregates (7 Queries - `02_aggregates.sql`)**: `COUNT`, `AVG`, `SUM`, `MIN`, `MAX`, `GROUP BY`, and `HAVING` filters (e.g., airline revenue rankings, baggage totals, average seat fares).
- **Subqueries (39 Queries - `03_subqueries.sql`)**: Correlated subqueries, nested `IN`, `EXISTS`, `NOT EXISTS`, and scalar subqueries divided into:
  - *User Queries (U1–U14)*: Route searching, seat availability checks, personal itineraries, spending totals.
  - *Admin Queries (A1–A25)*: High-demand flight identification, occupancy metrics, unutilized aircraft/airports, frequent flyers.

---

## 🖥️ Web Management Interface

The built-in web portal runs locally on Flask & Waitress:

- **Dashboard / Overview**: Live system summary and record counts.
- **Operational Workflows**:
  - Register passenger
  - Create booking & check-in first bag
  - Transfer booking to new flight
  - Add baggage with weight limit enforcement
  - Update contact info & flight statuses
  - Cancel flight with automated audit retention
  - Schedule aircraft & onboard new airlines
- **Query Explorer**: Live execution of all 54 SQL queries categorized by domain.
- **Interactive Transaction & Trigger Demos**: Visual execution displaying query output, affected rows, and rollback behavior.
- **Database Logs**: Live inspection of `flight_status_log`, `booking_creation_log`, and `booking_cancellation_log`.

---

## 📁 Project Structure

```text
flight-management-db/
├── .env.example                # Sample database configuration
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies (Flask, mysql-connector, waitress, etc.)
├── requirements-dev.txt        # Development dependencies (pytest)
├── run.py                      # Production WSGI entry point (Waitress)
│
├── airline/                    # Flask Application Package
│   ├── __init__.py             # App factory & route registrations
│   ├── catalogue.py            # SQL file parser and query catalogue indexer
│   ├── db.py                   # Direct MySQL connection pool & CLI commands
│   ├── demos.py                # Transaction & trigger runner logic
│   ├── workflows.py            # Form validation & parameterized workflow handlers
│   ├── static/                 # CSS & JavaScript assets (Bootstrap bundled)
│   └── templates/              # Jinja2 HTML templates
│
├── docs/                       # Detailed Documentation
│   ├── interface.md            # Interface walkthrough & Windows setup instructions
│   ├── query-coverage.md       # Comprehensive 54-query mapping & catalogue
│   ├── relational_schema.md    # Normalized schema specifications
│   └── verification.md         # Testing & verification records
│
├── er/                         # Entity-Relationship Diagrams
│   └── MiniProject.drawio      # ER diagram source file (draw.io)
│
├── sql/                        # Pure SQL Scripts
│   ├── 01_create_database.sql  # Database creation script
│   ├── 02_create_tables.sql    # Table schema with constraints & foreign keys
│   ├── 03_insert_data.sql      # Seed data (airlines, airports, flights, bookings)
│   ├── queries/
│   │   ├── 01_joins.sql        # 8 Join queries
│   │   ├── 02_aggregates.sql   # 7 Aggregate queries
│   │   └── 03_subqueries.sql   # 39 Subqueries (User U1-U14, Admin A1-A25)
│   ├── transactions/
│   │   └── 01_transactions.sql # 10 ACID transaction scripts
│   └── triggers/
│       └── 01_triggers.sql     # 12 Database triggers & audit tables
│
└── tests/                      # Automated Test Suite
    ├── test_catalogue.py       # SQL query catalogue integrity tests
    └── test_database.py        # Database integration tests
```

---

## 🚀 Setup & Installation Guide (Windows)

### 1. Prerequisites
- **Python 3.10+**: [Download Python](https://www.python.org/downloads/) (Ensure *"Add python.exe to PATH"* is checked during installation).
- **MySQL Server 8.0 or 8.4**: [Download MySQL Installer](https://dev.mysql.com/downloads/installer/). Ensure the MySQL service (e.g., `MySQL80`) is running.

### 2. Clone & Virtual Environment
Open PowerShell in your desired folder:

```powershell
# Clone the repository (if not already downloaded)
git clone https://github.com/vivandesai/flight-management-db.git
cd flight-management-db

# Create Python virtual environment
python -m venv .venv

# Install project dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create your `.env` configuration file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in a text editor (e.g., Notepad or VS Code) and update your MySQL connection details:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=FlightManagement
SECRET_KEY=generate_a_random_string
APP_PORT=5000
```

> **Tip:** You can generate a random secret key quickly in PowerShell:
> ```powershell
> .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Database Initialization

#### Scenario A: Fresh Setup (Database does not exist yet)
Run the automated initialization command to create the database, tables, sample records, and triggers:

```powershell
.\.venv\Scripts\python.exe -m flask --app run init-db --fresh
```

#### Scenario B: Existing Database
If the database `FlightManagement` already exists, skip `init-db --fresh` (it refuses to overwrite existing tables). If you only need to ensure the audit tables and 12 triggers are applied, execute the triggers script directly:

```powershell
# In PowerShell:
Get-Content sql\triggers\01_triggers.sql | mysql -u root -p FlightManagement
```

### 5. Run the Application
Start the local web server:

```powershell
.\.venv\Scripts\python.exe run.py
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

*(Press `Ctrl + C` in the PowerShell window to stop the server).*

---

## 🧪 Testing & Verification

To run automated checks against the query catalogue and test suite:

```powershell
# Install development test dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# Run pytest suite
.\.venv\Scripts\python.exe -m pytest
```

---

## 📖 Documentation Links

- **[Setup & Presentation Walkthrough](docs/interface.md)**: Detailed step-by-step instructions for viva/presentation prep and user workflows.
- **[Query Coverage Matrix](docs/query-coverage.md)**: Line-by-line index mapping each SQL query to the interface screen.
- **[Relational Schema Specification](docs/relational_schema.md)**: Mathematical schema notation and foreign key references.
- **[Verification Guide](docs/verification.md)**: Operational verification steps and checklist.
