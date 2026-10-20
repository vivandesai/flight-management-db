from datetime import datetime, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import re

import mysql.connector
import pytest

from airline.catalogue import ROOT
from airline.db import connect, install_views, query
from airline.dba import ENTITIES, STATEMENTS, dependencies, form_values, get_record, mutate, row_token
from airline.demos import snapshot
from airline.view_catalogue import VIEWS, select_views


def test_new_sql_catalogues():
    assert len(VIEWS) == 7
    assert len(STATEMENTS) == 54
    for name, spec in STATEMENTS.items():
        source = (ROOT / spec['source']).read_text()
        assert spec['sql'] in source
        assert source.splitlines()[spec['line']-1].strip() == spec['sql'].splitlines()[0]
    for view in VIEWS.values():
        assert 'SQL SECURITY INVOKER' in view['sql']
        assert (ROOT / view['source']).read_text().splitlines()[view['line']-1].startswith('CREATE OR REPLACE')


def test_view_category_and_search_catalogue():
    expected = {'Flights': ['vw_flight_operations','vw_flight_occupancy'],
                'Revenue': ['vw_airline_performance'], 'Passengers': ['vw_passenger_activity'],
                'Bookings': ['vw_booking_manifest'], 'Baggage': ['vw_booking_baggage'],
                'Fleet & airports': ['vw_airport_traffic']}
    for category, names in expected.items():
        assert [v['name'] for v in select_views(category)] == names
    assert [v['name'] for v in select_views(search='V7')] == ['vw_airport_traffic']
    assert [v['name'] for v in select_views(search='vw_booking_manifest')] == ['vw_booking_manifest']
    assert len(select_views(search='SQL view')) == 7
    assert not select_views('Revenue','occupancy')


def edit(conn, name, key, **changes):
    spec = ENTITIES[name]
    old = get_record(conn, spec, key)
    values = {**form_values(old), **{k: str(v) for k,v in changes.items()}}
    mutate(conn, spec, key, 'update', row_token(spec, old, 'update'), values)
    return old, get_record(conn, spec, key)


@pytest.mark.integration
@pytest.mark.parametrize('name,key,changes', [
    ('Airline','1',dict(code='DBA',airline_name='Updated airline')),
    ('Aircraft','1',dict(registration_no='DBA-REG',model='Updated model',capacity='200')),
    ('Airport','1',dict(airport_code='DBA',airport_name='Updated airport',city='Updated city')),
    ('Passenger','1',dict(passenger_name='Updated passenger',dob='2001-02-03',phone='',email='updated@example.com',passport_no='DBAPASS')),
    ('Flight','1',dict(flight_status='Delayed')),
    ('Booking','1',dict(seat_number='99Z',fare='12345.67')),
    ('Baggage','1-1',dict(baggage_weight='19.50')),
])
def test_edits_persist_and_preserve_relationships(database, name, key, changes):
    before,after = edit(database,name,key,**changes)
    editable = {f['name'] for f in ENTITIES[name].fields}
    assert {k:v for k,v in before.items() if k not in editable} == {k:v for k,v in after.items() if k not in editable}
    assert before != after
    other = connect()
    try:
        assert get_record(other,ENTITIES[name],key) == after
    finally:
        other.close()
    if name == 'Flight':
        assert query(database,"SELECT * FROM flight_status_log WHERE flight_id=1")[-1]['new_status'] == 'Delayed'


