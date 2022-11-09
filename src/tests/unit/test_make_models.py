import unittest
from app.models import Recommender

class TestModelMaking(unittest.TestCase):

    ### TESTING ML MODEL BASIC FUNCTIONALITY

    def test_can_create_als_model(self):
        
        actual = None
        expected = None
        self.assertEqual(expected, actual)

if __name__=="__main__":
    unittest.main()