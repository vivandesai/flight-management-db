-- This query retrieves flight information along with the corresponding airline information

SELECT f.flight_id, f.departure_time, f.arrival_time, a.airline_name
FROM Flight f
JOIN Airline a ON f.airline_id = a.airline_id;


-- This query retrieves aircraft information along with the corresponding airline information

SELECT ac.aircraft_id, ac.registration_no, ac.model, ac.capacity, a.airline_name
FROM Aircraft ac
JOIN Airline a ON ac.airline_id = a.airline_id;


-- This query retrieves flight information along with the corresponding departure and arrival airport information

SELECT f.flight_id,
       dep.airport_code AS departure_airport,
       dep.city AS departure_city,
       arr.airport_code AS arrival_airport,
       arr.city AS arrival_city
FROM Flight f
JOIN Airport dep ON f.departure_airport_id = dep.airport_id
JOIN Airport arr ON f.arrival_airport_id = arr.airport_id;


-- Displays complete flight information

SELECT f.flight_id,
       a.airline_name AS airline_name, ac.registration_no, ac.model,
       dep.airport_code AS departure_airport,
       arr.airport_code AS arrival_airport,
       f.departure_time, f.arrival_time, f.flight_status
FROM Flight f
JOIN Airline a ON f.airline_id = a.airline_id
JOIN Aircraft ac ON f.aircraft_id = ac.aircraft_id
JOIN Airport dep ON f.departure_airport_id = dep.airport_id
JOIN Airport arr ON f.arrival_airport_id = arr.airport_id;


-- Display Passenger booking information

SELECT p.passenger_id, p.passenger_name AS passenger_name,
       b.booking_id, b.booking_date, b.seat_number, b.fare
FROM Passenger p
JOIN Booking b ON p.passenger_id = b.passenger_id;


-- Display Passenger booking information along with flight and airline details

SELECT p.passenger_name AS passenger_name, b.booking_id,
       f.flight_id,
       a.airline_name AS airline_name,
       f.departure_time,
       f.arrival_time
FROM Passenger p
JOIN Booking b ON p.passenger_id = b.passenger_id
JOIN Flight f ON b.flight_id = f.flight_id
JOIN Airline a ON f.airline_id = a.airline_id;


-- Display all passengers and their bookings

SELECT p.passenger_id, p.passenger_name AS passenger_name,
       b.booking_id, b.flight_id, b.seat_number
FROM Passenger p
LEFT JOIN Booking b ON p.passenger_id = b.passenger_id;


-- Display all flights and total number of bookings for each flight

SELECT f.flight_id, f.flight_status, COUNT(b.booking_id) AS total_bookings
FROM Flight f
LEFT JOIN Booking b ON f.flight_id = b.flight_id
GROUP BY f.flight_id, f.flight_status;