import unittest
from copy import deepcopy

from dateutil import parser
from time import sleep

from util import create_appointment, update_appointment, get_appointment, get_user_session_id, get_admin_session_id, \
    get_another_user_session_id, vote_for_option, delete_vote, get_notifications, mark_delivered, \
    mark_delivered_current_notifications, create_notifications


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.user_session = get_user_session_id()
        self.another_user_session = get_another_user_session_id()
        self.admin_session = get_admin_session_id()

    def test_create_and_get_appointment(self):
        post_response = create_appointment().json()
        get_response = get_appointment(post_response['id']).json()

        get_options = [{'id': option['id'], 'time': parser.isoparse(option['dateTime']), 'comment': option['comment']}
                       for option in get_response['options']]
        post_options = [{'id': option['id'], 'time': parser.isoparse(option['dateTime']), 'comment': option['comment']}
                        for option in post_response['options']]

        self.assertEqual(get_response['id'], post_response['id'])
        self.assertEqual(get_response['comment'], post_response['comment'])
        self.assertEqual(parser.isoparse(get_response['till']), parser.isoparse(post_response['till']))
        self.assertEqual(len(get_response['options']), len(post_response['options']))
        self.assertTrue(all(element in post_options for element in get_options))
        self.assertTrue(all(element in get_options for element in post_options))

    def test_update_appointment(self):
        post_response = create_appointment({'JSESSIONID': self.user_session}).json()

        self.assertTrue(post_response['creatorName'], 'test')
        self.assertEqual(post_response['comment'], 'test')

        update_json = deepcopy(post_response)
        update_json['comment'] = 'test2'
        id_to_update = update_json['options'][0]['id']
        update_json['options'][0]['comment'] = '3'
        id_to_delete = update_json['options'][1]['id']
        update_json['options'][1]['id'] = None

        update_response = update_appointment(post_response['id'], cookies={'JSESSIONID': self.user_session},
                                             json=update_json).json()

        self.assertEqual(post_response['id'], update_response['id'])
        self.assertNotEqual(post_response['comment'], update_response['comment'])
        self.assertEqual(update_response['comment'], 'test2')
        self.assertEqual(len(update_response['options']), len(post_response['options']))
        self.assertFalse(id_to_delete in [option['id'] for option in update_response['options']])

        for option in update_response['options']:
            if option['id'] == id_to_update:
                self.assertEqual(option['comment'], '3')

    def test_move_option_to_other_appointment(self):
        first = create_appointment({'JSESSIONID': self.user_session}).json()
        second = create_appointment({'JSESSIONID': self.user_session}).json()

        first['options'][0]['id'] = second['options'][0]['id']
        self.assertEqual(update_appointment(first['id'], cookies={'JSESSIONID': self.user_session},
                                             json=first).status_code, 400)


    def test_update_rights(self):
        post_response = create_appointment({'JSESSIONID': self.user_session}).json()
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.user_session},
                                            json=post_response).status_code, 200)
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.another_user_session},
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies=None,
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.admin_session},
                                            json=post_response).status_code, 200)

        post_response = create_appointment().json()
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.user_session},
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.another_user_session},
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies=None,
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.admin_session},
                                            json=post_response).status_code, 200)

        post_response = create_appointment({'JSESSIONID': self.admin_session}).json()
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.user_session},
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.another_user_session},
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies=None,
                                            json=post_response).status_code, 400)
        self.assertEqual(update_appointment(post_response['id'], cookies={'JSESSIONID': self.admin_session},
                                            json=post_response).status_code, 200)

    def test_vote(self):
        post_response = create_appointment({'JSESSIONID': self.user_session}).json()
        option_id = post_response['options'][0]['id']
        vote_json = {'comment': 'test', 'optionId': option_id, 'type': 'AGREE'}
        anon_vote_id = vote_for_option(json=vote_json).json()['id']
        user_vote_id = vote_for_option(json=vote_json, cookies={'JSESSIONID': self.user_session}).json()['id']
        another_user_vote_id = \
            vote_for_option(json=vote_json, cookies={'JSESSIONID': self.another_user_session}).json()['id']
        admin_vote_id = vote_for_option(json=vote_json, cookies={'JSESSIONID': self.admin_session}).json()['id']

        result = get_appointment(post_response['id']).json()
        self.assertTrue(option_id in [option['id'] for option in result['options']])
        for option in result['options']:
            if option['id'] == option_id:
                self.assertTrue(anon_vote_id in [vote['id'] for vote in option['votes']])
                self.assertTrue(user_vote_id in [vote['id'] for vote in option['votes']])
                self.assertTrue(another_user_vote_id in [vote['id'] for vote in option['votes']])
                self.assertTrue(admin_vote_id in [vote['id'] for vote in option['votes']])

        self.assertEqual(delete_vote(anon_vote_id).status_code, 403)
        self.assertEqual(delete_vote(anon_vote_id, {'JSESSIONID': self.user_session}).status_code, 400)
        self.assertEqual(delete_vote(anon_vote_id, {'JSESSIONID': self.admin_session}).status_code, 200)

        self.assertEqual(delete_vote(user_vote_id).status_code, 403)
        self.assertEqual(delete_vote(user_vote_id, {'JSESSIONID': self.user_session}).status_code, 200)

        self.assertEqual(delete_vote(another_user_vote_id).status_code, 403)
        self.assertEqual(delete_vote(another_user_vote_id, {'JSESSIONID': self.user_session}).status_code, 400)
        self.assertEqual(delete_vote(another_user_vote_id, {'JSESSIONID': self.admin_session}).status_code, 200)

        self.assertEqual(delete_vote(admin_vote_id).status_code, 403)
        self.assertEqual(delete_vote(admin_vote_id, {'JSESSIONID': self.user_session}).status_code, 400)
        self.assertEqual(delete_vote(admin_vote_id, {'JSESSIONID': self.another_user_session}).status_code, 400)
        self.assertEqual(delete_vote(admin_vote_id, {'JSESSIONID': self.admin_session}).status_code, 200)

    def test_get_notifications(self):
        # sleep(15)
        create_notifications()
        mark_delivered_current_notifications({'JSESSIONID': self.user_session})
        mark_delivered_current_notifications({'JSESSIONID': self.another_user_session})
        mark_delivered_current_notifications({'JSESSIONID': self.admin_session})

        post_response = create_appointment({'JSESSIONID': self.user_session}).json()
        option_id = post_response['options'][0]['id']
        vote_json = {'comment': 'test', 'optionId': option_id, 'type': 'AGREE'}
        vote_for_option(json=vote_json, cookies={'JSESSIONID': self.user_session})
        vote_for_option(json=vote_json, cookies={'JSESSIONID': self.another_user_session})
        vote_for_option(json=vote_json, cookies={'JSESSIONID': self.admin_session})

        user_notifications_response = get_notifications({'JSESSIONID': self.user_session}).json()
        another_user_notifications_response = get_notifications({'JSESSIONID': self.another_user_session}).json()
        admin_notification_response = get_notifications({'JSESSIONID': self.admin_session}).json()

        self.assertEqual(len(user_notifications_response), 0)
        self.assertEqual(len(another_user_notifications_response), 0)
        self.assertEqual(len(admin_notification_response), 0)

        sleep(15)
        create_notifications()

        user_notifications_response = get_notifications({'JSESSIONID': self.user_session}).json()
        another_user_notifications_response = get_notifications({'JSESSIONID': self.another_user_session}).json()
        admin_notification_response = get_notifications({'JSESSIONID': self.admin_session}).json()

        self.assertEqual(len(user_notifications_response), 2)
        self.assertEqual(len(another_user_notifications_response), 1)
        self.assertEqual(len(admin_notification_response), 1)


if __name__ == '__main__':
    unittest.main()
