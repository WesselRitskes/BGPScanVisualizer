import secrets
import string
import json
import hashlib
import hmac
import time
from argon2 import PasswordHasher
from pathlib import Path

from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()
credentials_file = Path("credentials.json")
sessions = {}
# Consider storing in a real database

import os
from dotenv import load_dotenv
load_dotenv()

admin_hash = os.getenv('ADMIN_KEY_HASH')
username_secret = os.getenv('USERNAME_SECRET').encode()


def authenticate_session(token):
    expires = sessions.get(token)

    if expires is None:
        return False

    if expires < time.time():
        sessions.pop(token, None)
        return False

    return True


def authenticate_user(username, password):
    username_hash = gen_username_hash(username)

    data = _load_credentials()

    if username_hash not in data.keys():
        return False

    try:
        if ph.verify(data[username_hash], password):
            return True
    except VerifyMismatchError:
        return False


def gen_credentials(username, admin_key):
    if not ph.verify(admin_hash, admin_key):
        raise KeyError("Incorrect admin key")

    username_hash = gen_username_hash(username)
    password = gen_password()
    password_hash = ph.hash(password)

    data = _load_credentials()

    data[username_hash] = password_hash

    _save_credentials(data)

    return password


def del_credentials(username, admin_key):
    if not ph.verify(admin_hash, admin_key):
        raise KeyError("Incorrect admin key")

    username_hash = gen_username_hash(username)

    data = _load_credentials()
    data.pop(username_hash)

    _save_credentials(data)


def gen_password(length=20):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def gen_username_hash(username):
    username = username.strip().lower()
    return hmac.new(
        username_secret,
        username.encode(),
        hashlib.sha256
    ).hexdigest()


def gen_session():
    token = secrets.token_urlsafe(32)
    sessions[token] = time.time() + 86400
    return token


def del_session(token):
    if token is not None:
        sessions.pop(token, None)


def _load_credentials():
    if not credentials_file.exists():
        _save_credentials({})
        return {}

    with credentials_file.open('r') as f:
        return json.load(f)


def _save_credentials(data):
    with credentials_file.open('w') as f:
        json.dump(data, f, indent=4)