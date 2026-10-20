# Airline management interface

The application is a small visual layer over the DBMS project. Flask handles routes and form submissions, Jinja renders HTML, Bootstrap supplies locally bundled styling, and MySQL Connector/Python executes SQL directly. There is no ORM, migration system, separate frontend build, or new stored procedure.

## Windows setup on either laptop

Install Python 3.10 or newer and MySQL Community Server 8.4 (Workbench is optional). Start MySQL and keep your local username and password available. Your friend should clone or pull this repository; copying your `.venv` or `.env` is unnecessary.

```powershell
git clone https://github.com/vivandesai/flight-management-db.git
cd flight-management-db
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If the repository is already cloned, run `git pull` inside it, then install the current requirements. Edit `.env` locally:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_local_mysql_password
MYSQL_DATABASE=FlightManagement
SECRET_KEY=your_random_value
APP_PORT=5000
```

Generate the secret with:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Do not commit `.env`; it is ignored. If SECRET_KEY is blank, the app generates a temporary one at startup, so forms opened before a restart need reloading. Install dependencies once with internet access; all browser assets run locally afterward.

### Fresh database

If `FlightManagement` does **not** exist, initialize it explicitly:

```powershell
.\.venv\Scripts\python.exe -m flask --app run init-db --fresh
```

This executes the four original files, without changing their contents, in this order:

1. `sql/01_create_database.sql`
2. `sql/02_create_tables.sql`
3. `sql/03_insert_data.sql`
4. `sql/triggers/01_triggers.sql`

It then executes the new `sql/views/01_management_views.sql` to install seven management views. All four original setup files remain unchanged. The DBA statement-template file is never executed as an initialization batch.

The seed runs before triggers because its fixed sample flight dates may be in the past. Connector/Python processes the trigger script's `DELIMITER` directives. The initialization account needs permission to create the database, tables and triggers. If initialization fails partway, the app does not drop the partially created database; inspect the reported error in your MySQL client.

The initializer refuses to overwrite or reseed an existing `FlightManagement` database. It never runs the transaction examples as part of setup.

### Existing database

Set the connection details and skip initialization. All seven base tables, three audit tables and twelve triggers must be present. If only triggers/audit tables are missing, execute the **unchanged** `sql/triggers/01_triggers.sql` in your MySQL client. For other missing objects, inspect the database and import the relevant original setup scripts deliberately; do not rerun the seed over populated tables.

To add only the seven new views to an existing database, run `.\.venv\Scripts\python.exe -m flask --app run install-views`. Missing views do not block staff reports or the DBA panel. See [DBA and views](dba-and-views.md) for privileges and installation details.

The original trigger uses `BEFORE DELETE ON airline`, while the table is created as `Airline`. Windows MySQL's case-insensitive table handling supports this unchanged source. On a case-sensitive MySQL server it can fail. Use a case-insensitive server configuration for this project rather than editing the SQL. Runtime verification used MySQL 8.4 on Windows with `lower_case_table_names=1`.

### Start the application

```powershell
.\.venv\Scripts\python.exe run.py
```

Open **http://127.0.0.1:5000**. Waitress serves the app on localhost only. To use another port, change `APP_PORT` in `.env`. Stop with Ctrl+C. Startup never creates, reseeds or resets a database.

## Using the interface

- **Overview:** original database counts, total booking revenue, flight schedule, occupancy and most-booked flights.
- **Flights, Fleet & airports, Passengers, Bookings, Baggage, Revenue:** reports grouped by the business question they answer.
- **All 54 reports:** search by title, description, query ID or SQL technique. Similar queries remain separately accessible.
- **Management actions:** registration, booking with optional baggage, transfer with actual baggage preservation, baggage registration, contact updates, status updates, flight cancellation, scheduling and airline onboarding.
- **Browse records:** all seven entities and three audit tables, read-only.
- **DBA panel:** search and edit selected fields across the seven entities, plus confirmed individual deletion when dependencies permit it. IDs and relationships stay read-only.
- **SQL views:** seven separately installed MySQL views with live results and source definitions; these do not replace the 54 original reports.
- **Database demos:** original transactions plus reversible trigger demonstrations.

Reports needing inputs use dropdowns populated from MySQL. Dates are explicit selections, not rewritten sample values. The supplied route-search default of 1 October 2026 has no matching seed flight; use **Mumbai → Delhi, 5 October 2026** to demonstrate an existing match. Zero-result reports are expected for the initial sample data, including almost-full flights.

