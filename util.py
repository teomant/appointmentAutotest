from datetime import datetime, timedelta

import requests
from dateutil.tz.tz import tzlocal
from requests import post


def create_appointment(cookies=None):
    return requests.post('http://localhost:8080/rest/appointment/create',
                         cookies=cookies,
                         json={
                             'comment': "test",
                             'latitude': 50.0,
                             'longitude': 50.0,
                             'till': (datetime.now(tzlocal()) + timedelta(0, 10)).isoformat(),
                             'options': [
                                 {
                                     'id': None,
                                     'comment': '1',
                                     'dateTime': '2017-07-03T20:32:56.525+04:00'
                                 },
                                 {
                                     'id': None,
                                     'comment': '2',
                                     'dateTime': '2017-07-03T20:32:56.525+04:00'
                                 }
                             ]
                         })


def update_appointment(id, cookies=None, json=None):
    return requests.post(f'http://localhost:8080/rest/appointment/{id}',
                         cookies=cookies,
                         json=json)


def vote_for_option(cookies=None, json=None):
    return requests.post('http://localhost:8080/rest/appointment/vote',
                         cookies=cookies,
                         json=json)


def delete_vote(id, cookies=None):
    return requests.post(f'http://localhost:8080/rest/appointment/deleteVote/{id}',
                         cookies=cookies)


def get_notifications(cookies=None):
    return requests.get('http://localhost:8080/rest/notification/get?delivered=false',
                        cookies=cookies)


def create_notifications():
    return requests.post('http://localhost:8080/actuator/scheduler-test')


def mark_delivered(id, cookies=None):
    return requests.post(f'http://localhost:8080/rest/notification/delivered/{id}',
                         cookies=cookies)


def mark_delivered_client(id, token=None, user_id=1):
    return requests.post(f'http://localhost:8080/api/notification/delivered/{id}?userId={user_id}',
                         headers=token)


def mark_delivered_current_notifications(cookies=None):
    for notification in get_notifications(cookies).json():
        mark_delivered(notification['id'], cookies)


def mark_delivered_current_client_notifications(token=None, user_id=1):
    for notification in get_notifications_from_client(token, user_id).json():
        mark_delivered_client(notification['id'], token)


def get_appointment(number):
    return requests.get(f'http://localhost:8080/rest/appointment/{number}', {})


def get_admin_session_id():
    return post('http://localhost:8080/login?username=admin&password=admin').cookies.get('JSESSIONID')


def get_user_session_id():
    return post('http://localhost:8080/login?username=test&password=test').cookies.get('JSESSIONID')


def get_another_user_session_id():
    return post('http://localhost:8080/login?username=test1&password=test').cookies.get('JSESSIONID')


def get_jwt_token():
    return post('http://localhost:8080/client/login_client', json={'username': 'client', 'password': 'client'}).text


def add_client_user(token):
    return post('http://localhost:8080/api/add-user', json={'username': 'client_user', 'clientId': 1},
                headers=token)


def vote_from_client(client_vote_json, token):
    post('http://localhost:8080/api/vote', json=client_vote_json, headers=token)


def get_notifications_from_client(token=None, user_id=1):
    return requests.get(f'http://localhost:8080/api/notification?delivered=false&userId={user_id}',
                        headers=token)
