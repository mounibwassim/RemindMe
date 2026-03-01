import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.crypto import derive_key, encrypt_bytes, decrypt_bytes, gen_salt

def verify_crypto():
    print("Testing PyCryptodome Implementation...")
    
    salt = gen_salt()
    print(f"Salt generated: {salt.hex()}")
    
    password = "test_password"
    key = derive_key(password, salt)
    print(f"Key derived: {key.hex()}")
    
    plaintext = b"Hello World"
    ct_b64, nonce_b64 = encrypt_bytes(plaintext, key)
    print(f"Encrypted: {ct_b64} (nonce: {nonce_b64})")
    
    decrypted = decrypt_bytes(ct_b64, nonce_b64, key)
    print(f"Decrypted: {decrypted}")
    
    if decrypted == plaintext:
        print("SUCCESS: Encryption/Decryption verified!")
    else:
        print("FAILURE: Decrypted text does not match!")

if __name__ == "__main__":
    verify_crypto()
