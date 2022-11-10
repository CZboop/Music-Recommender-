import unittest
from app import app
from app.functions import get_db_connection
import random, string, re, secrets
import os
from db.db_access import setup_tables
from flask import request
from urllib.parse import urlparse

class TestUserFunctionality(unittest.TestCase):
    
    # removing max diff so can see whole diff if test are failing
    maxDiff = None

    ### TESTING THE USER RELATED FUNCS AND ROUTES

    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'postgres'
        os.environ['DB_PASSWORD'] = 'password'
        setup_tables()

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
        try:
            connection = get_db_connection()
            cur = connection.cursor()
            # passes if does not throw undefinedtable error/ gets any result set
            cur.execute("SELECT * FROM users LIMIT 1;")
            actual = cur.fetchall()
            cur.close()
            connection.close()
            # self.assertTrue(actual)
        
        except UndefinedTable:
            self.fail("Selecting from 'User' table raised an Undefined Table error")

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
        # GIVEN - an existing user with a certain username
        client = app.test_client(self) 
        username = 'user1'
        email = f'{username}@email.com'
        response = client.post('/sign-up', data=dict(username=username, password='P@ssword123', 
        confirm_password='P@ssword123', email=email), follow_redirects=True)

        #WHEN - trying to add another user with the same username
        # will de signed in from above (by default sign in when sign up), will get a fresh test client, may change when log out tested
        client = app.test_client(self)

        undertest_response = client.post('/sign-up', data=dict(username=username, password='P@ssword123', 
        confirm_password='P@ssword123', email=email), follow_redirects=True)

        #THEN - the expected flash message is shown on the web page
        flash_message = 'Username already in use. Please try again.'
        response_data = undertest_response.get_data(as_text = True)
        self.assertTrue(flash_message in response_data)

    # TODO: fix or test with selenium
    # def test_can_sign_in_with_all_valid_info(self):
    #     # GIVEN - user info added to db in previous test
    #     client = app.test_client(self) 
    #     username = 'test_user1'
    #     password = 'P@ssword123'
        
    #     # WHEN - we sign in with all correct info
    #     with client:
            
    #         response = client.post('/login', data=dict(username=username, password=password), follow_redirects=True)
    #         with client.session_transaction() as sess:
    #             sess.modified = True
    #         response_url = str(urlparse(response.location).path, encoding='utf-8')
    #         response_text = response.get_data(as_text = True)
    #         welcome_message = f'Welcome, {username}!'
    #         # with app.test_client(self) as client:
            

    #     # THEN - sign in and redirect to a welcome page containing the username :)
    #         self.assertEqual(response_url, '')
    #         self.assertEqual(welcome_message, response_text)
    #         self.assertTrue(welcome_message in response_text)

    def test_cannot_sign_in_with_all_invalid_info(self):
        # GIVEN - user info not in the db
        client = app.test_client(self) 
        username = 'user1999_test'
        password = 'oopswronginfosorry'
        
        # WHEN - we sign in with all incorrect info
        with client:
            # note: need to make request and get path both within this 'with client' context
            response = client.post('/login', data=dict(username=username, password=password), follow_redirects=True)
            response_url = request.path
            response_text = response.get_data(as_text = True)
            flash_message = 'Invalid login details. Try again or <a href="/sign-up">sign up.</a>.'

            # THEN - new url is still login and error message is on the page
            self.assertEqual(response_url, '/login')
            self.assertTrue(flash_message in response_text)

    def test_cannot_sign_in_with_valid_username_invalid_password(self):
        # GIVEN - user in the db, wrong password
        client = app.test_client(self) 
        username = 'user1'
        password = 'iforgot'
        
        # WHEN - we sign in with wrong password
        with client:
            response = client.post('/login', data=dict(username=username, password=password), follow_redirects=True)
            response_url = request.path
            response_text = response.get_data(as_text = True)
            flash_message = 'Invalid login details. Try again or <a href="/sign-up">sign up.</a>.'

            # THEN - new url is still login and error message is on the page
            self.assertEqual(response_url, '/login')
            self.assertTrue(flash_message in response_text)
    
    def test_cannot_sign_in_with_invalid_username_valid_password(self):
        # GIVEN - user not in db, password exists in db
        client = app.test_client(self) 
        username = 'user1999_test'
        password = 'P@ssword123'
        
        # WHEN - we sign in with wrong username
        with client:
            response = client.post('/login', data=dict(username=username, password=password), follow_redirects=True)
            response_url = request.path
            response_text = response.get_data(as_text = True)
            flash_message = 'Invalid login details. Try again or <a href="/sign-up">sign up.</a>.'

            # THEN - new url is still login and error message is on the page
            self.assertEqual(response_url, '/login')
            self.assertTrue(flash_message in response_text)

    def test_cannot_sign_in_if_already_signed_in(self):
        # GIVEN - we have already signed in with valid info (mocking straight into session cookie)
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = 'dummy_token'
            
        # WHEN - we visit sign in page again
            undertest_response = client.get('/login')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say already logged in
            expected_message = 'You are already logged in.'
            self.assertTrue(expected_message in actual_response) 

    def test_can_log_out_if_signed_in(self):
        # GIVEN - we have already signed in with valid info (mocking straight into session cookie)
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = 'dummy_token'
        
        # WHEN - we visit log out page
            undertest_response = client.get('/log-out', follow_redirects=True)
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - we get a success message
            expected_message = 'Logged out successfully!'
            self.assertTrue(expected_message in actual_response)

    def test_cannot_log_out_if_not_signed_in(self):
        # GIVEN - we have not signed in
        client = app.test_client(self) 
        
        # WHEN - we visit log out page
        undertest_response = client.get('/log-out', follow_redirects=True)
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - we get a message to say we weren't logged in
        expected_message = 'You can\'t log out if you\'re not logged in.'
        self.assertTrue(expected_message in actual_response)

    # TODO: fix or test with selenium
    # def test_login_adds_token_to_session(self):
    #     # GIVEN - we sign in with valid info
    #     secret = secrets.token_urlsafe(32)
    #     test_app = app
    #     test_app.config['SECRET_KEY'] = secret
    #     # test_app.config.update(SESSION_COOKIE_DOMAIN = None)
    #     # test_app.config['SERVER_NAME'] = 'localhost'

    #     # client = app.test_client(self) 
    #     username = 'user1'
    #     password = 'P@ssword123'
    #     # response = c.post('/login', data=dict(username=username, password=password), follow_redirects=True)
        
        
    #     # WHEN - we check the session cookie
    #     with test_app as c:
    #         c.post('/login', data=dict(username=username, password=password))
            
    #         with c.session_transaction() as sess:
                
    #             actual_session = c.session['user']
    #         print(actual_session)
    #     # THEN - token is there
    #     self.assertEqual('user', actual_session)

    def test_log_out_removes_token_from_session(self):
        # GIVEN - we sign in with valid info
        client = app.test_client(self) 
        username = 'user1'
        password = 'P@ssword123'
        response = client.post('/login', data=dict(username=username, password=password), follow_redirects=True)
        
        # WHEN - we sign out and then check the session cookie
        client.get('/log-out', follow_redirects=True)
        with client as c:
            with c.session_transaction() as session:
                actual_session = session
        # THEN - token is not there
        self.assertFalse('user' in actual_session)

    def cleanup_remove_from_db(self, username):
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM users WHERE name = '{username}';")
        cur.close()
        connection.close()
    
    #TODO: remove all new user info from db once tests all run

if __name__=="__main__":
    unittest.main()