import hashlib

dom_hex = set('0123456789abcdef')


def get_sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def is_sha1(s):
    return len(dom_hex - set(s)) == 0

