# import mysql.connector
import MySQLdb
import sshtunnel


class SqlEngine:
    def __init__(self, db_host, db_name, db_user, db_pass, ssh_host, ssh_user, ssh_pass, ssh_bind_addr):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_pass = ssh_pass
        self.ssh_bind_addr = ssh_bind_addr
        self.tunnel = None
        self.connection = None
        #
        # self.tunnel = sshtunnel.SSHTunnelForwarder(
        #         ssh_host, ssh_username=ssh_user, ssh_password=ssh_pass, remote_bind_address=(ssh_bind_addr, 3306))
        # self.tunnel.start()
        # try:
        #     self.connect()
        # except Exception as ex:
        #     print(ex)
        #     self.connection = None

    def __del__(self):
        if self.connection is not None:
            self.connection.close()
        # if self.tunnel is not None:
        #     self.tunnel.close()

    @staticmethod
    def connect_decorator(method):
        def wrapper(self, sql):
            try:
                if self.connection is None:
                    self.connect()
                result = method(self, sql)
                # self.connection.close()
                # self.connection = None
                return result
            except Exception as ex:
                print(ex)
                self.connection = None
                return None
        return wrapper

    # Use this method for TCP connection without SSH
    # def connect_mocha(self):
    #     config = {
    #         'user': self.db_user,
    #         'password': self.db_pass,
    #         'host': self.db_host,
    #         'database': self.db_name,
    #         'raise_on_warnings': True
    #     }
    #     conn = mysql.connector.connect(**config)
    #     return conn

    def connect(self):
        if self.ssh_host is None:
            mysql_port = 3306
        else:
            self.tunnel = sshtunnel.SSHTunnelForwarder(
                self.ssh_host, ssh_username=self.ssh_user, ssh_password=self.ssh_pass,
                remote_bind_address=(self.ssh_bind_addr, 3306))
            self.tunnel.start()
            mysql_port = self.tunnel.local_bind_port
        config = {
            'user': self.db_user,
            'passwd': self.db_pass,
            'host': self.db_host,
            'db': self.db_name,
            'port': mysql_port
        }
        self.connection = MySQLdb.connect(**config)

    def table_exists(self, tblname):
        tbl = self.exec_table('SHOW TABLES')
        return any([s for s in tbl if tblname in s])  # tbl is a list of sets

    @connect_decorator
    def exec_scalar(self, sql):
        if not sql:
            return None
        cur = self.execute(sql)
        if cur is None:
            return None
        result = cur.fetchone()
        return result[0] if result else None

    @connect_decorator
    def execute_sql_file(self, filename):
        """ Executes a file with multiple SQL statements. Statements must be separated by ';' """
        with open(filename, 'rt', encoding='utf-8') as f:
            sql = f.read()
            statements = [s.strip() for s in sql.split(';')]
            for statement in statements:
                try:
                    self.execute(statement)
                except Exception as ex:
                    self.connection.rollback()
                    print('ERROR: ', ex)

    @connect_decorator
    def exec_table(self, sql):
        """ Executes a SELECT statement and returns the result rowset as a table. """
        if not sql:
            return None
        cur = self.execute(sql)
        return cur.fetchall()

    @connect_decorator
    def exec_update(self, q):
        self.execute(q)
        self.connection.commit()
        return None  # This may be improved

    @connect_decorator
    def exec_insert(self, sql):
        self.exec_update(sql)
        return self.exec_scalar("SELECT LAST_INSERT_ID();")

    def execute(self, sql):
        if not sql:
            return None
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
