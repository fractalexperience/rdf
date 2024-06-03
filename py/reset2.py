import os
from common.rdfengine import RdfEngine
from common.rdfschema import RdfSchema
import common.dbconfig as dbconfig
from common.sqlengine import SqlEngine
import common.util as util
from common.rdfcms import RdfCms

location = os.path.join(os.getcwd(), '..', 'assets', 'schema.json')
sh = RdfSchema(location)
if sh.errors:
    print('Errors found in shcma: ')
    print('\n'.join(sh.errors))
    exit()

sqleng = SqlEngine(
    db_host=dbconfig.DB_HOST, db_name=dbconfig.DB_NAME, db_user=dbconfig.DB_USER, db_pass=dbconfig.DB_PASS,
    ssh_host=dbconfig.SSH_HOST, ssh_user=dbconfig.DB_USER, ssh_pass=dbconfig.SSH_PASS,
    ssh_bind_addr=dbconfig.SSH_BIND_ADDRESS)
rdfeng = RdfEngine(sh, sqleng)
cms = RdfCms(sh, sqleng)

tn = 'root'
rdfeng.reset_rdf_table(tn)

# Organization, which owns the site
t = rdfeng.cms.o_instantiate(tn, 'org')
print(t)
org_id = t[0]
rdfeng.cms.o_add_property(tn, 'org', org_id, 'Name', None, 'Owner organization')
rdfeng.cms.o_add_property(tn, 'org', org_id, 'Description', None, 'Organization, which owns the website')
rdfeng.cms.o_add_property(tn, 'org', org_id, 'Database', None, 'root')
print('Created master organization', org_id)

t = rdfeng.cms.o_instantiate(tn, 'address')
addr_id = t[0]
print(t)
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Country', None, 'Owner address country')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Country', None, 'Owner address ZIP code')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'City', None, 'Owner address city')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Address line 1', None, 'Owner address line 1')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Address line 2', None, 'Owner address line 2')
t = rdfeng.cms.o_associate(tn, 'org', org_id, 'address', addr_id, 'Address')
print(t)

# Super admin
t = rdfeng.cms.o_instantiate(tn, 'user')
usr_id = t[0]
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Email', None, 'rdf@fractalexperience.com')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Name', None, 'Super Admin')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Username', None, 'sa')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Role', None, 'SA')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Password hash', None,  util.get_sha1('123'))
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Language', None,  'de')
print(t)
rdfeng.cms.o_associate(tn, 'user', usr_id, 'org', org_id, 'Organization')
print('Created super admin user for master organization =>', usr_id)

# Organization admin
t = rdfeng.cms.o_instantiate(tn, 'user')
usr_id = t[0]
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Email', None, 'ardmin.rdf@fractalexperience.com')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Name', None, 'Organization Admin')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Username', None, 'oa')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Role', None, 'OA')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Password hash', None,  util.get_sha1('123'))
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Language', None,  'en')
print(t)
rdfeng.cms.o_associate(tn, 'user', usr_id, 'org', org_id, 'Organization')
print('Created organization admin user for master organization =>', usr_id)

# Data contributor
t = rdfeng.cms.o_instantiate(tn, 'user')
usr_id = t[0]
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Email', None, 'conributor.rdf@fractalexperience.com')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Name', None, 'Data contributor')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Username', None, 'dc')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Role', None, 'DC')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Password hash', None,  util.get_sha1('123'))
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Language', None,  'bg')
print(t)
rdfeng.cms.o_associate(tn, 'user', usr_id, 'org', org_id, 'Organization')
print('Created data contributor user for master organization =>', usr_id)


# Demo Organization
t = rdfeng.cms.o_instantiate(tn, 'org')
print(t)
org_id = t[0]
rdfeng.cms.o_add_property(tn, 'org', org_id, 'Name', None, 'Demo organization')
rdfeng.cms.o_add_property(tn, 'org', org_id, 'Description', None, 'Organization account to be used for demonstrations')
print('Created demo organization', org_id)

demo_org_db = rdfeng.get_autoincrement_id(tn, 'Organization', 'Database', 'db', 4)
rdfeng.create_rdf_table(demo_org_db)
rdfeng.cms.o_add_property(tn, 'org', org_id, 'Database', None, demo_org_db)
print('Created database for demo organization => ', demo_org_db)

t = rdfeng.cms.o_instantiate(tn, 'address')
addr_id = t[0]
print(t)
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Country', None, 'Demo address country')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Country', None, 'Demo address ZIP code')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'City', None, 'Demo address city')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Address line 1', None, 'Demo address line 1')
rdfeng.cms.o_add_property(tn, 'address', addr_id, 'Address line 2', None, 'Demo address line 2')
t = rdfeng.cms.o_associate(tn, 'org', org_id, 'address', addr_id, 'Address')
print(t)
print('Created address for demo organization', addr_id, 'and associated with demo organization', org_id)

