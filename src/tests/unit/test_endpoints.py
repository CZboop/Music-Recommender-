import unittest, pytest
from app import app

# @pytest.mark.skip(reason="temp skipping for speed on new tests")
class TestRouteStatuses(unittest.TestCase):

    ### TESTING THE STATUS CODES FOR EACH ENDPOINT ###

    def test_home_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_invalid_endpoint_gives_404(self):
        client = app.test_client(self)
        response = client.get('/bla')
        status_code = response.status_code

        self.assertEqual(status_code, 404)

    def test_welcome_without_login_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/welcome')
        status_code = response.status_code

        self.assertEqual(status_code, 200)
    # TODO: add test for when user in session

    def test_success_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/success')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_spotify_portal_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/portal')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_add_artist_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/add-artist')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_rate_artist_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/rate-artist')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_update_rated_gives_200_status(self):
        client = app.test_client(self)
        response = client.post('/update-rated')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_recommend_gives_200_status(self):
        client = app.test_client(self)
        response = client.post('/recommend')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_recommendations_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/recommendations')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_sign_up_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/sign-up')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_login_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/login')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_logging_in_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/logging-in')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_logout_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/log-out')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

class TestRouteResponseTypes(unittest.TestCase):

    ### TESTING CONTENT TYPE FOR EACH ROUTE ###

    def test_home_content_type(self):
        client = app.test_client(self)
        response = client.get('/')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_404_content_type(self):
        client = app.test_client(self)
        response = client.get('/bla')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_welcome_content_type(self):
        client = app.test_client(self)
        response = client.get('/welcome')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_success_content_type(self):
        client = app.test_client(self)
        response = client.get('/success')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_spotify_portal_content_type(self):
        client = app.test_client(self)
        response = client.get('/portal')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_add_artist_content_type(self):
        client = app.test_client(self)
        response = client.get('/add-artist')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_rate_artist_content_type(self):
        client = app.test_client(self)
        response = client.get('/rate-artist')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_update_rated_content_type(self):
        client = app.test_client(self)
        response = client.get('/update-rated')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    # recommend
    def test_recommend_content_type(self):
        client = app.test_client(self)
        response = client.get('/recommend')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
    # recommendations
    def test_recommendations_content_type(self):
        client = app.test_client(self)
        response = client.get('/recommendations')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
    
    def test_sing_up_content_type(self):
        client = app.test_client(self)
        response = client.get('/sign-up')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
    
    def test_login_content_type(self):
        client = app.test_client(self)
        response = client.get('/login')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
    
    def test_logging_in_content_type(self):
        client = app.test_client(self)
        response = client.get('/logging-in')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

    def test_log_out_content_type(self):
        client = app.test_client(self)
        response = client.get('/log-out')
        self.assertEqual(response.content_type, "text/html; charset=utf-8")

if __name__ == "__main__":
    unittest.main()