@pytest.mark.integration
@pytest.mark.parametrize('name,key,changes,message', [
    ('Airline','1',dict(code='6E'),'Duplicate'),
    ('Airport','1',dict(airport_code='DEL'),'Duplicate'),
    ('Passenger','1',dict(passport_no='P100002'),'Duplicate'),
    ('Passenger','1',dict(email='invalid-email'),'Invalid email'),
    ('Passenger','1',dict(dob='2999-01-01'),'birth'),
    ('Booking','1',dict(fare='0'),'greater than zero'),
    ('Booking','1',dict(fare='NaN'),'invalid'),
    ('Booking','1',dict(fare='1.234'),'invalid'),
    ('Booking','1',dict(seat_number='12B'),'Duplicate'),
    ('Aircraft','1',dict(capacity='2'),'booked seat'),
    ('Aircraft','1',dict(capacity='0'),'invalid'),
    ('Baggage','1-1',dict(baggage_weight='51'),'50 kg'),
    ('Baggage','1-1',dict(baggage_weight='0'),'50 kg'),
])
def test_invalid_updates_rollback(database,name,key,changes,message):
    before = snapshot(database)
    with pytest.raises((ValueError,mysql.connector.Error),match=message):
        edit(database,name,key,**changes)
    assert snapshot(database) == before


@pytest.mark.integration
def test_baggage_total_and_composite_key(database):
    query(database,'DELETE FROM Baggage WHERE booking_id=1')
    query(database,'INSERT INTO Baggage VALUES (1,1,40),(1,2,40)')
    before = snapshot(database)
    with pytest.raises(ValueError,match='80kg'):
        edit(database,'Baggage','1-2',baggage_weight='41')
    assert snapshot(database) == before
    edit(database,'Baggage','1-2',baggage_weight='35')
    assert get_record(database,ENTITIES['Baggage'],'1-1')['baggage_weight'] == 40
    assert query(database,'SELECT total_baggage_weight FROM vw_booking_baggage WHERE booking_id=1')[0]['total_baggage_weight'] == 75


@pytest.mark.integration
def test_stale_tampered_cross_record_and_delete_tokens(database):
    spec = ENTITIES['Airline']
    old = get_record(database,spec,'1')
    token = row_token(spec,old,'update')
    edit(database,'Airline','1',airline_name='Concurrent update')
    for value in (token,'tampered'):
        with pytest.raises(ValueError,match='changed|expired'):
            mutate(database,spec,'1','update',value,form_values(old))
    assert get_record(database,spec,'1')['airline_name'] == 'Concurrent update'
    for key,operation in [('2','update'),('1','delete')]:
        with pytest.raises(ValueError,match='changed'):
            mutate(database,spec,key,operation,token,form_values(old))


def insert(conn, sql, params=()):
    query(conn,sql,params)
    return query(conn,'SELECT LAST_INSERT_ID() AS id')[0]['id']


def new_fixtures(conn):
    airline = insert(conn,"INSERT INTO Airline(code,airline_name) VALUES ('ZZ','DBA fixture')")
    aircraft = insert(conn,"INSERT INTO Aircraft(registration_no,model,capacity,airline_id) VALUES ('ZZ-DBA','DBA fixture',10,%s)",(airline,))
    airport = insert(conn,"INSERT INTO Airport(airport_code,airport_name,city) VALUES ('ZZZ','DBA fixture','DBA city')")
    passenger = insert(conn,"INSERT INTO Passenger(passenger_name,dob,passport_no) VALUES ('DBA fixture','2000-01-01','DBAFIXTURE')")
    future = datetime.now().replace(microsecond=0) + timedelta(days=90)
    flight = insert(conn,"INSERT INTO Flight(departure_time,arrival_time,flight_status,airline_id,aircraft_id,departure_airport_id,arrival_airport_id) VALUES (%s,%s,'Scheduled',%s,%s,%s,1)",(future,future+timedelta(hours=2),airline,aircraft,airport))
    booking = insert(conn,"INSERT INTO Booking(booking_date,seat_number,fare,passenger_id,flight_id) VALUES (CURDATE(),'1A',100,%s,%s)",(passenger,flight))
    query(conn,'INSERT INTO Baggage VALUES (%s,1,10)',(booking,))
    return dict(Airline=str(airline),Aircraft=str(aircraft),Airport=str(airport),Passenger=str(passenger),Flight=str(flight),Booking=str(booking),Baggage=f'{booking}-1')


