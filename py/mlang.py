import re
import os
import json
import pandas as pd
from common.rdfschema import RdfSchema
import common.util as util


def upd_kwd(keywords, kw, en='', de='', fr='', it=''):
    d = keywords.setdefault(kw, {})
    if 'en' not in d:
        d['en'] = en
    if 'de' not in d:
        d['de'] = de
    if 'fr' not in d:
        d['fr'] = fr
    if 'it' not in d:
        d['it'] = it


def process_path(path, pattern, types, keywords):
    w = os.walk(path)
    for (dirpath, dirnames, filenames) in w:
        for filename in filenames:
            ext = filename.split('.')[-1]
            if ext not in types:
                continue
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r') as f:
                s = f.read()
                lst = pattern.findall(s)
                for kw in lst:
                    print(kw)
                    upd_kwd(keywords, kw, en='', de='', fr='', it='')


mlang_file = os.path.join(os.getcwd(), '..', 'assets', 'mlang.json')
with open(mlang_file, 'r', encoding="utf-8") as f:
    keywords = json.load(f)
types = {'html', 'py', 'js'}
pattern = re.compile('mlang="(\\w+)"+')
process_path(os.path.join(os.getcwd(), '..', 'py'), pattern, types, keywords)
process_path(os.path.join(os.getcwd(), '..', 'js'), pattern, types, keywords)
process_path(os.path.join(os.getcwd(), '..', 'html'), pattern, types, keywords)

schema_file = os.path.join(os.getcwd(), '..', 'assets', 'schema.json')
schema = RdfSchema(schema_file)
for code, cdef in schema.classes.items():
    upd_kwd(keywords, util.to_snakecase(cdef.name), en=cdef.name)
    if not cdef.members:
        continue
    for ndx, mem in cdef.members.items():
        upd_kwd(keywords, util.to_snakecase(mem.name), en=mem.name)

with open(mlang_file, 'w') as f:
    json.dump(keywords, f)

m = []
heading = ['key', 'en', 'de', 'fr', 'it']
m.append(heading)
for k, lst in keywords.items():
    m.append([k, lst.get('en'), lst.get('de'), lst.get('fr'), lst.get('it')])
df = pd.DataFrame(m)

mlang_file = os.path.join(os.getcwd(), '..', 'assets', 'mlang.csv')
df.to_csv(mlang_file, header=False, index=False)
mlang_xlsx = os.path.join(os.getcwd(), '..', 'assets', 'mlang.xlsx')
df.to_excel(mlang_xlsx, header=False, index=False)

