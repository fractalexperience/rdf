import json
import os.path
import datetime

import pandas as pd
import common.util as util
import common.htmlutil as htmlutil


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
            'image': self.resolve_image,
            'media': self.resolve_media,
        }

        self.complex_content_view_methods = {
            'custom_report': self.play_custom_report,
        }

    @staticmethod
    def view_row_decorator(method):
        def wrapper(self, tn, un, mem, valstr, h, pid, u, o, bgc):
            o.append(f'<div class="row align-items-start">')
            o.append('<div class="col-2" style="text-align: right;">')
            o.append(
                f'<label for="{mem.name}" mlang="{mem.name}" class="text-primary">{mem.name}</label>')
            o.append('</div>')
            o.append('<div class="col-10">')
            method(self, tn, un, mem, valstr, h, pid, u, o)
            o.append('</div></div>')
        return wrapper

    # --- View methods - used to view properties in form ---

    @view_row_decorator
    def view_standalone(self, tn, un, mem, valstr, h, pid, u, o):
        olst = self.rdfeng.o_list(tn, mem.ref)
        for ref_obj in olst:
            ref_n = ref_obj.get('Name')
            ref_id = ref_obj.get('id')
            if ref_id == valstr:
                o.append(f'<div class="bg-light">{ref_n}</div>')

    @view_row_decorator
    def view_string(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<div>{valstr}</div>')

    @view_row_decorator
    def view_text(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<div class="bg-light">{valstr}</div>')

    @view_row_decorator
    def view_date(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<div style="width: 150px; text-align: right;">{valstr}</div>')

    @view_row_decorator
    def view_int(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<div style="width: 150px; text-align: right;">{valstr}</div>')

    @view_row_decorator
    def view_float(self, tn, un, mem, valstr, h, pid, u, o):
        try:
            val = float(valstr)
            o.append(f'<div style="width: 150px; text-align: right;">{val: ,2f}</div>')
            return
        except:
            o.append(f'<div style="width: 150px; text-align: right;">{valstr}</div>')

    @view_row_decorator
    def view_boolean(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<div><b>{valstr.title()}</b></div>')

    @view_row_decorator
    def view_email(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<div><a href="mailto:{valstr}">{valstr}</a></div>')

    def view_image(self, tn, un, mem, valstr, h, pid, u, o, bgc):
        img_data = json.loads(valstr) if valstr else None
        if img_data is None:
            o.append('<div><img src="img/picture.png" width="45px" /></div>')
            return
        location_thumb = img_data.get('thumb') if img_data else 'img/picture.png'
        location_img = img_data.get('img') if img_data else 'img/picture.png'
        filename = img_data.get('filename') if img_data else ''
        o.append(f'<a href="{location_img}" target="_blank">'
                 f'<img src="{location_thumb}" style="max-width:150px;" alt="{filename}" title="{filename}" />'
                 f'</a>')

    def view_media(self, tn, un, mem, valstr, h, pid, u, o, bgc):
        img_data = json.loads(valstr) if valstr else None
        if img_data is None:
            o.append('<div><img src="img/unchecked.png" /></div>')
            return
        location_thumb = img_data.get('thumb') if img_data else 'img/media.png'
        location_img = img_data.get('media') if img_data else 'img/media.png'
        filename = img_data.get('filename') if img_data else ''
        o.append(f'<a href="{location_img}" target="_blank">'
                 f'<img src="{location_thumb}" style="max-width:100px;" alt="{filename}" title="{filename}" />'
                 f'</a>')

    @view_row_decorator
    def view_lang(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: View lang {mem.name} - {valstr}</h1>')

    @view_row_decorator
    def view_role(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h1>TODO: View role {mem.name} - {valstr}</h1>')

    @view_row_decorator
    def view_db_table(self, tn, un, mem, valstr, h, pid, u, o):
        o.append(f'<h4>{valstr}</h4>')

    @view_row_decorator
    def view_report_def(self, tn, mem, valstr, h, pid, u, o):
        o.append(f'<div class="bg-light">{valstr}</div>')

    # --- View-tab methods - used to view properties in table view ---
    def resolve_report_def(self, tn, un, mem, valstr, h, pid, u, o, bgc):
        return (f'<div class="bg-light">'
                f'<span id="view_{h}">'
                f'<button class="btn btn-primary btn-sm" onclick="window.open(\'view?h={h}\')" mlang="view_report">'
                f'View'
                f'</button></span>'
                f'<span id="export_{h}" style="margin-left: 10px;">'
                f'<button class="btn btn-primary btn-sm" '
                f'onclick="update_content(\'export_{h}\', \'view?h={h}&format=excel\')" mlang="export_excel">'
                f'Export to Excel'
                f'</button></span>'
                f'</div>')

    def resolve_image(self, tn, un, mem, valstr, h, pid, u, o, bgc):
        o2 = []
        img_data = json.loads(valstr) if valstr else None
        if img_data is None:
            return 'n.a.'
        location_thumb = img_data.get('thumb') if img_data else 'img/picture.png'
        location_img = img_data.get('img') if img_data else 'img/picture.png'
        filename = img_data.get('filename') if img_data else ''
        o2.append(f'<img src="{location_thumb}" style="max-width:80px;" alt="{filename}" title="{filename}" />')
        return ''.join(o2)

    def resolve_media(self, tn, un, mem, valstr, h, pid, u, o, bgc):
        o2 = []
        img_data = json.loads(valstr) if valstr else None
        if img_data is None:
            return 'n.a.'
        location_thumb = img_data.get('thumb') if img_data else 'img/media.png'
        location_img = img_data.get('media') if img_data else 'img/media.png'
        filename = img_data.get('filename') if img_data else ''
        o2.append(f'<img src="{location_thumb}" style="max-width:80px;" alt="{filename}" title="{filename}" />')
        return ''.join(o2)

    # --- Methods, which can be used inside reports select areas
    def resolve_img(self, s):
        imgdef = json.loads(s)
        url_img = imgdef.get('img')
        filename = imgdef.get('filename')
        url_thumb = imgdef.get('thumb')
        return f'<a href="{url_img}" target="_blank"><img src="{url_thumb}" width="100px" alt="{filename}" /></a>'

    # --- Predefined view methods for complex content objects ---
    # def populate_rep_cache(self, tn, cache, var):
    #     if not var:
    #         return
    #     if len(var) == 1:
    #         return
    #     code = var[0]
    #     if code in cache:
    #         return
    #     objects = self.rdfeng.o_list(tn, code, True)
    #     cache[code] = objects
    #     cdef = self.rdfeng.schema.get_class(code)
    #     # print('Looping class', cdef.name)
    #     self.populate_rep_cache(tn, cache, var[1:])

    def play_custom_report(self, tn, obj, cdef, fmt):
        if obj is None:
            return '<h1>Object not found</h1>'
        if cdef is None or cdef.uri != 'custom_report':
            return '<h1>Wrong object type</h1>'

        data = obj.get('data')
        if data is None:
            return '<h1>Wrong object definition</h1>'

        return self.rdfeng.rep.r_rep(tn, fmt, data)