@pytest.mark.integration
def test_dependency_blocks_then_individual_deletions_and_audit(database):
    keys = new_fixtures(database)
    for name in ('Airline','Aircraft','Airport','Passenger','Flight','Booking'):
        spec = ENTITIES[name]
        key = keys[name]
        assert any(r['row_count'] for r in dependencies(database,spec,key))
        before = snapshot(database)
        with pytest.raises(ValueError,match='dependent records'):
            mutate(database,spec,key,'delete',row_token(spec,get_record(database,spec,key),'delete'))
        assert snapshot(database) == before
    for name in ('Baggage','Booking','Flight','Passenger','Aircraft','Airport','Airline'):
        spec = ENTITIES[name]
        key = keys[name]
        mutate(database,spec,key,'delete',row_token(spec,get_record(database,spec,key),'delete'))
        with pytest.raises(LookupError):
            get_record(database,spec,key)
    assert len(query(database,'SELECT * FROM booking_cancellation_log WHERE booking_id=%s',(keys['Booking'],))) == 1
    assert len(query(database,'SELECT * FROM booking_creation_log WHERE booking_id=%s',(keys['Booking'],))) == 1
    assert not query(database,'SELECT * FROM vw_booking_manifest WHERE booking_id=%s',(keys['Booking'],))
    assert not query(database,'SELECT * FROM vw_flight_operations WHERE flight_id=%s',(keys['Flight'],))


@pytest.mark.integration
def test_flight_time_overlap_and_status_lock(database):
    fixtures = new_fixtures(database)
    other = get_record(database,ENTITIES['Flight'],fixtures['Flight'])
    # Same aircraft: the second flight must be created at a non-overlapping time.
    later = other['arrival_time'] + timedelta(hours=1)
    second = insert(database,"INSERT INTO Flight(departure_time,arrival_time,flight_status,airline_id,aircraft_id,departure_airport_id,arrival_airport_id) VALUES (%s,%s,'Scheduled',%s,%s,%s,1)",(later,later+timedelta(hours=1),other['airline_id'],other['aircraft_id'],other['departure_airport_id']))
    before = snapshot(database)
    with pytest.raises(ValueError,match='already scheduled'):
        edit(database,'Flight',str(second),departure_time=other['departure_time'].isoformat(),arrival_time=other['arrival_time'].isoformat())
    with pytest.raises(ValueError,match='future'):
        edit(database,'Flight',str(second),departure_time='2000-01-01T12:00',arrival_time='2000-01-01T13:00')
    with pytest.raises(ValueError,match='Arrival'):
        edit(database,'Flight',str(second),arrival_time=other['departure_time'].isoformat())
    assert snapshot(database) == before
    edit(database,'Flight',str(second),flight_status='Arrived')
    before = snapshot(database)
    with pytest.raises(mysql.connector.Error,match='already arrived'):
        edit(database,'Flight',str(second),flight_status='Scheduled')
    assert snapshot(database) == before
    edit(database,'Flight','1',flight_status='Delayed')  # Original past dates are still editable.


def form_tokens(response):
    return {name: re.search(f'name="{name}" value="([^"]+)"',response.text)[1] for name in ('csrf_token','row_token')}


