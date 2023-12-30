import hashlib
import config

def get_sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()

