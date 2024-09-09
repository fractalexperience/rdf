import json
import datetime
import common.util as util

class RdfInputs:
    """ Implements methods to generate input controls for various RDF data """

    def __init__(self, rdfengine):
        self.rdfeng = rdfengine

        self.input_methods = {
            'standalone': self.input_standalone,
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
            'report_def': self.input_report_def,
            'current_user': self.input_current_user,
            'ts_creation': self.input_ts_creation,
            'ts_modification': self.input_ts_modification,
        }

    @staticmethod
    def input_row_decorator(method):
        def wrapper(self, tn, un, mem, valstr, h, pid, u, o, bgc):
            lbl = f'<b>{mem.name} *</b> ' if mem.required and mem.required.lower() == 'true' else mem.name
            o.append(f'<div class="row align-items-start" style="background-color: {bgc};">')
            o.append('<div class="col-2" style="text-align: right;">')
            o.append(f'<label for="{mem.name}" mlang="{mem.name}" class="text-primary">{lbl}</label>')
            o.append('</div>')
            o.append('<div class="col-10">')
            method(self, tn, un, mem, valstr, h, pid, u, o)
            o.append('</div></div>')
        return wrapper

    @input_row_decorator
    def input_standalone(self, tn, un, mem, valstr, h, pid, u, o):
        olst = self.rdfeng.o_list(tn, mem.ref)
        o.append(f'<select id="{mem.name}" mlang="{mem.name}" '
                 f'onchange="$(this).addClass(\'rdf-changed\')" '
                 f'class="form-select rdf-property" i="{pid}" p="{mem.name}" u="{u}" >'
                 f'<option value=""> ... </option>')
        for ref_obj in olst:
            ref_h = ref_obj.get('hash')
            ref_n = ref_obj.get('Name')
            ref_id = ref_obj.get('id')
            is_selected = ' selected="true"' if ref_id == valstr else ''
            o.append(f'<option value="{ref_id}"{is_selected}>{util.escape_xml(ref_n)}</option>')
        o.append('</select>')

    @input_row_decorator
    def input_string(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<input type="text" class="form-control rdf-property" value="{valstr}" id="{mem.name}" '
                 f'oninput="$(this).addClass(\'rdf-changed\')" '
                 f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_text(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<textarea type="text" class="form-control rdf-property" rows="2" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}">{valstr}</textarea>')

    @input_row_decorator
    def input_date(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="date" class="form-control rdf-property" style="width: 150px;" value="{valstr}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_ts_creation(self, tn, un, mem, valstr, h, pid, u, o):
        date_creation = valstr if valstr else datetime.datetime.now().strftime('%Y-%m-%d')
        o.append(
            f'<input type="date" class="form-control rdf-property" style="width: 150px;" value="{date_creation}" '
            f'disabled="true" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_ts_modification(self, tn, un, mem, valstr, h, pid, u, o):
        date_modification = datetime.datetime.now().strftime('%Y-%m-%d')
        o.append(
            f'<input type="date" class="form-control rdf-property" style="width: 150px;" value="{date_modification}" '
            f'disabled="true" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_current_user(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="text" class="form-control rdf-property" value="{un}" '
            f'disabled="true" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_int(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="number" step="1" class="form-control rdf-property" style="width: 150px;" value="{valstr}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_float(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="number" step="any" class="form-control rdf-property" style="width: 150px;" value="{valstr}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'id="{mem.name}" name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />')

    @input_row_decorator
    def input_boolean(self, tn, un, mem, valstr, h, pid, u, o):
        frag_checked = 'checked' if valstr.lower() == 'true' else ''
        o.append(
            f'<div class="form-check form-switch">'
            f'<input type="checkbox" {frag_checked} class="form-check-input rdf-property" value="{valstr}" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}" />'
            f'</div>')

    @input_row_decorator
    def input_email(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<input type="email" class="form-control rdf-property" style="width: 150px;" value="{valstr}" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" h="{h}" i="{pid}" p="{mem.name}" u="{u}" />')

    def input_image(self, tn, un, mem, valstr, h, pid, u, o, bgc):
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

    @input_row_decorator
    def input_media(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input media {mem.name}</h1>')

    @input_row_decorator
    def input_lang(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input lang {mem.name}</h1>')

    @input_row_decorator
    def input_role(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input role {mem.name}</h1>')

    @input_row_decorator
    def input_db_table(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: Input DB table {mem.name}</h1>')

    @input_row_decorator
    def input_report_def(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(
            f'<textarea type="text" class="form-control rdf-property" rows="2" id="{mem.name}" '
            f'oninput="$(this).addClass(\'rdf-changed\')" '
            f'name="{mem.name}" i="{pid}" p="{mem.name}" u="{u}">{valstr}</textarea>')
