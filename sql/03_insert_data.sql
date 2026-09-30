USE FlightManagement;


INSERT INTO Airline (code, airline_name)
VALUES
('AI', 'Air India'),
('6E', 'IndiGo'),
('UK', 'Vistara'),
('EK', 'Emirates'),
('SQ', 'Singapore Airlines');


INSERT INTO Aircraft
(registration_no, model, capacity, airline_id)
VALUES
('VT-ANR', 'Airbus A320', 180, 1),
('VT-ANL', 'Boeing 737-800', 189, 2),
('VT-TQD', 'Airbus A321', 220, 2),
('VT-TAB', 'Airbus A320neo', 186, 3),
('A6-EQA', 'Boeing 777-300ER', 354, 4),
('9V-SKA', 'Airbus A350-900', 253, 5),
('VT-AXX', 'Boeing 787-9', 256, 1);


INSERT INTO Airport
(airport_code, airport_name, city)
VALUES
('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai'),
('DEL', 'Indira Gandhi International Airport', 'Delhi'),
('BLR', 'Kempegowda International Airport', 'Bengaluru'),
('MAA', 'Chennai International Airport', 'Chennai'),
('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad'),
('GOI', 'Manohar International Airport', 'Goa'),
('DXB', 'Dubai International Airport', 'Dubai'),
('SIN', 'Singapore Changi Airport', 'Singapore'),
('CCU', 'Netaji Subhas Chandra Bose International Airport', 'Kolkata'),
('PNQ', 'Pune Airport', 'Pune');


INSERT INTO Passenger
(passenger_name, dob, phone, email, passport_no)
VALUES
('Rahul Sharma', '2002-04-15', '9876543210', 'rahul.sharma@email.com', 'P100001'),
('Ananya Mehta', '2001-08-22', '9876543211', 'ananya.mehta@email.com', 'P100002'),
('Arjun Patel', '1999-11-10', '9876543212', 'arjun.patel@email.com', 'P100003'),
('Isha Shah', '2003-01-05', '9876543213', 'isha.shah@email.com', 'P100004'),
('Rohan Desai', '2000-06-18', '9876543214', 'rohan.desai@email.com', 'P100005'),
('Priya Nair', '1998-09-27', '9876543215', 'priya.nair@email.com', 'P100006'),
('Aditya Joshi', '2002-12-14', '9876543216', 'aditya.joshi@email.com', 'P100007'),
('Sneha Kapoor', '2001-03-30', '9876543217', 'sneha.kapoor@email.com', 'P100008'),
('Karan Malhotra', '1997-07-21', '9876543218', 'karan.malhotra@email.com', 'P100009'),
('Neha Verma', '2004-02-11', '9876543219', 'neha.verma@email.com', 'P100010'),
('Vikram Singh', '1996-05-09', '9876543220', 'vikram.singh@email.com', 'P100011'),
('Aarav Shah', '2003-10-17', '9876543221', 'aarav.shah@email.com', 'P100012'),
('Meera Iyer', '2000-01-25', '9876543222', 'meera.iyer@email.com', 'P100013'),
('Kabir Khan', '1999-04-08', '9876543223', 'kabir.khan@email.com', 'P100014'),
('Tanya Roy', '2002-09-13', '9876543224', 'tanya.roy@email.com', 'P100015');


INSERT INTO Flight
(departure_time, arrival_time, flight_status,
 airline_id, aircraft_id, departure_airport_id, arrival_airport_id)
VALUES
('2026-10-05 08:00:00', '2026-10-05 10:15:00',
 'Scheduled', 1, 1, 1, 2),

('2026-10-05 11:30:00', '2026-10-05 13:20:00',
 'Scheduled', 2, 2, 2, 3),

('2026-10-06 09:00:00', '2026-10-06 11:00:00',
 'Scheduled', 2, 3, 1, 4),

('2026-10-06 14:00:00', '2026-10-06 15:15:00',
 'Scheduled', 3, 4, 1, 6),

('2026-10-07 20:00:00', '2026-10-07 22:45:00',
 'Scheduled', 4, 5, 1, 7),

('2026-10-08 22:00:00', '2026-10-09 05:30:00',
 'Scheduled', 5, 6, 1, 8),

('2026-10-09 07:30:00', '2026-10-09 09:30:00',
 'Scheduled', 1, 7, 3, 5),

('2026-10-10 16:00:00', '2026-10-10 18:00:00',
 'Scheduled', 2, 2, 4, 1),

('2026-10-11 10:00:00', '2026-10-11 12:00:00',
 'Scheduled', 3, 4, 6, 1),

('2026-10-12 18:30:00', '2026-10-12 20:45:00',
 'Scheduled', 1, 1, 2, 1),

('2026-10-13 09:00:00', '2026-10-13 11:10:00',
 'Scheduled', 2, 3, 3, 2),

('2026-10-14 21:00:00', '2026-10-15 00:15:00',
 'Scheduled', 4, 5, 7, 1);


INSERT INTO Booking
(booking_date, seat_number, fare, passenger_id, flight_id)
VALUES
('2026-09-20', '12A', 6500.00, 1, 1),
('2026-09-21', '12B', 6500.00, 2, 1),
('2026-09-22', '14A', 7200.00, 3, 1),

('2026-09-20', '10A', 5500.00, 4, 2),
('2026-09-23', '10B', 5500.00, 5, 2),
('2026-09-24', '11A', 6000.00, 6, 2),

('2026-09-25', '15A', 7000.00, 7, 3),
('2026-09-25', '15B', 7000.00, 8, 3),

('2026-09-26', '5A', 4500.00, 9, 4),
('2026-09-26', '5B', 4500.00, 10, 4),
('2026-09-27', '6A', 4800.00, 11, 4),

('2026-09-27', '20A', 18000.00, 12, 5),
('2026-09-28', '20B', 18000.00, 13, 5),
('2026-09-28', '21A', 19500.00, 14, 5),

('2026-09-28', '30A', 32000.00, 15, 6),

('2026-09-28', '8A', 8000.00, 1, 7),
('2026-09-28', '8B', 8000.00, 2, 7),

('2026-09-29', '16A', 6000.00, 3, 8),
('2026-09-29', '16B', 6000.00, 4, 8),
('2026-09-29', '17A', 6200.00, 5, 8),

('2026-09-29', '7A', 5000.00, 6, 9),
('2026-09-29', '7B', 5000.00, 7, 9),

('2026-09-29', '18A', 7500.00, 8, 10),
('2026-09-29', '18B', 7500.00, 9, 10),
('2026-09-29', '19A', 8000.00, 10, 10),

('2026-09-29', '11A', 6800.00, 11, 11),
('2026-09-29', '11B', 6800.00, 12, 11),

('2026-09-29', '22A', 19000.00, 13, 12),
('2026-09-29', '22B', 19000.00, 14, 12);


INSERT INTO Baggage
(booking_id, baggage_no, baggage_weight)
VALUES
(1, 1, 18.50),
(1, 2, 7.20),

(2, 1, 15.00),

(3, 1, 20.50),

(4, 1, 12.00),
(4, 2, 8.50),

(5, 1, 17.00),

(7, 1, 22.00),

(9, 1, 14.50),

(10, 1, 19.00),
(10, 2, 6.50),

(12, 1, 25.00),

(13, 1, 18.00),

(15, 1, 20.00),

(16, 1, 13.50),

(18, 1, 16.00),

(20, 1, 21.50),

(22, 1, 15.50),

(25, 1, 18.00),

(28, 1, 24.00);