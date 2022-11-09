import unittest
from app import app
from app.functions import get_db_connection
import random, string, re

class TestUserFunctionality(unittest.TestCase):

    ### TESTING THE USER RELATED FUNCS AND ROUTES

    def test_connect_to_db_gives_connection_instance(self):
        connection_obj = get_db_connection()
        actual = type(connection_obj).__name__
        expected = 'connection'
        self.assertEqual(expected, actual)

    def test_connect_to_right_db(self):
        connection_obj = get_db_connection()
        actual = connection_obj.info.dbname
        expected = 'recommend'
        self.assertEqual(expected, actual)

    def test_db_has_user_table(self):
        connection = get_db_connection()
        cur = connection.cursor()
        # passes if does not throw undefinedtable error/ gets any result set
        cur.execute("SELECT * FROM users LIMIT 1;")
        actual = cur.fetchall()
        cur.close()
        connection.close()
        self.assertTrue(actual)


    def test_can_add_new_user(self):
        client = app.test_client(self)
        # random so that won't always be testing first insertion into the db, will still delete once test run
        username = 'test_' + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
        email = f'{username}@email.com'
        response = client.post('/sign-up', data=dict(username=username, password='P@ssword123', 
        confirm_password='P@ssword123', email=email), follow_redirects=True)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"SELECT * FROM users WHERE name = '{username}';")
        actual = cur.fetchall()[0]
        cur.close()
        connection.close()

        actual_name = actual[1]
        expected_name = username

        actual_email = actual[3]
        expected_email = email
        self.assertEqual(actual_name, expected_name)
        self.assertEqual(actual_email, expected_email)

        self.cleanup_remove_from_db(username)

    def test_password_validator_in_route_flash_message(self):
        client = app.test_client(self)
        username = 'test_' + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
        email = f'{username}@email.com'
        response = client.post('/sign-up', data=dict(username=username, password='pass', 
        confirm_password='pass', email=email), follow_redirects=True)

        flash_message = 'Password should contain at least one character, one number, one special character and should be at least 8 characters long. Please try again.'
        response_data = response.get_data(as_text = True)

        self.assertTrue(flash_message in response_data)

    def test_email_validator_in_route_flash_message(self):
        client = app.test_client(self)
        username = 'test_' + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
        
        response = client.post('/sign-up', data=dict(username=username, password='P@ssword123', 
        confirm_password='P@ssword123', email='notanemail'), follow_redirects=True)

        flash_message = 'Email is invalid. Please try again.'
        response_data = response.get_data(as_text = True)

        self.assertTrue(flash_message in response_data)
    
    def test_username_validator_in_route_flash_message(self):
        client = app.test_client(self)
        email = 'user1@email.com'
        response = client.post('/sign-up', data=dict(username='user1', password='P@ssword123', 
        confirm_password='P@ssword123', email=email), follow_redirects=True)

        flash_message = 'Username already in use. Please try again.'
        response_data = response.get_data(as_text = True)

        self.assertTrue(flash_message in response_data)

    def cleanup_remove_from_db(self, username):
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM users WHERE name = '{username}';")
        cur.close()
        connection.close()

if __name__=="__main__":
    unittest.main()