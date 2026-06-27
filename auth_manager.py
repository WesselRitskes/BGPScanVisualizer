import secrets
import string
import hashlib
import hmac
import time
import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()
sessions = {}

import os
from dotenv import load_dotenv
load_dotenv()

admin_hash = os.getenv('ADMIN_KEY_HASH')
username_secret = os.getenv('USERNAME_SECRET').encode()
db_uri = os.getenv("DB_URI")


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
    password_hash = _load_credentials(username_hash)

    if not password_hash:
        return False

    try:
        if ph.verify(password_hash, password):
            return True
    except VerifyMismatchError:
        return False


def gen_credentials(username, admin_key):
    if not ph.verify(admin_hash, admin_key):
        raise KeyError("Incorrect admin key")

    username_hash = gen_username_hash(username)
    password = gen_password()
    password_hash = ph.hash(password)

    _save_credentials(username_hash, password_hash)

    return password


def del_credentials(username, admin_key):
    if not ph.verify(admin_hash, admin_key):
        raise KeyError("Incorrect admin key")

    username_hash = gen_username_hash(username)

    _delete_credentials(username_hash)


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


def _load_credentials(username_hash):
    with psycopg.connect(db_uri, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM credentials WHERE username_hash = %s;", [username_hash])
            rows = cur.fetchall()

            if len(rows) >= 1:
                return rows[0][0]


def _save_credentials(username_hash, password_hash):
    with psycopg.connect(db_uri, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO credentials (username_hash, password_hash) 
                VALUES (%s, %s)
                ON CONFLICT (username_hash) 
                DO UPDATE SET password_hash = EXCLUDED.password_hash;
                """, (username_hash, password_hash))


def _delete_credentials(username_hash):
    with psycopg.connect(db_uri, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM credentials WHERE username_hash = %s;",
                [username_hash]
            )