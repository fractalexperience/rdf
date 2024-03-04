import os
import json
from common import dbconfig
from common import util
from common.rdfschema import RdfSchema
from common.rdfengine import RdfEngine
from common.sqlengine import SqlEngine


location = os.path.join(os.getcwd(), '..', 'assets', 'schema.json')
sh = RdfSchema(location)
sqleng = SqlEngine(
    db_host=dbconfig.DB_HOST, db_name=dbconfig.DB_NAME, db_user=dbconfig.DB_USER, db_pass=dbconfig.DB_PASS,
    ssh_host=dbconfig.SSH_HOST, ssh_user=dbconfig.DB_USER, ssh_pass=dbconfig.SSH_PASS,
    ssh_bind_addr=dbconfig.SSH_BIND_ADDRESS)
rdfeng = RdfEngine(sh, sqleng)
tn = 'root'

# Get definition of a specific user
obj = rdfeng.o_read(tn, util.get_sha1('user.admin'))
print(json.dumps(obj, indent=4))
org = rdfeng.o_read(tn, '1')
print(json.dumps(org, indent=4))

# # Create an enumeration of type "Location"
# tn = 'db0002'
# rdfeng.o_save(tn, 'inventory_location', {'Name': 'Basel'})
# rdfeng.o_save(tn, 'inventory_location', {'Name': 'Zurich'})
# rdfeng.o_save(tn, 'inventory_location', {'Name': 'Bern'})
# rdfeng.o_save(tn, 'inventory_location', {'Name': 'Locarno'})
# rdfeng.o_save(tn, 'inventory_location', {'Name': 'Geneva'})
# # Update with the same name - should not duplicate the object
# rdfeng.o_save(tn, 'inventory_location', {'Name': 'Geneva'})
# # List locations
# locations = rdfeng.o_list(tn, 'inventory_location')
# print(json.dumps(locations, indent=4))
# # Delete the second enumeration (Zurich) by passing the hash code externally generated
# # (Because the only property "Name" of the enumeration is the key)
# result = rdfeng.o_delete(tn, util.get_sha1('inventory_location.Zurich'))
# print(result)
# obj = rdfeng.o_read(tn, util.get_sha1('inventory_location.Bern'))
# print(json.dumps(obj, indent=4))


#
# org_id = rdfeng.get_autoincrement_id(tblname, 'Organization', None, 'org', None)
# print(org_id)
#
# db_id = rdfeng.get_autoincrement_id(tblname, 'Organization', 'Database', 'db')
# print(db_id)

# print(rdfeng.r_data(tblname, 0, 100))
# Read specific object
# obj = rdfeng.o_read(tblname, '3d53b6fb7d14c5208664bea22164d68ede2c294c')
# print(json.dumps(obj, indent=4))

# # List all organizations
# objects = rdfeng.o_list(tblname, 'org')
# print(json.dumps(objects, indent=4))

# # List all users
# objects = rdfeng.list_objects(tblname, 'user')
# print(json.dumps(objects, indent=4))


# tbl = eng.exec_table('SHOW TABLES')
# print(tbl)
# tbl = eng.exec_table('SELECT * FROM reg')
# for row in tbl:
#     print(row)
