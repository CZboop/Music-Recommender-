import re

class PasswordValidator:
    def __init__(self, password):
        self.password = password

    def is_valid(self):
        if len(self.password) < 8:
            return False
        if not any([i in self.password for i in "!?@*&%$#_"]):
            return False
        if not any([i.lower() == i for i in self.password]):
            return False
        if not any([i.upper() == i for i in self.password]):
            return False
        if not any([i.isdigit() for i in self.password]):
            return False
        return True
