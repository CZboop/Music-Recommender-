import unittest
from app import app
from app.functions import authenticate, get_db_connection, create_token, store_token_user_info, get_username_from_token, get_artists_rated, get_user_from_name, get_all_artists, get_all_artist_ids, rating_artist, get_past_recs, is_artist_rated, get_highest_user_id, get_artist_link_from_id, get_artist_id_from_name, add_new_artist, get_artist_names
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
    def test_can_get_correct_user_id_from_name(self):
        # GIVEN - a username
        expected_username = 'test_user_1234'
        user_id = 2244
        if not self.does_user_already_exist(expected_username):
            self.setup_test_user(expected_username, user_id)

        # WHEN - we call the get user (id) from name function
        actual_result = get_user_from_name(expected_username)
        # and get the username for that returned id
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"SELECT name FROM users WHERE auto_id = {actual_result};")
        actual_username = cur.fetchall()[0][0]
        cur.close()
        connection.close()

        # THEN - the result has the correct details
        self.assertEqual(actual_username, expected_username)

    def test_getting_id_for_invalid_username_returns_none(self):
        # GIVEN - a username
        expected_username = 'afakeuserwhodoesnotexist'

        # WHEN - we call the get user (id) from name function
        actual_result = get_user_from_name(expected_username)

        # THEN - the result is none
        expected_result = None
        self.assertEqual(actual_result, expected_result)

    ## TEST GET ALL ARTISTS
    def test_get_all_artists_returns_list_of_artists(self):
        # GIVEN - the setup has added all artists to the db
        # WHEN - we call the undertest function
        all_artists = get_all_artists()

        # THEN - we have a result which is a list of tuples, and each tuple matches expected for artist row
        expected_result_type = 'list'
        actual_result_type = type(all_artists).__name__

        expected_element_type = 'tuple'
        actual_element_type = type(all_artists[0]).__name__

        # note length of result will change as more artists are added from spotify imports, not testing atm

        self.assertEqual(expected_result_type, actual_result_type)
        self.assertEqual(expected_element_type, actual_element_type)

    ## TEST GET ALL ARTIST IDS (from spotify api, needs auth so not testing here)   

    ## TEST RATING ARTIST
    def test_rating_artist_returns_true_if_updating_rating(self):
        # GIVEN - user has rated an artist
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        user_id = get_user_from_name(username)
        artist_name = '2pac'
        artist_id = get_artist_id_from_name(artist_name)
        rating = 7

        self.cleanup_remove_rating(username)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
            
        conn.commit()
        cur.close()
        conn.close()

        # WHEN - we call the rating artist boolean returning function for that artist (as if rating again)
        actual_result = rating_artist(artist_name, user_id, rating)

        # THEN - return true to say artist was already rated
        self.assertTrue(actual_result)

    def test_rating_artist_returns_false_if_new_rating(self):
        # GIVEN - user has not rated the artist
        username = 'test_user_123456'
        user_id = 4455667
        artist_name = '2pac'
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)

        self.cleanup_remove_rating(username)

        # WHEN - we call the rating artist boolean returning function for that artist (as if rating again)
        user_id = get_user_from_name(username)
        artist_id = get_artist_id_from_name(artist_name)
        rating = 7

        actual_result = rating_artist(artist_name, user_id, rating)

        # THEN - return false to say not rated before
        self.assertFalse(actual_result)

    ## TEST GET PAST RECOMMENDATIONS
    def test_can_get_past_recs_for_user_with_past_recs(self):
        # GIVEN - a user who has past recommendations in the database
        username = 'test_user_123456'
        user_id = 4455667
        artist_name = '2pac'
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)

        user_id = get_user_from_name(username)
        past_recs_to_add = [100, 200, 300, 400] # artist ids just ints
        conn = get_db_connection()
        cur = conn.cursor()

        for rec in past_recs_to_add:
            cur.execute(f"INSERT INTO user_recommendations (user_id, artist_id) VALUES ({user_id}, {rec});")
            
        conn.commit()
        cur.close()
        conn.close()

        # WHEN - we call get past recommendations
        actual_past_recs = get_past_recs(user_id)
        actual_artist_ids = [result[-1] for result in actual_past_recs]

        # THEN - these past recommendations are returned
        self.assertEqual(actual_artist_ids, past_recs_to_add)
        
        self.cleanup_remove_recs(username)

    def test_getting_past_recs_for_user_with_no_past_recs(self):
        # GIVEN - a user with no past recs
        username = 'test_user_123456'
        user_id = 4455667
        artist_name = '2pac'
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)

        user_id = get_user_from_name(username)

        # WHEN - we call get past recommendations
        actual_past_recs = get_past_recs(user_id)
        expected_past_recs = []

        # THEN - we get an empty result set
        self.assertEqual(actual_past_recs, expected_past_recs)
        
        self.cleanup_remove_recs(username)

    ## TEST IS ARTIST RATED
    def test_is_artist_rated_returns_none_if_no_user_id(self):
        # GIVEN - no user id
        # WHEN - we call the is artist rated func
        is_rated = is_artist_rated('2pac')

        # THEN - result is None
        self.assertEqual(is_rated, None)

    def test_is_artist_rated_returns_true_if_already_rated(self):
        # GIVEN - a user who has rated an artist
        username = 'test_user_123456'
        user_id = 4455667
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)
        user_id = get_user_from_name(username)
        artist_name = '2pac'
        artist_id = get_artist_id_from_name(artist_name)
        rating = 7

        self.cleanup_remove_rating(username)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO user_ratings (user_id, artist_id, rating) VALUES ({user_id}, {artist_id}, {rating});")
        conn.commit()
        cur.close()
        conn.close()

        # WHEN - we call the is artist rated func
        is_rated = is_artist_rated(artist_name, user_id)

        # THEN - result is true
        self.assertTrue(is_rated)

    def test_is_artist_rated_returns_false_if_not_rated(self):
        # GIVEN - a user who has not rated an artist
        username = 'test_user_123456'
        user_id = 4455667
        artist_name = '2pac'
        if not self.does_user_already_exist(username):
            self.setup_test_user(username, user_id)

        user_id = get_user_from_name(username)

        # WHEN - we call the is artist rated func
        is_rated = is_artist_rated(artist_name, user_id)

        # THEN - result is false
        self.assertFalse(is_rated)

    ## TEST GET HIGHEST USER ID
    
    # how to test this without deleting the table/ messing up ids for later tests
    # def test_get_highest_user_id_with_no_data_gives_zero(self):
    #     pass

    def test_get_highest_user_id_gets_highest_id(self):
        # GIVEN - an empty user table
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT auto_id FROM users ORDER BY auto_id DESC LIMIT 1;")
        expected = cur.fetchall()[0][0]
        conn.commit()
        cur.close()
        conn.close()

        # WHEN - we call the get highest id function
        actual = get_highest_user_id()

        # THEN - the highest user id returned matches the number of users added
        self.assertEqual(actual, expected)

    ## TEST GET ARTIST LINK FROM ID
    # TODO: make this part of starter data - was added manually after rather than getting from og dataset
    # def test_can_get_artist_link_from_id(self):
    #     pass

    ## TEST CAN ADD A NEW ARTIST
    def test_can_add_a_new_artist(self):
        # GIVEN - an artist not in the db
        artist_name = 'test artist 123'
        # WHEN - we the artist and query the db for it
        add_new_artist(artist_name)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM artists WHERE name = '{artist_name}';")
        result_name = cur.fetchall()[0][1]
        conn.commit()
        cur.close()
        conn.close()

        # THEN - the db returns the artist
        self.assertEqual(result_name, artist_name)

        self.cleanup_remove_artist(artist_name)

    def test_adding_new_artist_can_handle_single_quotes_in_name(self):
        # GIVEN - an artist not in the db, with single quotes in the name
        artist_name = "test mana'ish za'atar"
        # WHEN - we the artist and query the db for it
        add_new_artist(artist_name)

        artist_name_escaped = artist_name.replace("'", "''")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM artists WHERE name = '{artist_name_escaped}';")
        result_name = cur.fetchall()[0][1]
        conn.commit()
        cur.close()
        conn.close()

        # THEN - the db returns the artist
        self.assertEqual(result_name, artist_name)

        self.cleanup_remove_artist(artist_name_escaped)

    ## TEST CAN STORE TOKEN IN SESSION
    # has same attribute error that may be due to not making client request
    # def test_storing_token_adds_it_to_session(self):
    #     username = 'test_user_1234'
    #     token = create_token(username)
    #     with app.test_client(self) as client:
    #         with client.session_transaction() as session:
    #             store_token_user_info(token)
    #             self.assertTrue(session['logged_in'])

    ## TEST CAN GET ALL ARTIST NAMES FROM DB
    def test_can_get_artist_names_from_db(self):
        # GIVEN - setup has added starter data to db
        # WHEN - we call the function to get all artist names
        all_artist_names = get_artist_names()
        # THEN - flat list of artist names returned
        self.assertTrue(all(isinstance(artist, str) for artist in all_artist_names))

    def test_all_artist_names_returned(self):
        # GIVEN - setup has added starter data to db
        # WHEN - we call the function to get all artist names, and also manually query to get all artists
        actual_artist_names = get_artist_names()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM artists;")
        expected_all_artists = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        # THEN - length of both result sets is the same
        self.assertEqual(len(actual_artist_names), len(expected_all_artists))

    ## TEST STORE RECOMMENDATIONS IN DB
    def test_store_recommendations_in_db(self):
        # GIVEN - 

        # WHEN - 

        # THEN - 
        pass

    ## TEST GET ARTIST NAME FROM ID

    ## TEST GET ARTIST LASTFM LINK FROM ID

    def cleanup_remove_rating(self, username):
        user_id = get_user_from_name(username)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM user_ratings WHERE user_id = {user_id};")
        connection.commit()
        cur.close()
        connection.close()

    def cleanup_remove_artist(self, artist_name):
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM artists WHERE name = '{artist_name}';")
        connection.commit()
        cur.close()
        connection.close()

    def cleanup_remove_recs(self, username):
        user_id = get_user_from_name(username)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM user_recommendations WHERE user_id = {user_id};")
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
