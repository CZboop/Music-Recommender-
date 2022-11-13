import unittest
from unittest.mock import Mock, patch
from app import app
from app.functions import authenticate, get_db_connection, create_token, store_token_user_info, get_username_from_token, get_artists_rated, get_user_from_name, get_all_artists, get_all_artist_ids, rating_artist, get_past_recs, is_artist_rated, get_highest_user_id, get_artist_link_from_id, get_artist_id_from_name
import datetime as dt
import jwt, os
from db.db_access import setup_tables, add_starter_data_to_db

class TestSpotifyIntegration(unittest.TestCase):

    ### TESTING FUNCTIONS THAT USE EXTERNAL SPOTIFY API

    maxDiff = None

    ## TEST CAN GET SPOTIFY RECENTLY PLAYED

    ## TEST CAN GET SPOTIFY TOP ARTISTS
    def test_sptoify_top_artists_adds_ratings_for_current_user(self):
        pass

    ## TEST CAN ADD RATINGS FOR SPOTIFY ARTISTS
    # should abstract token in session check from this func?
    # adds if not in db already
    # doesn't add if already in db
    # adds rating 

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