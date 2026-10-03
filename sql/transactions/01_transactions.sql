
-- ================================================================
-- TRANSACTIONS FOR FLIGHT MANAGEMENT DATABASE
-- Demonstrates: COMMIT, ROLLBACK, SAVEPOINT, error handling
-- ================================================================

USE FlightManagement;


-- ================================================================
-- TRANSACTION 1: Book a passenger on a flight with baggage
-- (Multi-table insert — all-or-nothing)
--
-- Scenario: A new passenger registers AND books a flight AND
--           checks in baggage. If any step fails the entire
--           operation must roll back so we don't end up with
--           an orphan passenger or booking record.
-- ================================================================

START TRANSACTION;

    -- Step 1: Register a new passenger
    INSERT INTO Passenger (passenger_name, dob, phone, email, passport_no)
    VALUES ('Riya Gupta', '2001-07-19', '9876543230', 'riya.gupta@email.com', 'P100016');

    -- Step 2: Create a booking on Flight 1 (BOM → DEL)
    INSERT INTO Booking (booking_date, seat_number, fare, passenger_id, flight_id)
    VALUES (CURDATE(), '22A', 6800.00, LAST_INSERT_ID(), 1);

    -- Step 3: Add baggage for that booking
    INSERT INTO Baggage (booking_id, baggage_no, baggage_weight)
    VALUES (LAST_INSERT_ID(), 1, 15.00);

COMMIT;
-- If all three INSERTs succeed the data is permanently saved.

SELECT '--- Transaction 1 committed: New passenger + booking + baggage ---' AS Result;


-- ================================================================
-- TRANSACTION 2: Transfer a passenger to a different flight
-- (Update + Insert + Delete — atomic rebooking)
--
-- Scenario: Passenger 1 (Rahul Sharma) is currently booked on
--           Flight 1. We want to move him to Flight 10 instead.
--           We must delete the old booking, create the new one,
--           and move baggage records — all atomically.
-- ================================================================

START TRANSACTION;

    -- Step 1: Remember old booking details for baggage transfer
    SET @old_booking_id = (SELECT booking_id FROM Booking
                           WHERE passenger_id = 1 AND flight_id = 1);

    -- Step 2: Delete baggage tied to the old booking
    DELETE FROM Baggage
    WHERE booking_id = @old_booking_id;

    -- Step 3: Delete the old booking
    DELETE FROM Booking
    WHERE booking_id = @old_booking_id;

    -- Step 4: Create new booking on Flight 10
    INSERT INTO Booking (booking_date, seat_number, fare, passenger_id, flight_id)
    VALUES (CURDATE(), '20A', 7800.00, 1, 10);

    -- Step 5: Re-add baggage under the new booking
    INSERT INTO Baggage (booking_id, baggage_no, baggage_weight)
    VALUES (LAST_INSERT_ID(), 1, 18.50),
           (LAST_INSERT_ID(), 2, 7.20);

COMMIT;

SELECT '--- Transaction 2 committed: Passenger rebooking completed ---' AS Result;


-- ================================================================
-- TRANSACTION 3: ROLLBACK demonstration
-- (Intentional failure — insert violates business rule)
--
-- Scenario: Attempt to book a passenger on a cancelled flight.
--           The trigger trg_booking_before_insert will reject
--           the INSERT, and the transaction is rolled back.
-- ================================================================

-- First, cancel Flight 11 so the demo works
UPDATE Flight SET flight_status = 'Cancelled' WHERE flight_id = 11;

START TRANSACTION;

    -- This INSERT should FAIL because Flight 11 is now cancelled
    -- (trigger trg_booking_before_insert raises SQLSTATE 45000)
    INSERT INTO Booking (booking_date, seat_number, fare, passenger_id, flight_id)
    VALUES (CURDATE(), '25A', 7000.00, 15, 11);

    -- This line would never execute because the error above
    -- causes an implicit rollback in most clients.

