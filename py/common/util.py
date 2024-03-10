import hashlib

dom_hex = set('0123456789abcdef')


def get_sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def is_sha1(s):
    return len(s) == 40 and len(set(s) - dom_hex) == 0

