import unittest
from app.validator import PasswordValidator, EmailValidator, UsernameValidator

class TestValidators(unittest.TestCase):

    ### TEST PASSWORD VALIDATOR

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

    def test_password_validator_no_nums_returns_false(self):
        validator = PasswordValidator('P@SSWORDpassword!')
        actual = validator.is_valid()
        self.assertFalse(actual)

    def test_password_validator_no_special_chars_returns_false(self):
        validator = PasswordValidator('PASSWORDpassword1234')
        actual = validator.is_valid()
        self.assertFalse(actual)

    def test_password_validator_empty_String_returns_false(self):
        validator = PasswordValidator('')
        actual = validator.is_valid()
        self.assertFalse(actual)

    ### TEST EMAIL VALIDATOR

    def test_email_validator_valid_dot_com_returns_true(self):
        validator = EmailValidator('example_email@email.com')
        actual = validator.is_email_valid()
        self.assertTrue(actual)

    def test_email_validator_valid_dot_co_dot_uk_returns_true(self):
        validator = EmailValidator('example_email@email.co.uk')
        actual = validator.is_email_valid()
        self.assertTrue(actual)

    def test_email_validator_valid_no_at_returns_false(self):
        validator = EmailValidator('example_emailatemail.com')
        actual = validator.is_email_valid()
        self.assertFalse(actual)

    def test_email_validator_valid_no_dot_returns_false(self):
        validator = EmailValidator('example_email@emaildotcom')
        actual = validator.is_email_valid()
        self.assertFalse(actual)

    # TODO: test with db connection
    def test_email_validator_already_in_use_returns_false(self):
        validator = EmailValidator('example_email@emaildotcom')
        actual = validator.is_email_valid()
        self.assertFalse(actual)

    ### TEST USERNAME VALIDATOR

    def test_username_not_in_use_returns_true(self):
        pass

    def test_username_already_in_use_return_false(self):
        pass

if __name__=="__main__":
    unittest.main()