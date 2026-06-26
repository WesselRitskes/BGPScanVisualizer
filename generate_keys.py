import secrets
from argon2 import PasswordHasher

ph = PasswordHasher()
generated_admin_key = secrets.token_hex(32)

print(f"Admin Key: {generated_admin_key}")
print(f"ADMIN_KEY_HASH={ph.hash(generated_admin_key)}")
print(f"USERNAME_SECRET={secrets.token_hex(32)}")