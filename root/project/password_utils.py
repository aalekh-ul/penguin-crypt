from argon2.low_level import hash_secret_raw, Type
import hashlib,re


def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True

def derive_key(password,salt):
    password = f'{password}'.encode('utf-8')
    salt = salt
    memory_cost = 65536   
    time_cost = 4           
    parallelism = 2       
    key_length = 32    

    key = hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=key_length,
        type=Type.ID  
    )
    key_hash = hashlib.sha512(key).hexdigest()
    return key_hash