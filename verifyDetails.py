import re

class VerifyDetails:
    
    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password
        
    def verifyName(self):
        pattern = re.compile(r"^(?![\s.]+$)[a-zA-Z\s.]*$")
        return self.verifyRegex(pattern, self.name)
    
    def verifyEmail(self):
        pattern = re.compile(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        return self.verifyRegex(pattern, self.email)
            
    def verifyPassword(self):
        pattern = re.compile(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$")
        return self.verifyRegex(pattern, self.password)
    
    def verifyRegex(self, pattern, string):
        result = re.match(pattern, string)

        if result:
            return True
        else:
            return False
