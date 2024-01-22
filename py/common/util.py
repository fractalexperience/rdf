import hashlib


def get_sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()

