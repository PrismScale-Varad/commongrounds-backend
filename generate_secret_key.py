import secrets

# Generate a 32-byte (256-bit) secret key and encode it in a URL-safe format
secret_key = secrets.token_urlsafe(64)
print(secret_key)
