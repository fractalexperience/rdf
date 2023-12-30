

class RdfEngine:
    def __init__(self, schema, sqleng):
        self.sqleng = sqleng
        self.schema = schema

    def reset_rdf_table(self, tblname):
        if self.sqleng.table_exists(tblname):
            # print('Removing existing root table')
            self.sqleng.exec_update(f"DROP TABLE {tblname}")
        self.create_rdf_table(tblname)

    def create_rdf_table(self, tblname):
        sql = f"CREATE TABLE `{tblname}` ( " \
              "`id` int(10) UNSIGNED NOT NULL COMMENT 'Primary identifier', " \
              "`s` int(10) UNSIGNED DEFAULT NULL COMMENT 'Subject', " \
              "`p` int(10) UNSIGNED DEFAULT NULL COMMENT 'Predicate', " \
              "`o` int(10) UNSIGNED DEFAULT NULL COMMENT 'Object', " \
              "`v` varchar(10240) DEFAULT NULL COMMENT 'Value', " \
              "`h` char(40) DEFAULT NULL COMMENT 'Hash code' " \
              ") ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='RDF Tripples';"
        self.sqleng.exec_update(sql)

        sql = f"ALTER TABLE `{tblname}` ADD KEY `s` (`s`), ADD KEY `p` (`p`), ADD KEY `o` (`o`), ADD KEY `h` (`h`);"
        self.sqleng.exec_update(sql)

        sql = f"ALTER TABLE `{tblname}` ADD FULLTEXT KEY `v` (`v`);"
        self.sqleng.exec_update(sql)
