import os
import base64
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

ITERATIONS = 200_000
KEY_LEN = 32  # 256-bit

def gen_salt() -> bytes:
    return get_random_bytes(16)

def save_salt_for(username: str, salt: bytes, path=".") -> str:
    fn = os.path.join(path, f"key_salt_{username}.bin")
    with open(fn, "wb") as f:
        f.write(salt)
    return fn

def load_salt_for(username: str, path=".") -> bytes:
    fn = os.path.join(path, f"key_salt_{username}.bin")
    if not os.path.exists(fn):
        return None
    with open(fn, "rb") as f:
        return f.read()

def derive_key(passphrase: str, salt: bytes) -> bytes:
    # PyCryptodome PBKDF2
    return PBKDF2(passphrase, salt, dkLen=KEY_LEN, count=ITERATIONS, hmac_hash_module=SHA256)

def encrypt_bytes(plaintext: bytes, key: bytes) -> (str, str):
    # AES GCM
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(plaintext)
    
    # Provide compatibility with cryptography lib (ct + tag)
    full_ct = ct + tag
    
    return base64.b64encode(full_ct).decode(), base64.b64encode(nonce).decode()

def decrypt_bytes(ct_b64: str, nonce_b64: str, key: bytes) -> bytes:
    ct_full = base64.b64decode(ct_b64)
    nonce = base64.b64decode(nonce_b64)
    
    # Split tag (last 16 bytes) and ciphertext
    tag = ct_full[-16:]
    ciphertext = ct_full[:-16]
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)