import json
import common.util as util


class RdfViews:
    """ Implements methods to view RDF data """

    def __init__(self, rdfengine):
        self.rdfeng = rdfengine

        self.view_methods = {
            'standalone': self.view_standalone,
            'string': self.view_string,
            'text': self.view_text,
            'date': self.view_date,
            'integer': self.view_int,
            'float': self.view_float,
            'boolean': self.view_boolean,
            'email': self.view_email,
            'image': self.view_image,
            'media': self.view_media,
            'lang': self.view_lang,
            'db_table': self.view_db_table,
            'report_def': self.view_report_def,
        }

        self.view_tab_methods = {
            'report_def': self.resolve_report_def,
        }

        self.complex_content_view_methods = {
            'custom_report' : self.play_custom_report,
        }

    @staticmethod
    def view_row_decorator(method):
        def wrapper(self, tn, mem, valstr, h, pid, u, o, bgc):
            o.append(f'<div class="row align-items-start">')
            o.append('<div class="col-2" style="text-align: right;">')
            o.append(
                f'<label for="{mem.name}" mlang="{mem.name}" class="text-primary">{mem.name}</label>')
            o.append('</div>')
            o.append('<div class="col-10">')
            method(self, tn, mem, valstr, h, pid, u, o)
            o.append('</div></div>')
        return wrapper

    # --- View methods - used to view properties in form ---

    @view_row_decorator
    def view_standalone(self, tn, mem, valstr, h, pid, u, o):
        olst = self.rdfeng.o_list(tn, mem.ref)
        for ref_obj in olst:
            ref_n = ref_obj.get('Name')
            ref_id = ref_obj.get('id')
            if ref_id == valstr:
                o.append(f'<div class="bg-light">{ref_n}</div>')

    @view_row_decorator
    def view_string(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div>{valstr}</div>')

    @view_row_decorator
    def view_text(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div class="bg-light">{valstr}</div>')

    @view_row_decorator
    def view_date(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div style="width: 150px; text-align: right;">{valstr}</div>')

    @view_row_decorator
    def view_int(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div style="width: 150px; text-align: right;">{valstr}</div>')

    @view_row_decorator
    def view_float(self, tn, mem, valstr, h, pid, u, o):
        try:
            val = float(valstr)
            o.append(f'<div style="width: 150px; text-align: right;">{val: ,2f}</div>')
            return
        except:
            o.append(f'<div style="width: 150px; text-align: right;">{valstr}</div>')

    @view_row_decorator
    def view_boolean(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div><b>{valstr.title()}</b></div>')

    @view_row_decorator
    def view_email(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div><a href="mailto:{valstr}">{valstr}</a></div>')

    def view_image(self, tn, mem, valstr, h, pid, u, o, bgc):
        img_data = json.loads(valstr) if valstr else None
        if img_data is None:
            o.append('<div><img src="img/unchecked.png" /></div>')
            return
        location_thumb = img_data.get('thumb') if img_data else 'img/picture.png'
        location_img = img_data.get('img') if img_data else 'img/picture.png'
        filename = img_data.get('filename') if img_data else ''
        o.append(f'<a href="{location_img}" target="_blank">'
                 f'<img src="{location_thumb}" style="max-width:400px;" alt="{filename}" title="{filename}" />'
                 f'</a>')

    @view_row_decorator
    def view_media(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: View media {mem.name} - {valstr}</h1>')

    @view_row_decorator
    def view_lang(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: View lang {mem.name} - {valstr}</h1>')

    @view_row_decorator
    def view_role(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: View role {mem.name} - {valstr}</h1>')

    @view_row_decorator
    def view_db_table(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: View DB table {mem.name} - {valstr}</h1>')

    @view_row_decorator
    def view_report_def(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div class="bg-light">{valstr}</div>')

    # --- View-tab methods - used to view properties in table view ---
    def resolve_report_def(self, tn, mem, valstr, h, pid, u, o, bgc):
        return (f'<div class="bg-light">'
                f'<button class="btn btn-primary" onclick="window.open(\'view?h={h}\')" mlang="view_report">'
                f'View report'
                f'</button>'
                f'</div>')

    # --- Predefined view methods for complex content objects ---
    def populate_rep_cache(self, tn, cache, var):
        if not var:
            return
        if len(var) == 1:
            return
        code = var[0]
        if code in cache:
            return
        objects = self.rdfeng.o_list(tn, code, True)
        cache[code] = objects
        cdef = self.rdfeng.schema.get_class(code)
        # print('Looping class', cdef.name)
        self.populate_rep_cache(tn, cache, var[1:])

    def init_rep_variables(self, variables, cache, rep, roots, select, where, order):
        # Prepare variables_by_expr
        variables_by_expr = {}
        for var_name, var_expr in variables.items():
            variables_by_expr.setdefault(var_expr, []).append(var_name)
        for root in roots:
            objects = cache.get(root)
            if not objects:
                continue
            for obj in objects:
                stack, row, header, body, keys = [root], [], rep.get('header'), rep.get('body'), rep.get('keys')
                self.loop_obj(obj, stack, row, variables_by_expr, select, where, order, header, body, keys)

    def loop_obj(self, obj, stack, row, variables_by_expr, select, where, order, header, body, keys):
        cdef = self.rdfeng.schema.get_class(obj.get('code'))
        properties = [p for p in obj.items() if p[0] not in ['id', 'hash', 'code', 'type']]
        self.loop_properties(cdef, properties, stack, row, variables_by_expr, select, where, order, header, body, keys)

    def loop_properties(self, cdef, properties, stack, row, variables_by_expr, select, where, order, header, body, keys):
        if len(properties) == 0:
            # print(stack, row)
            base = '.'.join(stack)
            # Init the variable
            for ndx, value in row:
                key = f'{base}.{ndx}'
                variable_names = variables_by_expr.get(key)
                if not variable_names:
                    continue
                for variable_name in variable_names:
                    if variable_name:
                        property_name = cdef.members.get(ndx).name
                        header[variable_name] = property_name
                        try:
                            exec(f'{variable_name}=\'{value}\'')
                        except:
                            pass

            # Evaluate order key - TODO
            # Evaluate select expressions
            result_row = []
            for expr in [s.split('|')[0] for s in select]:
                try:
                    result_value = eval(expr)
                    result_row.append(result_value)
                except:
                    result_row.append(None)

            if any(v for v in result_row if v is not None):
                # Evaluate where condition
                condition  = True
                for expr in where:
                    try:
                        local_condition = eval(expr)
                        if not local_condition:
                            condition = False
                    except:
                        condition = False

                if condition:
                    h = util.get_sha1(''.join(f'{result_row}'))
                    if h not in keys:
                        body.append(result_row)
                        keys.add(h)
            return

        first = properties[0]
        ndx = first[0]
        values = first[1]

        for value in values:
            if isinstance(value, dict):  # property is a complex object
                stack.append(ndx)
                self.loop_obj(value, stack, row, variables_by_expr, select, where, order, header, body, keys)
                stack.pop()
                continue

            # Property is simple string value
            row.append((ndx, value))
            self.loop_properties(cdef, properties[1:], stack, row, variables_by_expr, select, where, order, header, body, keys)
            row.pop()

    def play_custom_report(self, tn, obj, cdef):
        # rdf_h = h[0:40]
        # tn = h[40:]
        # obj, cdef = self.get_obj_and_cdef(tn, rdf_h)
        if obj is None:
            return '<h1>Object not found</h1>'
        if cdef is None or cdef.uri != 'custom_report':
            return '<h1>Wrong object type</h1>'

        data = obj.get('data')
        if data is None:
            return '<h1>Wrong object definition</h1>'

        try:
            rdef = json.loads(data.get('Definition')[0])
            title = data.get('Name')[0]
            variables = rdef.get('var')
            if not variables:
                return '<h1>Incorrect report definition - no variables defined.</h1>'
            select = rdef.get('select')
            if not select:
                return '<h1>Incorrect report definition - no select expressions defined.</h1>'
            where = rdef.get('where', [])
            order = rdef.get('order', [])

            # Step 1 - Prepare object cache
            cache = {}  # Here we store raw data
            roots = set([v.split('.')[0] for v in variables.values()])
            for pair in variables.items():
                var_name = pair[0]
                var = pair[1]
                self.populate_rep_cache(tn, cache, var.split('.'))

            # Step 2 - Evaluate variables
            # header => Header captions collected from variable definitions. If no header in variable definition,
            #           the caption is extracted from class definition.
            # body => the report data
            # keys => a set containing all unique hash codes generated by report rows content - only unique rows
            #         are included
            rep = {'header': {}, 'body': [], 'keys': set()}
            self.init_rep_variables(variables, cache, rep, roots, select, where, order)

            # Step 3 - Render report
            header = rep.get('header')
            body = rep.get('body')
            o = [f'<h1 style="margin-top: 30px;">{title}</h1>'
                 f'<table class="table table-bordered display dataTable"><thead>'
                 f'<tr class="table-info">']
            for expr in select:
                capt = expr.split('|')[1] if '|' in expr else header.get(expr, '-')
                o.append(f'<th>{capt}</th>')
            o.append('</tr></thead><tbody>')
            for row in body:
                o.append('<tr>')
                for value in row:
                    value_str = '&nbsp;' if value is None else value
                    o.append(f'<td>{value_str}</td>')
                o.append('</tr>')
            o.append(f'</tbody></table>')

            # Interactive table snippet - !! UNREM to enable interactive table !!
            o.append("""
<script>
$('.dataTable').each(function () {
    var t = $(this).DataTable({
        "paging":true,
        "ordering":true,
        "info":true,
        "pageLength": 50})
    t.order([]).draw();
});
</script>
            """)
            return ''.join(o)

        except Exception as ex:
            return f'<h1>Incorrect object definition: {ex}</h1>'





