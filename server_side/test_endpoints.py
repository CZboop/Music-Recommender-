import unittest
# import server_side
from api_main import app
# test each route gives 200 where expected

# test 404 for random url

# 
class TestRoutes(unittest.TestCase):

    def test_home(self):
        client = app.test_client(self)
        response = client.get('/')
        status_code = response.status_code

        self.assertEqual(status_code, 200)


if __name__ == "__main__":
    unittest.main()