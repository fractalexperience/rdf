from rdf.py.common import sqlengine, dbconfig

eng = sqlengine.SqlEngine(db_host=dbconfig.DB_HOST, db_name=dbconfig.DB_NAME, db_user=dbconfig.DB_USER, db_pass=dbconfig.DB_PASS)
tbl = eng.exec_sql_table('SHOW TABLES')
print(tbl)
tbl = eng.exec_sql_table('SELECT * FROM reg')
for row in tbl:
    print(row)
