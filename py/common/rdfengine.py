import json
import rdf.py.common.util as util


class RdfEngine:
    def __init__(self, schema, sqleng):
        self.sqleng = sqleng
        self.schema = schema

    def read_object(self, tblname, obj_id, depth=0):
        if depth > 99:  # Not too deep recursion
            return

        frag = f"r1.id={obj_id}" if isinstance(obj_id, int) or obj_id.isnumeric() else f"r1.h='{obj_id}'"
        q = ('SELECT r1.id AS obj_id, r1.h AS obj_h, r1.s AS code, r2.id AS prop_id, r2.p AS p, r2.o AS o, r2.v AS v '
             f'FROM {tblname} as r1 INNER JOIN {tblname} as r2 on r1.id=r2.s '
             f'WHERE {frag};')
        t = self.sqleng.exec_table(q)
        if t is None or len(t) == 0:
            return None

        r = t[0]  # There should be only one object with that hash code or id
        obj_id, obj_h, obj_code = r[0], r[1], r[2]
        clsdef = self.schema.classes.get(str(obj_code))
        obj = {'id': obj_id, 'hash': obj_h, 'code': obj_code, 'type': clsdef.name}
        data = {}
        obj['data'] = data
        for r in t:
            obj_p, obj_o, obj_v = r[4], r[5], r[6]
            p_def = self.schema.classes.get(str(obj_p))
            member = clsdef.members.get(str(obj_p))
            if p_def is None or member is None:
                continue
            if obj_o is None:
                data[member.name] = obj_v
                continue
            obj_child = self.read_object(tblname, obj_o, depth+1)
            data[member.name] = obj_child

        return obj

    def list_objects(self, tblname, clsname):
        clsdef = self.schema.classes.get(clsname)
        code = clsdef.code

        # List all instances together with their properties
        q = (f"SELECT r1.id AS id, r1.h AS h, r2.p AS p, r2.o AS o, r2.v AS v "
             f"FROM {tblname} AS r1 INNER JOIN {tblname} as r2 ON r1.id=r2.s "
             f"WHERE r1.s={code} AND r1.p IS NULL AND r1.o IS NULL;")
        t = self.sqleng.exec_table(q)
        res = []
        curr_obj, curr_obj_id = None, None
        for r in t:
            obj_id, obj_h, obj_p, obj_o, obj_v = r[0], r[1], r[2], r[3], r[4]
            if curr_obj_id != obj_id:
                curr_obj = {'id': obj_id, 'hash': obj_h}
                res.append(curr_obj)
                curr_obj_id = obj_id

            p_def = self.schema.classes.get(str(obj_p))
            member = clsdef.members.get(str(obj_p))
            if p_def is None or member is None:
                continue
            curr_obj[member.name] = obj_o if obj_o else obj_v

        return res

    def r_data(self, tblname, start, limit):
        """ Provides a basic render of RDF data based on a join with the schema. """
        tbl = self.sqleng.exec_table(f'SELECT * FROM {tblname} ORDER BY id LIMIT {start}, {limit}')
        o = [f'<h1>RDF Data</h1>'
             f'<table id="reportTable" class="table table-hover table-bordered">'
             '<tr>'
             '<th>id</th>'
             '<th>subject</th>'
             '<th>predicate</th>'
             '<th>object</th>'
             '<th>value</th>'
             '<th>hash</th>'             
             '</tr>']
        for row in tbl:
            row_id, sbj, pre, obj, val, ha = row[0], row[1], row[2], row[3], row[4], row[5]

            sdef = self.schema.classes.get(str(sbj)) if pre is None and obj is None else None
            sbjstr = f'[{sbj}] {sdef.name}' if sdef else sbj
            predef = self.schema.classes.get(str(pre))
            prestr = f'[{pre}] {predef.name}' if predef else pre

            cls_id = 'class="table-warning"' if pre is None and obj is None else ''
            cls_s = '' if sdef else 'class="table-warning"'
            obj_href = '' if obj is None else f'<a href="#{obj}">{obj}</a>'
            cls_obj = '' if obj is None else ' class="table-warning"'
            o.append(f'<tr>'
                     f'<td id="{row_id}" {cls_id}>{row_id}</td>'
                     f'<td {cls_s}>{sbjstr}</td>'
                     f'<td>{prestr}</td>'
                     f'<td {cls_obj}>{obj_href}</td>'
                     f'<td>{val}</td>'
                     f'<td>{ha}</td>'
                     f'</tr>')
        o.append('</table>')
        return ''.join(o)

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
        # print(clsdef)
        # Instantiate class
        code = clsdef.code
        key_parts = set(f'{code}')
        all_parts = set(f'{code}')
        # Find key and calculate hash
        for name, prop_def in clsdef.members.items():
            prop_cls_def = self.schema.classes.get(prop_def.ref)
            if prop_cls_def is None:
                continue
            rdf_v = obj.get(prop_cls_def.name)
            if rdf_v is None:
                continue
            if prop_def.key and prop_def.key.lower() == 'true':
                key_parts.add(rdf_v)
            all_parts.add(rdf_v)
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

            rdf_s = obj_id
            rdf_p = prop_def.ref
            # If data type is "ref" we need to connect the property to an existing object by setting it to "o" column,
            # otherwise write it as a literal in "v" column
            value = obj.get(prop_cls_def.name)
            if value is None:  # Non existing property
                continue
            rdf_v = 'NULL' if prop_def.data_type == 'ref' else value
            rdf_o = value if prop_def.data_type == 'ref' else 'NULL'

            # Either o (object), or value must be NOT NULL
            # If o is NULL, this means we have a property with value = v
            # If we have o NOT NULL, this means there is an other related instantiated object, which is property
            # of the master object
            q = f"INSERT INTO {tblname} (s, p, o, v, h) VALUES ('{rdf_s}', {rdf_p}, {rdf_o}, '{rdf_v}', NULL);"
            prop_id = self.sqleng.exec_insert(q)
            print(prop_id, '=>', rdf_v)

        return obj_id

    def update_rdf_object(self, tblname, clsname, data, obj_id):
        if not data:
            return
        clsdef = self.schema.classes.get(clsname)
        code = clsdef.code
        field = 'id' if isinstance(obj_id, int) or obj_id.isnumeric() else 'h'
        q = f"SELECT id FROM {tblname} WHERE {field} = '{obj_id}'"
        obj_id_found = self.sqleng.exec_scalar(q)
        # Check if there is an existing property of that type
        for p_name, p_value in data.items():
            rdf_p = clsdef.members.get(p_name).ref
            data_type = clsdef.members.get(p_name).data_type
            rdf_o = 'NULL' if data_type == 'property' else p_value
            rdf_v = 'NULL' if data_type == 'ref' else p_value

            q = f"SELECT * FROM {tblname} WHERE s={obj_id_found} AND p={rdf_p}"
            prop_id = self.sqleng.exec_scalar(q)
            if prop_id:
                if data_type == 'property':
                    q = f"UPDATE {tblname} SET v='{rdf_v}' WHERE id={prop_id} "
                else:
                    q = f"UPDATE {tblname} SET o={rdf_o} WHERE id={prop_id} "
            else:
                q = f"INSERT INTO {tblname} (s, p, o, v, h) VALUES({obj_id_found},{rdf_p},{rdf_o},'{rdf_v}',NULL)"

            self.sqleng.exec_update(q)
