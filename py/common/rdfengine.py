import json
import rdf.py.common.util as util
import rdf.py.common.htmlutil as htmlutil


class RdfEngine:
    def __init__(self, schema, sqleng):
        self.sqleng = sqleng
        self.schema = schema

    def o_read(self, tblname, obj_id, depth=0):
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
            obj_child = self.o_read(tblname, obj_o, depth + 1)
            data[member.name] = obj_child

        return obj

    def o_list(self, tn, cn):
        """ tn => Table name, cn => class name, cd => Class definition """
        cdef = self.schema.get_class(cn)
        # List all instances together with their properties
        q = (f"SELECT r1.id AS id, r1.h AS h, r2.p AS p, r2.o AS o, r2.v AS v "
             f"FROM {tn} AS r1 INNER JOIN {tn} as r2 ON r1.id=r2.s "
             f"WHERE r1.s={cdef.code} AND r1.p IS NULL AND r1.o IS NULL;")
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
            member = cdef.members.get(str(obj_p))
            if p_def is None or member is None:
                continue
            curr_obj[member.name] = obj_o if obj_o else obj_v

        return res

    def r_data(self, tblname, start, limit):
        """ Provides a basic render of RDF data based on a join with the schema. """
        tbl = self.sqleng.exec_table(f'SELECT * FROM {tblname} ORDER BY id LIMIT {start}, {limit}')
        o = []
        current_cdef = None
        for row in tbl:
            row_id, rdf_s, rdf_p, rdf_o, rdf_v, rdf_h = row[0], row[1], row[2], row[3], row[4], row[5]
            cdef = self.schema.classes.get(str(rdf_s)) if rdf_p is None and rdf_o is None else None
            if cdef:
                current_cdef = cdef  # Remember class definition for next iterations
            cdef_str = f'[{rdf_s}] {cdef.name}' if cdef else rdf_s

            # predef = self.schema.classes.get(str(pre))
            pdef = current_cdef.members.get(str(rdf_p)) if current_cdef and current_cdef.members else None
            pdef_str = f'[{rdf_p}] {pdef.name}' if pdef else rdf_p

            cls_id = 'class="table-warning"' if rdf_p is None and rdf_o is None else ''
            cls_s = '' if cdef else 'class="table-warning"'
            obj_href = '' if rdf_o is None else f'<a href="#{rdf_o}">{rdf_o}</a>'
            cls_obj = '' if rdf_o is None else ' class="table-warning"'
            attr = f'id="{row_id}" {cls_id}'
            htmlutil.wrap_tr(o, [(attr, row_id), (cls_s, cdef_str), pdef_str, (cls_obj, obj_href), rdf_v, rdf_h])

        htmlutil.wrap_h(o, ['id', 'subject', 'predicate', 'object', 'value', 'hash'], 'RDF Data')
        return ''.join(o)

    def o_browse(self, tn, cn, fi):
        """
        cn => Class name, fi => Filter
        Creates a render of all objects with a given name and filtered using a given criteria
        Filter consists of property#value pairs concatenated with "|"
        """
        if not tn:
            return '<h1>No database selected</h1>'
        if not self.sqleng.table_exists(tn):
            return f'<h1>Database table does not exist {tn}</h1>'
        js = self.o_list(tn, cn)
        if not js:
            return f'<h1>No objects found of type {cn}</h1>'
        cdef = self.schema.get_class(cn)
        # This should be improved - we should be able to instantiate even a simple type
        if not cdef.members:
            return f'<h1>Class {cn} is a property</h1>'

        o = []
        fields_show, fields_all = [], []
        for mem_ndx in cdef.members.keys():
            mem = cdef.members.get(mem_ndx)
            fields_all.append(mem)
            if mem.show.lower() == 'true':
                fields_show.append(mem)
            # htmlutil.wrap_tr(o, [mem_ndx, mem.name, mem.data_type, mem.show, mem.ref])

        fields = fields_show if fields_show else fields_all
        for obj in js:
            obj_row = []
            h = obj.get('hash')
            for mem in fields:
                obj_row.append(obj.get(mem.name))
            htmlutil.wrap_tr(o, obj_row, f'onclick="o_edit(\'{h}\')"')

        htmlutil.wrap_table(o)
        return ''.join(o)

    def o_edit(self, tn, h):
        """ Generates an edit form for an object. It is identified by its hash code. """
        obj = self.o_read(tn, h, depth=0)
        cdef = self.schema.get_class(obj.get('code'))
        if cdef is None:
            return f'<h2><span mlang="msg_unknown_object">Unknown object</span></h2>'
        o = [f'<h4 mlang="user_settings">{cdef.name}</h4>']
        if cdef.members is None:
            return f'<h2><span mlang="msg_todo"></span></h2>'
        o.append(f'<form action="" id="form_object_edit" class="needs-validation" novalidate method="post"> '
                 f'<div class="form-group">')
        for mem in cdef.members.values():
            o.append(f'<label for="{mem.name}" mlang="{mem.name}">{mem.name}:</label>')
            o.append(f'<input type="text" class="form-control" value="{mem.code}" id="{mem.name}" name="{mem.name}" '
                     f'required>')
        o.append('</div></form>')

        o.append(
            f'<div style="text-align: right; margin-top:10px;">'
            f'<button type="button" class="btn btn-primary" style="margin-right: 10px;" '
            f'onclick="o_save()" id="btn_o_save" mlang="o_save">'
            f'Save data'
            f'</button>' 
            f'<button type="button" class="btn btn-primary" style="margin-right: 10px;" '
            f'onclick="update_content(\'output\',\'b?cn={cdef.uri}\')" id="btn_o_cancel" mlang="o_cancel">'
            f'Cancel'
            f'</button>'
            f'</div>')

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

    def get_object_hash(self, obj, cdef):
        # Instantiate class
        key_parts = set(f'{cdef.code}')
        all_parts = set(f'{cdef.code}')
        # Find key and calculate hash
        for name, prop_def in cdef.members_by_name.items():
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
        return h

    def store_rdf_object(self, tn, cn, data):
        """ Reads an object serialized in JSON and stores it in the given rdf table using a given schema. """
        obj = json.loads(data) if isinstance(data, str) else data
        cdef = self.schema.get_class(cn)
        h = self.get_object_hash(obj, cdef)
        # If predicate is NULL and object is NULL, this means object instantiation
        q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES ('{cdef.code}', NULL, NULL, NULL, '{h}');"
        obj_id = self.sqleng.exec_insert(q)
        # Effectively write properties
        for name, prop_def in cdef.members_by_name.items():
            prop_cls_def = self.schema.classes.get(prop_def.ref)
            if prop_cls_def is None:
                continue
            rdf_s = obj_id
            rdf_p = prop_def.ndx
            # If data type is "ref" we need to connect the property to an existing object by setting it to "o" column,
            # otherwise write it as a literal in "v" column
            value = obj.get(name)
            if value is None:  # Non existing property
                # print('ERROR: Non existing property in data:', name)
                continue
            rdf_v = 'NULL' if prop_def.data_type == 'ref' else value
            rdf_o = value if prop_def.data_type == 'ref' else 'NULL'

            # Either o (object), or value must be NOT NULL
            # If o is NULL, this means we have a property with value = v
            # If we have o NOT NULL, this means there is an other related instantiated object, which is property
            # of the master object
            q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES ('{rdf_s}', {rdf_p}, {rdf_o}, '{rdf_v}', NULL);"
            self.sqleng.exec_insert(q)
            # print(q)
            # print(prop_id, '=>', (rdf_o, rdf_v))
        return obj_id

    def update_rdf_object(self, tblname, cn, data, obj_id):
        if not data:
            return
        cdef = self.schema.get_class(cn)
        field = 'id' if isinstance(obj_id, int) or obj_id.isnumeric() else 'h'
        q = f"SELECT id FROM {tblname} WHERE {field} = '{obj_id}'"
        obj_id_found = self.sqleng.exec_scalar(q)
        # Check if there is an existing property of that type
        for p_name, p_value in data.items():
            mem = cdef.members_by_name.get(p_name)
            rdf_p = mem.ndx
            data_type = mem.data_type
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

    def get_autoincrement_id(self, tn, cn, pn, pref, zfill_len=6):
        """
        Generates an auto increment identifier
        tn => Master table name
        cn => Class name (URI)
        property name
        """
        cdef = self.schema.get_class(cn)  # Master class
        if not cdef:
            return None

        pdef = None if pn is None else cdef.members_by_name.get(pn)  # Property class
        if pn is None or pdef is None:
            q = f"SELECT count(*) FROM {tn} WHERE s={cdef.code};"
        else:
            q = (f"SELECT count(*) "
                 f"FROM root AS r1 INNER JOIN root AS r2 ON r1.s = r2.id "
                 f"WHERE r2.s = {cdef.code} AND r1.p = {pdef.ndx};")

        # print(q)
        ai_id = self.sqleng.exec_scalar(q)
        ai_id = str(int(ai_id) + 1)
        if zfill_len is not None:
            ai_id = ai_id.zfill(zfill_len)
        return f'{pref}{ai_id}'
