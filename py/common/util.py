import hashlib
import rdf.py.common.config

def get_sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()

