# Flight Management System – Relational Schema

## 1. AIRLINE

**AIRLINE**(
**airline_id**,
code,
airline_name
)

- Primary Key: `airline_id`
- `code` is unique

---

## 2. AIRCRAFT

**AIRCRAFT**(
**aircraft_id**,
registration_no,
model,
capacity,
airline_id
)

- Primary Key: `aircraft_id`
- Foreign Key: `airline_id` → `AIRLINE(airline_id)`
- `registration_no` is unique

---

## 3. AIRPORT

**AIRPORT**(
**airport_id**,
airport_code,
airport_name,
city
)

- Primary Key: `airport_id`
- `airport_code` is unique

---

## 4. PASSENGER

**PASSENGER**(
**passenger_id**,
passenger_name,
dob,
phone,
email,
passport_no
)

- Primary Key: `passenger_id`
- `passport_no` is unique

---

## 5. FLIGHT

**FLIGHT**(
**flight_id**,
departure_time,
arrival_time,
status,
airline_id,
aircraft_id,
departure_airport_id,
arrival_airport_id
)

- Primary Key: `flight_id`
- Foreign Key: `airline_id` → `AIRLINE(airline_id)`
- Foreign Key: `aircraft_id` → `AIRCRAFT(aircraft_id)`
- Foreign Key: `departure_airport_id` → `AIRPORT(airport_id)`
- Foreign Key: `arrival_airport_id` → `AIRPORT(airport_id)`

---

## 6. BOOKING

**BOOKING**(
**booking_id**,
booking_date,
seat_number,
fare,
passenger_id,
flight_id
)

- Primary Key: `booking_id`
- Foreign Key: `passenger_id` → `PASSENGER(passenger_id)`
- Foreign Key: `flight_id` → `FLIGHT(flight_id)`
- Composite unique constraint: (`flight_id`, `seat_number`)

---

## 7. BAGGAGE

**BAGGAGE**(
**booking_id**,
**baggage_no**,
weight
)

- Composite Primary Key: (`booking_id`, `baggage_no`)
- Foreign Key: `booking_id` → `BOOKING(booking_id)`
- `baggage_no` is the partial key of the weak entity `BAGGAGE`

---

## Summary of Relationships

| Relationship | Cardinality |
|---|---|
| AIRLINE — AIRCRAFT | 1 : N |
| AIRLINE — FLIGHT | 1 : N |
| AIRCRAFT — FLIGHT | 1 : N |
| FLIGHT — DEPARTURE AIRPORT | N : 1 |
| FLIGHT — ARRIVAL AIRPORT | N : 1 |
| PASSENGER — BOOKING | 1 : N |
| FLIGHT — BOOKING | 1 : N |
| BOOKING — BAGGAGE | 1 : N |

## Foreign Key Mapping

| Table | Foreign Key | References |
|---|---|---|
| AIRCRAFT | `airline_id` | `AIRLINE(airline_id)` |
| FLIGHT | `airline_id` | `AIRLINE(airline_id)` |
| FLIGHT | `aircraft_id` | `AIRCRAFT(aircraft_id)` |
| FLIGHT | `departure_airport_id` | `AIRPORT(airport_id)` |
| FLIGHT | `arrival_airport_id` | `AIRPORT(airport_id)` |
| BOOKING | `passenger_id` | `PASSENGER(passenger_id)` |
| BOOKING | `flight_id` | `FLIGHT(flight_id)` |
| BAGGAGE | `booking_id` | `BOOKING(booking_id)` |