import json
import common.util as util
import common.htmlutil as htmlutil
import common.rdfcms as rdfcms


class RdfEngine:
    def __init__(self, schema, sqleng):
        self.sqleng = sqleng
        self.schema = schema
        self.cms = rdfcms.RdfCms(self.schema, self.sqleng)
        # self.special_handling_classes = {
        #     'img', 'db_table', 'hash', 'user_role', 'lang', 'text', 'email', 'image', 'media'}

        self.methods_input = {
            'string': self.input_string,
            'text': self.input_text,
            'date': self.input_date,
            'integer': self.input_int,
            'float': self.input_float,
            'boolean': self.input_boolean,
            'email': self.input_email,
            'image': self.input_image,
            'media': self.input_media,
            'lang': self.input_lang,
            'user_role': self.input_role,
            'db_table': self.input_db_table,
        }
        self.bgcolors = {0: '#FFFFFF', 1: '#EBF5FB', 2: '#AED6F1', 3: '#85C1E9', 4: '#5DADE2', 5: '#3498DB'}

    def o_rep(self, tn, cn):
        cdef = self.schema.get_class(cn)
        if not cdef:
            return f'<h1 style="color: Red;">Class not defined: {cn}</h1>'

        olst = self.o_list(tn, cn)
        o = [f'<h1>{cdef.name}</h1>'
             '<table class="table table-bordered">', '<tr>']
        for ndx, mem in cdef.members.items():
            mdef = self.schema.get_class(mem.ref)
            if not mdef or mdef.data_type == 'object':
                continue
            o.append(f'<td>{mem.name}</td>')

        o.append('</tr>')
        for obj in olst:
            o.append('<tr>')
            for ndx, mem in cdef.members.items():
                mdef = self.schema.get_class(mem.ref)
                if not mdef or mdef.data_type == 'object':
                    continue
                v = obj.get(mem.name, '')
                o.append(f'<td>{v}</td>')
            o.append('</tr>')
        o.append('</table>')
        return ''.join(o)

    def o_query(self, tn, q):
        if q == 'enumerations':  # List rnumerations only - complex type objects having only one member
            return list(sorted([(cdef.uri, cdef.name) for code, cdef in self.schema.classes.items()
                                if cdef.members and len(cdef.members) == 1], key=lambda t: t[1]))
        if q == 'complex':  # List objects having complex type
            return list(sorted([(cdef.uri, cdef.name) for code, cdef in self.schema.classes.items()
                                if cdef.members and len(cdef.members) > 0], key=lambda t: t[1]))
        if q == 'simple':  # List objects having simple type
            return list(sorted([(cdef.uri, cdef.name) for code, cdef in self.schema.classes.items()
                                if cdef.members is None], key=lambda t: t[1]))

        if '.all' in q:
            """ Collects all properties for the given class, or list of classes. """
            result = []
            cn = q.replace('$', '').replace('.all', '')
            cdefs = [c for c in self.schema.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_all_properties(cdef, result)
            return result

        if '$' in q or '.optional' in q:
            """ Collects these members, which are: 
            - Not standalone - i.e. of type property
            - Not mandatory """
            result = []
            cn = q.replace('$', '').replace('.optional', '')
            cdefs = [c for c in self.schema.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_optional_properties(cdef, result)
            return result

        if '.mandatory' in q:
            """ Collects mandatory members """
            result = []
            cn = q.replace('$', '').replace('.mandatory', '')
            cdefs = [c for c in self.schema.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_mandatory_properties(cdef, result)
            return result

        if '^' in q or '.standalone':
            """ Collects standalone members for the given class. This means these members, which are of type ref 
            (are instantiated separately) and only referred from class instances."""
            result = []
            cn = q.replace('^', '').replace('.standalone', '')
            cdefs = [c for c in self.schema.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_standalone_members(cdef, result)
            return result

        return self.o_list(tn, q)  # Plain list of classes

    def get_all_properties(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.schema.get_class(mem.ref)
            result.append((mdef.uri, mem.name))

    def get_optional_properties(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.schema.get_class(mem.ref)
            if mem.data_type == 'property' and not mem.required:
                result.append((mdef.uri, mem.name))

    def get_mandatory_properties(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.schema.get_class(mem.ref)
            if mem.data_type == 'property' and mem.required:
                result.append((mdef.uri, mem.name))

    def get_standalone_members(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.schema.get_class(mem.ref)
            if not mdef.members:
                continue
            # if mem.data_type == 'property':
            #     continue
            self.get_standalone_members(mdef, result)
            if mdef.data_type == 'object' and mem.data_type == 'ref':
                result.append((mdef.uri, mem.name))

    def o_list(self, tn, cn):
        """ tn => Table name, cn => class name, cd => Class definition """
        cdef = self.schema.get_class(cn)
        # List all instances together with their properties
        sql = (f"SELECT r1.id AS id, r1.h AS h, r1.s AS s, r2.p AS p, r2.o AS o, r2.v AS v "
               f"FROM {tn} AS r1 LEFT JOIN {tn} as r2 ON r1.id=r2.s "
               f"WHERE r1.s={cdef.code} AND r1.p IS NULL AND r1.o IS NULL;")
        t = self.sqleng.exec_table(sql)
        res = []
        curr_obj, curr_obj_id = None, None
        for r in t:
            rdf_id, rdf_h, rdf_s, rdf_p, rdf_o, rdf_v = r[0], r[1], r[2], r[3], r[4], r[5]

            if curr_obj_id != rdf_id:
                curr_obj = {'id': rdf_id, 'hash': rdf_h, 'code': rdf_s, 'type': cdef.name}
                res.append(curr_obj)
                curr_obj_id = rdf_id

            p_def = self.schema.classes.get(str(rdf_p))
            member = cdef.members.get(str(rdf_p))
            if p_def is None or member is None:
                continue

            if rdf_o is not None and rdf_v is None:  # Referred object
                if member.data_type == 'property':  # Make recursion and retrieve full referred object
                    child_obj = self.cms.o_read(tn, rdf_o)
                    rdf_v = child_obj
                # There is a reference to separate object, but it is standalone and to avoid infinite recursions
                # we just give the id
                else:
                    rdf_v = rdf_o

            curr_obj[member.name] = rdf_v

        return res

    def r_data(self, tblname, start, limit):
        """ Provides a basic render of RDF data based on a join with the schema. """
        q = f'SELECT * FROM {tblname} ORDER BY id LIMIT {start}, {limit}'
        tbl = self.sqleng.exec_table(q)
        if not tbl:
            return f'<h1 style="color: Red;">Cannot execute tatement</h1><br/>{q}'
        o = []
        cdefs_by_id = {}
        for row in tbl:
            row_id, rdf_s, rdf_p, rdf_o, rdf_v, rdf_h = row[0], row[1], row[2], row[3], row[4], row[5]

            # Identify object instantiation
            cdef = self.schema.classes.get(str(rdf_s)) if rdf_p is None and rdf_o is None else None
            if cdef:
                cdefs_by_id[row_id] = cdef  # Remember class definition for next iterations
            cdef_str = f'[{rdf_s}] {cdef.name}' if cdef else rdf_s

            if not cdef:
                cdef = cdefs_by_id.get(rdf_s)
            pdef = cdef.members.get(str(rdf_p)) if cdef and cdef.members else None

            pdef_str = f'[{rdf_p}] {pdef.name}' if pdef else rdf_p if rdf_p else 'NULL'

            cls_id = 'class="table-warning"' if rdf_p is None and rdf_o is None else ''
            cls_s = '' if cdef else 'class="table-warning"'
            obj_href = 'NULL' if rdf_o is None else f'<a href="#{rdf_o}">{rdf_o}</a>'
            cls_obj = ' class="table-secondary"' if rdf_o is None else ' class="table-warning"'
            attr = f'id="{row_id}" {cls_id}'
            htmlutil.wrap_tr(o, [(attr, row_id), (cls_s, cdef_str),
                                 pdef_str,
                                 (cls_obj, obj_href),
                                 rdf_v if rdf_v else 'NULL',
                                 rdf_h if rdf_h else 'NULL'])

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
        cdef = self.schema.get_class(cn)
        # This should be improved - we should be able to instantiate even a simple type
        if not cdef.members:
            return f'<h1>Class {cn} is a property</h1>'

        o = []
        fields = self.get_fields_to_show(cdef)
        htmlutil.wrap_tr(o, [f.name for f in fields], 'class="table-info"')
        for obj in sorted(js, key=lambda ob: ob.get('id'), reverse=True):
            obj_row = []
            h = obj.get('hash')
            self.o_populate_field_values(tn, obj, obj_row)
            htmlutil.wrap_tr(o, obj_row, f'onclick="o_edit(\'{h}\')"')

        htmlutil.wrap_table(o)
        o.insert(0, f'<div style="margin-top: 10px;">'
                    f'<button id="btn_new" class="btn btn-primary" onclick="o_new(\'{cdef.uri}\')" mlang="o_save">'
                    f'New {cdef.name}'
                    f'</button>'
                    f'</div>')

        return ''.join(o)

    def o_populate_field_values(self, tn, obj, o):
        if obj is None:
            o.append('-')
            return
        cdef = self.schema.get_class(obj.get('code'))
        fields = self.get_fields_to_show(cdef)
        for mem in fields:
            prop_val = obj.get(mem.name)
            prop_val_resolved = prop_val[0] if isinstance(prop_val, tuple) else prop_val

            if mem.data_type == 'ref' and isinstance(prop_val, int):
                # Referred standalone object
                prop_obj = self.cms.o_read(tn, prop_val_resolved)
                if prop_obj is not None:
                    data = prop_obj.get('data') if 'data' in prop_obj else prop_obj
                    data['code'] = mem.ref
                    self.o_populate_field_values(tn, data, o)
                else:
                    o.append(prop_val_resolved)
                continue

            o.append(prop_val_resolved)

    def get_fields_to_show(self, cdef):
        if cdef is None:
            return None
        fields_show, fields_all = [], []
        for mem_ndx in cdef.members.keys():
            mem = cdef.members.get(mem_ndx)
            fields_all.append(mem)
            if mem.show.lower() == 'true':
                fields_show.append(mem)
        return fields_show if fields_show else fields_all

    def get_obj_and_cdef(self, tn, h_u):
        """ Reads an object (from the given table) and class definition (from schema)
         corresponding to a hash or uri identifier. """
        if util.is_sha1(h_u):
            obj = self.cms.o_read(tn, h_u, depth=0)
            cdef = self.schema.get_class(obj.get('code'))
        else:
            obj = None
            cdef = self.schema.get_class(h_u)
        return obj, cdef

    def r_frag(self, tn, o, p, n):
        """ Renders an entry form fragment for a given object (or class to be instantiated)
        o: URI of the property
        p: URI of the parent class
        n: Name of the property
        """
        obj, cdef = self.get_obj_and_cdef(tn, o)
        obj_parent, pdef = self.get_obj_and_cdef(tn, p)
        mem = pdef.members_by_name.get(n)
        val = obj.get('v') if obj else None
        if cdef.members is None:
            o = []
            self.o_edit_prop(o, mem, val, [cdef], obj)
            return ''.join(o)

        return self.o_get_html(tn, obj, cdef, obj_parent)

    def o_edit(self, tn, h_u):
        """ Generates an edit form for an object. It is identified by its hash code. """
        obj, cdef = self.get_obj_and_cdef(tn, h_u)
        if cdef is None:
            return f'<h2><span mlang="msg_unknown_object">Unknown object</span></h2>'
        if cdef.members is None:
            return f'<h2><span mlang="msg_todo"></span></h2>'

        o = [f'<form action="" id="form_object_edit" class="needs-validation" novalidate method="post"> ']
        # Always start from root
        frag_div = self.o_get_html(tn, obj, cdef, None)
        # ---
        o.append(frag_div)
        self.o_edit_footer(o, obj, cdef)
        return ''.join(o)

    def o_get_html(self, tn, obj, cdef, pdef):
        """ Creates a HTML div element to be embedded in editing form for the given object. """
        o = []
        self.o_edit_members(o, tn, [cdef], obj)
        return ''.join(o)

    def o_edit_footer(self, o, obj, cdef):
        h = obj.get('hash') if obj else None
        frag_o_save = f'o_save(null, [], 0, function() {{ o_edit(\'{h}\')}} )' \
            if h \
            else f'o_save(null, [], 0, function() {{ update_content(\'output\', \'b?cn={cdef.uri}\'); }})'
        frag_btn_save = (f'<button type="button" class="btn btn-primary" style="margin-right: 10px;" '
                         f'onclick="{frag_o_save}" '
                         f'id="btn_o_save" mlang="o_save">Save data</button>')

        frag_btn_del = (f'<button type="button" class="btn btn-danger" style="margin-right: 10px;" '
                        f'onclick="o_delete(function() {{update_content(\'output\', \'b?cn={cdef.uri}\', null)}})" '
                        f'id="btn_o_delete" mlang="o_delete">Delete</button>') if obj else ''

        frag_btn_cancel = (f'<button type="button" class="btn btn-info" style="margin-right: 10px;" '
                           f'onclick="update_content(\'output\',\'b?cn={cdef.uri}\')" '
                           f'id="btn_o_cancel" mlang="o_cancel">Cancel</button>')

        o.append('</form>'
                 '<div style="text-align: right; margin-top:10px;">')
        o.append(frag_btn_save)
        o.append(frag_btn_del)
        o.append(frag_btn_cancel)
        o.append('</div>')

    def o_edit_members(self, o, tn, stack, obj=None):
        if not stack:
            return
        cdef = stack[-1]
        div_id = obj.get('hash') if obj else cdef.uri
        i = obj.get('id') if obj else ''
        u = cdef.uri if cdef else ''

        if cdef.members is None:
            # if pdef:
            #     mem = pdef.members_by_name.get(cdef.name)
            #     self.o_edit_member(o, tn, mem, stack, obj)
            return

        bgc = self.bgcolors.get(len(stack), self.bgcolors.get(0))
        o.append(f'<div class="form-group rdf-container" id="{div_id}" i="{i}" u="{u}">')
        o.append(f'<div class="row align-items-start" style="padding-bottom: 20px;background-color: {bgc};">')
        o.append(f'<div class="col-9"><h4 mlang="o_edit_members">{cdef.name}</h4></div>')
        if obj is not None:
            self.add_property_button(o, tn, cdef, obj)
        o.append('</div>')

        for mem in cdef.members.values():
            self.o_edit_member(o, tn, mem, stack, obj)

        o.append('</div>')

    def add_property_button(self, o, tn, cdef, obj):
        if not obj:
            return
        if not cdef:
            return
        if not cdef.members:
            return
        obj_data = obj.get('data', {})
        o_temp, cnt = [], 0
        for mem in cdef.members.values():
            # pdef = self.schema.get_class(it[0])
            allow_multiple = mem.multiple.lower() == 'true'
            mdef = self.schema.get_class(mem.ref)
            uri = mdef.uri if mdef else None
            if mem.name in obj_data and not allow_multiple:
                continue
            if mem.data_type == 'ref':
                continue  # This needs to be improved !!! It is a legal case to add multiple references
            frag_multiple = 'true' if allow_multiple else 'false'
            obj_id = obj.get('id')
            o_temp.append(
                f'<a class="dropdown-item" '
                f'href="javascript:add_property_panel(\'{uri}\', \'{cdef.uri}\', \'{mem.name}\', \'{obj.get("hash")}\', {frag_multiple})" '
                f'id="add_prop_{mem.name}" mlang="add_prop_{mem.name}" '
                f'p="{mem.name}" u="{cdef.uri}" i="{obj_id}">{mem.name}</a>')
            cnt += 1
        if cnt == 0:
            return

        # Add property button
        o.append('<div class="col-3" style="text-align: right;">'
                 '<div class="btn-group">'
                 '<button type="button" class="btn btn-primary" '
                 'id="btn_append_property" '
                 'mlang="btn_append_property">Append property</button> '
                 '<button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" '
                 'data-bs-toggle="dropdown"> '
                 '<span class="caret"></span> '
                 '</button> '
                 '<div class="dropdown-menu" id="properties_dropdown">')
        o.append(''.join(o_temp))
        o.append('</div>')
        o.append('</div>')
        o.append('</div>')

    def o_edit_member(self, o, tn, mem, stack, obj):
        data = obj.get('data') if obj else {}
        mdef = self.schema.get_class(mem.ref)
        allow_multiple = mem and mem.multiple.lower() == 'true'
        val = data.get(mem.name) if data else None
        if mdef.data_type == 'object':
            if mem.data_type == 'property':
                # ---
                sub_data = data.get(mem.name)
                if not sub_data:
                    return
                stack.append(mdef)
                self.o_edit_members(o, tn, stack, sub_data)
                stack.pop(len(stack) - 1)
                # ---
            else:  # Independent reference
                self.o_edit_prop_independent(o, tn, mem, val, stack, obj)
        else:
            if val is not None or not allow_multiple:
                # If property is defined once, it should be displayed even empty.
                # If it defined to allowed multiple occurrences, then it should be added from "Add property"
                self.o_edit_prop(o, mem, val, stack, obj)

    def o_edit_prop_independent(self, o, tn, mem, val, stack, obj):
        h = obj.get('hash') if obj else ''
        valstr = val[0] if val and isinstance(val, tuple) else ''
        pid = val[1] if val and isinstance(val, tuple) else ''
        # u = '.'.join([cdef.uri for cdef in stack])
        mdef = self.schema.get_class(mem.ref)
        u = mdef.uri
        olst = self.o_list(tn, mem.ref)
        bgc = self.bgcolors.get(len(stack), self.bgcolors.get(0))
        o.append(f'<div class="row align-items-start" style="background-color: {bgc};">'
                 f'<div class="col-2" style="text-align: right;">'
                 f'<label for="{mem.name}" mlang="{mem.name}" class="text-success">{mem.name}</label>'
                 f'</div>'
                 f'<div class="col-10">'
                 f'<select id="{mem.name}" mlang="{mem.name}" '
                 f'onchange="$(this).addClass(\'rdf-changed\')" '
                 f'class="form-select rdf-property" i="{pid}" p="{mem.name}" u="{u}" >'
                 f'<option value=""> ... </option>')
        for ref_obj in olst:
            ref_h = ref_obj.get('hash')
            ref_n = ref_obj.get('Name')
            ref_id = ref_obj.get('id')
            is_selected = ' selected="true"' if ref_id == valstr else ''
            # o.append(f'<option value="{ref_h}"{is_selected}>{util.escape_xml(ref_n)}</option>')
            o.append(f'<option value="{ref_id}"{is_selected}>{util.escape_xml(ref_n)}</option>')
        o.append('</select>'
                 '</div>'
                 '</div>')

    def o_edit_prop(self, o, mem, val, stack, obj):
        if isinstance(val, list):
            for v in val:
                self.o_edit_prop_single(o, mem, v, stack, obj)
            return
        # Normal case
        self.o_edit_prop_single(o, mem, val, stack, obj)

    def o_edit_prop_single(self, o, mem, val, stack, obj):
        """
        :param o: Output list
        :param mem: Ptoperty class
        :param val: Value of the property
        :param stack: list of the involved classes
        :param obj: Object instance (if any), None for new object
        :return: None
        """
        h = obj.get('hash') if obj else ''
        valstr = val[0] if val and isinstance(val, tuple) else ''
        pid = val[1] if val and isinstance(val, tuple) else ''
        bgc = self.bgcolors.get(len(stack), self.bgcolors.get(0))
        mdef = self.schema.get_class(mem.ref)
        u = mdef.uri
        method_input = self.methods_input.get(mdef.data_type, self.methods_input.get('string'))
        method_input(mem, valstr, h, pid, u, o, bgc)

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

    def o_hash(self, obj, cdef):
        # Instantiate class
        key_parts = set()  # set(f'{cdef.code}')
        # all_parts = set(f'{cdef.code}')
        # Find key and calculate hash
        for name, prop_def in cdef.members_by_name.items():
            prop_cls_def = self.schema.classes.get(prop_def.ref)
            if prop_cls_def is None:
                continue
            rdf_v = obj.get(prop_def.name)
            if rdf_v is None:
                continue
            if prop_def.key and prop_def.key.lower() == 'true':
                key_parts.add(rdf_v)
            # all_parts.add(rdf_v)
        obj_key = '.'.join(key_parts if key_parts else [json.dumps(obj)])
        h = util.get_sha1(f'{cdef.uri}.{obj_key}')
        return h

    def o_save_i(self, tn, data):
        """
        Version of save method, where we have a list of tuples, where eah tuple has the following members:
        0: property id
        1: hash code of the master object
        2: Property value
        3: Parent class URI

        if property id is NULL or empty, this means we add new record for that property
        if property value is empty, the property is deleted. 9This might be improved eventually)

        :param tn: Database table to operate with
        :param data: Data collection
        """
        objects = json.loads(data) if isinstance(data, str) else data
        msg = None
        cdefs = {}
        new_objects = {}
        for t in objects:
            p, h, i, v, u = t[0], t[1], t[2], t[3], t[4]
            if not h and not u:
                continue
            if not h and u:
                new_objects.setdefault(u, []).append(t)
                continue
            msg = self.o_save_i_prop(tn, t, cdefs)

        # Here we instantiate new objects
        for uri, tpls in new_objects.items():
            data = dict(zip([t[0] for t in tpls], [t[3] for t in tpls]))
            self.o_save(tn, uri, data)
            msg = '>Object created'

        return msg, set([cdef[0].uri for cdef in cdefs.values()])

    def o_save_i_prop(self, tn, t, cdefs):
        p, h, i, v, u = t[0], t[1], t[2], t[3], t[4]
        # Here we save data for already instantiated objects
        tcdef = cdefs.get(h)
        if tcdef is None:
            q = f"SELECT id,s FROM {tn} WHERE h='{h}'"
            tobj = self.sqleng.exec_table(q)
            if not tobj or len(tobj) < 1:
                return f'ERROR: Cannot find object instance [{h}]', None  # Should not happen
            obj_id = tobj[0][0]
            cls_code = tobj[0][1]
            cdef = self.schema.get_class(cls_code)
            if not cdef.members:
                return 'ERROR: Cannot find class ' + cls_code, None  # Should not happen
            tcdef = (cdef, obj_id)
            cdefs[h] = tcdef

        cdef = tcdef[0]
        obj_id = tcdef[1]
        if i:
            # Only replace the value
            q = f'UPDATE {tn} SET v={self.sqleng.resolve_sql_value(v)} WHERE id={i}'
            self.sqleng.exec_update(q)
            return '>Data saved'

        mem = cdef.members_by_name.get(p)
        q = (f"INSERT INTO {tn} (s,p,o,v,h) "
             f"VALUES ({obj_id}, {mem.ndx}, NULL, {self.sqleng.resolve_sql_value(v)}, NULL)")
        self.sqleng.exec_update(q)
        msg = '>Data saved'
        return msg

    def o_save_h(self, tn, data):
        """ Version of save method, where data is a collection of objects each indexed by its hash code. """
        objects = json.loads(data) if isinstance(data, str) else data
        # for h, obj in objects.items():
        #     TODO !!!

    def o_save(self, tn, cn, data):
        """ Reads an object serialized in JSON and stores it in the given rdf table using a given schema. """
        obj = json.loads(data) if isinstance(data, str) else data
        cdef = self.schema.get_class(cn)
        h = self.o_hash(obj, cdef)
        obj_id_found, cdef_found = self.o_seek(tn, h)
        if obj_id_found:  # There is already an object with the same key
            self.o_update(tn, h, data)
            return
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

            # Either o (object), or value must be NOT NULL
            # If o is NULL, this means we have a property with value = v
            # If we have o NOT NULL, this means there is an other related instantiated object, which is property
            # of the master object
            if prop_def.data_type == 'ref':  # we store a ref to an existing object
                rdf_v, rdf_o = 'NULL', value
            else:
                if prop_cls_def.members:  # It is a nested compound object
                    prop_obj_id = self.o_save(tn, prop_cls_def.name, value)  # Recursion
                    rdf_v, rdf_o = 'NULL', prop_obj_id
                else:  # Simple content string property
                    rdf_v, rdf_o = value, 'NULL'

            rdf_v = rdf_v if rdf_v == 'NULL' else f"'{rdf_v}'"
            q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES ({rdf_s}, {rdf_p}, {rdf_o}, {rdf_v}, NULL);"
            self.sqleng.exec_insert(q)
        return obj_id

    def o_save_recursive(self, tn, data, cdef=None, parent_id=None):
        """ Version of save, where we have data as nested objects. """
        obj = json.loads(data) if isinstance(data, str) else data
        # Container identifier - it is the has of the object, if it is already instantiated, otherwise the class uri
        uri_or_hash = obj.get('id')
        # Internal database id if any
        p = obj.get('p')  # Property name
        i = obj.get('i')
        u = obj.get('u')
        mdef = cdef.members_by_name.get(p) if cdef else self.schema.get_class(u)
        obj_data = obj.get('data')
        puri = cdef.uri if cdef else None
        if not p:
            mem = cdef.members.get(cdef.idx_memuri_ndx.get(u)) if cdef else None
            p = mem.name if mem else None

        if not obj_data:
            v = obj.get('v')
            t = self.cms.o_add_property(tn, puri, parent_id, p, i, v)
            return t

        if not mdef:
            mdef = self.schema.get_class(u)
        h = None
        if not i and uri_or_hash != 'root':
            i, h, success, msg = self.cms.o_instantiate(tn, uri_or_hash)
            if parent_id:
                # Save the new instantiated object as a property in the parent record
                if p:
                    self.cms.o_associate(tn, puri, parent_id, u, i, p)
                #
                # ndx = cdef.idx_memuri_ndx.get(mdef.uri) if cdef else None
                # if ndx:
                #     q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({parent_id},{ndx},'{i}',NULL,NULL)"
                #     self.sqleng.exec_insert(q)

        for nested_obj in obj_data:
            t2 = self.o_save_recursive(tn, nested_obj, mdef, i)
            h = t2[1]

        return 'Data saved', [u], i, h

    def o_save_instantiate(self, tn, uri):
        """ Instantiates a new compound object and returns the new id. """
        cdef = self.schema.get_class(uri)
        if not cdef:
            print('ERROR: Class not found ', uri)
            return
        h = util.get_id_sha1()
        q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({cdef.code},NULL,NULL,NULL,'{h}')"
        obj_id = self.sqleng.exec_insert(q)
        return obj_id, h

    def o_seek(self, tn, obj_id):
        # Normally we will address object by hash, but it can be also internal id
        field_id = 'id' if isinstance(obj_id, int) or obj_id.isnumeric() else 'h'
        q = f"SELECT id, s FROM {tn} WHERE {field_id} = '{obj_id}'"
        t = self.sqleng.exec_table(q)
        if t is None or len(t) == 0:
            return None, None

        r = t[0]  # We expect only one row to be in the result set

        obj_id_found = r[0]
        obj_code = r[1]
        cdef = self.schema.get_class(obj_code)
        return obj_id_found, cdef

    def o_update(self, tn, obj_id, data):
        if not data:
            return
        # cdef = self.schema.get_class(cn)
        obj_id_found, cdef = self.o_seek(tn, obj_id)
        if obj_id_found is None:
            return
        # Check if there is an existing property of that type
        for p_name, p_value in data.items():
            mem = cdef.members_by_name.get(p_name)
            rdf_p = mem.ndx
            data_type = mem.data_type
            rdf_o = 'NULL' if data_type == 'property' else p_value
            rdf_v = 'NULL' if data_type == 'ref' else p_value
            q = f"SELECT * FROM {tn} WHERE s={obj_id_found} AND p={rdf_p}"
            prop_id = self.sqleng.exec_scalar(q)
            if prop_id:
                if data_type == 'property':
                    q = f"UPDATE {tn} SET v='{rdf_v}' WHERE id={prop_id} "
                else:
                    q = f"UPDATE {tn} SET o={rdf_o} WHERE id={prop_id} "
            else:
                q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({obj_id_found},{rdf_p},{rdf_o},'{rdf_v}',NULL)"
            self.sqleng.exec_update(q)

    def o_collect_ids(self, tn, obj_id, id_set):
        """
        Collects the ids of all properties for an object including nested compound objects of type "property"
        IMPORTANT! obj_id is always the internal id of the object.
        """
        id_set.add(obj_id)
        q = f"SELECT id, o FROM {tn} WHERE s={obj_id}"
        t = self.sqleng.exec_table(q)
        for r in t:
            rdf_id = r[0]
            rdf_o = r[1]
            id_set.add(rdf_id)
            if rdf_o:
                self.o_collect_ids(tn, rdf_o, id_set)  # Recursion

    def o_delete_batch(self, tn, data):
        lst = data if isinstance(data, list) else json.loads(data)
        msg = None
        for obj_id in lst:
            result, msg = self.o_delete(tn, obj_id)
        return msg

    def o_delete(self, tn, obj_id):
        obj_id_found, cdef = self.o_seek(tn, obj_id)
        if not obj_id_found:
            return False, f'Object not found {obj_id}'
        id_set = set()
        self.o_collect_ids(tn, obj_id_found, id_set)
        ids = ','.join([f'{i}' for i in id_set])
        q = f"DELETE FROM {tn} WHERE id IN ({ids})"
        self.sqleng.exec_update(q)
        return True, 'Object deleted'

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

    def srcbase(self, tn, src, uri):
        """ Basic search for a specified object type (uri). If ur is None, we search in any object. """
        return f'Search [{src}] in [{uri}]'

    # INPUT METHODS
    @staticmethod
    def table_row_decorator(method):
        def wrapper(self, mem, valstr, h, pid, u, o, bgc):
            o.append(f'<div class="row align-items-start" style="background-color: {bgc};">')
            o.append('<div class="col-2" style="text-align: right;">')
            o.append(
                f'<label for="{mem.name}" mlang="{mem.name}" class="text-primary">{mem.name}</label>')
            o.append('</div>')
            o.append('<div class="col-10">')
            method(self, mem, valstr, h, pid, u, o)
            o.append('</div></div>')

        return wrapper

    @table_row_decorator
    def input_string(self, mem, valstr, h, pid, u, o):
        o.append(f'<input type="text" class="form-control rdf-property" value="{valstr}" id="{mem.name}" '
                        f'oninput="$(this).addClass(\'rdf-changed\')" '
                        f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @table_row_decorator
    def input_text(self, mem, valstr, h, pid, u, o):
        o.append(
            f'<textarea type="text" class="form-control rdf-property" rows="2" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}">{valstr}</textarea>')

    @table_row_decorator
    def input_date(self, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="date" class="form-control rdf-property" style="width: 150px;" value="{valstr}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @table_row_decorator
    def input_int(self, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="number" step="1" class="form-control rdf-property" style="width: 150px;" value="{valstr}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @table_row_decorator
    def input_float(self, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="number" step="any" class="form-control rdf-property" style="width: 150px;" value="{valstr}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @table_row_decorator
    def input_boolean(self, mem, valstr, h, pid, u, o):
        frag_checked = 'checked' if valstr.lower() == 'true' else ''
        o.append(
            f'<div class="form-check form-switch">'
            f'<input type="checkbox" {frag_checked} class="form-check-input rdf-property" value="{valstr}" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />'
            f'</div>')

    @table_row_decorator
    def input_email(self, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="email" class="form-control rdf-property" style="width: 150px;" value="{valstr}" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" h="{h}" i="{pid}" p="{mem.name}" u="{u}" />')

    def input_image(self, mem, valstr, h, pid, u, o, bgc):
        img_data = json.loads(valstr) if valstr else None
        location_thumb = img_data.get('thumb') if img_data else 'img/picture.png'
        location_img = img_data.get('img') if img_data else 'img/picture.png'
        filename = img_data.get('filename') if img_data else ''
        o.append(f"""
<div class="row align-items-start" style="background-color: {bgc};">
    <div class="col-2" style="text-align: right;">
        <div id="div_thumbnail" style="text-align: center;">
            <a href="{location_img}" target="_blank">
            <img src="{location_thumb}" alt="{filename}" title="{filename}" 
                height="60" id="img_thumb_{pid}" style="margin:5px;">
            </a>
        </div>
    </div>
    <div class="col-10">
        <span>Choose image</span>
        <input 
            type="file" id="file_img_{pid}" accept="*" style="display: block;" 
            onchange="handle_files(this.files, \'{pid}\')"/>
        <input 
            type="text" class="form-control rdf-property"
            value=\'{valstr}\' 
            oninput="$(this).addClass(\'rdf-changed\') " 
            name="{mem.name}" h="{h}" i="{pid}" p="{mem.name}" u="{u}" " 
            id="img_data_{pid}" disabled="true" style="display: none;"/>
    </div>
</div>""")

    @table_row_decorator
    def input_media(self, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input media {mem.name}</h1>')

    @table_row_decorator
    def input_lang(self, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input lang {mem.name}</h1>')

    @table_row_decorator
    def input_role(self, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input role {mem.name}</h1>')

    @table_row_decorator
    def input_db_table(self, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input DB table {mem.name}</h1>')
