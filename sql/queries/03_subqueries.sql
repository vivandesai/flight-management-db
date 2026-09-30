USE FlightManagement;

-- ============================================================
-- 03_subqueries.sql
-- Flight Management Mini Project
--
-- Purpose:
--   Subqueries used by BOTH the user-facing website and
--   the administrator panel.
--
-- Tables available in the current schema:
--   Airline, Aircraft, Airport, Passenger,
--   Flight, Booking, Baggage
--
-- IMPORTANT:
-- Before testing, change the sample variables below as needed.
-- ============================================================


/* ============================================================
   SAMPLE INPUTS FOR USER-SIDE QUERIES
   ============================================================ */

SET @from_city = 'Mumbai';
SET @to_city = 'Delhi';
SET @travel_date = '2026-10-01';
SET @airline_code = 'AI';
SET @passenger_id = 1;
SET @flight_id = 1;


/* ============================================================
   ======================= USER PANEL =========================
   ============================================================ */


/* ------------------------------------------------------------
   U1. SEARCH FLIGHTS BY SOURCE CITY, DESTINATION CITY,
       AND TRAVEL DATE

   Website use:
   Main "Search Flights" page.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    ar.airline_name,
    f.departure_time,
    f.arrival_time,
    f.flight_status,
    dep.airport_code AS departure_airport,
    dep.city AS departure_city,
    arr.airport_code AS arrival_airport,
    arr.city AS arrival_city
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
JOIN Airport dep
    ON f.departure_airport_id = dep.airport_id
JOIN Airport arr
    ON f.arrival_airport_id = arr.airport_id
WHERE f.departure_airport_id IN (
    SELECT airport_id
    FROM Airport
    WHERE city = @from_city
)
AND f.arrival_airport_id IN (
    SELECT airport_id
    FROM Airport
    WHERE city = @to_city
)
AND DATE(f.departure_time) = @travel_date
ORDER BY f.departure_time;


/* ------------------------------------------------------------
   U2. FILTER FLIGHTS BY AIRLINE

   Website use:
   Search-result airline filter.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    ar.airline_name,
    f.departure_time,
    f.arrival_time,
    f.flight_status
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
WHERE f.airline_id IN (
    SELECT airline_id
    FROM Airline
    WHERE code = @airline_code
)
ORDER BY f.departure_time;


/* ------------------------------------------------------------
   U3. SHOW AVAILABLE SEATS FOR A SELECTED FLIGHT

   Website use:
   Flight details / booking page.

   Since there is no Seat table in the current schema:
       available seats = aircraft capacity - bookings.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    a.capacity AS total_seats,
    (
        a.capacity -
        (
            SELECT COUNT(*)
            FROM Booking b
            WHERE b.flight_id = f.flight_id
        )
    ) AS available_seats
FROM Flight f
JOIN Aircraft a
    ON f.aircraft_id = a.aircraft_id
WHERE f.flight_id = @flight_id;


/* ------------------------------------------------------------
   U4. SHOW ONLY FLIGHTS THAT STILL HAVE AVAILABLE SEATS

   Website use:
   Search results / booking eligibility.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    ar.airline_name,
    f.departure_time,
    f.arrival_time,
    f.flight_status,
    a.capacity AS total_seats,
    (
        a.capacity -
        (
            SELECT COUNT(*)
            FROM Booking b
            WHERE b.flight_id = f.flight_id
        )
    ) AS available_seats
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
JOIN Aircraft a
    ON f.aircraft_id = a.aircraft_id
WHERE a.capacity >
      (
          SELECT COUNT(*)
          FROM Booking b
          WHERE b.flight_id = f.flight_id
      )
ORDER BY f.departure_time;


/* ------------------------------------------------------------
   U5. SHOW A PASSENGER'S BOOKINGS

   Website use:
   "My Bookings" page.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    b.booking_date,
    b.seat_number,
    b.fare
FROM Booking b
WHERE b.passenger_id IN (
    SELECT passenger_id
    FROM Passenger
    WHERE passenger_id = @passenger_id
)
ORDER BY b.booking_date DESC;


/* ------------------------------------------------------------
   U6. SHOW DETAILED BOOKINGS FOR A PASSENGER

   Website use:
   Booking history page.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.booking_date,
    b.seat_number,
    b.fare,
    f.flight_id,
    f.departure_time,
    f.arrival_time,
    f.flight_status,
    dep.airport_code AS departure_airport,
    dep.city AS departure_city,
    arr.airport_code AS arrival_airport,
    arr.city AS arrival_city,
    ar.airline_name
FROM Booking b
JOIN Flight f
    ON b.flight_id = f.flight_id
JOIN Airline ar
    ON f.airline_id = ar.airline_id
JOIN Airport dep
    ON f.departure_airport_id = dep.airport_id
JOIN Airport arr
    ON f.arrival_airport_id = arr.airport_id
WHERE b.passenger_id IN (
    SELECT passenger_id
    FROM Passenger
    WHERE passenger_id = @passenger_id
)
ORDER BY b.booking_date DESC;


/* ------------------------------------------------------------
   U7. CHECK WHETHER A PASSENGER HAS MADE ANY BOOKING

   Website use:
   Profile/dashboard.
   ------------------------------------------------------------ */

