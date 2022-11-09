import unittest
from app import app
from app.functions import get_db_connection
import random, string, re
import os
from db.db_access import setup_tables

class TestRateArtistFunctionality(unittest.TestCase):

    ### TESTING THE ABILITY FOR USER TO RATE ARTISTS
    # mocking login which will test separately

    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'testuser'
        os.environ['DB_PASSWORD'] = ''
        setup_tables()

    def test_rating_artist_not_yet_rated_adds_to_db(self):
        pass

    def test_rating_artist_already_rated_updates_db(self):
        pass

if __name__=="__main__":
    unittest.main()