import unittest
from app.validator import PasswordValidator, EmailValidator, UsernameValidator

class TestValidators(unittest.TestCase):

    ### TEST VALIDATORS

    def test_password_validator_valid_returns_true(self):
        validator = PasswordValidator('T3stP@ssword123')
        actual = validator.is_valid()
        self.assertTrue(actual)

    def test_password_validator_low_length_returns_false(self):
        validator = PasswordValidator('P@s1')
        actual = validator.is_valid()
        self.assertFalse(actual)

    def test_password_validator_no_uppercase_returns_false(self):
        validator = PasswordValidator('p@ssword12345!')
        actual = validator.is_valid()
        self.assertFalse(actual)
    
    def test_password_validator_no_lowercase_returns_false(self):
        validator = PasswordValidator('P@SSWORD12345!')
        actual = validator.is_valid()
        self.assertFalse(actual)

if __name__=="__main__":
    unittest.main()