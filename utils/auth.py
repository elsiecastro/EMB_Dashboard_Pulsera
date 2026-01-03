# utils/auth.py

USERS = {
    "monitor1": "1234",
    "admin": "admin123"
}

def authenticate(user, password):
    return USERS.get(user) == password
