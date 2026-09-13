import secrets

ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
LENGTH = 6  # or wherever LENGTH is defined

def generate_short_code():
    return "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))