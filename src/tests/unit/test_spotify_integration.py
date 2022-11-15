import unittest
from unittest.mock import Mock, patch
import requests
from app import app, functions
from app.functions import authenticate, get_db_connection, create_token, store_token_user_info, get_username_from_token, get_artists_rated, get_user_from_name, get_all_artists, get_all_artist_ids, rating_artist, get_past_recs, is_artist_rated, get_highest_user_id, get_artist_link_from_id, get_artist_id_from_name, get_spotify_top
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

    def test_spotify_top_artists_adds_artist_ratings(self):
        pass

    ## TEST CAN ADD RATINGS FOR SPOTIFY ARTISTS
    # def test_add_ratings_from_spotify_returns_false_if_no_user(self):
    #     pass
    #     # GIVEN - session has no user key and some artists

    #     # WHEN - we call the add ratings from spotify func
    #     result = add_ratings_for_spotify_artists()

    #     # THEN - false is returneds
    #     self.assertFalse(result)

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
    # returns false if not found in db

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
        # ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name INTEGER;

        # WHEN - 

        # THEN - 
        pass

if __name__=="__main__":
    unittest.main()