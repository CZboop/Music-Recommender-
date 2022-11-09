import unittest
from app.validator import PasswordValidator, EmailValidator, UsernameValidator

class TestValidators(unittest.TestCase):

    ### TEST VALIDATORS

    def test_password_validator_length(self):
        actual = None
        expected = None
        self.assertEqual(expected, actual)

    def test_password_validator_uppercase(self):
        actual = None
        expected = None
        self.assertEqual(expected, actual)

if __name__=="__main__":
    unittest.main()