import json
import os

import common.util as util
import common.htmlutil as htmlutil
from common.rdfcms import RdfCms
from common.rdfinputs import RdfInputs
from common.rdfviews import RdfViews
from common.rdfvalidators import RdfValidators
from common.rdfrep import RdfReporter


class RdfEngine:
    def __init__(self, schema, sqleng, base_rdf, base_data, assets_folder, data_folder):
        self.sqleng = sqleng
        self.schema = schema
        self.base_rdf = base_rdf
        self.base_data = base_data
        self.assets_folder = assets_folder
        self.data_folder = data_folder

        self.cms = RdfCms(self.schema, self.sqleng, self.base_rdf, self.base_data, self.assets_folder, self.data_folder)
        self.inp = RdfInputs(self)
        self.vws = RdfViews(self)
        self.vld = RdfValidators(self)
        self.rep = RdfReporter(self)

        self.bgcolors = {0: '#FFFFFF', 1: '#EBF5FB', 2: '#AED6F1', 3: '#85C1E9', 4: '#5DADE2', 5: '#3498DB'}

    def o_rep(self, tn, un, cn):
        cdef = self.schema.get_class(cn)
        if not cdef:
            return f'<h1 style="color: Red;">Class not defined: {cn}</h1>'

        olst = self.o_list(tn, cn)
        o = [f'<h1>{cdef.name}</h1>'
             '<table class="table table-bordered display dataTable">'
             '<thead><tr class="table-info">']
        for ndx, mem in cdef.members.items():
            mdef = self.schema.get_class(mem.ref)
            if not mdef or mdef.data_type == 'object':
                continue
            o.append(f'<th>{mem.name}</th>')
        o.append('</tr></thead>')

        for obj in olst:
            o.append('<tr>')
            for ndx, mem in cdef.members.items():
                mdef = self.schema.get_class(mem.ref)
                if not mdef or mdef.data_type == 'object':
                    continue
                v = obj.get(mem.name, '')
                method = self.vws.view_tab_methods.get(mdef.data_type)
                if method is not None:
                    h = obj.get('hash')
                    pid = obj.get('id')
                    v = method(tn, un, mem, v, h, pid, mdef.data_type, o, 'White')

                o.append(f'<td>{v}</td>')

            o.append('</tr>')
        o.append('</table>')

        htmlutil.append_interactive_table(o)
        return ''.join(o)

    def o_query(self, tn, q):
        lst = self.schema.query(q)
        if lst:
            return lst
        return self.o_list(tn, q)  # Plain list of classes

    def o_list(self, tn, cn, use_ndx=False):
        """ tn => Table name, cn => class name, use_ndx - Whether to use ndx value instead of property name in index """
        cdef = self.schema.get_class(cn)
        # List all instances together with their properties
        sql = (f"SELECT r1.id AS id, r1.h AS h, r1.s AS s, r2.p AS p, r2.o AS o, r2.v AS v "
               f"FROM {tn} AS r1 LEFT JOIN {tn} as r2 ON r1.id=r2.s "
               f"WHERE r1.s={cdef.code} ")
        t = self.sqleng.exec_table(sql)
        res = []
        curr_obj, curr_obj_id = None, None
        for r in t:
            rdf_id, rdf_h, rdf_s, rdf_p, rdf_o, rdf_v = r[0], r[1], r[2], r[3], r[4], r[5]

            if curr_obj_id != rdf_id:
                curr_obj = {'id': rdf_id, 'hash': rdf_h, 'code': rdf_s, 'type': cdef.name}
                res.append(curr_obj)
                curr_obj_id = rdf_id

            member = cdef.members.get(str(rdf_p))
            if not member:
                continue

            if rdf_o is not None and rdf_v is None:  # Referred object
                if use_ndx:
                    rdf_v = rdf_o
                else:
                    if member.data_type == 'property':  # Make recursion and retrieve full referred object
                        child_obj = self.cms.o_read(tn, rdf_o)
                        rdf_v = child_obj
                    # There is a reference to separate object, but it is standalone and to avoid infinite recursions
                    # we just give the id
                    else:
                        rdf_v = rdf_o

            if use_ndx:
                curr_obj.setdefault(member.ndx, []).append(rdf_v)
            else:
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

    def check_browse_condition(self, tn, cn):
        if not tn:
            return False, 'No database selected'
        if not self.sqleng.table_exists(tn):
            return False, f'Database table does not exist {tn}'
        cdef = self.schema.get_class(cn)
        # This should be improved - we should be able to instantiate even a simple type
        if not cdef.members:
            return False, f'Class {cn} is a property'
        return True, 'Ok'

    def o_browse(self, tn, cn, fi):
        """
        cn => Class name, fi => Filter
        Creates a render of all objects with a given name and filtered using a given criteria
        Filter consists of property#value pairs concatenated with "|"
        """
        success, msg = self.check_browse_condition(tn, cn)
        if not success:
            return f'<h1>{msg}</h1>'

        o = []
        cdef = self.schema.get_class(cn)
        fields = self.get_fields_to_show(cdef)
        o.append('<thead>')
        htmlutil.wrap_tr(o, [f.name for f in fields], 'class="table-info"', is_th=True)
        o.append('</thead>')

        js = self.o_list(tn, cn)
        for obj in sorted(js, key=lambda ob: ob.get('id'), reverse=True):
            obj_row = []
            h = obj.get('hash')
            self.o_populate_field_values(tn, obj, obj_row)
            htmlutil.wrap_tr(o, obj_row, f'onclick="o_edit(\'{h}\')"')

        htmlutil.wrap_table(o, attr='class="table table-hover table-bordered display dataTable"')
        o.insert(0, f'<div class="row" style="margin-top: 10px;">'
                    f'<div class="col-sm-3">'
                    f'<button id="btn_new" class="btn btn-primary" onclick="o_new(\'{cdef.uri}\')" mlang="o_new" style="margin-right: 5px;">'
                    f'New {cdef.name}'
                    f'</button>'
                    f'</div>'
                    f'<div class="col-sm-9" style="text-align: right;">'
                    f'<span id="o_export_slot">'
                    f'<button id="btn_export" class="btn btn-info btn-sm" '
                    f'onclick="update_content(\'o_export_slot\', \'export?cn={cdef.uri}\')" mlang="o_export">'
                    f'Export data for {cdef.name}'
                    f'</button>'
                    f'</span>'
                    f'</div>'
                    f'</div>')
        htmlutil.append_interactive_table(o)
        return ''.join(o)

    def o_export(self, tn, cn, fi):
        success, msg = self.check_browse_condition(tn, cn)
        if not success:
            return f'<h1>{msg}</h1>'
        js = self.o_list(tn, cn)
        path_temp = self.cms.get_path_temp(tn)
        filename = f'{cn}_export.json'
        location = os.path.join(path_temp, filename)
        with open(location, 'w') as f:
            json.dump(js, f, indent=4)
        url = f'{self.cms.base_data}/{tn}/{self.cms.base_temp}/{filename}'
        return f'<span mlang="download_link">Download: </span><a href="{url}" target="_blank"><img src="img/json.png" width="32px" alt="{filename}"/></a>'

    def std_reports(self, tn, un):
        location = os.path.join(self.assets_folder, 'reports.json')
        try:
            with open(location, 'r') as f:
                reps = json.load(f)
        except:
            return f'<h1 mlang="no_standard_reports_found">No standard reports found</h1>'

        o = [f'<h1 mlang="std_reports">Standard reports</h1>'
             f'<table class="table table-hover table-bordered display dataTable">'
             f'<thead><tr><th>Name</th><th>Description</th><th>Definition</th></tr></thead>'
             f'<tbody>']
        for rep in reps:
            name = rep.get('Name')
            desc = rep.get('Description')
            h = rep.get('hash')
            o.append(f'<tr><td>{name}</td><td>{desc}</td>'
                     f'<td>'
                     f'<div class="bg-light">'
                     f'<span id="view_{h}">'
                     f'<button class="btn btn-info btn-sm" onclick="window.open(\'view_std_rep?h={h}\')" mlang="view_report">'
                     f'View'
                     f'</button></span>'
                     f'<span id="export_{h}" style="margin-left: 10px;">'
                     f'<button class="btn btn-info btn-sm" '
                     f'onclick="update_content(\'export_{h}\', \'view_std_rep?h={h}&format=excel\')" mlang="export_excel">'
                     f'Export to Excel'
                     f'</button></span>'
                     f'</div>'
                     f'</td>'
                     f'</tr>')
        o.append('</tbody></table>')
        htmlutil.append_interactive_table(o)
        return ''.join(o)

    def o_view_std_rep(self, tn, u, h, format):
        location = os.path.join(self.assets_folder, 'reports.json')
        try:
            with open(location, 'r') as f:
                reps = json.load(f)
        except:
            return f'<h1 mlang="no_standard_reports_found">No standard reports found</h1>'
        rep_matching = [r for r in reps if r.get('hash') == h]
        if not rep_matching:
            return f'<h1 mlang="report_not_found">Report not found [{h}]</h1>'
        rep = rep_matching[0]
        return self.rep.r_rep(tn, format, rep)

    def o_populate_field_values(self, tn, obj, o):
        if obj is None:
            o.append('-')
            return
        cdef = self.schema.get_class(obj.get('code'))
        fields = self.get_fields_to_show(cdef)
        for mem in fields:
            mdef = self.schema.get_class(mem.ref)
            prop_val = obj.get(mem.name)
            prop_val_resolved = prop_val[0] if isinstance(prop_val, tuple) else prop_val
            if mdef:
                method = self.vws.view_tab_methods.get(mdef.data_type)
                if method:
                    h = obj.get('hash')
                    pid = obj.get('id')
                    prop_val_resolved = method(tn, mem, prop_val_resolved, h, pid, mdef.data_type, o, 'White')

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

    def get_near_object(self, tn, h, go):
        if not go or go not in ['prev', 'next']:
            return h
        sign = '<' if go == 'prev' else '>'
        rdf_s = self.sqleng.exec_scalar(f"SELECT s FROM {tn} WHERE h='{h}'")
        rdf_id = self.sqleng.exec_scalar(f"SELECT id FROM {tn} WHERE h='{h}'")  # This could be optimized

        q = f"SELECT h FROM {tn} WHERE s = {rdf_s} AND id < {rdf_id} ORDER BY id DESC LIMIT 1" \
            if go == 'prev' \
            else f"SELECT h FROM {tn} WHERE s = {rdf_s} AND id > {rdf_id} ORDER BY id LIMIT 1"

        near_h = self.sqleng.exec_scalar(q)
        return h if near_h is None else near_h

    def get_obj_and_cdef(self, tn, h_u, go=None):
        """ Reads an object (from the given table) and class definition (from schema)
         corresponding to a hash or uri identifier.
         tn: Table name
         h_u: Hash code of the object, or the URI of the class definition
         go: Instruction where to go - this object, previous, or next
         """
        if util.is_sha1(h_u):
            h = h_u if go is None else self.get_near_object(tn, h_u, go)
            obj = self.cms.o_read(tn, h, depth=0)
            cdef = self.schema.get_class(obj.get('code'))
        else:
            obj = None
            cdef = self.schema.get_class(h_u)
        return obj, cdef

    def r_frag(self, tn, un, o_uri, p_uri, prop_name):
        """ Renders an entry form fragment for a given object (or class to be instantiated)
        o_uri: URI of the property
        p_uri: URI of the parent class
        n: Name of the property
        """
        obj, cdef = self.get_obj_and_cdef(tn, o_uri)
        obj_parent, pdef = self.get_obj_and_cdef(tn, p_uri)
        mem = pdef.members_by_name.get(prop_name)
        val = obj.get('v') if obj else None
        o = []
        if cdef.members is None:
            # o = []
            self.o_edit_prop(o, tn, un, mem, val, [cdef], obj, self.inp.input_methods)
            # return ''.join(o)
        else:
            self.o_edit_members(o, tn, un, [cdef], obj, self.inp.input_methods, False, obj)
        return ''.join(o)
        # return self.o_get_html(tn, obj, cdef, obj_parent, self.inp.input_methods)

    def o_view(self, u, h_u, go, format):
        rdf_h = h_u[0:40] if len(h_u) > 40 else h_u
        tn = h_u[40:] if len(h_u) > 40 else None
        if tn is None:
            if u is None:  # Not logged in
                return '<h1 mlang="not_authorized">Not authorized</h1>'
            t = u.get('db')
            tn = t[0]
        # TODO: Check also cross-organization situation
        obj, cdef = self.get_obj_and_cdef(tn, rdf_h, go)
        if obj is None:
            return '<h1>Object not found</h1>'

        method = self.vws.complex_content_view_methods.get(cdef.uri)
        if method is not None:
            return method(tn, obj, cdef, format)

        un = u.get('name').split('|')[0] if u else ''
        return self.o_represent(tn, un, cdef, obj, self.vws.view_methods, False)

    def o_edit(self, tn, un, h_u):
        obj, cdef = self.get_obj_and_cdef(tn, h_u, None)
        return self.o_represent(tn, un, cdef, obj, self.inp.input_methods, True)

    def o_represent(self, tn, un, cdef, obj, methods, wrap_in_form):
        """ Generates an edit form for an object. It is identified by its hash code. """
        if cdef is None:
            return f'<h2><span mlang="msg_unknown_object">Unknown object</span></h2>'
        if cdef.members is None:
            return f'<h2><span mlang="msg_todo"></span></h2>'

        o = []
        if wrap_in_form:
            self.o_represent_header(o, obj, cdef)
        # ---
        self.o_edit_members(o, tn, un, [cdef], obj, methods, wrap_in_form, obj)
        # ---
        if wrap_in_form:
            self.o_represent_footer(o, obj, cdef)
        return ''.join(o)

    def o_represent_header(self, o, obj, cdef):
        o.append(f'<form action="" id="form_object_edit" class="needs-validation" novalidate method="post"> ')

    def o_represent_footer(self, o, obj, cdef):
        h = obj.get('hash') if obj else None
        frag_o_save = f'o_save(null, [], 0, false, function() {{ o_edit(\'{h}\')}} )' \
            if h \
            else f'o_save(null, [], 0, false, function() {{ update_content(\'output\', \'b?cn={cdef.uri}\'); }})'
        frag_o_clone = f'o_save(null, [], 0, true, function() {{ update_content(\'output\', \'b?cn={cdef.uri}\'); }})' \
            if h else f'alert("Cannot clone unsaved object");'

        frag_btn_save = (f'<button type="button" class="btn btn-primary" style="margin-right: 10px;" '
                         f'onclick="{frag_o_save}" '
                         f'id="btn_o_save" mlang="o_save">Save data</button>')

        frag_btn_del = (f'<button type="button" class="btn btn-danger" style="margin-right: 10px;" '
                        f'onclick="o_delete(function() {{update_content(\'output\', \'b?cn={cdef.uri}\', null)}})" '
                        f'id="btn_o_delete" mlang="o_delete">Delete</button>') if obj else ''

        frag_btn_cancel = (f'<button type="button" class="btn btn-info" style="margin-right: 10px;" '
                           f'onclick="update_content(\'output\',\'b?cn={cdef.uri}\')" '
                           f'id="btn_o_cancel" mlang="o_cancel">Cancel</button>')

        frag_btn_clone = (f'<button type="button" class="btn btn-warning" style="margin-right: 10px;" '
                          f'onclick="{frag_o_clone}" '
                          f'id="btn_o_clone" mlang="o_clone">Clone</button>') if h else ''

        o.append('</form>'
                 '<div style="text-align: right; margin-top:10px;">')
        o.append(frag_btn_save)
        o.append(frag_btn_del)
        o.append(frag_btn_cancel)
        o.append(frag_btn_clone)
        o.append('</div>')

    def o_edit_members(self, o, tn, un, stack, obj, methods, wrap_in_form, grand_parent):
        if not stack:
            return
        cdef = stack[-1]
        div_id = obj.get('hash') if obj else cdef.uri
        i = obj.get('id') if obj else ''
        u = cdef.uri if cdef else ''

        if cdef.members is None:
            return

        bgc = self.bgcolors.get(len(stack), self.bgcolors.get(0))
        o.append(f'<div class="form-group rdf-container" id="{div_id}" i="{i}" u="{u}">')
        o.append(f'<div class="row align-items-start" style="padding-bottom: 20px;background-color: {bgc};">')
        o.append(f'<div class="col-11"><h4 mlang="o_edit_members">{cdef.name}</h4></div>')

        if obj is not None:
            if len(stack) < 2:
                self.add_property_button(o, tn, cdef, obj, wrap_in_form)
            else:
                if methods == self.inp.input_methods:
                    self.add_delete_button(o, tn, cdef, obj, grand_parent)

        o.append('</div>')

        for mem in sorted([m for m in cdef.members.values()], key=lambda m: m.order.zfill(6)):
            self.o_edit_member(o, tn, un, mem, stack, obj, methods, grand_parent)

        o.append('</div>')

    def add_delete_button(self, o, tn, cdef, obj, grand_parent):
        h = obj.get('hash')
        h_gp = grand_parent.get('hash')
        o.append(f'<div class="col-1" style="text-align: right;">'
                 f'<button type="button" class="btn btn-danger btn-sm" mlang="btn_delete_property" '
                 f'onclick="o_delete_id(\'{h}\', function() {{ o_edit(\'{h_gp}\')}} )" '
                 f'id="btn_delete_property"> x </button>'
                 f'</div>')

    def add_property_button(self, o, tn, cdef, obj, wrap_in_form):
        if not obj:
            return
        if not cdef:
            return
        if not cdef.members:
            return
        obj_data = obj.get('data', {})
        o_temp, cnt = [], 0
        for mem in cdef.members.values():
            allow_multiple = mem.multiple.lower() == 'true'
            mdef = self.schema.get_class(mem.ref)
            uri = mdef.uri if mdef else None
            if mem.name in obj_data and obj_data.get(mem.name) is not None and not allow_multiple:
                continue
            if mem.data_type == 'ref':
                continue  # This needs to be improved !!! It is a legal case to add multiple references
            frag_multiple = 'true' if allow_multiple else 'false'
            obj_id = obj.get('id')
            o_temp.append(
                f'<a class="dropdown-item" '
                f'href="javascript:add_property_panel(\'{uri}\', \'{cdef.uri}\', \'{mem.name}\', \'{obj.get("hash")}\', {frag_multiple})" '
                f'id="add_prop_{mem.name}" mlang="add_prop_{mem.name}"  '
                f'p="{mem.name}" u="{cdef.uri}" i="{obj_id}">{mem.name}</a>')
            cnt += 1
        if cnt == 0:
            return

        # Add property button
        h = obj.get('hash')
        o.append('<div class="col-4" style="text-align: right;">')

        if not wrap_in_form:
            o.append('<button type="button" class="btn btn-light" style="margin-right: 5px;" '
                     'id="btn_previous_object" '
                     f'onclick="location.replace(\'view?h={h}&go=prev\');" '
                     'mlang="btn_previous_object"><img src="img/left.svg" width="24px"/> Previous</button>')
            o.append('<button type="button" class="btn btn-light" style="margin-right: 5px;" '
                     'id="btn_next_object" '
                     f'onclick="location.replace(\'view?h={h}&go=next\');" '
                     'mlang="btn_next_object">Next <img src="img/right.svg" width="24px"/></button>')

        if wrap_in_form:
            o.append('<button type="button" class="btn btn-primary" style="margin-right: 5px;" '
                     'id="btn_view_object" '
                     f'onclick="location.replace(\'view?h={h}\');" '
                     'mlang="btn_view_object">View Object</button>')

            o.append('<div class="btn-group">'
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

    def o_edit_member(self, o, tn, un, mem, stack, obj, methods, grand_parent):
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
                self.o_edit_members(o, tn, un, stack, sub_data, methods, False, grand_parent)
                stack.pop(len(stack) - 1)
                # ---
            else:  # Independent reference
                self.o_edit_prop(o, tn, un, mem, val, stack, obj, methods)
        else:
            if val is not None or not allow_multiple:
                # If property is defined once, it should be displayed even empty.
                # If it defined to allowed multiple occurrences, then it should be added from "Add property"
                self.o_edit_prop(o, tn, un, mem, val, stack, obj, methods)

    def o_edit_prop_standalone(self, o, tn, mem, val, stack, obj, methods):
        h = obj.get('hash') if obj else ''
        valstr = val[0] if val and isinstance(val, tuple) else ''
        pid = val[1] if val and isinstance(val, tuple) else ''
        mdef = self.schema.get_class(mem.ref)
        u = mdef.uri
        bgc = self.bgcolors.get(len(stack), self.bgcolors.get(0))
        method = methods.get('standalone', methods.get('string'))
        method(tn, mem, valstr, h, pid, u, o, bgc)

    def o_edit_prop(self, o, tn, un, mem, val, stack, obj, methods):
        if isinstance(val, list):
            for v in val:
                self.o_edit_prop_single(o, tn, un, mem, v, stack, obj, methods)
            return
        # Normal case
        self.o_edit_prop_single(o, tn, un, mem, val, stack, obj, methods)

    def o_edit_prop_single(self, o, tn, un, mem, val, stack, obj, methods):
        """
        :param methods: Methods collection to represent simple content properties
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
        method_ref = 'standalone' if mdef.data_type == 'object' else mdef.data_type
        method = methods.get(method_ref, methods.get('string'))
        method(tn, un, mem, valstr, h, pid, u, o, bgc)

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

            validation_result = self.o_validate(tn, u, obj_data)
            if not validation_result[0]:
                return validation_result[0], validation_result[1], [u], None, None

            i, h, success, msg = self.cms.o_instantiate(tn, uri_or_hash)
            if parent_id:
                # Save the new instantiated object as a property in the parent record
                if p:
                    self.cms.o_associate(tn, puri, parent_id, u, i, p)

        for nested_obj in obj_data:
            save_result = self.o_save_recursive(tn, nested_obj, mdef, i)
            if not save_result[0]:
                return save_result  # Escape from recursion with error message
            h = save_result[4]

        return True, 'Data saved', [u], i, h

    def o_validate(self, tn, uri, obj_data):
        cdef = self.schema.get_class(uri)
        if not cdef:
            return False, f'Class not found: {uri}'
        data = dict(zip([t.get('p') for t in obj_data], [t.get('v') for t in obj_data]))
        success, message = self.vld.v_generic(tn, cdef, data)
        if not success:
            return success, message
        method = self.vld.class_validators.get(uri)
        if method:
            success, message = method(tn, cdef, data)
            if not success:
                return success, message

        return True, 'Success'

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

    def srcbase(self, tn, un, src, uri, prop):
        """ Basic search for a specified object type (uri). If ur is None, we search in any object. """
        where_frag = ''
        if uri:
            cdef = self.schema.get_class(uri)
            where_frag = f" AND r2.s={cdef.code}"
            if prop:
                where_frag = f'{where_frag} AND r1.p={prop}'
        q = f"""
        SELECT r1.id as prop_id, r1.p AS prop_ndx, r1.v AS prop_value,
               r2.id AS obj_id, r2.s AS obj_type, r2.h AS objt_hash
        FROM {tn} AS r1 INNER JOIN {tn} AS r2 ON  r1.s = r2.id
        WHERE r1.v LIKE '%{src}%' {where_frag}
        LIMIT 100
        """
        t = self.sqleng.exec_table(q)
        o = [f'<table class="table table-bordered table-hover">'
             f'<tr><th>Object type</th><th>Property</th><th>Value</th></tr>']
        cnt = 0
        for row in t:
            cnt += 1
            prop_id = row[0]
            prop_ndx = row[1]
            obj_code = row[4]
            cdef = self.schema.get_class(obj_code)
            mem = cdef.members.get(f'{prop_ndx}')
            mdef = self.schema.get_class(mem.ref)
            u = mdef.uri if mdef else None
            h = row[5]
            prop_value = row[2]
            # print(cnt, '=>', len(prop_value))
            method = self.vws.view_tab_methods.get(u) if u else None
            v = prop_value.replace(src, f'<span style="background-color: Yellow;">{src}</span>')
            if method:
                v = method(tn, un, mem, prop_value, h, prop_id, u, o, 'White')
            o.append(f'<tr onclick="window.open(\'view?h={h}\')">'
                     f'<td>{cdef.name}</td><td>{mem.name}</td><td>{v}</td>'
                     f'</tr>')
        o.append('</table>')
        return ''.join(o)
