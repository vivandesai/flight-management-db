# Original SQL coverage

All report text is loaded directly from the existing SQL files. IDs follow source order: J = joins, G = aggregates, U = user subqueries and A = admin subqueries. Similar reports remain separate.

The seven additional MySQL views have their own source metadata and appear alongside these original reports in the same business-category grid and search. They do not replace reports. Their definitions are in [`sql/views/01_management_views.sql`](../sql/views/01_management_views.sql); the [DBA and views guide](dba-and-views.md) maps all seven scenarios and explains their original-query connections. DBA SELECT/UPDATE/DELETE templates are separately stored in [`sql/dba/01_entity_operations.sql`](../sql/dba/01_entity_operations.sql).

| ID | Management report | Category | Inputs | Original source |
| --- | --- | --- | --- | --- |
| J1 | Flights by airline | Flights | None | [sql/queries/01_joins.sql:3](../sql/queries/01_joins.sql#L3) |
| J2 | Aircraft ownership | Fleet & airports | None | [sql/queries/01_joins.sql:10](../sql/queries/01_joins.sql#L10) |
| J3 | Flight routes | Flights | None | [sql/queries/01_joins.sql:17](../sql/queries/01_joins.sql#L17) |
| J4 | Complete flight schedule | Flights | None | [sql/queries/01_joins.sql:29](../sql/queries/01_joins.sql#L29) |
| J5 | Passenger bookings | Passengers | None | [sql/queries/01_joins.sql:43](../sql/queries/01_joins.sql#L43) |
| J6 | Bookings with flight details | Bookings | None | [sql/queries/01_joins.sql:51](../sql/queries/01_joins.sql#L51) |
| J7 | All passengers and bookings | Passengers | None | [sql/queries/01_joins.sql:64](../sql/queries/01_joins.sql#L64) |
| J8 | Booking totals by flight | Bookings | None | [sql/queries/01_joins.sql:72](../sql/queries/01_joins.sql#L72) |
| G1 | Flight counts by airline | Flights | None | [sql/queries/02_aggregates.sql:3](../sql/queries/02_aggregates.sql#L3) |
| G2 | Average fare by flight | Revenue | None | [sql/queries/02_aggregates.sql:14](../sql/queries/02_aggregates.sql#L14) |
| G3 | Airline revenue · aggregate | Revenue | None | [sql/queries/02_aggregates.sql:24](../sql/queries/02_aggregates.sql#L24) |
| G4 | Booking counts by passenger | Passengers | None | [sql/queries/02_aggregates.sql:37](../sql/queries/02_aggregates.sql#L37) |
| G5 | Above-average airline activity · aggregate | Flights | None | [sql/queries/02_aggregates.sql:48](../sql/queries/02_aggregates.sql#L48) |
| G6 | Baggage totals · booked bags | Baggage | None | [sql/queries/02_aggregates.sql:69](../sql/queries/02_aggregates.sql#L69) |
| G7 | Baggage totals by passenger | Baggage | None | [sql/queries/02_aggregates.sql:79](../sql/queries/02_aggregates.sql#L79) |
| U1 | Search flight routes | Flights | from_city, to_city, travel_date | [sql/queries/03_subqueries.sql:45](../sql/queries/03_subqueries.sql#L45) |
| U2 | Flights for an airline | Flights | airline_code | [sql/queries/03_subqueries.sql:83](../sql/queries/03_subqueries.sql#L83) |
| U3 | Available seats on a flight | Flights | flight_id | [sql/queries/03_subqueries.sql:110](../sql/queries/03_subqueries.sql#L110) |
| U4 | Flights with available capacity | Flights | None | [sql/queries/03_subqueries.sql:134](../sql/queries/03_subqueries.sql#L134) |
| U5 | Passenger booking history | Passengers | passenger_id | [sql/queries/03_subqueries.sql:170](../sql/queries/03_subqueries.sql#L170) |
| U6 | Detailed passenger itinerary | Passengers | passenger_id | [sql/queries/03_subqueries.sql:192](../sql/queries/03_subqueries.sql#L192) |
| U7 | Passenger with a booking | Passengers | passenger_id | [sql/queries/03_subqueries.sql:230](../sql/queries/03_subqueries.sql#L230) |
| U8 | Bags on the latest booking | Baggage | passenger_id | [sql/queries/03_subqueries.sql:250](../sql/queries/03_subqueries.sql#L250) |
| U9 | Passenger baggage by booking | Baggage | passenger_id | [sql/queries/03_subqueries.sql:276](../sql/queries/03_subqueries.sql#L276) |
| U10 | Passenger total spending | Revenue | passenger_id | [sql/queries/03_subqueries.sql:296](../sql/queries/03_subqueries.sql#L296) |
| U11 | Lowest recorded fares per flight | Revenue | None | [sql/queries/03_subqueries.sql:315](../sql/queries/03_subqueries.sql#L315) |
| U12 | Bookings above the overall average fare | Revenue | None | [sql/queries/03_subqueries.sql:336](../sql/queries/03_subqueries.sql#L336) |
| U13 | Passengers without bookings | Passengers | None | [sql/queries/03_subqueries.sql:355](../sql/queries/03_subqueries.sql#L355) |
| U14 | Highest recorded fares per flight | Revenue | None | [sql/queries/03_subqueries.sql:376](../sql/queries/03_subqueries.sql#L376) |
| A1 | Database overview counts | Overview | None | [sql/queries/03_subqueries.sql:402](../sql/queries/03_subqueries.sql#L402) |
| A2 | Total booking revenue | Revenue | None | [sql/queries/03_subqueries.sql:419](../sql/queries/03_subqueries.sql#L419) |
| A3 | Airline revenue · subquery | Revenue | None | [sql/queries/03_subqueries.sql:436](../sql/queries/03_subqueries.sql#L436) |
| A4 | Flight booking performance | Bookings | None | [sql/queries/03_subqueries.sql:459](../sql/queries/03_subqueries.sql#L459) |
| A5 | Flight occupancy | Flights | None | [sql/queries/03_subqueries.sql:479](../sql/queries/03_subqueries.sql#L479) |
| A6 | Flights at least 90% full | Flights | None | [sql/queries/03_subqueries.sql:513](../sql/queries/03_subqueries.sql#L513) |
| A7 | Flights without bookings | Flights | None | [sql/queries/03_subqueries.sql:553](../sql/queries/03_subqueries.sql#L553) |
| A8 | Unused aircraft | Fleet & airports | None | [sql/queries/03_subqueries.sql:576](../sql/queries/03_subqueries.sql#L576) |
| A9 | Aircraft usage | Fleet & airports | None | [sql/queries/03_subqueries.sql:599](../sql/queries/03_subqueries.sql#L599) |
| A10 | Unused airports | Fleet & airports | None | [sql/queries/03_subqueries.sql:620](../sql/queries/03_subqueries.sql#L620) |
| A11 | Customer spending | Revenue | None | [sql/queries/03_subqueries.sql:642](../sql/queries/03_subqueries.sql#L642) |
| A12 | Customers above average spending | Revenue | None | [sql/queries/03_subqueries.sql:665](../sql/queries/03_subqueries.sql#L665) |
| A13 | Most booked flights | Bookings | None | [sql/queries/03_subqueries.sql:698](../sql/queries/03_subqueries.sql#L698) |
| A14 | Above-average airline activity · subquery | Flights | None | [sql/queries/03_subqueries.sql:734](../sql/queries/03_subqueries.sql#L734) |
| A15 | Bookings with baggage | Baggage | None | [sql/queries/03_subqueries.sql:762](../sql/queries/03_subqueries.sql#L762) |
| A16 | Bookings without baggage | Baggage | None | [sql/queries/03_subqueries.sql:785](../sql/queries/03_subqueries.sql#L785) |
| A17 | Baggage totals · all bookings | Baggage | None | [sql/queries/03_subqueries.sql:808](../sql/queries/03_subqueries.sql#L808) |
| A18 | Bags above average weight | Baggage | None | [sql/queries/03_subqueries.sql:828](../sql/queries/03_subqueries.sql#L828) |
| A19 | Highest fare bookings overall | Revenue | None | [sql/queries/03_subqueries.sql:847](../sql/queries/03_subqueries.sql#L847) |
| A20 | Flights above average revenue | Revenue | None | [sql/queries/03_subqueries.sql:869](../sql/queries/03_subqueries.sql#L869) |
| A21 | Aircraft above average capacity | Fleet & airports | None | [sql/queries/03_subqueries.sql:904](../sql/queries/03_subqueries.sql#L904) |
| A22 | Airports serving both directions | Fleet & airports | None | [sql/queries/03_subqueries.sql:927](../sql/queries/03_subqueries.sql#L927) |
| A23 | Frequent passengers | Passengers | None | [sql/queries/03_subqueries.sql:953](../sql/queries/03_subqueries.sql#L953) |
| A24 | Bookings on high-demand flights | Bookings | None | [sql/queries/03_subqueries.sql:986](../sql/queries/03_subqueries.sql#L986) |
| A25 | Fares above their flight average | Revenue | None | [sql/queries/03_subqueries.sql:1019](../sql/queries/03_subqueries.sql#L1019) |

## Original transactions

| Example | Purpose | Source |
| --- | --- | --- |
| 1 | Book a passenger on a flight with baggage | [sql/transactions/01_transactions.sql:11](../sql/transactions/01_transactions.sql#L11) |
| 2 | Transfer a passenger to a different flight | [sql/transactions/01_transactions.sql:41](../sql/transactions/01_transactions.sql#L41) |
| 3 | ROLLBACK demonstration | [sql/transactions/01_transactions.sql:79](../sql/transactions/01_transactions.sql#L79) |
| 4 | SAVEPOINT with partial rollback | [sql/transactions/01_transactions.sql:106](../sql/transactions/01_transactions.sql#L106) |
| 5 | Batch flight status update with SAVEPOINT | [sql/transactions/01_transactions.sql:142](../sql/transactions/01_transactions.sql#L142) |
| 6 | Cancel all bookings for a flight | [sql/transactions/01_transactions.sql:173](../sql/transactions/01_transactions.sql#L173) |
| 7 | Add a new airline with aircraft and a flight | [sql/transactions/01_transactions.sql:204](../sql/transactions/01_transactions.sql#L204) |
| 8 | ROLLBACK an entire fare-update batch | [sql/transactions/01_transactions.sql:239](../sql/transactions/01_transactions.sql#L239) |
| 9 | Passenger update with validation (SAVEPOINT) | [sql/transactions/01_transactions.sql:266](../sql/transactions/01_transactions.sql#L266) |
| 10 | Nested SAVEPOINTs — Add baggage in stages | [sql/transactions/01_transactions.sql:293](../sql/transactions/01_transactions.sql#L293) |

## Original triggers

| Trigger | Source |
| --- | --- |
| trg_flight_before_insert | [sql/triggers/01_triggers.sql:55](../sql/triggers/01_triggers.sql#L55) |
| trg_flight_before_update | [sql/triggers/01_triggers.sql:104](../sql/triggers/01_triggers.sql#L104) |
| trg_booking_before_insert | [sql/triggers/01_triggers.sql:125](../sql/triggers/01_triggers.sql#L125) |
| trg_baggage_before_insert | [sql/triggers/01_triggers.sql:186](../sql/triggers/01_triggers.sql#L186) |
| trg_passenger_before_insert | [sql/triggers/01_triggers.sql:201](../sql/triggers/01_triggers.sql#L201) |
| trg_flight_after_update | [sql/triggers/01_triggers.sql:221](../sql/triggers/01_triggers.sql#L221) |
| trg_booking_after_delete | [sql/triggers/01_triggers.sql:236](../sql/triggers/01_triggers.sql#L236) |
| trg_booking_after_insert | [sql/triggers/01_triggers.sql:249](../sql/triggers/01_triggers.sql#L249) |
| trg_flight_before_delete | [sql/triggers/01_triggers.sql:262](../sql/triggers/01_triggers.sql#L262) |
| trg_airline_before_delete | [sql/triggers/01_triggers.sql:283](../sql/triggers/01_triggers.sql#L283) |
| trg_flight_status_lock | [sql/triggers/01_triggers.sql:304](../sql/triggers/01_triggers.sql#L304) |
| trg_baggage_total_limit | [sql/triggers/01_triggers.sql:319](../sql/triggers/01_triggers.sql#L319) |
