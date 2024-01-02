import json
import rdf.py.common.util as util


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
        q = f"CREATE TABLE `{tblname}` ( " \
            "`id` int(10) UNSIGNED NOT NULL COMMENT 'Primary identifier', " \
            "`s` int(10) UNSIGNED DEFAULT NULL COMMENT 'Subject', " \
            "`p` int(10) UNSIGNED DEFAULT NULL COMMENT 'Predicate', " \
            "`o` int(10) UNSIGNED DEFAULT NULL COMMENT 'Object', " \
            "`v` varchar(10240) DEFAULT NULL COMMENT 'Value', " \
            "`h` char(40) DEFAULT NULL COMMENT 'Hash code' " \
            ") ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='RDF Tripples';"
        self.sqleng.exec_update(q)

        q = (f"ALTER TABLE `{tblname}` "
             f"ADD PRIMARY KEY (`id`), "
             f"ADD KEY `s` (`s`), "
             f"ADD KEY `p` (`p`), "
             f"ADD KEY `o` (`o`), "
             f"ADD KEY `h` (`h`);")
        self.sqleng.exec_update(q)

        q = f"ALTER TABLE `{tblname}` ADD FULLTEXT KEY `v` (`v`);"
        self.sqleng.exec_update(q)

        q = (f"ALTER TABLE `{tblname}` "
             f"MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT "
             f"COMMENT 'Primary identifier', AUTO_INCREMENT=0;")
        self.sqleng.exec_update(q)

    def store_rdf_object(self, tblname, clsname, data):
        """ Reads an object serialized in JSON and stores it in the given rdf table using a given schema. """
        obj = json.loads(data) if isinstance(data, str) else data
        clsdef = self.schema.classes.get(clsname)  # In this case this is the URI
        print(clsdef)
        # Instantiate class
        code = clsdef.code
        key_parts = set(f'{code}')
        all_parts = set(f'{code}')
        # Find key and calculate hash
        for name, prop_def in clsdef.members.items():
            prop_cls_def = self.schema.classes.get(prop_def.ref)
            if prop_cls_def is None:
                continue
            value = obj.get(prop_cls_def.name)
            if value is None:
                continue
            if prop_def.key and prop_def.key.lower() == 'true':
                key_parts.add(value)
            all_parts.add(value)
        obj_key = '.'.join(key_parts if key_parts else all_parts)
        h = util.get_sha1(obj_key)

        # If predicate is NULL and object is NULL, this means object instantiation
        # Writing obj_key as value of the heading record is redundant - may be skipped one day
        q = f"INSERT INTO {tblname} (s, p, o, v, h) VALUES ('{code}', NULL, NULL, '{obj_key}', '{h}');"
        obj_id = self.sqleng.exec_insert(q)
        # Effectively write properties
        for name, prop_def in clsdef.members.items():
            prop_cls_def = self.schema.classes.get(prop_def.ref)
            if prop_cls_def is None:
                continue
            value = obj.get(prop_cls_def.name)
            if value is None:
                continue
            # Either o (object), or value must be NOT NULL
            # If o is NULL, this means we have a property with value = v
            # If we have o NOT NULL, this means there is an other related instantiated object, which is property
            # of the master object
            q = f"INSERT INTO {tblname} (s, p, o, v, h) VALUES ('{obj_id}', {prop_def.ref}, NULL, '{value}', NULL);"
            prop_id = self.sqleng.exec_insert(q)
            print(prop_id, '=>', value)

        return obj_id
