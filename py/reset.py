import os
from rdf.py.common.rdfengine import RdfEngine
from rdf.py.common.rdfschema import RdfSchema
import rdf.py.common.dbconfig as dbconfig
from rdf.py.common.sqlengine import SqlEngine
import rdf.py.common.util as util

location = os.path.join(os.getcwd(), '..', 'assets', 'schema.json')
sh = RdfSchema(location)
if sh.errors:
    print('Errors found in shcma: ')
    print('\n'.join(sh.errors))
    exit()

sqleng = SqlEngine(
    db_host=dbconfig.DB_HOST, db_name=dbconfig.DB_NAME, db_user=dbconfig.DB_USER, db_pass=dbconfig.DB_PASS)

tblname = 'root'

rdfeng = RdfEngine(sh, sqleng)

rdfeng.reset_rdf_table(tblname)

# Organization, which owns the site
data = {
    'Name': 'Owner organization',
    'Description': 'Organization, which owns the website',
    'Database': tblname
}
org_id = rdfeng.store_rdf_object(tblname, 'org', data)


data_sa = {
    'Email': 'rdf@fractalexperience.com',
    'Name': 'Super Admin',
    'Username': 'sa',
    'Organization': org_id,
    'Role': 'SA',
    'Password hash': util.get_sha1('123')
}
sa_id = rdfeng.store_rdf_object(tblname, 'user', data_sa)

data_oa = {
    'Email': 'ardmin.rdf@fractalexperience.com',
    'Name': 'Organization Admin',
    'Username': 'admin',
    'Organization': org_id,
    'Role': 'OA',
    'Password hash': util.get_sha1('123')
}
oa_id = rdfeng.store_rdf_object(tblname, 'user', data_oa)

data_dc = {
    'Email': 'contributor.rdf@fractalexperience.com',
    'Name': 'Data contributor',
    'Username': 'contributor',
    'Organization': org_id,
    'Role': 'DC',
    'Password hash': util.get_sha1('123')
}
dc_id = rdfeng.store_rdf_object(tblname, 'user', data_dc)

# Demo organization
demo_org_data = {
    'Name': 'Demo organization',
    'Description': 'Organization, to be used for test/demonstration'
}
demo_org_id = rdfeng.store_rdf_object(tblname, 'org', demo_org_data)

demo_org_db = 'db' + f'{demo_org_id}'.zfill(4)
rdfeng.create_rdf_table(demo_org_db)
rdfeng.update_rdf_object(tblname, 'org', {'Database': demo_org_db}, demo_org_id)

data_oa = {
    'Email': 'demo_ardmin.rdf@fractalexperience.com',
    'Name': '   Demo organization Admin',
    'Username': 'demo_oa',
    'Organization': demo_org_id,
    'Role': 'OA',
    'Password hash': util.get_sha1('123')
}
oa_id = rdfeng.store_rdf_object(tblname, 'user', data_oa)

data_dc = {
    'Email': 'demo_contributor.rdf@fractalexperience.com',
    'Name': 'Demo data contributor',
    'Username': 'demo_dc',
    'Organization': demo_org_id,
    'Role': 'DC',
    'Password hash': util.get_sha1('123')
}
dc_id = rdfeng.store_rdf_object(tblname, 'user', data_dc)