SELECT
    p.passenger_id,
    p.passenger_name,
    p.email
FROM Passenger p
WHERE p.passenger_id = @passenger_id
AND EXISTS (
    SELECT 1
    FROM Booking b
    WHERE b.passenger_id = p.passenger_id
);


/* ------------------------------------------------------------
   U8. SHOW ALL BAGGAGE FOR ONE BOOKING

   Website use:
   Booking details / baggage page.
   ------------------------------------------------------------ */

SELECT
    bg.booking_id,
    bg.baggage_no,
    bg.baggage_weight
FROM Baggage bg
WHERE bg.booking_id IN (
    SELECT booking_id
    FROM Booking
    WHERE booking_id = (
        SELECT booking_id
        FROM Booking
        WHERE passenger_id = @passenger_id
        ORDER BY booking_date DESC, booking_id DESC
        LIMIT 1
    )
)
ORDER BY bg.baggage_no;


/* ------------------------------------------------------------
   U9. SHOW TOTAL BAGGAGE WEIGHT FOR EACH BOOKING OF A PASSENGER

   Website use:
   "My Bookings" / baggage summary.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    (
        SELECT COALESCE(SUM(bg.baggage_weight), 0)
        FROM Baggage bg
        WHERE bg.booking_id = b.booking_id
    ) AS total_baggage_weight
FROM Booking b
WHERE b.passenger_id = @passenger_id
ORDER BY b.booking_date DESC;


/* ------------------------------------------------------------
   U10. SHOW THE PASSENGER'S TOTAL SPENDING

   Website use:
   Customer profile / dashboard.
   ------------------------------------------------------------ */

SELECT
    p.passenger_id,
    p.passenger_name,
    (
        SELECT COALESCE(SUM(b.fare), 0)
        FROM Booking b
        WHERE b.passenger_id = p.passenger_id
    ) AS total_spent
FROM Passenger p
WHERE p.passenger_id = @passenger_id;


/* ------------------------------------------------------------
   U11. FIND THE CHEAPEST BOOKING ON EACH FLIGHT

   Website use:
   Fare comparison / flight details.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    b.passenger_id,
    b.fare
FROM Booking b
WHERE b.fare = (
    SELECT MIN(b2.fare)
    FROM Booking b2
    WHERE b2.flight_id = b.flight_id
)
ORDER BY b.flight_id;


/* ------------------------------------------------------------
   U12. FIND FLIGHTS WITH FARES ABOVE THE OVERALL AVERAGE

   Website use:
   Optional "premium/high-fare" filter or display.
   ------------------------------------------------------------ */

SELECT
    b.flight_id,
    b.booking_id,
    b.fare
