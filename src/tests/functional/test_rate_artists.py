import unittest
from app import app
from app.functions import get_db_connection, create_token, get_user_from_name, get_artist_id_from_name
import random, string, re
import os, pytest
from db.db_access import setup_tables, add_starter_data_to_db

# @pytest.mark.skip(reason="temp skipping for speed on new tests")
class TestRateArtistFunctionality(unittest.TestCase):

    ### TESTING THE ABILITY FOR USER TO RATE ARTISTS
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'postgres'
        os.environ['DB_PASSWORD'] = 'password'
        setup_tables()
        # TODO: add just the few artists that testing to db 
        add_starter_data_to_db()

    def setup_test_user(self, username, user_id, email='test_dummy_email@email.com', password='P@ssword123'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', {user_id}, '{email}', crypt('{password}', gen_salt('bf', 8)));")
        conn.commit()
        cur.close()
        conn.close()

    def does_user_already_exist(self, username):
        return False if not get_user_from_name(username) else True

    def test_rating_artist_not_yet_rated_gives_added_rating_message(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        
        artist_name = '__Max__'
        test_token = create_token(username)

        self.cleanup_remove_rating(username, artist_name)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
            # self.cleanup_remove_rating(username, artist_name)
            
        # WHEN - we make a post request to rate artist with valid info
            undertest_response = client.post('/rate-artist', data=dict(artist = artist_name, rating = 8), follow_redirects=True)
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - success message appears on page
            expected_message = 'You successfully gave __Max__ a rating of 8'
            # self.assertEqual(expected_message, actual_response)
            self.assertTrue(expected_message in actual_response) 

        self.cleanup_remove_rating(username, artist_name)

    def test_rating_artist_already_rated_gives_updated_rating_message(self):
        # GIVEN - we have signed in with valid info (mocking token straight into session cookie)
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        
        artist_name = '2pac'
        test_token = create_token(username)

        self.cleanup_remove_rating(username, artist_name)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we make two post requests to rate the same artist with valid info
            first_response = client.post('/rate-artist', data=dict(artist = artist_name, rating = 8), follow_redirects=True)

            undertest_response = client.post('/rate-artist', data=dict(artist = artist_name, rating = 10), follow_redirects=True)
            actual_response = undertest_response.get_data(as_text = True)

        # THEN - success message appears on page
            expected_message = 'You successfully updated your rating for 2pac to 10'
            # self.assertEqual(expected_message, self.cleanup_remove_rating(username, artist_name))
            self.assertTrue(expected_message in actual_response) 

        self.cleanup_remove_rating(username, artist_name)

    def test_rating_artist_not_rated_adds_to_db(self):
        # GIVEN - we have signed in with valid info for a user with no ratings yet
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        
        artist_name = '2pac'
        test_token = create_token(username)

        # note this method currently removes all ratings for the user
        self.cleanup_remove_rating(username, artist_name)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we make a post request to rate an artist and check the user_ratings table
            undertest_response = client.post('/rate-artist', data=dict(artist = artist_name, rating = 10), follow_redirects=True)
            # just getting final column from first row (expecting one row result)
            actual_rating = self.query_user_ratings(username, artist_name)[0][-1]

        # THEN - the rating is in the db
            expected_rating = 10
            self.assertEqual(expected_rating, actual_rating) 

        self.cleanup_remove_rating(username, artist_name) 

    def test_rating_artist_already_rated_updates_db(self):
        # GIVEN - we have signed in with valid info for a user with no ratings yet
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        
        artist_name = '2pac'
        test_token = create_token(username)

        # note this method currently removes all ratings for the user
        self.cleanup_remove_rating(username, artist_name)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            
        # WHEN - we make two post requests to rate the same artist and check the user_ratings table
            response1 = client.post('/rate-artist', data=dict(artist = artist_name, rating = 10), follow_redirects=True)
            response2 = client.post('/rate-artist', data=dict(artist = artist_name, rating = 7), follow_redirects=True)
            # just getting final column from first row (expecting one row result)
            actual_rating = self.query_user_ratings(username, artist_name)[0][-1]

        # THEN - the rating is in the db, with the new ratings as the first (only) result from db
            expected_rating = 7
            self.assertEqual(expected_rating, actual_rating) 

        self.cleanup_remove_rating(username, artist_name)

    def query_user_ratings(self, username, artist_name):
        user_id = get_user_from_name(username)
        artist_id = get_artist_id_from_name(artist_name)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"SELECT * FROM user_ratings WHERE user_id = {user_id} AND artist_id = {artist_id};")
        result = cur.fetchall()
        cur.close()
        connection.close()

        return result

    def cleanup_remove_rating(self, username, artist_name):
        user_id = get_user_from_name(username)
        artist_id = get_artist_id_from_name(artist_name)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM user_ratings WHERE user_id = {user_id};")
        connection.commit()
        cur.close()
        connection.close()

    # TODO: 
    ## TEST RATING AN ARTIST THROUGH WELCOME ROUTE

if __name__=="__main__":
    unittest.main()