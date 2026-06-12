from cryptography.fernet import Fernet
from .config import settings
import base64

# It's crucial that APP_SECRET_KEY is a 32-byte URL-safe base64-encoded key.
# We'll generate one if the default is used, but this should be set in production.
try:
    key = base64.urlsafe_b64decode(settings.APP_SECRET_KEY)
except:
    key = Fernet.generate_key()

cipher_suite = Fernet(key)

def encrypt_data(data: str) -> bytes:
    return cipher_suite.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    return cipher_suite.decrypt(encrypted_data).decode()