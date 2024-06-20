import json


class RdfInputs:
    """ Implements methods to generate input controls for various RDF data """

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