@pytest.mark.integration
def test_http_forms_search_allowlist_confirmation_and_keys(database,app):
    client = app.test_client()
    for name in ENTITIES:
        assert client.get('/dba/'+name).status_code == 200
    assert client.get('/dba').status_code == 302
    for path in ('/dba/booking_creation_log','/dba/Airline/1-2/edit','/dba/Airline/0/edit','/dba/Airline/999999/edit','/views/unknown'):
        assert client.get(path).status_code == 404
    assert b'0 matching records' in client.get('/dba/Airline?q=%27%20OR%201%3D1').data
    assert b'Air India' in client.get('/dba/Airline?q=Air+India').data
    assert client.post('/dba/Airline/1/edit',data={}).status_code == 400
    response = client.get('/dba/Passenger/1/edit')
    values = form_values(get_record(database,ENTITIES['Passenger'],'1'))
    response = client.post('/dba/Passenger/1/edit',data={**values,**form_tokens(response),'phone':'1234567890','passenger_id':'2'})
    assert response.status_code == 302
    assert get_record(database,ENTITIES['Passenger'],'1')['phone'] == '1234567890'
    response = client.get('/dba/Baggage/1-1/delete')
    assert get_record(database,ENTITIES['Baggage'],'1-1')  # GET must not delete.
    tokens = form_tokens(response)
    assert client.post('/dba/Baggage/1-1/delete',data=tokens).status_code == 409
    assert client.post('/dba/Baggage/1-1/delete',data={**tokens,'confirmed':'yes'}).status_code == 302
    assert client.get('/dba/Baggage/1-1/edit').status_code == 404
    response = client.get('/dba/Flight/1/delete')
    assert b'Deletion is blocked' in response.data
    assert client.post('/dba/Flight/1/delete',data={**form_tokens(response),'confirmed':'yes'}).status_code == 409


@pytest.mark.integration
def test_view_totals_zero_activity_and_live_changes(database,app):
    for name in VIEWS:
        assert app.test_client().get('/views/'+name).status_code == 200
    assert len(query(database,'SELECT * FROM vw_flight_operations')) == 12
    assert len(query(database,'SELECT * FROM vw_booking_manifest')) == 29
    assert sum(r['total_revenue'] for r in query(database,'SELECT * FROM vw_airline_performance')) == Decimal('271300.00')
    assert sum(r['total_spent'] for r in query(database,'SELECT * FROM vw_passenger_activity')) == Decimal('271300.00')
    assert sum(r['booked_seats'] for r in query(database,'SELECT * FROM vw_flight_occupancy')) == 29
    assert sum(r['bag_count'] for r in query(database,'SELECT * FROM vw_booking_baggage')) == 20
    assert sum(r['total_baggage_weight'] for r in query(database,'SELECT * FROM vw_booking_baggage')) == query(database,'SELECT SUM(baggage_weight) AS total FROM Baggage')[0]['total']
    traffic = query(database,'SELECT * FROM vw_airport_traffic')
    assert sum(r['departure_count'] for r in traffic) == sum(r['arrival_count'] for r in traffic) == 12
    assert any(r['bag_count']==0 for r in query(database,'SELECT * FROM vw_booking_baggage'))
    airline = insert(database,"INSERT INTO Airline(code,airline_name) VALUES ('ZZ','Unused')")
    passenger = insert(database,"INSERT INTO Passenger(passenger_name,dob,passport_no) VALUES ('Unused','2000-01-01','UNUSEDDBA')")
    airport = insert(database,"INSERT INTO Airport(airport_code,airport_name,city) VALUES ('ZZZ','Unused','Unused')")
    assert query(database,'SELECT * FROM vw_airline_performance WHERE airline_id=%s',(airline,))[0]['flight_count'] == 0
    assert query(database,'SELECT * FROM vw_passenger_activity WHERE passenger_id=%s',(passenger,))[0]['total_spent'] == 0
    assert query(database,'SELECT * FROM vw_airport_traffic WHERE airport_id=%s',(airport,))[0]['total_movements'] == 0
    edit(database,'Booking','1',fare='100')
    assert query(database,'SELECT fare FROM vw_booking_manifest WHERE booking_id=1')[0]['fare'] == 100
    edit(database,'Flight','1',flight_status='Cancelled')
    assert query(database,'SELECT flight_status FROM vw_flight_occupancy WHERE flight_id=1')[0]['flight_status'] == 'Cancelled'
    assert len(query(database,'SELECT * FROM vw_flight_operations')) == 12


