import unittest
from api_main import app

class TestRoutes(unittest.TestCase):

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

    def test_welcome_without_login_gives_redirect_status(self):
        client = app.test_client(self)
        response = client.get('/welcome')
        status_code = response.status_code

        self.assertEqual(status_code, 302)
    # TODO: add test for when user in session

    def test_success_gives_200_status(self):
        client = app.test_client(self)
        response = client.get('/success')
        status_code = response.status_code

        self.assertEqual(status_code, 200)

    def test_spotify_portal_gives_redirect_status(self):
        client = app.test_client(self)
        response = client.get('/portal')
        status_code = response.status_code

        self.assertEqual(status_code, 302)

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

    # TODO: test remaining add-spotify-info route that needs to mock/ use session storage
    # TODO: test other methods for routes that have both get and post

if __name__ == "__main__":
    unittest.main()