FROM Booking b
WHERE b.fare > (
    SELECT AVG(fare)
    FROM Booking
)
ORDER BY b.fare DESC;


/* ------------------------------------------------------------
   U13. FIND PASSENGERS WHO HAVE NEVER MADE A BOOKING

   Website use:
   This can support a profile/customer-state page.
   ------------------------------------------------------------ */

SELECT
    p.passenger_id,
    p.passenger_name,
    p.email,
    p.phone
FROM Passenger p
WHERE NOT EXISTS (
    SELECT 1
    FROM Booking b
    WHERE b.passenger_id = p.passenger_id
)
ORDER BY p.passenger_name;


/* ------------------------------------------------------------
   U14. FIND THE MOST EXPENSIVE BOOKING FOR EACH FLIGHT

   Website use:
   Fare analytics on a flight details page.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    b.passenger_id,
    b.fare
FROM Booking b
WHERE b.fare = (
    SELECT MAX(b2.fare)
    FROM Booking b2
    WHERE b2.flight_id = b.flight_id
)
ORDER BY b.flight_id;


/* ============================================================
   ======================= ADMIN PANEL =========================
   ============================================================ */


/* ------------------------------------------------------------
   A1. ADMIN DASHBOARD - TOTAL COUNTS

   Admin use:
   Main dashboard.
   ------------------------------------------------------------ */

SELECT
    (SELECT COUNT(*) FROM Airline)   AS total_airlines,
    (SELECT COUNT(*) FROM Aircraft)  AS total_aircraft,
    (SELECT COUNT(*) FROM Airport)   AS total_airports,
    (SELECT COUNT(*) FROM Passenger) AS total_passengers,
    (SELECT COUNT(*) FROM Flight)    AS total_flights,
    (SELECT COUNT(*) FROM Booking)   AS total_bookings,
    (SELECT COUNT(*) FROM Baggage)   AS total_baggage;


/* ------------------------------------------------------------
   A2. TOTAL REVENUE GENERATED BY ALL BOOKINGS

   Admin use:
   Revenue card on dashboard.
   ------------------------------------------------------------ */

SELECT
    COALESCE(
        (
            SELECT SUM(fare)
            FROM Booking
        ),
        0
    ) AS total_revenue;


/* ------------------------------------------------------------
   A3. REVENUE BY AIRLINE

   Admin use:
   Airline performance/revenue report.
   ------------------------------------------------------------ */

SELECT
    ar.airline_id,
    ar.airline_name,
    (
        SELECT COALESCE(SUM(b.fare), 0)
        FROM Booking b
        WHERE b.flight_id IN (
            SELECT f.flight_id
            FROM Flight f
            WHERE f.airline_id = ar.airline_id
        )
    ) AS total_revenue
FROM Airline ar
ORDER BY total_revenue DESC;


