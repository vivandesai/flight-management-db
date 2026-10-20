-- Seven management views. Install explicitly; never reseed or alter base tables.
-- SQL SECURITY INVOKER uses the connected account's existing privileges.
-- V1: based on J4 in sql/queries/01_joins.sql.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_flight_operations
(flight_id, airline_name, registration_no, model, departure_airport,
 arrival_airport, departure_time, arrival_time, flight_status) AS
SELECT f.flight_id, a.airline_name, ac.registration_no, ac.model,
       dep.airport_code, arr.airport_code,
       f.departure_time, f.arrival_time, f.flight_status
FROM Flight f
JOIN Airline a ON a.airline_id = f.airline_id
JOIN Aircraft ac ON ac.aircraft_id = f.aircraft_id
JOIN Airport dep ON dep.airport_id = f.departure_airport_id
JOIN Airport arr ON arr.airport_id = f.arrival_airport_id;

-- V2: based on A5 in sql/queries/03_subqueries.sql; includes all flight statuses.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_flight_occupancy
(flight_id, airline_name, flight_status, total_seats, booked_seats,
 available_seats, occupancy_percentage) AS
SELECT f.flight_id, ar.airline_name, f.flight_status, ac.capacity,
       COUNT(b.booking_id), ac.capacity - COUNT(b.booking_id),
       ROUND(100.0 * COUNT(b.booking_id) / ac.capacity, 2)
FROM Flight f
JOIN Airline ar ON ar.airline_id = f.airline_id
JOIN Aircraft ac ON ac.aircraft_id = f.aircraft_id
LEFT JOIN Booking b ON b.flight_id = f.flight_id
GROUP BY f.flight_id, ar.airline_name, f.flight_status, ac.capacity;

-- V3: combines G1 and A3; independent aggregates avoid aircraft/booking fan-out.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_airline_performance
(airline_id, code, airline_name, aircraft_count, flight_count, booking_count, total_revenue) AS
SELECT a.airline_id, a.code, a.airline_name,
       (SELECT COUNT(*) FROM Aircraft ac WHERE ac.airline_id = a.airline_id),
       (SELECT COUNT(*) FROM Flight f WHERE f.airline_id = a.airline_id),
       (SELECT COUNT(*) FROM Booking b JOIN Flight f ON f.flight_id = b.flight_id
        WHERE f.airline_id = a.airline_id),
       (SELECT COALESCE(SUM(b.fare), 0) FROM Booking b
        JOIN Flight f ON f.flight_id = b.flight_id WHERE f.airline_id = a.airline_id)
FROM Airline a;

-- V4: combines G4 and A11. Passengers with no bookings remain visible.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_passenger_activity
(passenger_id, passenger_name, phone, email, booking_count, total_spent, latest_booking_date) AS
SELECT p.passenger_id, p.passenger_name, p.phone, p.email,
       COUNT(b.booking_id), COALESCE(SUM(b.fare), 0), MAX(b.booking_date)
FROM Passenger p LEFT JOIN Booking b ON b.passenger_id = p.passenger_id
GROUP BY p.passenger_id, p.passenger_name, p.phone, p.email;

-- V5: extends J5/J6 with readable routes. Exactly one row per booking.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_booking_manifest
(booking_id, booking_date, passenger_id, passenger_name, flight_id, airline_name,
 departure_airport, arrival_airport, departure_time, arrival_time, flight_status, seat_number, fare) AS
SELECT b.booking_id, b.booking_date, p.passenger_id, p.passenger_name,
       f.flight_id, a.airline_name, dep.airport_code, arr.airport_code,
       f.departure_time, f.arrival_time, f.flight_status, b.seat_number, b.fare
FROM Booking b JOIN Passenger p ON p.passenger_id = b.passenger_id
JOIN Flight f ON f.flight_id = b.flight_id
JOIN Airline a ON a.airline_id = f.airline_id
JOIN Airport dep ON dep.airport_id = f.departure_airport_id
JOIN Airport arr ON arr.airport_id = f.arrival_airport_id;

-- V6: extends A17. Bookings without baggage show zero bags and zero weight.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_booking_baggage
(booking_id, passenger_id, passenger_name, flight_id, flight_status, bag_count, total_baggage_weight) AS
SELECT b.booking_id, p.passenger_id, p.passenger_name, f.flight_id, f.flight_status,
       COUNT(bg.baggage_no), COALESCE(SUM(bg.baggage_weight), 0)
FROM Booking b JOIN Passenger p ON p.passenger_id = b.passenger_id
JOIN Flight f ON f.flight_id = b.flight_id
LEFT JOIN Baggage bg ON bg.booking_id = b.booking_id
GROUP BY b.booking_id, p.passenger_id, p.passenger_name, f.flight_id, f.flight_status;

-- V7: airport traffic, complementing A10/A22. Independent counts avoid fan-out.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_airport_traffic
(airport_id, airport_code, airport_name, city, departure_count, arrival_count, total_movements) AS
SELECT a.airport_id, a.airport_code, a.airport_name, a.city,
       (SELECT COUNT(*) FROM Flight f WHERE f.departure_airport_id = a.airport_id),
       (SELECT COUNT(*) FROM Flight f WHERE f.arrival_airport_id = a.airport_id),
       (SELECT COUNT(*) FROM Flight f WHERE f.departure_airport_id = a.airport_id)
       + (SELECT COUNT(*) FROM Flight f WHERE f.arrival_airport_id = a.airport_id)
FROM Airport a;
