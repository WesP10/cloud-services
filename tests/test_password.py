import bcrypt

# Test the stored hashes
stored_hash_admin = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYWv/G/L8WC"
stored_hash_dev = "$2b$12$gPJKGpPWPLWjJ5VLjHJ6aO7L8hYE8XpJQnZ0yGvYhY0lGKGkH0YqO"

password_admin = "admin123"
password_dev = "dev123"

print("Testing admin password:")
try:
    password_bytes = password_admin.encode('utf-8')[:72]
    hashed_bytes = stored_hash_admin.encode('utf-8')
    result = bcrypt.checkpw(password_bytes, hashed_bytes)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

print("\nTesting dev password:")
try:
    password_bytes = password_dev.encode('utf-8')[:72]
    hashed_bytes = stored_hash_dev.encode('utf-8')
    result = bcrypt.checkpw(password_bytes, hashed_bytes)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

print("\nGenerating new valid hashes (no plaintext shown):")
print(f"admin hash: {bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')}")
print(f"developer hash: {bcrypt.hashpw(b'dev123', bcrypt.gensalt()).decode('utf-8')}")
