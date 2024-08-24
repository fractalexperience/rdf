import hashlib
import datetime
import re


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


def get_id_sha1():
    return get_sha1(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))


def to_camelcase(s):
    pattern = r'(_|-|/|\\|\?)+'
    s = re.sub(pattern, " ", s).title().replace(" ", "").replace("*", "")
    return ''.join([s[0].lower(), s[1:]])


def to_snakecase(s):
    if not s:
        return ''
    delimiters = {'_', '-', '?', '/', '\\', ':', ';', '.', ','}
    for d in delimiters:
        s = s.replace(d, ' ')
    lst = s.split(' ')
    return '_'.join([p.lower() for p in lst if p != ''])