/* ------------------------------------------------------------
   A4. BOOKINGS PER FLIGHT

   Admin use:
   Flight performance table.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    f.departure_time,
    f.arrival_time,
    (
        SELECT COUNT(*)
        FROM Booking b
        WHERE b.flight_id = f.flight_id
    ) AS total_bookings
FROM Flight f
ORDER BY total_bookings DESC;


/* ------------------------------------------------------------
   A5. FLIGHT OCCUPANCY AND AVAILABLE SEATS

   Admin use:
   Flight-management dashboard.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    ar.airline_name,
    a.capacity AS total_seats,
    (
        SELECT COUNT(*)
        FROM Booking b
        WHERE b.flight_id = f.flight_id
    ) AS booked_seats,
    (
        a.capacity -
        (
            SELECT COUNT(*)
            FROM Booking b
            WHERE b.flight_id = f.flight_id
        )
    ) AS available_seats
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
JOIN Aircraft a
    ON f.aircraft_id = a.aircraft_id
ORDER BY f.flight_id;


/* ------------------------------------------------------------
   A6. FLIGHTS THAT ARE ALMOST FULL

   Admin use:
   Operational alert.

   Here "almost full" means 90% or more occupied.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    ar.airline_name,
    a.capacity AS total_seats,
    (
        SELECT COUNT(*)
        FROM Booking b
        WHERE b.flight_id = f.flight_id
    ) AS booked_seats,
    ROUND(
        (
            (
                SELECT COUNT(*)
                FROM Booking b
                WHERE b.flight_id = f.flight_id
            ) / a.capacity
        ) * 100,
        2
    ) AS occupancy_percentage
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
JOIN Aircraft a
    ON f.aircraft_id = a.aircraft_id
WHERE
    (
        SELECT COUNT(*)
        FROM Booking b
        WHERE b.flight_id = f.flight_id
    ) >= a.capacity * 0.90
ORDER BY occupancy_percentage DESC;


/* ------------------------------------------------------------
   A7. FLIGHTS WITH NO BOOKINGS

   Admin use:
   Identify poorly utilized flights.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    f.departure_time,
    f.arrival_time,
    ar.airline_name
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
WHERE NOT EXISTS (
    SELECT 1
    FROM Booking b
    WHERE b.flight_id = f.flight_id
)
ORDER BY f.departure_time;


/* ------------------------------------------------------------
   A8. AIRCRAFT NEVER USED FOR ANY FLIGHT

   Admin use:
   Aircraft utilization.
   ------------------------------------------------------------ */

SELECT
    a.aircraft_id,
    a.registration_no,
    a.model,
    a.capacity,
    ar.airline_name
FROM Aircraft a
JOIN Airline ar
    ON a.airline_id = ar.airline_id
WHERE NOT EXISTS (
    SELECT 1
    FROM Flight f
    WHERE f.aircraft_id = a.aircraft_id
);


/* ------------------------------------------------------------
   A9. AIRCRAFT USAGE COUNT

   Admin use:
   Fleet-management dashboard.
   ------------------------------------------------------------ */

SELECT
    a.aircraft_id,
    a.registration_no,
    a.model,
    a.capacity,
    (
        SELECT COUNT(*)
        FROM Flight f
        WHERE f.aircraft_id = a.aircraft_id
    ) AS flights_operated
FROM Aircraft a
ORDER BY flights_operated DESC;


/* ------------------------------------------------------------
   A10. AIRPORTS NOT USED BY ANY FLIGHT

   Admin use:
   Airport-management report.
   ------------------------------------------------------------ */

SELECT
    ap.airport_id,
    ap.airport_code,
    ap.airport_name,
    ap.city
FROM Airport ap
WHERE NOT EXISTS (
    SELECT 1
    FROM Flight f
    WHERE f.departure_airport_id = ap.airport_id
       OR f.arrival_airport_id = ap.airport_id
)
ORDER BY ap.city;


/* ------------------------------------------------------------
   A11. PASSENGERS WITH THEIR TOTAL SPENDING

   Admin use:
   Customer-value report.
   ------------------------------------------------------------ */

SELECT
    p.passenger_id,
    p.passenger_name,
    p.email,
    (
        SELECT COALESCE(SUM(b.fare), 0)
        FROM Booking b
        WHERE b.passenger_id = p.passenger_id
    ) AS total_spent
FROM Passenger p
ORDER BY total_spent DESC;


/* ------------------------------------------------------------
   A12. PASSENGERS SPENDING MORE THAN THE AVERAGE

   Admin use:
   Customer analytics.

   Uses:
   Correlated subquery + nested aggregate subquery.
   ------------------------------------------------------------ */

SELECT
    p.passenger_id,
    p.passenger_name,
    (
        SELECT SUM(b.fare)
        FROM Booking b
        WHERE b.passenger_id = p.passenger_id
    ) AS total_spent
FROM Passenger p
WHERE (
    SELECT SUM(b.fare)
    FROM Booking b
    WHERE b.passenger_id = p.passenger_id
) > (
    SELECT AVG(passenger_total)
    FROM (
        SELECT
            passenger_id,
            SUM(fare) AS passenger_total
        FROM Booking
        GROUP BY passenger_id
    ) AS passenger_totals
)
ORDER BY total_spent DESC;