# Demo Organization admin
t = rdfeng.cms.o_instantiate(tn, 'user')
usr_id = t[0]
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Email', None, 'demo_ardmin.rdf@fractalexperience.com')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Name', None, 'Admin for demo organization')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Username', None, 'demo_oa')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Role', None, 'OA')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Password hash', None,  util.get_sha1('123'))
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Language', None,  'en')
print(t)
rdfeng.cms.o_associate(tn, 'user', usr_id, 'org', org_id, 'Organization')
print('Created organization admin user for demo organization =>', usr_id)


# Demo Organization daa contributor
t = rdfeng.cms.o_instantiate(tn, 'user')
usr_id = t[0]
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Email', None, 'demo_dc.rdf@fractalexperience.com')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Name', None, 'Data contributor for demo organization')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Username', None, 'demo_dc')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Role', None, 'DC')
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Password hash', None,  util.get_sha1('123'))
rdfeng.cms.o_add_property(tn, 'user', usr_id, 'Language', None,  'de')
print(t)
rdfeng.cms.o_associate(tn, 'user', usr_id, 'org', org_id, 'Organization')
print('Created data contributor user for demo organization =>', usr_id)


#
# data = {
#     'Name': 'Owner organization',
#     'Description': 'Organization, which owns the website',
#     'Database': tn,
#     'Address': {'Address line 1': 'Owner - address line 1',
#                 'Address line 2': 'Owner - address line 2',
#                 'City': 'Owner - city',
#                 'ZIP code': 'Owner - ZIP',
#                 'Country': 'Owner - Country'}
# }
#
# org_id = rdfeng.o_save(tn, 'org', data)
# print('Created master organization =>', org_id)

#
# data_sa = {
#     'Email': 'rdf@fractalexperience.com',
#     'Name': 'Super Admin',
#     'Username': 'sa',
#     'Organization': org_id,
#     'Role': 'SA',
#     'Password hash': util.get_sha1('123'),
#     'Language': 'de'
# }
# sa_id = rdfeng.o_save(tblname, 'user', data_sa)
# print('Created super admin user for master organization =>', sa_id)
#
# data_oa = {
#     'Email': 'ardmin.rdf@fractalexperience.com',
#     'Name': 'Organization Admin',
#     'Username': 'admin',
#     'Organization': org_id,
#     'Role': 'OA',
#     'Password hash': util.get_sha1('123'),
#     'Language': 'de'
# }
# oa_id = rdfeng.o_save(tblname, 'user', data_oa)
# print('Created organization admin user for master organization =>', oa_id)
#
# data_dc = {
#     'Email': 'contributor.rdf@fractalexperience.com',
#     'Name': 'Data contributor',
#     'Username': 'contributor',
#     'Organization': org_id,
#     'Role': 'DC',
#     'Password hash': util.get_sha1('123'),
#     'Language': 'de'
# }
# dc_id = rdfeng.o_save(tblname, 'user', data_dc)
# print('Created data contributor user for master organization =>', dc_id)
#
# # Demo organization
# demo_org_data = {
#     'Name': 'Demo organization',
#     'Description': 'Organization, to be used for test/demonstration',
#     'Address': {'Address line 1': 'Demo - address line 1',
#                 'Address line 2': 'Demo - address line 2',
#                 'City': 'Demo - city',
#                 'ZIP code': 'Demo - ZIP',
#                 'Country': 'Demo - Country'}
# }
# demo_org_id = rdfeng.o_save(tblname, 'org', demo_org_data)
# print('Created demo organization =>', demo_org_id)
# demo_org_db = rdfeng.get_autoincrement_id(tblname, 'Organization', 'Database', 'db', 4)
# print('Created database for demo organization => ', demo_org_db)
#
# rdfeng.create_rdf_table(demo_org_db)
# rdfeng.o_update(tblname, demo_org_id, {'Database': demo_org_db})
#
# data_oa = {
#     'Email': 'demo_ardmin.rdf@fractalexperience.com',
#     'Name': '   Demo organization Admin',
#     'Username': 'demo_oa',
#     'Organization': demo_org_id,
#     'Role': 'OA',
#     'Password hash': util.get_sha1('123'),
#     'Language': 'en'
# }
# demo_oa_id = rdfeng.o_save(tblname, 'user', data_oa)
# print('Created organization admin user for demo organization =>', demo_oa_id)
#
# data_dc = {
#     'Email': 'demo_contributor.rdf@fractalexperience.com',
#     'Name': 'Demo data contributor',
#     'Username': 'demo_dc',
#     'Organization': demo_org_id,
#     'Role': 'DC',
#     'Password hash': util.get_sha1('123'),
#     'Language': 'en'
# }
# demo_dc_id = rdfeng.o_save(tblname, 'user', data_dc)
# print('Created data contributor user for demo organization =>', demo_dc_id)
#
#
#
#
