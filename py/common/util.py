import hashlib

dom_hex = set('0123456789abcdef')


def get_sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def is_sha1(s):
    return s and len(s) == 40 and len(set(s) - dom_hex) == 0


def escape_xml(s):
    if not (isinstance(s, str) or isinstance(s, float) or isinstance(s, int)):
        return ''
    if isinstance(s, int) or isinstance(s, float):
        return escape_xml(f'{s}')
    return '' if not s else s \
        .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') \
        .replace("'", '&apos;').replace('"', '&quot;')


