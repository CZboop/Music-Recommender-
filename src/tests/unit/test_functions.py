import unittest
from app import app
from app.functions import authenticate, get_db_connection, create_token, store_token_user_info, get_username_from_token, get_artists_rated, get_user_from_name, get_all_artists, get_all_artist_ids, rating_artist, get_past_recs, is_artist_rated, get_highest_user_id, get_artist_link_from_id
import datetime as dt
import jwt, os
from db.db_access import setup_tables, add_starter_data_to_db

class TestFunctions(unittest.TestCase):

    ### TESTING FUNCTIONS USED WITHIN THE API/APP

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'postgres'
        os.environ['DB_PASSWORD'] = 'password'
        setup_tables()
        # TODO: add just the few artists that testing to db 
        add_starter_data_to_db()

    ## TESTING GETTING DB CONNECTION
    def test_db_connection_connects_to_right_db(self):
        # GIVEN - we create a new database connection
        conn = get_db_connection()
        # WHEN - we check the database name
        actual = conn.info.dbname
        # THEN - the database name is what we expect
        expected = 'recommend'
        self.assertEqual(actual, expected)

    def test_db_connection_is_correct_object_type(self):
        # GIVEN - we create a new database connection
        conn = get_db_connection()
        # WHEN - we check the type of the connection instance
        actual = type(conn).__name__
        # THEN - the database name is what we expect
        expected = 'connection'
        self.assertEqual(actual, expected)

    ## TESTING TOKEN CREATION
    def test_token_created_has_correct_expiry(self):
        # GIVEN - we create a new token
        undertest_token = create_token('test_user_1234')
        current_time = dt.datetime.utcnow()

        # WHEN - we check the expiry of the token
        undertest_decoded = jwt.decode(undertest_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        actual_expiry = undertest_decoded['expires']

        # THEN - the expiry is 24 hours from now (edge case slightly different seconds?)
        expected_expiry = (current_time +  dt.timedelta(hours=24)).strftime("%m/%d/%Y, %H:%M:%S")
        self.assertEqual(actual_expiry, expected_expiry)

    def test_token_has_correct_username(self):
        # GIVEN - we create a new token
        expected_username = 'test_user_1234'
        undertest_token = create_token(expected_username)

        # WHEN - we manually decode and check the username
        undertest_decoded = jwt.decode(undertest_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        actual_username = undertest_decoded['username']

        # THEN - the decoded username is the same as the one the token was created with
        self.assertEqual(actual_username, expected_username)

    ## TEST TOKEN ADDED TO SESSION (UNSURE ON TESTING THIS ATM)
    def test_token_added_to_session(self):
        pass

    ## TEST CAN GET USERNAME FROM TOKEN
    # def test_can_get_correct_username_back_from_token_with_function(self):
        # # GIVEN - we create a new token and test client
        # expected_username = 'test_user_1234'
        # undertest_token = create_token(expected_username)
        # # client = app.test_client(self)

        # # WHEN - we add the token to the session cookie and decode it with the function used in app
        # with app.test_client(self) as client:
        #     with client.session_transaction() as session:
        #         session['user'] = undertest_token
        #         actual_username = get_username_from_token()

        # # THEN - the decoded username is the same as the one the token was created with
        #     self.assertEqual(actual_username, expected_username)

    ## TEST GET ARTISTS RATED
    def test_can_get_correct_ratings_for_user_with_rated_artists(self):
        # GIVEN - a new user rates some artists
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        user_id = get_user_from_name(username)
        
        artist_ratings = {500: 5, 600: 2}
        test_token = create_token(username)

        self.cleanup_remove_rating(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            conn = get_db_connection()
            cur = conn.cursor()
            
            for artist_id, rating in artist_ratings.items():
                cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
                
            conn.commit()
            cur.close()
            conn.close()


        # WHEN - we get their rated artists with the undertest function
        actual_rated = get_artists_rated(user_id)
        actual_artist1 = actual_rated[0][-2]
        actual_rating1 = actual_rated[0][-1]
        actual_artist2 = actual_rated[1][-2]
        actual_rating2 = actual_rated[1][-1]

        expected_artist1 = 500
        expected_rating1 = 5
        expected_artist2 = 600
        expected_rating2 = 2

        # THEN - we get all of their ratings
        self.assertEqual(actual_artist1, expected_artist1)
        self.assertEqual(actual_rating1, expected_rating1)
        self.assertEqual(actual_artist2, expected_artist2)
        self.assertEqual(actual_rating2, expected_rating2)
        self.cleanup_remove_rating(username)

    def test_can_get_only_ratings_with_min_rating(self):
        # GIVEN - a new user rates some artists
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        user_id = get_user_from_name(username)
        
        artist_ratings = {500: 5, 600: 2}
        test_token = create_token(username)

        self.cleanup_remove_rating(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            conn = get_db_connection()
            cur = conn.cursor()
            
            for artist_id, rating in artist_ratings.items():
                cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
                
            conn.commit()
            cur.close()
            conn.close()

        # WHEN - we get their rated artists with the undertest function, passing in min rating
        actual_rated = get_artists_rated(user_id, 5)
        actual_artist1 = actual_rated[0][-2]
        actual_rating1 = actual_rated[0][-1]
        # THEN - trying to access full ratings throws error
        with self.assertRaises(IndexError):
            actual_artist2 = actual_rated[1][-2]

        self.cleanup_remove_rating(username)  

    def test_can_get_correct_rating_with_min_rating(self):
        # GIVEN - a new user rates some artists
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        user_id = get_user_from_name(username)
        
        artist_ratings = {500: 5, 600: 2}
        test_token = create_token(username)

        self.cleanup_remove_rating(username)
        
        with app.test_client(self) as client:
            with client.session_transaction() as sess:
                sess['user'] = test_token
            conn = get_db_connection()
            cur = conn.cursor()
            
            for artist_id, rating in artist_ratings.items():
                cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
                
            conn.commit()
            cur.close()
            conn.close()

        # WHEN - we get their rated artists with the undertest function, passing in min rating
        actual_rated = get_artists_rated(user_id, 5)
        actual_artist1 = actual_rated[0][-2]
        actual_rating1 = actual_rated[0][-1]

        expected_artist1 = 500
        expected_rating1 = 5

        # THEN - we get the correct higher rating
        self.assertEqual(actual_artist1, expected_artist1)
        self.assertEqual(actual_rating1, expected_rating1)

        self.cleanup_remove_rating(username)
        

    ## TEST GET USER FROM NAME

    ## TEST GET ALL ARTISTS

    ## TEST GET ALL ARTIST IDS

    ## TEST RATING ARTIST

    ## TEST GET PAST RECOMMENDATIONS

    ## TEST IS ARTIST RATED

    ## TEST GET HIGHEST USER ID

    ## TEST GET ARTIST LINK FROM ID

    def cleanup_remove_rating(self, username):
        user_id = get_user_from_name(username)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM user_ratings WHERE user_id = {user_id};")
        connection.commit()
        cur.close()
        connection.close()

    def setup_test_user(self, username, user_id, email='test_dummy_email@email.com', password='P@ssword123'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', {user_id}, '{email}', crypt('{password}', gen_salt('bf', 8)));")
        conn.commit()
        cur.close()
        conn.close()

    def does_user_already_exist(self, username):
        return False if not get_user_from_name(username) else True

if __name__=="__main__":
    unittest.main()
