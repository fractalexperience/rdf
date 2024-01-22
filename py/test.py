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


#
# org_id = rdfeng.get_autoincrement_id(tblname, 'Organization', None, 'org', None)
# print(org_id)
#
# db_id = rdfeng.get_autoincrement_id(tblname, 'Organization', 'Database', 'db')
# print(db_id)

# print(rdfeng.r_data(tblname, 0, 100))
#
# obj = rdfeng.read_object(tblname, '5ce5e7683d301384b484717fc35ebb4dbd74a45d')
# print(json.dumps(obj, indent=4))

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
