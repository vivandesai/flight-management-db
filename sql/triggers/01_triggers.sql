
-- ================================================
-- Trigger coverage:
--   BEFORE INSERT : flight, booking, baggage, passenger
--   AFTER  INSERT : booking
--   BEFORE UPDATE : flight validation, flight status lock
--   AFTER  UPDATE : flight status audit
--   BEFORE DELETE : flight, airline
--   AFTER  DELETE : booking cancellation audit
-- ================================================


USE FlightManagement;

-- ---------------------------------------------------------------------
-- Audit tables (used by the AFTER triggers)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS flight_status_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booking_cancellation_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    flight_id INT NOT NULL,
    passenger_id INT NOT NULL,
    seat_no VARCHAR(10) NOT NULL,
    fare DECIMAL(10, 2) NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booking_creation_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    flight_id INT NOT NULL,
    passenger_id INT NOT NULL,
    seat_no VARCHAR(10) NOT NULL,
    fare DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DELIMITER $$

-- ================================================
-- TRIGGER 1: trg_flight_before_insert
-- RULE: validate flight times, airports, departure time, aircraft airline,
--       and aircraft scheduling conflicts.
-- ===============================================
DROP TRIGGER IF EXISTS trg_flight_before_insert$$
CREATE TRIGGER trg_flight_before_insert
BEFORE INSERT ON Flight
FOR EACH ROW
BEGIN
    DECLARE v_aircraft_airline INT;
    DECLARE v_overlap INT;

    IF NEW.departure_time <= CURRENT_TIMESTAMP THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Departure time must be in the future.';
    END IF;

    IF NEW.arrival_time <= NEW.departure_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Arrival time must be after departure time.';
        END IF;

    IF NEW.departure_airport_id = NEW.arrival_airport_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Departure and arrival airports cannot be the same.';
    END IF;

    SELECT airline_id INTO v_aircraft_airline
    FROM Aircraft
    WHERE aircraft_id = NEW.aircraft_id;
    
    IF v_aircraft_airline <> NEW.airline_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aircraft does not belong to the specified airline.';
    END IF;

    SELECT COUNT(*) INTO v_overlap
    FROM Flight
    WHERE aircraft_id = NEW.aircraft_id
    AND flight_status <> 'Cancelled'
      AND NEW.departure_time < arrival_time
      AND NEW.arrival_time > departure_time;

    IF v_overlap > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aircraft is already scheduled for another flight during this time.';
    END IF;
END$$

-- ================================================
-- TRIGGER 2: trg_flight_before_update
-- RULE: keep time and airport validation on update
-- ================================================
DROP TRIGGER IF EXISTS trg_flight_before_update$$
CREATE TRIGGER trg_flight_before_update
BEFORE UPDATE ON Flight
FOR EACH ROW
BEGIN
    IF NEW.arrival_time <= NEW.departure_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Arrival time must be after departure time.';
    END IF;

    IF NEW.departure_airport_id = NEW.arrival_airport_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Departure and arrival airports cannot be the same.';
    END IF;
END$$

-- ================================================
-- TRIGGER 3: trg_booking_before_insert
-- RULE: flight not cancelled, fare > 0, no duplicate passenger on a
--       flight, no duplicate seat, no overbooking beyond aircraft capacity
-- =====================================================================
DROP TRIGGER IF EXISTS trg_booking_before_insert$$
CREATE TRIGGER trg_booking_before_insert
BEFORE INSERT ON Booking
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_capacity INT;
    DECLARE v_booked INT;
    DECLARE v_duplicate_passenger INT;
    DECLARE v_seat_used INT;

        SELECT f.flight_status, a.capacity
      INTO v_status, v_capacity
        FROM Flight f
        JOIN Aircraft a ON a.aircraft_id = f.aircraft_id
    WHERE f.flight_id = NEW.flight_id;
 
    IF v_status = 'Cancelled' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot book a cancelled flight';
    END IF;
 
    IF NEW.fare IS NULL OR NEW.fare <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Fare must be greater than zero';
    END IF;
 
    SELECT COUNT(*) INTO v_duplicate_passenger
    FROM Booking
    WHERE flight_id = NEW.flight_id
      AND passenger_id = NEW.passenger_id;
 
    IF v_duplicate_passenger > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Passenger already has a Booking on this flight';
    END IF;
 
        SELECT COUNT(*) INTO v_seat_used
        FROM Booking
        WHERE flight_id = NEW.flight_id
            AND seat_number = NEW.seat_number;
 
        IF v_seat_used > 0 THEN
                SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Seat is already taken on this flight';
    END IF;
 
    SELECT COUNT(*) INTO v_booked
    FROM Booking
    WHERE flight_id = NEW.flight_id;
 
    IF v_booked >= v_capacity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Flight is fully booked (aircraft capacity reached)';
    END IF;
END$$

-- =================================================
-- TRIGGER 4: trg_baggage_before_insert
-- RULE: a single bag must weigh between 0 and 50kg
-- =================================================
DROP TRIGGER IF EXISTS trg_baggage_before_insert$$
CREATE TRIGGER trg_baggage_before_insert
BEFORE INSERT ON Baggage
FOR EACH ROW
BEGIN
    IF NEW.baggage_weight <= 0 OR NEW.baggage_weight > 50 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Baggage weight must be between 0 and 50 kg';
    END IF;
