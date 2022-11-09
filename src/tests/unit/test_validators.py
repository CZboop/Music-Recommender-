import unittest
from app.validator import PasswordValidator, EmailValidator, UsernameValidator

class TestValidators(unittest.TestCase):

    ### TEST VALIDATORS

    def test_validator(self):
        actual = None
        expected = None
        self.assertEqual(expected, actual)

if __name__=="__main__":
    unittest.main()