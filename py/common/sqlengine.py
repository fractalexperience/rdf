import mysql.connector


class SqlEngine:
    def __init__(self, db_host, db_name, db_user, db_pass):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.connection = self.connect()

    def __del__(self):
        if self.connection is not None:
            self.connection.close()

    def connect(self):
        config = {
            'user': self.db_user,
            'password': self.db_pass,
            'host': self.db_host,
            'database': self.db_name,
            'raise_on_warnings': True
        }
        conn = mysql.connector.connect(**config)
        return conn

    def table_exists(self, tblname):
        tbl = self.exec_table('SHOW TABLES')
        return any([s for s in tbl if tblname in s])  # tbl is a list of sets

    def exec_scalar(self, sql):
        if not sql:
            return None
        cur = self.execute(sql)
        if cur is None:
            return None
        result = cur.fetchone()
        return result[0] if result else None

    def execute_sql(self, sql):
        """ Executes a SQL statement. Note that this method does not return a result, so if the statement returns a rowset,
            you must use exec_sql_table() """
        if not sql:
            return
        self.execute(sql)

    def execute_sql_file(self, filename):
        """ Executes a file with multiple SQL statements. Statements must be separated by ';' """
        with open(filename, 'rt', encoding='utf-8') as f:
            sql = f.read()
            statements = [s.strip() for s in sql.split(';')]
            for statement in statements:
                try:
                    self.execute_sql(statement)
                except Exception as ex:
                    self.connection.rollback()
                    print('ERROR: ', ex)

    def exec_table(self, sql):
        """ Executes a SELECT statement and returns the result rowset as a table. """
        if not sql:
            return None
        cur = self.execute(sql)
        return cur.fetchall()

    def exec_update(self, q):
        self.execute_sql(q)
        self.connection.commit()

    def exec_insert(self, sql):
        self.exec_update(sql)
        q = "SELECT LAST_INSERT_ID();"
        resulT_id = self.exec_scalar(q)
        return resulT_id

    def execute(self, sql):
        """ Executes a statement using current connection and then returns the cursor. """
        try:
            cur = self.connection.cursor()
            cur.execute(sql)
            return cur
        except Exception as e:
            print(e)
            self.connection.rollback()
            return None
        # Other exceptions will should be caught from upper levels code

    @staticmethod
    def resolve_sql_value(v):
        if v is None:
            return "'NONE'"
        return "'" + str(v).replace(chr(0xc2), ' ').replace('', '').replace('\'', '\'\'') + "'"