ROLLBACK;

SELECT '--- Transaction 3 rolled back: Cannot book a cancelled flight ---' AS Result;


-- ================================================================
-- TRANSACTION 4: SAVEPOINT with partial rollback
-- (Book multiple passengers; undo only the last one)
--
-- Scenario: A travel agent books three passengers on Flight 2.
--           After booking the third, they realise the third
--           passenger's details were wrong. We rollback to the
--           savepoint AFTER the second booking, keeping the
--           first two bookings intact.
-- ================================================================

START TRANSACTION;

    -- Booking A
    INSERT INTO Booking (booking_date, seat_number, fare, passenger_id, flight_id)
    VALUES (CURDATE(), '18A', 5800.00, 13, 2);
    SAVEPOINT after_booking_a;

    -- Booking B
    INSERT INTO Booking (booking_date, seat_number, fare, passenger_id, flight_id)
    VALUES (CURDATE(), '18B', 5800.00, 14, 2);
    SAVEPOINT after_booking_b;

    -- Booking C (will be undone)
    INSERT INTO Booking (booking_date, seat_number, fare, passenger_id, flight_id)
    VALUES (CURDATE(), '19A', 5800.00, 15, 2);

    -- Agent realises passenger 15's details are wrong — undo Booking C only
    ROLLBACK TO SAVEPOINT after_booking_b;

COMMIT;
-- Bookings A and B are saved; Booking C is discarded.

SELECT '--- Transaction 4 committed: Two bookings saved, third rolled back to savepoint ---' AS Result;


-- ================================================================
-- TRANSACTION 5: Batch flight status update with SAVEPOINT
-- (Update a set of flights; undo selective updates)
--
-- Scenario: An operations team marks several flights as
--           "Boarding". Midway they discover Flight 4 should
--           NOT be updated yet — rollback only that change.
-- ================================================================

START TRANSACTION;

    UPDATE Flight SET flight_status = 'Boarding'
    WHERE flight_id = 3;
    SAVEPOINT after_flight_3;

    UPDATE Flight SET flight_status = 'Boarding'
    WHERE flight_id = 4;
    SAVEPOINT after_flight_4;

    -- Oops — Flight 4 gate hasn't opened yet; undo only Flight 4
    ROLLBACK TO SAVEPOINT after_flight_3;

    UPDATE Flight SET flight_status = 'Boarding'
    WHERE flight_id = 7;

COMMIT;
-- Flight 3 and 7 are now "Boarding"; Flight 4 remains unchanged.

SELECT '--- Transaction 5 committed: Selective flight status updates ---' AS Result;


-- ================================================================
-- TRANSACTION 6: Cancel all bookings for a flight
-- (Cascading delete with audit — all-or-nothing)
--
-- Scenario: Flight 9 is cancelled. All its bookings and related
--           baggage must be removed. The AFTER DELETE trigger on
--           Booking logs each cancellation automatically.
-- ================================================================

START TRANSACTION;

    -- Step 1: Cancel the flight
    UPDATE Flight SET flight_status = 'Cancelled'
    WHERE flight_id = 9;

    -- Step 2: Remove baggage for all bookings on Flight 9
    DELETE FROM Baggage
    WHERE booking_id IN (
        SELECT booking_id FROM Booking WHERE flight_id = 9
    );

    -- Step 3: Remove all bookings for Flight 9
    -- (trg_booking_after_delete logs each deletion automatically)
    DELETE FROM Booking
    WHERE flight_id = 9;

COMMIT;

SELECT '--- Transaction 6 committed: Flight 9 cancelled, all bookings removed ---' AS Result;


-- ================================================================
-- TRANSACTION 7: Add a new airline with aircraft and a flight
-- (Multi-table setup — complete or nothing)
--
-- Scenario: Onboard a brand-new airline into the system:
--           create the airline record, register its aircraft,
--           and schedule the first flight. Uses SAVEPOINTs so
--           the airline+aircraft persist even if the flight
--           schedule fails.
-- ================================================================

