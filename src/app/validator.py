import re
import psycopg2
import os

class PasswordValidator:
    def __init__(self, password):
        self.password = password

    def is_valid(self):
        if len(self.password) < 8:
            return False
        if not any([i in self.password for i in "!?@*&%$#_"]):
            return False
        if not any([i.isupper() for i in self.password]):
            return False
        if not any([i.islower() for i in self.password]):
            return False
        if not any([i.isdigit() for i in self.password]):
            return False
        return True

class UsernameValidator:
    def __init__(self, username):
        self.username = username

    def get_db_connection(self):
        self.conn = psycopg2.connect(host='localhost',
                                database='recommend',
                                user=os.environ['DB_USERNAME'],
                                password=os.environ['DB_PASSWORD'])
        return self.conn

    def is_username_in_use(self):
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE name = '{self.username}';")
        matching_users = cur.fetchall()
        cur.close()
        conn.close()
        return False if not matching_users else True

class EmailValidator:
    def __init__(self, email):
        self.email = email

    def get_db_connection(self):
        self.conn = psycopg2.connect(host='localhost',
                                database='recommend',
                                user=os.environ['DB_USERNAME'],
                                password=os.environ['DB_PASSWORD'])
        return self.conn

    def is_email_in_use(self):
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE email = '{self.email}';")
        matching_emails = cur.fetchall()
        cur.close()
        conn.close()
        return False if not matching_emails else True

    def is_email_valid(self):
        pattern = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        return re.fullmatch(pattern, self.email)