@pytest.mark.integration
def test_install_views_repeatable_and_missing_only_affects_views(database,app):
    before = snapshot(database)
    query(database,'DROP VIEW vw_flight_operations')
    client = app.test_client()
    for path in ('/','/reports/J4','/dba/Airline'):
        assert client.get(path).status_code == 200
    assert client.get('/views').status_code == 302
    assert client.get('/views').location == '/reports'
    assert b'Flight operations' in client.get('/reports',query_string={'category':'Flights'}).data
    assert b'install-views' in client.get('/views/vw_flight_operations').data
    assert not query(database,"SELECT TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='vw_flight_operations'")
    result = app.test_cli_runner().invoke(args=['install-views'])
    assert result.exit_code == 0, result.output
    install_views(database)
    assert snapshot(database) == before
    assert len(query(database,'SELECT * FROM vw_flight_operations')) == 12


@pytest.mark.integration
def test_every_dba_form_get_preserves_data(database,app):
    before = snapshot(database)
    client = app.test_client()
    for name in ENTITIES:
        key = '1-1' if name == 'Baggage' else '1'
        for operation in ('edit','delete'):
            response = client.get(f'/dba/{name}/{key}/{operation}')
            assert response.status_code == 200
            assert b'View SQL' in response.data
            assert b'name="row_token"' in response.data
    assert snapshot(database) == before
    assert query(database,"SELECT SECURITY_TYPE FROM information_schema.VIEWS WHERE TABLE_SCHEMA=DATABASE()") == [{'SECURITY_TYPE':'INVOKER'}]*7


@pytest.mark.integration
def test_concurrent_edit_accepts_only_one_original_snapshot(database,app):
    spec = ENTITIES['Airline']
    old = get_record(database,spec,'1')
    token = row_token(spec,old,'update')
    def attempt(name):
        with app.app_context():
            conn = connect()
            try:
                mutate(conn,spec,'1','update',token,{**form_values(old),'airline_name':name})
                return 'committed'
            except ValueError as exc:
                assert 'changed since' in str(exc)
                return 'stale'
            finally:
                conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt,['Concurrent A','Concurrent B']))
    assert sorted(outcomes) == ['committed','stale']


@pytest.mark.integration
def test_expired_row_token_rejects_change(database,monkeypatch):
    import time
    spec = ENTITIES['Airline']
    old = get_record(database,spec,'1')
    timestamp = int(time.time())-4000
    with monkeypatch.context() as patch:
        patch.setattr('itsdangerous.timed.TimestampSigner.get_timestamp',lambda self:timestamp)
        token = row_token(spec,old,'update')
    with pytest.raises(ValueError,match='expired'):
        mutate(database,spec,'1','update',token,{**form_values(old),'airline_name':'Expired change'})
    assert get_record(database,spec,'1') == old


@pytest.mark.integration
def test_views_are_integrated_with_business_reports(database,app):
    from html import unescape
    from airline.catalogue import REPORTS
    from urllib.parse import urlencode
    client = app.test_client()
    response = client.get('/reports')
    links = re.findall(r'class="report-card" href="([^"]+)"',response.text)
    assert len(links) == 61
    assert {f'/reports/{name}' for name in REPORTS} <= set(links)
    assert {f'/views/{name}' for name in VIEWS} <= set(links)
    assert b'>SQL views</span>' not in response.data
    assert b'54 reports' in response.data and b'7 views' in response.data
    for name,view in VIEWS.items():
        response = client.get('/reports',query_string={'category':view['category']})
        assert f'/views/{name}' in response.text
        for other in VIEWS.values():
            assert (f'/views/{other["name"]}' in response.text) == (other['category'] == view['category'])
        detail = client.get('/views/'+name)
        assert f'← {view["category"]} reports' in unescape(detail.text)
        category_url = '/reports?' + urlencode({'category':view['category']})
        assert f'class="nav-item active" href="{category_url}"' in detail.text
    result = client.get('/reports',query_string={'q':'V1','category':'Flights'})
    assert '/views/vw_flight_operations' in result.text
    assert '/views/vw_flight_occupancy' not in result.text
    assert b'No reports found' not in result.data
    result = client.get('/reports',query_string={'q':'this-will-not-match-anything'})
    assert b'No reports found' in result.data
    assert client.get('/views').location == '/reports'
