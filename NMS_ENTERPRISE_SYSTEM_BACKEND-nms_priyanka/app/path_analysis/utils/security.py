import os
from cryptography.fernet import Fernet, MultiFernet
from dotenv import load_dotenv

load_dotenv()

# ✅ NEW: multi-key loader for rotation support
def _load_fernet() -> MultiFernet:
    keys = []

    # load versioned keys
    for i in range(1, 10):
        k = os.getenv(f"SECRET_KEY_v{i}")
        if k:
            keys.append(Fernet(k.encode()))

    # primary key (used for encryption)
    primary = os.getenv("SECRET_KEY")
    if primary:
        keys.insert(0, Fernet(primary.encode()))

    if not keys:
        raise ValueError("SECRET_KEY not set in .env")

    return MultiFernet(keys)


# ✅ REPLACED single key cipher with multi-key cipher
cipher = _load_fernet()


def encrypt_password(password: str) -> str:
    encrypted = cipher.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    decrypted = cipher.decrypt(encrypted_password.encode())
    return decrypted.decode()