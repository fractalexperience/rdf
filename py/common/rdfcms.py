import json
import os

import common.util as util
from PIL import Image


class RdfCms:
    """ Content management for RDF engine """
    def __init__(self, schema, sqleng, base_rdf, base_data, assets_folder, data_folder):
        self.sqleng = sqleng
        self.schema = schema

        self.base_image = 'img'
        self.base_temp = 'temp'
        self.base_thumbnail = 'thumb'

        self.base_rdf = base_rdf
        self.base_data = base_data
        self.assets_folder = assets_folder
        self.data_folder = data_folder


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
            return None, None, False, 'Empty value'
        pdef = self.schema.get_class(puri)
        if not pdef:
            return None, None, False, f'Class not defined {puri}'
        mem = pdef.members_by_name.get(cname)
        if not mem:
            return None, None, False, f'{cname} is not defined as a property of {puri}'

        if cid:
            q = f'UPDATE {tn} SET o=NULL, v={self.sqleng.resolve_sql_value(v)} WHERE id={cid}' \
                if mem.data_type != 'ref' \
                else f'UPDATE {tn} SET v=NULL, o={v} WHERE id={cid}'
            self.sqleng.exec_update(q)
            return cid, None, True, 'Property updated'

        cdef = self.schema.get_class(mem.ref)
        if not cdef:
            return None, None, False, f'Property class not defined {mem.uri}'
        ndx = mem.ndx
        if mem.multiple and mem.multiple.lower() == 'true':
            # Only insert, because multiple properties of that type are allowed
            q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid},{ndx},NULL,{self.sqleng.resolve_sql_value(v)},NULL)"
            i = self.sqleng.exec_insert(q)
            return i, None, True, f'Property added {cname} to {puri}'
        if cid:
            q = f"SELECT id FROM {tn} WHERE s={pid} AND p={cid}"
            i = self.sqleng.exec_scalar(q)
            if i is not None:
                # Update
                q = f"UPDATE {tn} SET o='{v}', v=NULL WHERE id={i}"
                self.sqleng.exec_update(q)
                return i, None, True, f'Property {cname} updated for {puri}'

        q = f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid},{ndx},NULL,{self.sqleng.resolve_sql_value(v)},NULL)" \
            if mem.data_type != 'ref' \
            else f"INSERT INTO {tn} (s, p, o, v, h) VALUES({pid},{ndx},{v},NULL,NULL)"
        i = self.sqleng.exec_insert(q)
        return i, None, True, f'Property inserted {cname} for {puri}'

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
        path_img = os.path.join(path_user, self.base_image)
        if not os.path.exists(path_img):
            os.mkdir(path_img)
        path_thumb = os.path.join(path_user, self.base_thumbnail)
        if not os.path.exists(path_thumb):
            os.mkdir(path_thumb)

        ext = file.filename.split('.')[-1]
        new_filename = f'{util.get_id_sha1()}.{ext}'
        location_img = os.path.join(path_img, new_filename)
        location_thumb = os.path.join(path_thumb, new_filename)

        # Save image
        size = 0
        with open(location_img, 'wb') as out:
            while True:
                data = file.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)

        # Create thumbnail
        size = 512, 512
        with Image.open(location_img) as im:
            im.thumbnail(size)
            im.save(location_thumb, "JPEG")

        u_img = '/'.join([self.base_data, tn, self.base_image, new_filename])
        u_thumb = '/'.join([self.base_data, tn, self.base_thumbnail, new_filename])
        result = {'img': u_img, 'thumb': u_thumb, 'filename': file.filename}
        return json.dumps(result)
