import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

def generate_keys():
    private_key=rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key=private_key.public_key()
    return private_key, public_key

def serialize_public_key(public_key):
    pem=public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

def load_public_key(pem_data):
    public_key=serialization.load_pem_public_key(
        pem_data.encode('utf-8')
    )
    return public_key

def serialize_private_key(private_key):
    pem=private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('utf-8')

def load_private_key(pem_data):
    private_key=serialization.load_pem_private_key(
        pem_data.encode('utf-8'),
        password=None
    )
    return private_key

def encrypt_message(message, public_key):
    encrypted_bytes=public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def decrypt_message(encrypted_message, private_key):
    encrypted_bytes=base64.b64decode(encrypted_message)
    original_message=private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return original_message.decode('utf-8')

