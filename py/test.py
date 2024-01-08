import os
import json
from common import dbconfig
from common.rdfschema import RdfSchema
from common.rdfengine import RdfEngine
from common.sqlengine import SqlEngine


location = os.path.join(os.getcwd(), '..', 'assets', 'schema.json')
sh = RdfSchema(location)
sqleng = SqlEngine(
    db_host=dbconfig.DB_HOST, db_name=dbconfig.DB_NAME, db_user=dbconfig.DB_USER, db_pass=dbconfig.DB_PASS)
rdfeng = RdfEngine(sh, sqleng)
tblname = 'root'

obj = rdfeng.read_object(tblname, 'ca56656811568c780a1b57213fbd0b61b1f17278')
print(json.dumps(obj, indent=4))

# # List all organizations
# objects = rdfeng.list_objects(tblname, 'org')
# print(json.dumps(objects, indent=4))
# # List all users
# objects = rdfeng.list_objects(tblname, 'user')
# print(json.dumps(objects, indent=4))


# tbl = eng.exec_table('SHOW TABLES')
# print(tbl)
# tbl = eng.exec_table('SELECT * FROM reg')
# for row in tbl:
#     print(row)
