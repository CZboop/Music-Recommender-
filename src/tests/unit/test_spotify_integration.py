import unittest
from unittest.mock import Mock, patch
import requests
from app import app, functions
from app.functions import authenticate, get_db_connection, create_token, store_token_user_info, get_username_from_token, get_artists_rated, get_user_from_name, get_all_artists, get_all_artist_ids, rating_artist, get_past_recs, is_artist_rated, get_highest_user_id, get_artist_link_from_id, get_artist_id_from_name, get_spotify_top, find_or_add_artist_from_spotify, add_ratings_for_spotify_artists
import datetime as dt
import jwt, os, pytest
from db.db_access import setup_tables, add_starter_data_to_db

# mock response so can mock requests to api, need a mock with methods like .json
class MockResponse:
    def __init__(self, response):
        self.response = response

    def json(self):
        return self.response

def mock_get_spotify_top_get_request(*args, **kwargs):
    mock_response = MockResponse({'items': [{'name': 'fake artist', 'other': 'n/a'}, {'name': 'unreal artist', 'other': 'none'}, {'name': 'real artist sike'}], 'irrelevant key': 333})
    return mock_response

# @pytest.mark.skip(reason="temp skipping for speed on new tests")
class TestSpotifyIntegration(unittest.TestCase):

    ### TESTING FUNCTIONS THAT USE EXTERNAL SPOTIFY API

    maxDiff = None

    ## TEST CAN GET SPOTIFY RECENTLY PLAYED

    ## TEST CAN GET SPOTIFY TOP ARTISTS
    @patch('requests.get', side_effect= mock_get_spotify_top_get_request)
    def test_spotify_top_artists_returns_top_artist_names_for_current_user(self, mock_get):
        # GIVEN - mock for the get request
        mock_response = {'items': [{'name': 'fake artist', 'other': 'n/a'}, {'name': 'unreal artist', 'other': 'none'}, {'name': 'real artist sike'}], 'irrelevant key': 333}
        mock_get.return_value.ok = mock_response

        with app.test_request_context('/'), app.test_client(self) as c:
            access_token = 'a real token ;)'

        # WHEN - call the undertest function
            actual_response = get_spotify_top(access_token)
            expected_response = ['fake artist', 'unreal artist', 'real artist sike']

        # THEN - response is what expect
            self.assertEqual(actual_response, expected_response)

    def setup_test_user(self, username, user_id, email='test_dummy_email@email.com', password='P@ssword123'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('{username}', {user_id}, '{email}', crypt('{password}', gen_salt('bf', 8)));")
        conn.commit()
        cur.close()
        conn.close()

    def does_user_already_exist(self, username):
        return False if not get_user_from_name(username) else True

    def cleanup_remove_rating(self, username):
        user_id = get_user_from_name(username)

        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM user_ratings WHERE user_id = {user_id};")
        connection.commit()
        cur.close()
        connection.close()

    def get_ratings_for_user(self, username):
        user_id = get_user_from_name(username)

        connection = get_db_connection()
        cur = connection.cursor()
        result = cur.execute(f"SELECT * FROM user_ratings WHERE user_id = {user_id};")
        connection.commit()
        cur.close()
        connection.close()

        return result

    def cleanup_remove_artist(self, artist_name):
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute(f"DELETE FROM artists WHERE name = '{artist_name}';")
        connection.commit()
        cur.close()
        connection.close()

    # issue with not picking up user in session
    # @patch('requests.get', side_effect= mock_get_spotify_top_get_request)
    # def test_spotify_top_artists_adds_artist_ratings(self, mock_get):
    #     # GIVEN - mock for the get request and a user with no ratings
    #     mock_response = {'items': [{'name': 'fake artist', 'other': 'n/a'}, {'name': 'unreal artist', 'other': 'none'}, {'name': 'real artist sike'}], 'irrelevant key': 333}
    #     mock_get.return_value.ok = mock_response

    #     username = 'test_user_123'
    #     if not self.does_user_already_exist(username):
    #         self.setup_test_user(username, 100)
    #     self.cleanup_remove_rating(username)

    #     with app.test_request_context('/'), app.test_client(self) as c:
    #         with c.session_transaction() as session:
    #             session['user'] = username
    #             access_token = 'a real token ;)'

    #     # WHEN - call the undertest function and query the db for 
    #         undertest = get_spotify_top(access_token)
    #         expected_ratings = ['fake artist', 'unreal artist', 'real artist sike']

    #         db_response = self.get_ratings_for_user(username)
    #         # getting artists name from result set
    #         actual_ratings = db_response

    #     # THEN - the ratings have been updated for the current user
    #         self.assertEqual(actual_ratings, expected_ratings)

    ## TEST CAN ADD RATINGS FOR SPOTIFY ARTISTS
    @patch('requests.get', side_effect= mock_get_spotify_top_get_request)
    def test_add_ratings_from_spotify_returns_false_if_no_user(self, mock_get):
        # GIVEN - session has no user key and some artists
        mock_response = {'items': [{'name': 'fake artist', 'other': 'n/a'}, {'name': 'unreal artist', 'other': 'none'}, {'name': 'real artist sike'}], 'irrelevant key': 333}
        mock_get.return_value.ok = mock_response

        with app.test_request_context('/'), app.test_client(self) as c:
            with c.session_transaction() as session:
                session['user'] = None

        # WHEN - we call the add ratings from spotify func
            artists = ['2pac', 'Lady Gaga']
            result = add_ratings_for_spotify_artists(artists)

        # THEN - false is returneds
        self.assertFalse(result)

    # should abstract token in session check from this func?
    # adds if not in db already
    # doesn't add if already in db
    # adds rating 
    # def test_can_add_ratings_for_spotify_artists_if_user(self, mock_get):
    #     pass 

    #     # GIVEN - 

    #     # WHEN - 

    #     # THEN - 

    ## TEST CAN CHECK IF ARTIST ALREADY IN DB (FIND OR ADD ARTIST FROM SPOTIFY)
    # returns true if found in db
    def test_find_or_add_artist_from_spotify_returns_true_if_in_db(self):
        # GIVEN -  an artist in the database
        artist = 'Metallica'

        # WHEN - we call the find or add function
        result = find_or_add_artist_from_spotify(artist)

        # THEN - true is returned
        self.assertTrue(result)

    # returns false if not found in db
    def test_find_or_add_artist_from_spotify_returns_false_if_not_in_db(self):
        # GIVEN - an artist not in the database
        artist = 'Test Artist'

        # WHEN - we call the find or add function
        result = find_or_add_artist_from_spotify(artist)

        # THEN - false is returned
        self.assertFalse(result)
        self.cleanup_remove_artist(artist)

    # adds to db if not found
    def test_find_or_add_artist_from_spotify_adds_if_not_in_db(self):
        pass
        # GIVEN - 

        # WHEN - 

        # THEN - 

    ## TEST CAN GET ARTISTS SPOTIFY ID
    # not found returns none
    # found returns id

    ## TEST GETTING ALL OR MULTIPLE ARTIST'S SPOTIFY IDS

    ## TEST GET SPOTIFY FOLLOWED ARTISTS

    ## TEST GET TOP SONGS FOR ARTIST FROM SPOTIFY

    ## TEST SAVE RECOMMENDATIONS AS SPOTIFY PLAYLIST

    ## TEST ADD TRACKS TO SPOTIFY PLAYLIST

    ## TEST GET CURRENT USER SPOTIFY ID

    ## TEST GET SPOTIFY AUTH TOKENS

    ## TEST REFRESH SPOTIFY TOKEN

    ## TEST ADDING SPOTIFY ID TO ARTIST TABLE
    def test_adding_spotify_id_to_db(self):
        # add column if not there for pipeline/ add to initial db
        # GIVEN - 

        # WHEN - 

        # THEN - 
        pass

    ## TEST PORTAL ROUTE

    ## TEST LOGGING IN ROUTE

    ## TEST GET SPOTIFY DATA ROUTE
    # ultimately returns placeholder data jsonified {'data': 'placeholder'}

    ## 

if __name__=="__main__":
    unittest.main()