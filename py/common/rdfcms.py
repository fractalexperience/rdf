import json
import os
import pandas as pd
import re
import math

import common.util as util
import common.rdfschema as rdfschema
from PIL import Image


class RdfCms:
    """ Content management for RDF engine """

    def __init__(self, schema, sqleng, base_rdf, base_data, assets_folder, data_folder):
        self.sqleng = sqleng
        self.schema = schema

        self.base_image = 'img'
        self.base_media = 'media'
        self.base_temp = 'temp'
        self.base_thumbnail = 'thumb'

        self.base_rdf = base_rdf
        self.base_data = base_data
        self.assets_folder = assets_folder
        self.data_folder = data_folder
        self.img_formats = ['bmp', 'dds', 'gif', 'jpg', 'jpeg', 'png', 'tif', 'tiff']

    """
    The CMS methods return a tuple with the following structure: 
    t[0] : Technical id of the object
    t[1] : Hash code of the object if any
    t[2] : True if operation is successful, otherwise False
    t[3] : Message
    """

    def o_instantiate(self, tn, uri):
        """ Instantiates a new compound object and returns the new id. """
        cdef = self.schema.get_class(uri)
        if not cdef:
            print('ERROR: Class not found ', uri)
            return
        h = util.get_id_sha1()
        q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({cdef.code},NULL,NULL,NULL,'{h}')"
        i = self.sqleng.exec_insert(q)
        success = i is not None
        msg = f'Class instantiated {uri}' if success else f'ERROR: Class not instantiated {uri}'
        return i, h, success, msg

    def o_associate(self, tn, puri, pid, curi, cid, prop):
        """
        Associates two previously instantiated objects with complex content by assigning the second one as a property
        of the first one.
        :param tn: Name of the database table
        :param puri: URI of the class definition of the parent object
        :param pid: Internal id of the parent object (must be instantiated in the database)
        :param curi: URI of the class definition of the child object
        :param cid: Internal id of the child object (must be instantiated in the database)
        :param prop: Name of the property inside the members collection of the parent object
        :return: Internal id of the association, Error message if any
        """
        pdef = self.schema.get_class(puri)
        if not pdef:
            return None, None, False, f'Parent class not defined {puri}'
        cdef = self.schema.get_class(curi)
        if not cdef:
            return None, None, False, f'Property class not defined {curi}'
        mem = pdef.members_by_name.get(prop)
        if not mem:
            return None, None, False, f'Property not found {prop} inside class {puri}'
        ndx = mem.ndx

        if mem.multiple and mem.multiple.lower() == 'true':
            i = self.sqleng.exec_scalar(f"SELECT id FROM {tn} WHERE s={pid} AND p={ndx} and o='{cid}")
            if i is not None:
                return i, None, True, 'Reference exists'  # There is already a reference between parent and child of that type
            return self.o_create_reference(tn, pid, ndx, cid)

        i = self.sqleng.exec_scalar(f"SELECT id FROM {tn} WHERE s={pid} AND p={ndx}")  # Any association of that type
        if i is not None:
            q = f'UPDATE {tn} SET o={cid} WHERE id={i}'  # Just update the reference to che child - it must be only one
            self.sqleng.exec_update(q)
            return i, None, True, 'Reference updated'
        return self.o_create_reference(tn, pid, ndx, cid)

    def o_create_reference(self, tn, pid, ndx, cid):
        q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid}, {ndx}, {cid}, NULL, NULL)"
        i = self.sqleng.exec_insert(q)
        return i, None, True, f'Reference created {cid} to {pid}'

    def o_add_property(self, tn, puri, pid, cname, cid, v):
        """ Adds a property to an object
        :param tn: Name of th edatabase table
        :param puri: URI f the parent object
        :param pid: Internal id of the parent object
        :param cname: Name of the property
        :param cid: Internal id of the property
        :param v: String value of the property
        """
        if not v:
            return True, None, None, False, 'Empty value'
        pdef = self.schema.get_class(puri)
        if not pdef:
            return False, None, None, False, f'Class not defined {puri}'
        mem = pdef.members_by_name.get(cname)
        if not mem:
            return False, None, None, False, f'{cname} is not defined as a property of {puri}'

        if cid:
            q = f'UPDATE {tn} SET o=NULL, v={self.sqleng.resolve_sql_value(v)} WHERE id={cid}' \
                if mem.data_type != 'ref' \
                else f'UPDATE {tn} SET v=NULL, o={v} WHERE id={cid}'
            self.sqleng.exec_update(q)
            return True, cid, None, True, 'Property updated'

        cdef = self.schema.get_class(mem.ref)
        if not cdef:
            return False, None, None, False, f'Property class not defined {mem.uri}'
        ndx = mem.ndx
        if mem.multiple and mem.multiple.lower() == 'true':
            # Only insert, because multiple properties of that type are allowed
            q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid},{ndx},NULL,{self.sqleng.resolve_sql_value(v)},NULL)"
            i = self.sqleng.exec_insert(q)
            return True, i, None, True, f'Property added {cname} to {puri}'
        if cid:
            q = f"SELECT id FROM {tn} WHERE s={pid} AND p={cid}"
            i = self.sqleng.exec_scalar(q)
            if i is not None:
                # Update
                q = f"UPDATE {tn} SET o='{v}', v=NULL WHERE id={i}"
                self.sqleng.exec_update(q)
                return True, i, None, True, f'Property {cname} updated for {puri}'

        q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid},{ndx},NULL,{self.sqleng.resolve_sql_value(v)},NULL)" \
            if mem.data_type != 'ref' \
            else f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid},{ndx},{v},NULL,NULL)"
        i = self.sqleng.exec_insert(q)
        return True, i, None, True, f'Property inserted {cname} for {puri}'

    def o_read(self, tblname, obj_id, depth=0, use_ndx=False):
        if obj_id is None:
            return None
        if depth > 99:  # Not too deep recursion
            return None
        frag = f"r1.id={obj_id}" if isinstance(obj_id, int) or str(obj_id).isnumeric() else f"r1.h='{obj_id}'"
        q = ('SELECT '
             'r1.id AS obj_id, '
             'r1.h AS obj_h, '
             'r1.s AS code, '
             'r2.id AS prop_id, '
             'r2.p AS p, '
             'r2.o AS o, '
             'r2.v AS v '
             f'FROM {tblname} as r1 INNER JOIN {tblname} as r2 on r1.id=r2.s '
             f'WHERE {frag};')

        t = self.sqleng.exec_table(q)
        if t is None or len(t) == 0:
            return None

        r = t[0]  # There should be only one object with that hash code or id
        obj_id, obj_h, obj_code = r[0], r[1], r[2]
        cdef = self.schema.classes.get(str(obj_code))
        obj = {'id': obj_id, 'hash': obj_h, 'code': obj_code, 'type': cdef.name}
        dta = {}
        obj['data'] = dta
        for r in t:
            rdf_id, rdf_p, rdf_o, rdf_v = r[3], r[4], r[5], r[6]
            mdef = self.schema.classes.get(str(rdf_p))
            mem = cdef.members.get(str(rdf_p))
            if mem is None:
                continue
            mdef = self.schema.get_class(mem.ref)
            if mdef is None:
                continue

            # key = mem.ndx if use_ndx else mem.name
            if rdf_o is None:
                if use_ndx:
                    dta.setdefault(mem.ndx, []).append(rdf_v)
                    continue
                else:
                    if mem.name not in dta:
                        dta[mem.name] = (rdf_v, rdf_id)
                        continue
                    val_existing = dta.get(mem.name)
                    if isinstance(val_existing, tuple):
                        dta[mem.name] = [val_existing, (rdf_v, rdf_id)]
                        continue
                    if isinstance(val_existing, list):
                        val_existing.append((rdf_v, rdf_id))
                        continue

            if use_ndx:
                dta[mem.ndx] = (rdf_o, rdf_id)
            else:
                if mem.data_type == 'property':
                    obj_child = self.o_read(tblname, rdf_o, depth + 1)
                    dta[mem.name] = obj_child
                else:
                    # If we have a reference, we do not do the recursion in order to save processing time.
                    # This can be done later if needed.
                    dta[mem.name] = (rdf_o, rdf_id)
        return obj

    def o_seek(self, tn, uri, p_name, p_value):
        """ Identifies an object with a given class and having a given value for a specified property.
            If there are more than one objects, only returns the first one.
        """
        cdef = self.schema.get_class(uri)
        if cdef is None:
            return None
        p_ndx = cdef.idx_mem_ndx.get(p_name)
        if p_ndx is None:
            return None
        q = (f"SELECT r2.id as object_id "
             f"FROM {tn} as r1 INNER JOIN {tn} as r2 on r1.s = r2.id "
             f"WHERE r1.v = {self.sqleng.resolve_sql_value(p_value)} AND r1.p = {p_ndx} AND r2.s = {cdef.code} "
             f"LIMIT 1")
        obj_id = self.sqleng.exec_scalar(q)
        if obj_id is None:
            return None
        return self.o_read(tn, obj_id)

    def o_list2(self, tn, cn):
        """
        tn => Table name
        cn => class name
        """
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

            mem = cdef.members.get(str(rdf_p))
            if not mem:
                continue

            if rdf_o is not None and rdf_v is None:  # Referred object
                rdf_v = rdf_o

            curr_obj.setdefault(mem.ndx, []).append(rdf_v)

        return res

    def get_path_temp(self, tn):
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)
        path_user = os.path.join(self.data_folder, tn)
        if not os.path.exists(path_user):
            os.mkdir(path_user)
        path_temp = os.path.join(path_user, self.base_temp)
        if not os.path.exists(path_temp):
            os.mkdir(path_temp)
        return path_temp

    def uplimg(self, tn, file):
        """
        :param tn: Table name of the current user
        :param folder: Data folder, where user uploads have to be saved
        :param base: Base location - part of the image address
        :param file: File to be uploaded
        :return: JSON snippet containing image properties
        """
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)
        path_user = os.path.join(self.data_folder, tn)
        if not os.path.exists(path_user):
            os.mkdir(path_user)

        ext = file.filename.split('.')[-1]
        new_filename = f'{util.get_id_sha1()}.{ext}'

        base = self.base_image if ext.lower() in self.img_formats else self.base_media
        path = os.path.join(path_user, base)
        if not os.path.exists(path):
            os.mkdir(path)
        path_thumb = os.path.join(path_user, self.base_thumbnail)
        if not os.path.exists(path_thumb):
            os.mkdir(path_thumb)

        location = os.path.join(path, new_filename)
        location_thumb = os.path.join(path_thumb, new_filename)
        u_media = '/'.join([self.base_data, tn, base, new_filename])
        u_thumb = '/'.join([self.base_data, tn, self.base_thumbnail, new_filename])

        # Save image
        size = 0
        with open(location, 'wb') as out:
            while True:
                data = file.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)

        if ext.lower() in self.img_formats:
            # Create thumbnail
            size = 512, 512
            with Image.open(location) as im:
                im.thumbnail(size)
                im.save(location_thumb, "JPEG")
        else:
            u_thumb = f'img/{ext}.png'

        result = {'img': u_media, 'media': u_media, 'thumb': u_thumb, 'filename': file.filename}
        return json.dumps(result)

    def data_summary(self, tn, cn):
        lst = self.schema.query(cn)
        codes_str = ','.join([f'\'{self.schema.get_class(t[0]).code}\'' for t in lst])
        codes = set([self.schema.get_class(c[0]).code for c in lst])
        q = f'SELECT count(*) FROM {tn} WHERE h IS NOT NULL AND s IN ({codes_str})'
        num_total = self.sqleng.exec_scalar(q)
        o = [f'<div class="row">'
             f'<div class="col-6"><h1 mlang="data_summary">Data Summary</h1></div>'
             f'<div class="col-6" style="text-align: right; margin-top: 10px;">'
             f'<button type="button" class="btn btn-primary btn-sm" onclick="data_export()" id="dbexport" '
             f'mlang="data_export">Data Export</button>'
             f'<button type="button" class="btn btn-primary btn-sm" style="margin-left: 5px;" '
             f'onclick="data_import()" id="dbimport" mlang="data_export">Data Import</button>'
             f'<button type="button" class="btn btn-primary btn-sm" style="margin-left: 5px;" '
             f'onclick="mass_changes()" id="mass_changes" mlang="mass_changes">Mass Changes</button>'
             f'</div>'
             f'</div>'
             f'<table class="table table-bordered">'
             f'<tr class="table-info">'
             f'<th style="width: 40px;">Action</th>'            
             f'<th>Object name</th>'
             f'<th style="width: 60px;">Code</th>'
             f'<th>Object description</th>'
             f'<th style="text-align: right;">Count</th></tr>',
             f'<tr>'
             f'<td>&nbsp;</td>'
             f'<td colspan="3"><div mlang="total_rows">Total rows</div></td>'
             f'<td style="text-align: right;">{num_total}</td>'
             f'</tr>'
             f'<tr>'
             f'<td>&nbsp;</td>'
             f'<th colspan="3">Objects by type</th>'
             f'</tr>']

        q = f"SELECT s, count(s) FROM {tn} WHERE h IS NOT NULL AND s IN ({codes_str}) GROUP BY s ORDER BY s"
        t = self.sqleng.exec_table(q)
        cdefs = set()
        for r in t:
            code = f'{r[0]}'
            if code in codes:
                codes.remove(code)
            cnt = r[1]
            cdef = self.schema.get_class(code)
            if cdef is None or cdef.members is None:
                continue
            cdefs.add((cdef, cnt))
        for pair in sorted(cdefs, key= lambda p: p[0].name):
            cdef = pair[0]
            cnt = pair[1]
            self.append_code_row(o, cdef, cnt)

        # Append remaining codes
        for code in codes:
            cdef = self.schema.get_class(code)
            self.append_code_row(o, cdef, 0)

        o.append('</table>')
        return ''.join(o)

    def append_code_row(self, o, cdef, cnt):
        name = cdef.name
        desc = cdef.description
        o.append(f'<tr>'
                 f'<td>'
                 f'<button type="button" class="btn btn-primary btn-sm" style="margin-left: 5px;" '
                 f'onclick="update_content(\'output\', \'b?cn={cdef.uri}\')" '
                 f'id="btn_edit_{cdef.uri}" '
                 f'mlang="btn_edit">Edit</button>'
                 f'</td>'                
                 f'<td nowrap>{name}</td>'
                 f'<td>{cdef.code}</td>'
                 f'<td>{desc}</td>'
                 f'<td style="text-align: right;">{cnt}</td>'
                 f'</tr>')

    def data_export_sql(self, tn):
        q = f'SELECT * FROM {tn} ORDER BY id'
        t = self.sqleng.exec_table(q)
        content = [f'TRUNCATE TABLE {tn};']
        for r in t:
            rdf_id = r[0]
            s = r[1] if r[1] else 'NULL'
            p = r[2] if r[2] else 'NULL'
            o = r[3] if r[3] else 'NULL'
            v = r[4] if r[4] else 'NULL'
            h = r[5] if r[5] else 'NULL'
            sql = f"INSERT INTO {tn} (id, s, p, o, v, h) VALUES ({rdf_id}, {s}, {p}, {o}, {self.sqleng.resolve_sql_value(v)}, '{h}'); "
            content.append(sql)

        path = self.get_path_temp(tn)
        filename = 'dbexport.sql'
        filepath = os.path.join(path, filename)
        # if os.path.exists(filepath):
        #     os.remove(filepath)
        try:
            with open(filepath, 'w', encoding="utf-8") as f:
                f.write('\n'.join(content), )
            url = '/'.join([self.base_data, tn, self.base_temp, filename])
            return url
        except Exception as ex:
            print(ex)
            return ex

    def data_export_excel(self, tn):
        q = f'SELECT * FROM {tn} ORDER BY id'
        try:
            df = pd.read_sql(q, con=self.sqleng.connection)
            path = self.get_path_temp(tn)
            filename = 'dbexport.xlsx'
            filepath = os.path.join(path, filename)
            df.to_excel(filepath)
            url = '/'.join([self.base_data, tn, self.base_temp, filename])
            return url
        except Exception as ex:
            print(ex)
            return ex

    def data_export_json(self, tn):
        q = f'SELECT * FROM {tn} ORDER BY id'
        t = self.sqleng.exec_table(q)
        content = []
        for r in t:
            rdf_id = r[0]
            s = r[1]
            p = r[2]
            o = r[3]
            v = r[4]
            h = r[5]
            content.append({'id': rdf_id, 's': s, 'p': p, 'o': o, 'v': v, 'h': h})
        path = self.get_path_temp(tn)
        filename = 'dbexport.json'
        filepath = os.path.join(path, filename)
        with open(filepath, 'w') as f:
            json.dump(content, f)
        url = '/'.join([self.base_data, tn, self.base_temp, filename])
        return url

    def data_export(self, tn, fmt):
        if fmt == 'json':
            return self.data_export_json(tn)
        if fmt == 'excel':
            return self.data_export_excel(tn)
        if fmt == 'sql':
            return self.data_export_sql(tn)

        return f'Unsupported format: {fmt}'

    def mlang_import(self, tn, content):

        # path_user = os.path.join(self.data_folder, tn)
        new_filename = 'mlang_for_import.xlsx'
        path = self.get_path_temp(tn)
        location = os.path.join(path, new_filename)

        size = 0
        with open(location, 'wb') as out:
            while True:
                data = content.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)

        # Read existing mlang base
        mlang_file = os.path.join(self.assets_folder, 'mlang.json')
        with open(mlang_file, 'r', encoding="utf-8") as f:
            ml = json.load(f)

        df = pd.read_excel(location, index_col=None, header=None)
        for row in df.iterrows():
            print(row)
            key = row[1][0]
            if not key:
                continue
            entry = ml.setdefault(key, {})

            en = row[1][1]
            if en and en != math.nan:
                entry['en'] = en

            de = row[1][2]
            if de and de != math.nan:
                entry['de'] = de

            fr = row[1][3]
            if fr and fr != math.nan:
                entry['fr'] = fr

            it = row[1][4]
            if it and it != math.nan:
                entry['it'] = it

        with open(mlang_file, 'w', encoding="utf-8") as f:
            json.dump(ml, f)

        return (f'<br/>'
                f'<h2 mlang="mlang_imported">Multi-language strings are imported. Please reload page!</h2>')

    def mlang_export(self, tn):
        mlang_file = os.path.join(self.assets_folder, 'mlang.json')
        with open(mlang_file, 'r', encoding="utf-8") as f:
            keywords = json.load(f)
        types = {'html', 'py', 'js'}
        pattern = re.compile('mlang="(\\w+)"+')
        self.process_path(os.path.join(self.base_rdf, 'py'), pattern, types, keywords)
        self.process_path(os.path.join(self.base_rdf, 'js'), pattern, types, keywords)
        self.process_path(os.path.join(self.base_rdf, 'html'), pattern, types, keywords)

        schema_file = os.path.join(self.assets_folder, 'schema.json')
        schema = rdfschema.RdfSchema(schema_file)
        for code, cdef in schema.classes.items():
            self.upd_kwd(keywords, util.to_snakecase(cdef.name), en=cdef.name)
            if not cdef.members:
                continue
            for ndx, mem in cdef.members.items():
                self.upd_kwd(keywords, util.to_snakecase(mem.name), en=mem.name)

        m = []
        heading = ['key', 'en', 'de', 'fr', 'it']
        m.append(heading)
        for k, lst in keywords.items():
            m.append([k, lst.get('en'), lst.get('de'), lst.get('fr'), lst.get('it')])
        # return m
        # JSON format
        path = self.get_path_temp(tn)
        mlang_file_json = os.path.join(path, 'mlang.json')
        with open(mlang_file_json, 'w') as f:
            json.dump(keywords, f)
        url_json = '/'.join([self.base_data, tn, self.base_temp, 'mlang.json'])

        # Excel
        mlang_file_excel = os.path.join(path, 'mlang.xlsx')
        df = pd.DataFrame(m)
        df.to_excel(mlang_file_excel, header=False, index=False)
        url_excel = '/'.join([self.base_data, tn, self.base_temp, 'mlang.xlsx'])
        return (f'<br/>'
                f'<h1 mlang="export_ready">Export Ready</h1>'
                f'<br/>'
                f'<h5 mlang="download_json_format">Download JSON format: '
                f'<a href="{url_json}" target="_blank"><img src="img/json.png" width="42"></a></h5>'
                f'<h5 mlang="download_excel_format">Download Excel format: '
                f'<a href="{url_excel}" target="_blank"><img src="img/xlsx.png" width="42"></a></h5>')

    def upd_kwd(self, keywords, kw, en='', de='', fr='', it=''):
        d = keywords.setdefault(kw, {})
        if 'en' not in d:
            d['en'] = en
        if 'de' not in d:
            d['de'] = de
        if 'fr' not in d:
            d['fr'] = fr
        if 'it' not in d:
            d['it'] = it

    def process_path(self, path, pattern, types, keywords):
        w = os.walk(path, topdown=True)
        for (dirpath, dirnames, filenames) in w:
            for filename in filenames:
                ext = filename.split('.')[-1]
                if ext not in types:
                    continue
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r') as f:
                    s = f.read()
                    lst = pattern.findall(s)
                    for kw in lst:
                        # print(kw)
                        self.upd_kwd(keywords, kw, en='', de='', fr='', it='')

    def data_import(self, tn, content):
        o = []
        while True:
            data = content.file.read(8192)
            if not data:
                break
            o.append(data.decode())
        try:
            s = ''.join(o)
            data = json.loads(s)
            q = f'TRUNCATE TABLE {tn}'
            self.sqleng.exec_update(q)
            for r in data:
                rdf_id = r.get('id')
                s = r.get('s')
                s = s if s else 'NULL'
                p = r.get('p')
                p = p if p else 'NULL'
                o = r.get('o')
                o = o if o else 'NULL'
                v = r.get('v')
                v = v if v else 'NULL'
                h = r.get('h')
                h = h if h else 'NULL'
                q = f"INSERT INTO {tn} (id, s, p, o, v, h) VALUES ({rdf_id}, {s}, {p}, {o}, {self.sqleng.resolve_sql_value(v)}, \'{h}\')"
                self.sqleng.exec_update(q)

        except Exception as ex:
            return ex

    def data_masschg(self, tn, cn, pn, v):
        """
        :param tn: Table name
        :param cn: Class identifier (URI)
        :param pn: Property identifier (ndx)
        :param v: Property value
        :return: Mass change result message
        """
        cdef = self.schema.get_class(cn)
        if not cdef:
            return f'Error: Incorrect class identifier: {cn}'
        if not cdef.members:
            return f'Error: Incorrect class definition: {cn} - no complex content'
        mem = cdef.members.get(pn)
        if not mem:
            return f'Error: Incorrect property for class: {cn}'
        # This double nesting in the query is specific for MYSQL
        q = (f"UPDATE {tn} SET v={self.sqleng.resolve_sql_value(v)} "
             f"WHERE s in (SELECT id FROM (SELECT id FROM {tn} WHERE s={cdef.code}) as t) AND p = {35}")
        self.sqleng.exec_update(q)
        # Maybe we shall add INSERT statements for objects, which don't have the property yet
        return f'Property value changed to: {v} in class {cdef.name}'

    def get_user_data_js(self, tn, usr, pwd):
        """ Prepares a JSON notation for user object suitable for usage in JavaScript """
        u = self.o_seek(tn, 'user', 'Username', usr)

        h_pwd = util.get_sha1(pwd)
        h_usr = u.get('data', {}).get('Password hash')[0]
        if h_usr != h_pwd:
            return None

        if u is not None:
            d_usr = u.get('data', {})
            o_id = d_usr.get('Organization')[0]
            o = self.o_read(tn, o_id)
            d_org = o.get('data', {})
            d_org['hash'] = o.get('hash')
            u_data = {
                'hash': u.get('hash'),
                'username': f'{d_usr.get("Username")[0]}|{d_usr.get("Username")[1]}',
                'role': f'{d_usr.get("Role")[0]}|{d_usr.get("Role")[1]}',
                'name': f'{d_usr.get("Name")[0]}|{d_usr.get("Name")[1]}',
                'email': f'{d_usr.get("Email")[0]}|{d_usr.get("Email")[1]}',
                'lang': f'{d_usr.get("Language")[0]}|{d_usr.get("Language")[1]}',  # To improve
                'authenticated': True,
                'org': d_org,
                'db': d_org.get('Database')
            }
            return u_data

    def get_org_data_js(self, tn, u_hash):
        """ Returns organization data for a specific user to be used by JavaScript """
        o_obj = self.o_read(tn, u_hash, 0)
        if not o_obj:
            return None
        o_data = o_obj.get('data')
        if not o_data:
            return None
        org_hash = o_data.get('Organization', (None, None))[0]
        if not org_hash:
            return None
        org_obj = self.o_read(tn, org_hash, 0)
        if not org_obj:
            return None
        org_data = org_obj.get('data')
        if not org_data:
            return '{}'
        org = {'hash': org_obj.get('hash')}
        self.upd_obj_js(org_data, org, 'Name', 'name')
        self.upd_obj_js(org_data, org, 'Description', 'description')
        self.upd_obj_js(org_data, org, 'Suitable for children', 'children')
        self.upd_obj_js(org_data, org, 'Wheelchair accessible', 'wheelchair')
        self.upd_obj_js(org_data, org, 'Restaurant/Cafe', 'cafe')
        self.upd_obj_js(org_data, org, 'WC', 'wc')
        self.upd_obj_js(org_data, org, 'Parking', 'parking')
        self.upd_obj_js(org_data, org, 'Museums Card', 'card')
        address = org_data.get('Address')
        address_data = address.get('data') if address else None
        self.upd_obj_js(address_data, org, 'Country', 'country')
        self.upd_obj_js(address_data, org, 'ZIP code', 'zip')
        self.upd_obj_js(address_data, org, 'City', 'city')
        self.upd_obj_js(address_data, org, 'Address line 2', 'address1')
        self.upd_obj_js(address_data, org, 'Address line 1', 'address2')
        return org

    def upd_obj_js(self, obj, obj_js, caption, key):
        """ Clips content of a tuple """
        obj_js[key] = '|'.join([f'{p}' for p in list(obj.get(caption, ()))])

