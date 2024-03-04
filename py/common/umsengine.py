import json
import common.util as util


class UmsEngine:
    def __init__(self, rdfeng, ums_table):
        self.rdfeng = rdfeng
        self.sqleng = self.rdfeng.sqleng
        self.ums_table = ums_table

    def chgpwd(self, h, p, np):
        user = self.rdfeng.o_read(self.ums_table, h)
        if not user:
            return 'Error: Cannot find user!'
        phash = util.get_sha1(p)
        tuphash = user.get('data').get('Password hash')
        if not tuphash:
            return 'Error: Cannot find user definition!'
        uphash = tuphash[0]
        if phash != uphash:
            return 'Error: Password does not match!'
        pid = tuphash[1]
        nphash = util.get_sha1(np)
        q = f'UPDATE {self.ums_table} SET v={self.sqleng.resolve_sql_value(nphash)} WHERE id={pid}'
        self.sqleng.exec_update(q)
        return '>Password changed'
