import unittest
from app.models import Recommender

class TestModelMaking(unittest.TestCase):

    ### TESTING ML MODEL BASIC FUNCTIONALITY
    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'testuser'
        os.environ['DB_PASSWORD'] = ''
        setup_tables()

    def test_can_create_object_of_type_als_model(self):
        undertest = Recommender()
        actual = type(undertest).__name__
        expected = ALSModel
        self.assertEqual(expected, actual)

if __name__=="__main__":
    unittest.main()