/* ------------------------------------------------------------
   A13. MOST BOOKED FLIGHT(S)

   Admin use:
   "Popular Flights" dashboard widget.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    f.departure_time,
    f.arrival_time,
    ar.airline_name,
    (
        SELECT COUNT(*)
        FROM Booking b
        WHERE b.flight_id = f.flight_id
    ) AS total_bookings
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
WHERE (
    SELECT COUNT(*)
    FROM Booking b
    WHERE b.flight_id = f.flight_id
) = (
    SELECT MAX(booking_count)
    FROM (
        SELECT
            flight_id,
            COUNT(*) AS booking_count
        FROM Booking
        GROUP BY flight_id
    ) AS flight_booking_counts
);


/* ------------------------------------------------------------
   A14. AIRLINES WITH ABOVE-AVERAGE FLIGHT COUNTS

   Admin use:
   Airline performance report.
   ------------------------------------------------------------ */

SELECT
    ar.airline_id,
    ar.code,
    ar.airline_name
FROM Airline ar
WHERE (
    SELECT COUNT(*)
    FROM Flight f
    WHERE f.airline_id = ar.airline_id
) > (
    SELECT AVG(flight_count)
    FROM (
        SELECT
            airline_id,
            COUNT(*) AS flight_count
        FROM Flight
        GROUP BY airline_id
    ) AS airline_counts
);


/* ------------------------------------------------------------
   A15. BOOKINGS THAT HAVE BAGGAGE

   Admin use:
   Baggage-management/report page.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.passenger_id,
    b.flight_id,
    b.booking_date,
    b.seat_number,
    b.fare
FROM Booking b
WHERE EXISTS (
    SELECT 1
    FROM Baggage bg
    WHERE bg.booking_id = b.booking_id
)
ORDER BY b.booking_date DESC;


/* ------------------------------------------------------------
   A16. BOOKINGS WITHOUT BAGGAGE

   Admin use:
   Baggage report.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.passenger_id,
    b.flight_id,
    b.booking_date,
    b.seat_number,
    b.fare
FROM Booking b
WHERE NOT EXISTS (
    SELECT 1
    FROM Baggage bg
    WHERE bg.booking_id = b.booking_id
)
ORDER BY b.booking_date DESC;


/* ------------------------------------------------------------
   A17. TOTAL BAGGAGE WEIGHT PER BOOKING

   Admin use:
   Baggage monitoring.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    b.passenger_id,
    (
        SELECT COALESCE(SUM(bg.baggage_weight), 0)
        FROM Baggage bg
        WHERE bg.booking_id = b.booking_id
    ) AS total_baggage_weight
FROM Booking b
ORDER BY total_baggage_weight DESC;


/* ------------------------------------------------------------
   A18. HEAVIER-THAN-AVERAGE BAGGAGE

   Admin use:
   Identify bookings carrying relatively heavy baggage.
   ------------------------------------------------------------ */

SELECT
    bg.booking_id,
    bg.baggage_no,
    bg.baggage_weight
FROM Baggage bg
WHERE bg.baggage_weight > (
    SELECT AVG(bg2.baggage_weight)
    FROM Baggage bg2
)
ORDER BY bg.baggage_weight DESC;


/* ------------------------------------------------------------
   A19. HIGHEST-FARE BOOKING(S)

   Admin use:
   Revenue/fare analytics.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.passenger_id,
    b.flight_id,
    b.fare
FROM Booking b
WHERE b.fare = (
    SELECT MAX(fare)
    FROM Booking
);


/* ------------------------------------------------------------
   A20. FLIGHTS WITH REVENUE ABOVE THE AVERAGE FLIGHT REVENUE

   Admin use:
   Flight revenue analytics.

   This returns flight-level revenue and compares it with
   the average revenue of flights that have bookings.
   ------------------------------------------------------------ */

