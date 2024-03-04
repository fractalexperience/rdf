import os
from common.rdfengine import RdfEngine
from common.rdfschema import RdfSchema
import common.dbconfig as dbconfig
from common.sqlengine import SqlEngine
import common.util as util

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

tblname = 'root'

rdfeng = RdfEngine(sh, sqleng)

rdfeng.reset_rdf_table(tblname)

# Organization, which owns the site
data = {
    'Name': 'Owner organization',
    'Description': 'Organization, which owns the website',
    'Database': tblname,
    'Address': {'Address line 1': 'Owner - address line 1',
                'Address line 2': 'Owner - address line 2',
                'City': 'Owner - city',
                'ZIP code': 'Owner - ZIP',
                'Country': 'Owner - Country'}
}
org_id = rdfeng.o_save(tblname, 'org', data)
print('Created master organization =>', org_id)

data_sa = {
    'Email': 'rdf@fractalexperience.com',
    'Name': 'Super Admin',
    'Username': 'sa',
    'Organization': org_id,
    'Role': 'SA',
    'Password hash': util.get_sha1('123'),
    'Language': 'de'
}
sa_id = rdfeng.o_save(tblname, 'user', data_sa)
print('Created super admin user for master organization =>', sa_id)

data_oa = {
    'Email': 'ardmin.rdf@fractalexperience.com',
    'Name': 'Organization Admin',
    'Username': 'admin',
    'Organization': org_id,
    'Role': 'OA',
    'Password hash': util.get_sha1('123'),
    'Language': 'de'
}
oa_id = rdfeng.o_save(tblname, 'user', data_oa)
print('Created organization admin user for master organization =>', oa_id)

data_dc = {
    'Email': 'contributor.rdf@fractalexperience.com',
    'Name': 'Data contributor',
    'Username': 'contributor',
    'Organization': org_id,
    'Role': 'DC',
    'Password hash': util.get_sha1('123'),
    'Language': 'de'
}
dc_id = rdfeng.o_save(tblname, 'user', data_dc)
print('Created data contributor user for master organization =>', dc_id)

# Demo organization
demo_org_data = {
    'Name': 'Demo organization',
    'Description': 'Organization, to be used for test/demonstration',
    'Address': {'Address line 1': 'Demo - address line 1',
                'Address line 2': 'Demo - address line 2',
                'City': 'Demo - city',
                'ZIP code': 'Demo - ZIP',
                'Country': 'Demo - Country'}
}
demo_org_id = rdfeng.o_save(tblname, 'org', demo_org_data)
print('Created demo organization =>', demo_org_id)
demo_org_db = rdfeng.get_autoincrement_id(tblname, 'Organization', 'Database', 'db', 4)
print('Created database for demo organization => ', demo_org_db)

rdfeng.create_rdf_table(demo_org_db)
rdfeng.o_update(tblname, demo_org_id, {'Database': demo_org_db})

data_oa = {
    'Email': 'demo_ardmin.rdf@fractalexperience.com',
    'Name': '   Demo organization Admin',
    'Username': 'demo_oa',
    'Organization': demo_org_id,
    'Role': 'OA',
    'Password hash': util.get_sha1('123'),
    'Language': 'en'
}
demo_oa_id = rdfeng.o_save(tblname, 'user', data_oa)
print('Created organization admin user for demo organization =>', demo_oa_id)

data_dc = {
    'Email': 'demo_contributor.rdf@fractalexperience.com',
    'Name': 'Demo data contributor',
    'Username': 'demo_dc',
    'Organization': demo_org_id,
    'Role': 'DC',
    'Password hash': util.get_sha1('123'),
    'Language': 'en'
}
demo_dc_id = rdfeng.o_save(tblname, 'user', data_dc)
print('Created data contributor user for demo organization =>', demo_dc_id)




