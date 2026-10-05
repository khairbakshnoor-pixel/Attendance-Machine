"""Password hashing, bounded login throttling, and safe spreadsheet exports."""
import base64
import hashlib
import hmac
import secrets
import threading
import time


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Use a password with at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt, expected = encoded.split("$")
        if scheme != "scrypt" or len(password) > 1024:
            return False
        result = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt, validate=True), n=16384, r=8, p=1)
        return hmac.compare_digest(result, base64.b64decode(expected, validate=True))
    except (ValueError, TypeError):
        return False


class LoginLimiter:
    """One local admin account: throttle across browser sessions within this process."""
    def __init__(self):
        self.failures = []
        self.lock = threading.Lock()

    def attempt(self, password: str, encoded: str) -> tuple[bool, str]:
        with self.lock:
            now = time.monotonic()
            self.failures = [stamp for stamp in self.failures if now - stamp < 300]
            if len(self.failures) >= 5:
                return False, "Too many attempts. Wait five minutes before trying again."
            if verify_password(password, encoded):
                self.failures.clear()
                return True, ""
            self.failures.append(now)
            return False, "Incorrect password."


def csv_safe(value):
    """Prevent names/IDs from becoming spreadsheet formulas when CSV is opened."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value
