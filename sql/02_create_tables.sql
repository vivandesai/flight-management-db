USE FlightManagement;

CREATE TABLE Airline (
    airline_id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(10) NOT NULL UNIQUE,
    airline_name VARCHAR(100) NOT NULL
);


CREATE TABLE Aircraft (
    aircraft_id INT PRIMARY KEY AUTO_INCREMENT,
    registration_no VARCHAR(20) NOT NULL UNIQUE,
    model VARCHAR(50) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    airline_id INT NOT NULL,

    FOREIGN KEY (airline_id)
        REFERENCES Airline(airline_id)
);


CREATE TABLE Airport (
    airport_id INT PRIMARY KEY AUTO_INCREMENT,
    airport_code VARCHAR(10) NOT NULL UNIQUE,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL
);


CREATE TABLE Passenger (
    passenger_id INT PRIMARY KEY AUTO_INCREMENT,
    passenger_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    passport_no VARCHAR(20) NOT NULL UNIQUE
);


CREATE TABLE Flight (
    flight_id INT PRIMARY KEY AUTO_INCREMENT,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    flight_status VARCHAR(30) NOT NULL,

    airline_id INT NOT NULL,
    aircraft_id INT NOT NULL,
    departure_airport_id INT NOT NULL,
    arrival_airport_id INT NOT NULL,

    FOREIGN KEY (airline_id)
        REFERENCES Airline(airline_id),

    FOREIGN KEY (aircraft_id)
        REFERENCES Aircraft(aircraft_id),

    FOREIGN KEY (departure_airport_id)
        REFERENCES Airport(airport_id),

    FOREIGN KEY (arrival_airport_id)
        REFERENCES Airport(airport_id),

    CHECK (arrival_time > departure_time),

    CHECK (departure_airport_id <> arrival_airport_id)
);


CREATE TABLE Booking (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    booking_date DATE NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    fare DECIMAL(10,2) NOT NULL CHECK (fare >= 0),

    passenger_id INT NOT NULL,
    flight_id INT NOT NULL,

    FOREIGN KEY (passenger_id)
        REFERENCES Passenger(passenger_id),

    FOREIGN KEY (flight_id)
        REFERENCES Flight(flight_id),

    UNIQUE (flight_id, seat_number)
);


CREATE TABLE Baggage (
    booking_id INT NOT NULL,
    baggage_no INT NOT NULL CHECK (baggage_no > 0),
    baggage_weight DECIMAL(5,2) NOT NULL CHECK (baggage_weight > 0),

    PRIMARY KEY (booking_id, baggage_no),

    FOREIGN KEY (booking_id)
        REFERENCES Booking(booking_id)
);