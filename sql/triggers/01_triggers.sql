
-- ================================================
-- Trigger coverage (every timing + event combination):
--   BEFORE INSERT : trg_flight_before_insert, trg_booking_before_insert,
--                   trg_baggage_before_insert, trg_passenger_before_insert
--   AFTER  INSERT : trg_booking_after_insert
--   BEFORE UPDATE : trg_flight_before_update
--   AFTER  UPDATE : trg_flight_after_update
--   BEFORE DELETE : trg_flight_before_delete
--   AFTER  DELETE : trg_booking_after_delete
-- ================================================


USE flight_management_db;

-- ---------------------------------------------------------------------
-- Audit tables (used by the AFTER triggers)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS flight_status_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE IF NOT EXISTS booking_cancellation_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    flight_id INT NOT NULL,
    passenger_id INT NOT NULL,
    seat_no VARCHAR(10) NOT NULL,
    fare DECIMAL(10, 2) NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE IF NOT EXISTS booking_creation_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    flight_id INT NOT NULL,
    passenger_id INT NOT NULL,
    seat_no VARCHAR(10) NOT NULL,
    fare DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

DELIMITER $$

-- ================================================
-- TRIGGER 1: trg_flight_before_insert  
-- RULE: Before inserting a new flight, ensure that the flight number 
--       is unique and the departure time is in the future.
-- ===============================================
DROP TRIGGER IF EXISTS trg_flight_before_insert$$
CREATE TRIGGER trg_flight_before_insert
BEFORE INSERT ON flights
FOR EACH ROW
BEGIN
    DECLARE v_aircraft_airline INT;
    DECLARE v_overlap INT;

    IF NEW.arrival_time <= NEW.departure_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Arrival time must be after departure time.';
        END IF;

    IF NEW.departure_airport_id = NEW.arrival_airport_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Departure and arrival airports cannot be the same.';
    END IF;

    SELECT airline_id INTO v_aircraft_airline
    FROM aircraft
    WHERE aircraft_id = NEW.aircraft_id;
    
    IF v_aircraft_airline <> NEW.airline_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Aircraft does not belong to the specified airline.';
    END IF;

    SELECT COUNT(*) INTO v_overlap
    FROM flight
    WHERE aircraft_id = NEW.aircraft_id
      AND status <> 'Cancelled'
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
BEFORE UPDATE ON flight
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

-- -- ================================================
-- TRIGGER 3: trg_booking_before_insert
-- RULE: flight not cancelled, fare > 0, no duplicate passenger on a
--       flight, no duplicate seat, no overbooking beyond aircraft capacity
-- =====================================================================
DROP TRIGGER IF EXISTS trg_booking_before_insert$$
CREATE TRIGGER trg_booking_before_insert
BEFORE INSERT ON booking
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_capacity INT;
    DECLARE v_booked INT;
    DECLARE v_duplicate_passenger INT;
    DECLARE v_seat_used INT;

    SELECT f.status, a.capacity
      INTO v_status, v_capacity
    FROM flight f
    JOIN aircraft a ON a.aircraft_id = f.aircraft_id
    WHERE f.flight_id = NEW.flight_id;
 
    IF v_status = 'Cancelled' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot book a cancelled flight';
    END IF;
 
    IF NEW.fare IS NULL OR NEW.fare <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Fare must be greater than zero';
    END IF;
 
    SELECT COUNT(*) INTO v_dup_pax
    FROM booking
    WHERE flight_id = NEW.flight_id
      AND passenger_id = NEW.passenger_id;
 
    IF v_dup_pax > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Passenger already has a booking on this flight';
    END IF;
 
    IF NEW.seat_no IS NOT NULL THEN
        SELECT COUNT(*) INTO v_seat_used
        FROM booking
        WHERE flight_id = NEW.flight_id
          AND seat_no = NEW.seat_no;
 
        IF v_seat_used > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Seat is already taken on this flight';
        END IF;
    END IF;
 
    SELECT COUNT(*) INTO v_booked
    FROM booking
    WHERE flight_id = NEW.flight_id;
 
    IF v_booked >= v_capacity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Flight is fully booked (aircraft capacity reached)';
    END IF;
END$$