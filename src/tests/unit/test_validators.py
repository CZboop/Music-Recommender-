import unittest
from app.validator import PasswordValidator, EmailValidator, UsernameValidator
from app.functions import get_db_connection
from db.db_access import setup_tables
import os, random, string

class TestValidators(unittest.TestCase):

    ### ONE-TIME SETUP FOR DB CONNECTION

    @classmethod
    def setUpClass(cls):
        os.environ['DB_USERNAME'] = 'postgres'
        os.environ['DB_PASSWORD'] = 'password'
        setup_tables()

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

    def test_email_validator_already_in_use_returns_true_if_already_in_use(self):
        # GIVEN - we have added a user with a given email (adding directly into db)
        email = 'example@email.com'
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('test_user', 123, '{email}', crypt('P@ssword123', gen_salt('bf', 8)));")
        conn.commit()
        cur.close()
        conn.close()

        # WHEN - we try to validate that email
        validator = EmailValidator(email)

        # THEN - email is in use
        actual = validator.is_email_in_use()
        self.assertTrue(actual)

    ### TEST USERNAME VALIDATOR

    def test_username_in_use_returns_true(self):
        # GIVEN - we have added a user with a given username (adding directly into db)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users (name, id, email, password) VALUES ('test_user', 123, 'example@email.com', crypt('P@ssword123', gen_salt('bf', 8)));")
        conn.commit()
        cur.close()
        conn.close()

        # WHEN - we try to validate that username
        validator = UsernameValidator('test_user')

        # THEN - username is in use
        actual = validator.is_username_in_use()
        self.assertTrue(actual)

    def test_username_not_in_use_return_false(self):
        # GIVEN - a username not in the db
        username = 'test_' + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))

        # WHEN - we try to validate that username
        validator = UsernameValidator(username)

        # THEN - username is in use
        actual = validator.is_username_in_use()
        self.assertFalse(actual)

if __name__=="__main__":
    unittest.main()