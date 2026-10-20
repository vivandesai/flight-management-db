# Database administrator panel and SQL views

The DBA panel is a local project interface, reached through **DBA panel** in the sidebar. It uses the same Flask server and MySQL connection as the staff screens. There is no login or independent MySQL role: the connected MySQL account determines database privileges. The application remains bound to localhost.

## Editing and deletion

Search the seven entity tabs by stored details or IDs. Results show 50 records per page. Each row has an Edit link and a Delete preview. Baggage is addressed by **booking ID and bag number together**, for example `1-2`.

| Entity | Editable fields |
| --- | --- |
| Airline | Code and name |
| Aircraft | Registration, model and capacity |
| Airport | Code, name and city |
| Passenger | Name, birth date, phone, email and passport |
| Flight | Departure, arrival and status |
| Booking | Seat and fare |
| Baggage | Weight |

IDs, relationships and booking dates stay read-only. Use the existing management actions to create records, assign aircraft or transfer bookings. Empty optional passenger contacts are stored as NULL. The three audit tables remain read-only in Browse records.

Every write uses a parameterized template from [`sql/dba/01_entity_operations.sql`](../sql/dba/01_entity_operations.sql). This file is an application statement catalogue, **not an executable batch**: its named placeholders must be bound by Connector/Python. Never SOURCE the whole file. It includes the existing management contact/status update and individual booking/baggage deletion patterns, plus dependency and consistency checks. It adds no tables, stored procedures or triggers.

Each mutation commits on one connection or rolls back fully. Forms carry a signed one-hour snapshot of the original row; a changed, missing or expired record must be reloaded before another attempt. Immutable values submitted by a client are ignored and never used as UPDATE assignments. Parent and target locks protect the relevant booking, aircraft, flight and baggage checks; database failures are displayed with their MySQL number and SQLSTATE.

The original triggers remain enabled. DBA updates also check rules which the original SQL enforces only during INSERT: past birth date, basic email format, positive fare, 50 kg individual and 80 kg total baggage limits. Aircraft capacity cannot fall below the booked count on any assigned flight. Changed flight times must be future-valid and non-overlapping for an active aircraft schedule. Reactivating a cancelled flight also checks overlap. Status-only changes to historical flights remain possible, subject to the existing arrived-status lock.

Deletion is **permanent and individual**, after a record/dependency preview and explicit checkbox confirmation. Dependencies are checked again on submission. Airline → aircraft/flights, aircraft → flights, airport → departures/arrivals, passenger → bookings, flight → bookings and booking → baggage references block deletion. Delete an eligible child separately if that is your intention; there is no cascade button. Booking deletion still creates the existing cancellation audit entry, and audit rows are retained.

## Installing seven MySQL views

Fresh `init-db --fresh` executes the four original scripts, then installs the new views. For an already populated database, deliberately run:

```powershell
.\.venv\Scripts\python.exe -m flask --app run install-views
```

The command connects to the database configured in `.env`, checks the original tables/triggers, and executes [`sql/views/01_management_views.sql`](../sql/views/01_management_views.sql). You may also execute that file in a MySQL client after selecting the intended database. It contains exactly seven CREATE OR REPLACE VIEW statements, explicit column lists and SQL SECURITY INVOKER; no hardcoded account DEFINER is stored in the source.

The installation account needs CREATE VIEW, SELECT for referenced columns, and DROP to replace existing views. SHOW VIEW is needed to inspect definitions in MySQL; grant SELECT on the views and underlying tables to the connected runtime account as needed. INVOKER views use that account's privileges. The application displays checked-in view definitions and source locations without requiring a browser user to know SQL.

View DDL is not wrapped in a rollback promise: MySQL commits DDL separately. If installation fails partway, correct the reported privilege or database issue and rerun it. Replacement is repeatable and changes no stored base rows. Startup never installs anything, and missing views show setup guidance only on view screens; staff reports and DBA records continue working.

| View | Business purpose / original-query connection |
| --- | --- |
| `vw_flight_operations` | Airline, aircraft, route, times and status; J4 |
| `vw_flight_occupancy` | Capacity, booked/available seats and occupancy; A5 |
| `vw_airline_performance` | Aircraft/flight/booking counts and fare revenue; G1/A3 |
| `vw_passenger_activity` | Contacts, bookings, total spending and latest booking date; G4/A11 |
| `vw_booking_manifest` | Passenger, seat, fare, airline and route for each booking; J5/J6 |
| `vw_booking_baggage` | Bag count and total weight per booking, including zero bags; A17 |
| `vw_airport_traffic` | Independent arrival/departure counts including unused airports; complements A10/A22 |

Open **SQL views** to inspect live SELECT results and expand each definition. These seven screens are separate from the unchanged 54-report catalogue. They include stored historical and cancelled flights; totals do not claim to represent only future or active service. Independent aggregates avoid multiplying revenue when airlines have multiple aircraft or bookings have multiple bags. View results reflect edits and deletions immediately after commit. Fare amounts have no invented currency metadata.

## Presentation walkthrough

1. Show a flight in Flight operations, its occupancy, and the corresponding original J4/A5 reports.
2. Edit an airline name and show it change in a view. Show the SQL template and CREATE VIEW definition.
3. Attempt to reduce aircraft capacity below its booked-seat count. Show the rejection and unchanged data.
4. Preview deletion of a booked flight: its bookings block deletion. Show the separate baggage/booking dependencies.
5. On a disposable demonstration database, delete a bag, then an eligible booking individually. Show the cancellation audit and changed booking/baggage view results.
6. Inspect airport traffic and a passenger without bookings to explain LEFT JOINs and zero-activity results.

For automated checks, follow the disposable-server instructions in [interface.md](interface.md). The tests reset only an explicitly marked separate server. Never use a database you want to keep.
