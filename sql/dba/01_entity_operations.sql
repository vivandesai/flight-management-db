-- DBA statement templates consumed individually by the Flask catalogue.
-- Values use Connector/Python named parameters; do not SOURCE this DML file.
-- No schema changes, cascades, or automatic child deletion.
-- Contact/status UPDATE and Booking/Baggage DELETE patterns follow airline/workflows.py.

-- name: Airline.list
SELECT * FROM Airline WHERE LOCATE(%(search)s, CONCAT_WS(' ', airline_id, code, airline_name)) > 0 ORDER BY airline_id LIMIT %(limit)s OFFSET %(offset)s;

-- name: Airline.count
SELECT COUNT(*) AS total FROM Airline WHERE LOCATE(%(search)s, CONCAT_WS(' ', airline_id, code, airline_name)) > 0;

-- name: Airline.get
SELECT * FROM Airline WHERE airline_id = %(key_airline_id)s;

-- name: Airline.lock
SELECT * FROM Airline WHERE airline_id = %(key_airline_id)s FOR UPDATE;

-- name: Airline.update
UPDATE Airline SET code = %(code)s, airline_name = %(airline_name)s WHERE airline_id = %(key_airline_id)s;

-- name: Airline.delete
DELETE FROM Airline WHERE airline_id = %(key_airline_id)s;

-- name: Airline.dependencies
SELECT 'Aircraft' AS entity, COUNT(*) AS row_count FROM Aircraft WHERE airline_id = %(key_airline_id)s
UNION ALL
SELECT 'Flight' AS entity, COUNT(*) AS row_count FROM Flight WHERE airline_id = %(key_airline_id)s;

-- name: Aircraft.list
SELECT * FROM Aircraft WHERE LOCATE(%(search)s, CONCAT_WS(' ', aircraft_id, registration_no, model, capacity, airline_id)) > 0 ORDER BY aircraft_id LIMIT %(limit)s OFFSET %(offset)s;

-- name: Aircraft.count
SELECT COUNT(*) AS total FROM Aircraft WHERE LOCATE(%(search)s, CONCAT_WS(' ', aircraft_id, registration_no, model, capacity, airline_id)) > 0;

-- name: Aircraft.get
SELECT * FROM Aircraft WHERE aircraft_id = %(key_aircraft_id)s;

-- name: Aircraft.lock
SELECT * FROM Aircraft WHERE aircraft_id = %(key_aircraft_id)s FOR UPDATE;

-- name: Aircraft.update
UPDATE Aircraft SET registration_no = %(registration_no)s, model = %(model)s, capacity = %(capacity)s WHERE aircraft_id = %(key_aircraft_id)s;

-- name: Aircraft.delete
DELETE FROM Aircraft WHERE aircraft_id = %(key_aircraft_id)s;

-- name: Aircraft.dependencies
SELECT 'Flight' AS entity, COUNT(*) AS row_count FROM Flight WHERE aircraft_id = %(key_aircraft_id)s;

-- name: Airport.list
SELECT * FROM Airport WHERE LOCATE(%(search)s, CONCAT_WS(' ', airport_id, airport_code, airport_name, city)) > 0 ORDER BY airport_id LIMIT %(limit)s OFFSET %(offset)s;

-- name: Airport.count
SELECT COUNT(*) AS total FROM Airport WHERE LOCATE(%(search)s, CONCAT_WS(' ', airport_id, airport_code, airport_name, city)) > 0;

-- name: Airport.get
SELECT * FROM Airport WHERE airport_id = %(key_airport_id)s;

-- name: Airport.lock
SELECT * FROM Airport WHERE airport_id = %(key_airport_id)s FOR UPDATE;

-- name: Airport.update
UPDATE Airport SET airport_code = %(airport_code)s, airport_name = %(airport_name)s, city = %(city)s WHERE airport_id = %(key_airport_id)s;

-- name: Airport.delete
DELETE FROM Airport WHERE airport_id = %(key_airport_id)s;

-- name: Airport.dependencies
SELECT 'Flight departures' AS entity, COUNT(*) AS row_count FROM Flight WHERE departure_airport_id = %(key_airport_id)s
UNION ALL
SELECT 'Flight arrivals' AS entity, COUNT(*) AS row_count FROM Flight WHERE arrival_airport_id = %(key_airport_id)s;

-- name: Passenger.list
SELECT * FROM Passenger WHERE LOCATE(%(search)s, CONCAT_WS(' ', passenger_id, passenger_name, dob, phone, email, passport_no)) > 0 ORDER BY passenger_id LIMIT %(limit)s OFFSET %(offset)s;

-- name: Passenger.count
SELECT COUNT(*) AS total FROM Passenger WHERE LOCATE(%(search)s, CONCAT_WS(' ', passenger_id, passenger_name, dob, phone, email, passport_no)) > 0;

-- name: Passenger.get
SELECT * FROM Passenger WHERE passenger_id = %(key_passenger_id)s;

-- name: Passenger.lock
SELECT * FROM Passenger WHERE passenger_id = %(key_passenger_id)s FOR UPDATE;

