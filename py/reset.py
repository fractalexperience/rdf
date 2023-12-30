import os
from rdf.py.common.rdfengine import RdfEngine
from rdf.py.common.rdfschema import RdfSchema
import rdf.py.common.dbconfig as dbconfig
from rdf.py.common.sqlengine import SqlEngine

location = os.path.join(os.getcwd(), '..', 'assets', 'schema.json')
sh = RdfSchema(location)
if sh.errors:
    print('Errors found in shcma: ')
    print('\n'.join(sh.errors))
    exit()

sqleng = SqlEngine(
    db_host=dbconfig.DB_HOST, db_name=dbconfig.DB_NAME, db_user=dbconfig.DB_USER, db_pass=dbconfig.DB_PASS)

rdfeng = RdfEngine(sh, sqleng)
rdfeng.reset_rdf_table('root')
