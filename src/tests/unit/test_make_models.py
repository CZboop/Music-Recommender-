import unittest
from app.models import Recommender, Model
from db.db_access import setup_tables
import os

class TestModelMaking(unittest.TestCase):

    ### TESTING ML MODEL BASIC FUNCTIONALITY
    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'testuser'
        os.environ['DB_PASSWORD'] = ''
        setup_tables()

    # TODO: fix error when trying to test (cannot infer schema from empty dataset)
    # def test_can_create_object_of_type_als_model_when_loading_trained_model(self):
    #     undertest = Recommender(model_path='../app/models/trained_model')
    #     actual = type(undertest).__name__
    #     expected = 'ALSModel'
    #     self.assertEqual(expected, actual)

    # def test_model_created_has_recommend_functionality(self):
    #     undertest = Recommender(model_path='../app/models/trained_model')
    #     rec_method = getattr(undertest, 'recommend_subset', None)
    #     self.assertTrue(callable(rec_method))

if __name__=="__main__":
    unittest.main()