-- name: Passenger.update
UPDATE Passenger SET passenger_name = %(passenger_name)s, dob = %(dob)s, phone = %(phone)s, email = %(email)s, passport_no = %(passport_no)s WHERE passenger_id = %(key_passenger_id)s;

-- name: Passenger.delete
DELETE FROM Passenger WHERE passenger_id = %(key_passenger_id)s;

-- name: Passenger.dependencies
SELECT 'Booking' AS entity, COUNT(*) AS row_count FROM Booking WHERE passenger_id = %(key_passenger_id)s;

-- name: Flight.list
SELECT * FROM Flight WHERE LOCATE(%(search)s, CONCAT_WS(' ', flight_id, departure_time, arrival_time, flight_status, airline_id, aircraft_id, departure_airport_id, arrival_airport_id)) > 0 ORDER BY flight_id LIMIT %(limit)s OFFSET %(offset)s;

-- name: Flight.count
SELECT COUNT(*) AS total FROM Flight WHERE LOCATE(%(search)s, CONCAT_WS(' ', flight_id, departure_time, arrival_time, flight_status, airline_id, aircraft_id, departure_airport_id, arrival_airport_id)) > 0;

-- name: Flight.get
SELECT * FROM Flight WHERE flight_id = %(key_flight_id)s;

-- name: Flight.lock
SELECT * FROM Flight WHERE flight_id = %(key_flight_id)s FOR UPDATE;

-- name: Flight.update
UPDATE Flight SET departure_time = %(departure_time)s, arrival_time = %(arrival_time)s, flight_status = %(flight_status)s WHERE flight_id = %(key_flight_id)s;

-- name: Flight.delete
DELETE FROM Flight WHERE flight_id = %(key_flight_id)s;

-- name: Flight.dependencies
SELECT 'Booking' AS entity, COUNT(*) AS row_count FROM Booking WHERE flight_id = %(key_flight_id)s;

-- name: Booking.list
SELECT * FROM Booking WHERE LOCATE(%(search)s, CONCAT_WS(' ', booking_id, booking_date, seat_number, fare, passenger_id, flight_id)) > 0 ORDER BY booking_id LIMIT %(limit)s OFFSET %(offset)s;

-- name: Booking.count
SELECT COUNT(*) AS total FROM Booking WHERE LOCATE(%(search)s, CONCAT_WS(' ', booking_id, booking_date, seat_number, fare, passenger_id, flight_id)) > 0;

-- name: Booking.get
SELECT * FROM Booking WHERE booking_id = %(key_booking_id)s;

-- name: Booking.lock
SELECT * FROM Booking WHERE booking_id = %(key_booking_id)s FOR UPDATE;

-- name: Booking.update
UPDATE Booking SET seat_number = %(seat_number)s, fare = %(fare)s WHERE booking_id = %(key_booking_id)s;

-- name: Booking.delete
DELETE FROM Booking WHERE booking_id = %(key_booking_id)s;

-- name: Booking.dependencies
SELECT 'Baggage' AS entity, COUNT(*) AS row_count FROM Baggage WHERE booking_id = %(key_booking_id)s;

-- name: Baggage.list
SELECT * FROM Baggage WHERE LOCATE(%(search)s, CONCAT_WS(' ', booking_id, baggage_no, baggage_weight)) > 0 ORDER BY booking_id, baggage_no LIMIT %(limit)s OFFSET %(offset)s;

-- name: Baggage.count
SELECT COUNT(*) AS total FROM Baggage WHERE LOCATE(%(search)s, CONCAT_WS(' ', booking_id, baggage_no, baggage_weight)) > 0;

-- name: Baggage.get
SELECT * FROM Baggage WHERE booking_id = %(key_booking_id)s AND baggage_no = %(key_baggage_no)s;

-- name: Baggage.lock
SELECT * FROM Baggage WHERE booking_id = %(key_booking_id)s AND baggage_no = %(key_baggage_no)s FOR UPDATE;

-- name: Baggage.update
UPDATE Baggage SET baggage_weight = %(baggage_weight)s WHERE booking_id = %(key_booking_id)s AND baggage_no = %(key_baggage_no)s;

-- name: Baggage.delete
DELETE FROM Baggage WHERE booking_id = %(key_booking_id)s AND baggage_no = %(key_baggage_no)s;

-- name: Baggage.dependencies
SELECT 'Dependent records' AS entity, 0 AS row_count;

-- name: rule.clock
SELECT CURRENT_TIMESTAMP AS now, CURDATE() AS today;

-- name: rule.aircraft_flights
SELECT flight_id FROM Flight WHERE aircraft_id = %(aircraft_id)s ORDER BY flight_id FOR UPDATE;

-- name: rule.booked_seats
SELECT COUNT(*) AS booked FROM Booking WHERE flight_id = %(flight_id)s;

-- name: rule.overlap
SELECT flight_id FROM Flight WHERE aircraft_id = %(aircraft_id)s AND flight_id <> %(flight_id)s AND flight_status <> 'Cancelled' AND %(departure_time)s < arrival_time AND %(arrival_time)s > departure_time LIMIT 1;

-- name: rule.baggage_total
SELECT COALESCE(SUM(baggage_weight), 0) AS total FROM Baggage WHERE booking_id = %(booking_id)s AND baggage_no <> %(baggage_no)s;