END$$

-- =======================================================================
-- TRIGGER 5: trg_passenger_before_insert
-- RULE: date of birth should be in the past, and basic email format check
-- =======================================================================
DROP TRIGGER IF EXISTS trg_passenger_before_insert$$
CREATE TRIGGER trg_passenger_before_insert
BEFORE INSERT ON Passenger
FOR EACH ROW
BEGIN
    IF NEW.dob >= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Date of birth must be in the past';
        END IF;

    IF NEW.email IS NOT NULL AND NEW.email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid email format';
    END IF;
END$$

-- =====================================================
-- TRIGGER 6: trg_flight_after_update
-- RULE: log flight status changes to flight_status_log
-- =====================================================
DROP TRIGGER IF EXISTS trg_flight_after_update$$
CREATE TRIGGER trg_flight_after_update
AFTER UPDATE ON Flight
FOR EACH ROW
BEGIN
    IF NOT (OLD.flight_status <=> NEW.flight_status) THEN
        INSERT INTO flight_status_log (flight_id, old_status, new_status)
        VALUES (OLD.flight_id, OLD.flight_status, NEW.flight_status);
    END IF;
END$$

-- =====================================================================
-- TRIGGER 7: trg_booking_after_delete
-- RULE: log booking cancellations to booking_cancellation_log
-- =====================================================================
DROP TRIGGER IF EXISTS trg_booking_after_delete$$
CREATE TRIGGER trg_booking_after_delete
AFTER DELETE ON Booking
FOR EACH ROW
BEGIN
    INSERT INTO booking_cancellation_log (booking_id, flight_id, passenger_id, seat_no, fare)
    VALUES (OLD.booking_id, OLD.flight_id, OLD.passenger_id, OLD.seat_number, OLD.fare);
END$$

-- =====================================================================
-- TRIGGER 8: trg_booking_after_insert
-- RULE: log booking creations to booking_creation_log
-- =====================================================================
DROP TRIGGER IF EXISTS trg_booking_after_insert$$
CREATE TRIGGER trg_booking_after_insert
AFTER INSERT ON Booking
FOR EACH ROW 
BEGIN
    INSERT INTO booking_creation_log (booking_id, flight_id, passenger_id, seat_no, fare)
    VALUES (NEW.booking_id, NEW.flight_id, NEW.passenger_id, NEW.seat_number, NEW.fare);
END$$

-- =====================================================================
-- TRIGGER 9: trg_flight_before_delete
-- RULE: a flight cannot be deleted if it has any bookings
-- =====================================================================
DROP TRIGGER IF EXISTS trg_flight_before_delete$$
CREATE TRIGGER trg_flight_before_delete
BEFORE DELETE ON Flight
FOR EACH ROW
BEGIN
    DECLARE v_bookings INT;

    SELECT COUNT(*) INTO v_bookings
    FROM Booking
    WHERE flight_id = OLD.flight_id;

    IF v_bookings > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot delete flight with existing bookings';
    END IF;
END$$

-- =====================================================================
-- TRIGGER 10: trg_airline_before_delete
-- RULE: an airline that services any flights cannot be deleted
-- =====================================================================
DROP TRIGGER IF EXISTS trg_airline_before_delete$$
CREATE TRIGGER trg_airline_before_delete
BEFORE DELETE ON airline
FOR EACH ROW
BEGIN
    DECLARE v_flights INT;

    SELECT COUNT(*) INTO v_flights
    FROM Flight
    WHERE airline_id = OLD.airline_id;

    IF v_flights > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot delete airline that services existing flights';
    END IF;
END$$

-- ===========================================================================
-- TRIGGER 11: trg_flight_status_lock
-- RULE: if a flight has arrived its status cannot be changed to anything else
-- ===========================================================================
DROP TRIGGER IF EXISTS trg_flight_status_lock$$
CREATE TRIGGER trg_flight_status_lock
BEFORE UPDATE ON Flight
FOR EACH ROW
BEGIN
    IF OLD.flight_status = 'Arrived' AND NEW.flight_status <> 'Arrived' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot change status of a flight that has already arrived';
    END IF;
END$$

-- =========================================================================
-- TRIGGER 12: trg_baggage_total_limit
-- RULE: total baggage weight for a passenger on a flight cannot exceed 80kg
-- =========================================================================
DROP TRIGGER IF EXISTS trg_baggage_total_limit$$
CREATE TRIGGER trg_baggage_total_limit
BEFORE INSERT ON Baggage
FOR EACH ROW
BEGIN
    DECLARE v_total_weight DECIMAL(10,2);

    SELECT COALESCE(SUM(baggage_weight), 0) INTO v_total_weight
    FROM Baggage
    WHERE booking_id = NEW.booking_id;

    IF v_total_weight + NEW.baggage_weight > 80 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Total baggage weight for this booking cannot exceed 80kg';
    END IF;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- Verify triggers were created
-- ---------------------------------------------------------------------
SHOW TRIGGERS;