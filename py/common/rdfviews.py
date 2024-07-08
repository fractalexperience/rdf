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


    @view_row_decorator
    def view_standalone(self, tn, mem, valstr, h, pid, u, o):
        # o.append(f'<div class="bg-dark fw-warning">{valstr}</div>')
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