START TRANSACTION;

    -- Step 1: Add new airline
    INSERT INTO Airline (code, airline_name)
    VALUES ('QR', 'Qatar Airways');
    SET @new_airline = LAST_INSERT_ID();
    SAVEPOINT after_airline;

    -- Step 2: Register aircraft for the airline
    INSERT INTO Aircraft (registration_no, model, capacity, airline_id)
    VALUES ('A7-BCA', 'Boeing 787-8', 254, @new_airline);
    SAVEPOINT after_aircraft;

    -- Step 3: Schedule the first flight (BOM → DXB)
    INSERT INTO Flight (departure_time, arrival_time, flight_status,
                        airline_id, aircraft_id, departure_airport_id, arrival_airport_id)
    VALUES ('2026-11-01 10:00:00', '2026-11-01 12:30:00', 'Scheduled',
            @new_airline, LAST_INSERT_ID(), 1, 7);

COMMIT;

SELECT '--- Transaction 7 committed: New airline + aircraft + flight added ---' AS Result;


-- ================================================================
-- TRANSACTION 8: ROLLBACK an entire fare-update batch
-- (Demonstrate full rollback without savepoints)
--
-- Scenario: Finance decides to increase fares by 10% on all
--           bookings for Flight 5, but then management vetoes
--           the change before COMMIT. The whole batch is undone.
-- ================================================================

START TRANSACTION;

    -- Increase fares by 10%
    UPDATE Booking
    SET fare = fare * 1.10
    WHERE flight_id = 5;

    -- Management says NO — rollback everything
ROLLBACK;

SELECT '--- Transaction 8 rolled back: Fare increase reverted ---' AS Result;

-- Verify fares are unchanged
SELECT booking_id, seat_number, fare
FROM Booking
WHERE flight_id = 5;


-- ================================================================
-- TRANSACTION 9: Passenger update with validation (SAVEPOINT)
--
-- Scenario: Update contact details for two passengers.
--           The second update has an invalid email that the
--           trigger rejects. Use SAVEPOINT so the first
--           update still goes through.
-- ================================================================

START TRANSACTION;

    -- Update Passenger 3 — valid
    UPDATE Passenger
    SET phone = '9000000003', email = 'arjun.new@email.com'
    WHERE passenger_id = 3;
    SAVEPOINT after_passenger_3;

    -- Update Passenger 4 — the email is valid, proceed normally
    UPDATE Passenger
    SET phone = '9000000004', email = 'isha.new@email.com'
    WHERE passenger_id = 4;

COMMIT;

SELECT '--- Transaction 9 committed: Passenger details updated ---' AS Result;


-- ================================================================
-- TRANSACTION 10: Nested SAVEPOINTs — Add baggage in stages
--
-- Scenario: A passenger adds baggage piece-by-piece during
--           check-in. After adding the third piece they
--           decide it's too heavy and remove it, keeping the
--           first two.
-- ================================================================

START TRANSACTION;

    -- Bag 1
    INSERT INTO Baggage (booking_id, baggage_no, baggage_weight)
    VALUES (5, 2, 12.00);
    SAVEPOINT bag_1;

    -- Bag 2
    INSERT INTO Baggage (booking_id, baggage_no, baggage_weight)
    VALUES (5, 3, 8.50);
    SAVEPOINT bag_2;

    -- Bag 3 (passenger changes their mind)
    INSERT INTO Baggage (booking_id, baggage_no, baggage_weight)
    VALUES (5, 4, 22.00);

    -- Remove Bag 3 only
    ROLLBACK TO SAVEPOINT bag_2;

COMMIT;

SELECT '--- Transaction 10 committed: Two bags kept, third removed ---' AS Result;

-- Verify final baggage for booking 5
SELECT * FROM Baggage WHERE booking_id = 5;
