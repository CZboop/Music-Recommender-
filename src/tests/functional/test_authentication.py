import unittest
from app import app
from app.functions import get_db_connection, create_token, get_user_from_name
import random, string, re, secrets
import os, pytest
from db.db_access import setup_tables
from flask import request
from urllib.parse import urlparse

# @pytest.mark.skip(reason="temp skipping for speed on new tests")
class TestAuthentication(unittest.TestCase):
    
    # removing max diff so can see whole diff if test are failing
    maxDiff = None

    ### TESTING ROUTES THAT HAVE DIFFERENT VERSIONS OF PAGE FOR AUTHENTICATION

    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'postgres'
        os.environ['DB_PASSWORD'] = 'password'
        setup_tables()

        def setup_add_test_user(username='test_user'):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', 999999, 'test_user999@email.com', crypt('P@ssword123', gen_salt('bf', 8)));")
            conn.commit()
            cur.close()
            conn.close()
        setup_add_test_user()

    def test_home_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit home
        undertest_response = client.get('/')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a generic welcome message
        expected_message = 'Welcome!'
        self.assertTrue(expected_message in actual_response) 

    def test_home_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit home page
            undertest_response = client.get('/')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a welcome message with username
            expected_message = f'Welcome, {username}!'
            self.assertTrue(expected_message in actual_response) 

    def test_rate_artist_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the rate artist page
        undertest_response = client.get('/rate-artist')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response) 

    def test_rate_artist_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit rate artist page
            undertest_response = client.get('/rate-artist')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - can see the rating form
            expected_message = 'Click on a star to submit your rating!'
            self.assertTrue(expected_message in actual_response) 

    # TODO: test this as part of test recommendations
    def test_recommendations_auth(self):
        pass

    def test_recommendations_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the recommendations page
        undertest_response = client.get('/recommendations')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response) 

    def test_login_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit login page
            undertest_response = client.get('/login')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - see message to say logged in already
            expected_message = 'You are already logged in.'
            self.assertTrue(expected_message in actual_response)

    def test_login_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the login page
        undertest_response = client.get('/login')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - can see login form
        expected_message = 'Username:'
        self.assertTrue(expected_message in actual_response)

    def test_logout_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit log out page
            undertest_response = client.get('/log-out')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - see message that logged out
            expected_message = 'Logged out successfully!'
            self.assertTrue(expected_message in actual_response)

    def test_logout_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the login page
        undertest_response = client.get('/log-out')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get message that cannot log out
        expected_message = 'You can\'t log out if you\'re not logged in.'
        self.assertTrue(expected_message in actual_response)

    def test_update_rated_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit update rated page
            undertest_response = client.post('/update-rated')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - see jsonified dict with number of artists rated by that user (test user rating in other tests)
            expected_message = '{"num_rated":'
            self.assertTrue(expected_message in actual_response)

    def test_update_rated_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the updated rated page
        undertest_response = client.post('/update-rated')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in (generic from decorator)
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response) 

    # TODO: test as part of spotify api integration testing
    # def test_spotify_portal_auth(self):
    #     pass

    def test_spotify_portal_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the spotify portal page
        undertest_response = client.get('/portal')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in (generic from decorator)
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response) 
    
    # TODO: test as part of spotify api integration testing
    # def test_spotify_login_auth(self):
    #     pass

    def test_spotify_login_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the spotify logging in page
        undertest_response = client.get('/logging-in')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in (generic from decorator)
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response)

    # TODO: test as part of testing recommendation functionality
    # def test_recommend_auth(self):
    #     pass

    def test_recommend_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the recommend page
        undertest_response = client.post('/recommend')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in (generic from decorator)
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response) 

    def test_add_artist_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit add artist page
            undertest_response = client.get('/add-artist')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - see add artist form
            expected_message = 'Artist Name:'
            self.assertTrue(expected_message in actual_response)

    def test_add_artist_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the add artist page
        undertest_response = client.get('/add-artist')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in (generic from decorator)
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response)

    def test_welcome_auth(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user'
        test_token = create_token(username)

        self.cleanup_remove_rating(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we visit welcome page
            undertest_response = client.get(f'/welcome?username={username}')
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - see add artist form
            expected_message = 'Rate 10 artists to get started!'
            self.assertTrue(expected_message in actual_response)

    def test_welcome_not_auth(self):
        # GIVEN - not signed in/ no token in session cookie
        client = app.test_client(self)
        # WHEN - we visit the welcome page
        undertest_response = client.get('/welcome')
        actual_response = undertest_response.get_data(as_text = True)

        # THEN - get a message to say you need to sign in (generic from decorator)
        expected_message = 'You need to be signed in to see this page.'
        self.assertTrue(expected_message in actual_response) 

    def cleanup_remove_rating(self, username):
        user_id = get_user_from_name(username)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM user_ratings WHERE user_id = {user_id};")
        connection.commit()
        cur.close()
        connection.close()

if __name__=="__main__":
    unittest.main()