SELECT
    f.flight_id,
    ar.airline_name,
    (
        SELECT COALESCE(SUM(b.fare), 0)
        FROM Booking b
        WHERE b.flight_id = f.flight_id
    ) AS flight_revenue
FROM Flight f
JOIN Airline ar
    ON f.airline_id = ar.airline_id
WHERE (
    SELECT COALESCE(SUM(b.fare), 0)
    FROM Booking b
    WHERE b.flight_id = f.flight_id
) > (
    SELECT AVG(flight_revenue)
    FROM (
        SELECT
            flight_id,
            SUM(fare) AS flight_revenue
        FROM Booking
        GROUP BY flight_id
    ) AS flight_revenues
)
ORDER BY flight_revenue DESC;


/* ------------------------------------------------------------
   A21. AIRCRAFT WITH CAPACITY ABOVE THE AVERAGE CAPACITY

   Admin use:
   Fleet analytics.
   ------------------------------------------------------------ */

SELECT
    a.aircraft_id,
    a.registration_no,
    a.model,
    a.capacity
FROM Aircraft a
WHERE a.capacity > (
    SELECT AVG(capacity)
    FROM Aircraft
)
ORDER BY a.capacity DESC;


/* ------------------------------------------------------------
   A22. AIRPORTS USED AS BOTH DEPARTURE AND ARRIVAL AIRPORTS

   Admin use:
   Network analysis.

   Uses:
   Two correlated EXISTS checks.
   ------------------------------------------------------------ */

SELECT
    ap.airport_id,
    ap.airport_code,
    ap.airport_name,
    ap.city
FROM Airport ap
WHERE EXISTS (
    SELECT 1
    FROM Flight f
    WHERE f.departure_airport_id = ap.airport_id
)
AND EXISTS (
    SELECT 1
    FROM Flight f
    WHERE f.arrival_airport_id = ap.airport_id
)
ORDER BY ap.city;


/* ------------------------------------------------------------
   A23. PASSENGERS WITH MORE BOOKINGS THAN THE AVERAGE

   Admin use:
   Frequent-customer analytics.
   ------------------------------------------------------------ */

SELECT
    p.passenger_id,
    p.passenger_name,
    (
        SELECT COUNT(*)
        FROM Booking b
        WHERE b.passenger_id = p.passenger_id
    ) AS booking_count
FROM Passenger p
WHERE (
    SELECT COUNT(*)
    FROM Booking b
    WHERE b.passenger_id = p.passenger_id
) > (
    SELECT AVG(booking_count)
    FROM (
        SELECT
            passenger_id,
            COUNT(*) AS booking_count
        FROM Booking
        GROUP BY passenger_id
    ) AS passenger_booking_counts
)
ORDER BY booking_count DESC;


/* ------------------------------------------------------------
   A24. BOOKINGS ON FLIGHTS WITH MORE THAN AVERAGE BOOKINGS

   Admin use:
   Identify high-demand flights and their bookings.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    b.passenger_id,
    b.fare
FROM Booking b
WHERE b.flight_id IN (
    SELECT flight_id
    FROM Booking
    GROUP BY flight_id
    HAVING COUNT(*) > (
        SELECT AVG(booking_count)
        FROM (
            SELECT
                flight_id,
                COUNT(*) AS booking_count
            FROM Booking
            GROUP BY flight_id
        ) AS flight_counts
    )
)
ORDER BY b.flight_id, b.fare DESC;


/* ------------------------------------------------------------
   A25. BOOKINGS WITH ABOVE-AVERAGE FARE FOR THEIR OWN FLIGHT

   Admin use:
   Detect relatively expensive bookings within each flight.

   This is a correlated subquery.
   ------------------------------------------------------------ */

SELECT
    b.booking_id,
    b.flight_id,
    b.passenger_id,
    b.fare
FROM Booking b
WHERE b.fare > (
    SELECT AVG(b2.fare)
    FROM Booking b2
    WHERE b2.flight_id = b.flight_id
)
ORDER BY b.flight_id, b.fare DESC;