SQL `DATETIME` values are displayed as stored, without automatic timezone conversion. Fare values have no currency metadata in the schema; the UI displays numeric amounts without inventing a currency. A dash represents SQL NULL and is distinct from zero. Passenger, flight and booking IDs remain visible for tracing relationships.

### Database demonstrations

**Original transactions:** review the SQL and confirm before executing. These examples use fixed literals, may commit changes, and can fail on repeated runs or changed data. The runner executes one statement at a time on the same connection, shows real result sets and affected-row counts, and explicitly rolls back active transactions on MySQL errors. It stops after the failed statement rather than displaying later success messages.

Transaction 3 cancels Flight 11 outside `START TRANSACTION`. That cancellation and its status audit persist even when the booking attempt rolls back. Transaction 7's first flight uses 1 November 2026; the future-departure trigger rejects it once the date has passed. Transaction 9 actually updates two valid contacts and commits both; its SQL does not attempt an invalid email or roll back to a savepoint, regardless of its comments. No source code was changed to conceal these behaviors.

**Trigger demos:** each creates its own temporary airline, aircraft, airports, passenger, flight and booking inside a transaction. It then exercises the selected trigger, shows changes and audit evidence, and rolls back all fixture and demo rows. MySQL auto-increment counters can still advance after a rollback. No existing stored rows are changed by these demos. Invalid input being rejected is a successful demonstration of the database rule.

Management forms commit only complete workflows. If booking baggage fails, the booking and its audit row roll back too. If rebooking fails, the old booking and its actual baggage return. The existing contact workflow retains its original behavior: email validation exists for passenger **inserts**, not updates. The new DBA editing screen explicitly checks birth date/email, fare, baggage and capacity rules for its updates without altering any original trigger or workflow. See [DBA and views](dba-and-views.md).

## Short presentation walkthrough

1. Open Overview and explain the seven entity relationships using Browse records. A fresh seed has 5 airlines, 7 aircraft, 10 airports, 15 passengers, 12 flights, 29 bookings and 20 bags; total booking revenue is 271,300.00.
2. Search the reports for `U1`, select Mumbai, Delhi and 5 October 2026, then expand View SQL. Show `J4` for the full flight join and `G3` / `A3` for two distinct revenue queries.
3. Create a booking for an existing passenger on a flight they have not booked, with an unused seat and optional bag. Open the booking creation audit to show the AFTER INSERT trigger.
4. Run the single-bag weight or cancelled-flight trigger demo. Show the actual MySQL rejection and the rollback outcome.
5. On a prepared fresh demonstration database, run transaction 4 (two bookings retained, third rolled back to savepoint) and transaction 8 (fare batch completely rolled back). Show before/after rows and audit evidence.
6. Review transaction 3's pre-transaction cancellation before running it. This illustrates why the transaction boundary matters.

Use normal management forms for new dates and values. For original examples, prepare a fresh **demonstration** database manually before your presentation if earlier runs changed their prerequisites. There is no reset button in the app.

## Verification

Install the development requirements and run the portable catalogue/source checks:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

MySQL integration tests require a separate disposable server. **Never point them at a database you want to keep.** The tests drop and recreate `FlightManagement` on the explicitly designated server before each database test. They refuse to run without a server marker schema.

For example, start a separate MySQL 8.4 instance on port 33317, then deliberately create an empty schema named `vivu_disposable_test_server` on that instance in your MySQL client. Configure the tests:

```powershell
$env:TEST_MYSQL_HOST='127.0.0.1'
$env:TEST_MYSQL_PORT='33317'
$env:TEST_MYSQL_USER='root'
$env:TEST_MYSQL_PASSWORD='your_disposable_server_password'
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover all report executions and pages, supplied sample totals, parameter binding/isolation, all original transaction outcomes, all trigger demos, additional validation rules, workflow rollback, baggage preservation, audit creation, CSRF, cancellation confirmation, unavailable databases and missing triggers. SQL SHA-256 tests allow only platform checkout line-ending differences; Git also verifies original SQL blobs remain unchanged.

Bootstrap 5.3.8 is bundled locally under its MIT license. See `airline/static/vendor/LICENSE-bootstrap`.
