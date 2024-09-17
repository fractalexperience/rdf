import json
from common.rdfclass import RdfClass
import common.htmlutil as htmlutil


class RdfSchema:
    def __init__(self, location):
        self.base = 'http://fractalexperience.com/rdf'
        self.location = location
        self.classes = None
        self.classes_by_uri = None
        self.classes_by_name = None

        # TODO - Set this from outside when initializing schema
        self.allowed_types = (
            'string', 'integer', 'float', 'boolean', 'date',
            'object', 'property', 'ref', 'email', 'text',
            # These here require special handling in UI
            'thumbnail', 'db_table', 'lang', 'image', 'media', 'report_def',
            'ts_creation',  'ts_modification', 'current_user', 'hash', 'user_role')
        self.errors = None

        self.init()
        self.check()

    def init(self):
        try:
            with open(self.location, 'r') as f:
                sh_raw = json.load(f)
                self.classes, self.classes_by_uri, self.classes_by_name = {}, {}, {}
                self.errors = []
                current_class = None
                current_namespace = None
                for props in sh_raw:
                    namespace = props.get('namespace')
                    code = props.get('code')
                    name = props.get('name')
                    uri = props.get('uri')
                    if not name:
                        continue
                    if not code and current_class is None:
                        continue
                    cls = RdfClass(self, current_class, props)
                    if namespace:
                        current_namespace = namespace
                    if not cls.namespace:
                        cls.namespace = current_namespace
                    if code:
                        self.classes[code] = cls
                        if uri in self.classes_by_uri:
                            self.errors.append(f'Duplicate URI for class {name} and {self.classes_by_uri.get(uri)}')
                        else:
                            self.classes_by_uri[uri] = cls

                        if name in self.classes_by_name:
                            self.errors.append(f'Duplicate class names: {name}')
                        else:
                            self.classes_by_name[name] = cls
                        current_class = cls
                        continue
                    if current_class:
                        current_class.add_member(cls)

            for name, cdef in self.classes.items():
                if not cdef.members:
                    continue
                for key, mem in cdef.members.items():
                    cdef.idx_mem_ndx[mem.name] = mem.ndx
                    mdef = self.get_class(mem.ref)
                    cdef.idx_memuri_ndx[mdef.uri] = mem.ndx

        except Exception as ex:
            print(ex)

    def check(self):
        if self.classes is None:
            return True  # Nothing to check
        for name, cls in self.classes.items():
            # If the class does not have members, check if there is a valid data type
            self.check_part(cls)
            if cls.members:
                for code, mem in cls.members.items():
                    self.check_part(mem)

    def check_part(self, part):
        if part.data_type not in self.allowed_types:
            self.errors.append(f'Unknown data type: {part.data_type} for [{part.code}] {part.name}')
        if part.code and not part.uri:
            self.errors.append(f'Missing uri for [{part.code}]')
        if not part.code and not part.ref:
            self.errors.append(f'Missing class reference for [{part.code}]')
        if not part.code and part.ref and part.ref not in self.classes:
            self.errors.append(f'Reference to non-existing class for [{part.code}]')
        if not (part.ndx or part.code):
            self.errors.append(f'Missing index (ndx) for [{part.name}] inside {part.parent.name}')

    def get_class(self, cn):
        # Search either by URI, or by name - this may be reconsidered
        return self.classes_by_uri.get(cn, self.classes_by_name.get(cn, self.classes.get(str(cn))))

    def get_all_properties(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.get_class(mem.ref)
            result.append((mdef.uri, mem.name))

    def get_optional_properties(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.get_class(mem.ref)
            if mem.data_type == 'property' and not mem.required:
                result.append((mdef.uri, mem.name))

    def get_mandatory_properties(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.get_class(mem.ref)
            if mem.data_type == 'property' and mem.required:
                result.append((mdef.uri, mem.name))

    def get_standalone_members(self, cdef, result):
        if cdef is None or not cdef.members:
            return
        for mem in cdef.members.values():
            mdef = self.get_class(mem.ref)
            if not mdef.members:
                continue
            # if mem.data_type == 'property':
            #     continue
            self.get_standalone_members(mdef, result)
            if mdef.data_type == 'object' and mem.data_type == 'ref':
                result.append((mdef.uri, mem.name))

    def get_class_properties(self, cdef, result):
        if not cdef or not cdef.members:
            return
        for ndx, mem in cdef.members.items():
            mdef = self.get_class(mem.ref)
            if mdef.members:
                continue
            result.append((mem.ndx, mem.name))

    def query(self, q):
        if q == 'enumerations':  # List rnumerations only - complex type objects having only one member
            return list(sorted([(cdef.uri, cdef.name) for code, cdef in self.classes.items()
                                if cdef.members and len(cdef.members) == 1], key=lambda t: t[1]))
        if q == 'complex':  # List objects having complex type
            return list(sorted([(cdef.uri, cdef.name) for code, cdef in self.classes.items()
                                if cdef.members and len(cdef.members) > 0], key=lambda t: t[1]))
        if q == 'simple':  # List objects having simple type
            return list(sorted([(cdef.uri, cdef.name) for code, cdef in self.classes.items()
                                if cdef.members is None], key=lambda t: t[1]))

        if '.all' in q:
            """ Collects all properties for the given class, or list of classes. """
            result = []
            cn = q.replace('$', '').replace('.all', '')
            cdefs = [c for c in self.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_all_properties(cdef, result)
            return result

        if '$' in q or '.optional' in q:
            """ Collects these members, which are: 
            - Not standalone - i.e. of type property
            - Not mandatory """
            result = []
            cn = q.replace('$', '').replace('.optional', '')
            cdefs = [c for c in self.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_optional_properties(cdef, result)
            return result

        if '.mandatory' in q:
            """ Collects mandatory members """
            result = []
            cn = q.replace('$', '').replace('.mandatory', '')
            cdefs = [c for c in self.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_mandatory_properties(cdef, result)
            return result

        if '^' in q or '.standalone' in q:
            """ Collects standalone members for the given class. This means these members, which are of type ref 
            (are instantiated separately) and only referred from class instances."""
            result = []
            cn = q.replace('^', '').replace('.standalone', '')
            cdefs = [c for c in self.classes.values() if (cn == '*' or c.uri in cn.split(',')) and c.members]
            for cdef in cdefs:
                self.get_standalone_members(cdef, result)
            return result

        if '.properties' in q:
            result = []
            uri = q.split('.')[0]
            cdef = self.get_class(uri)
            if not cdef:
                return result
            self.get_class_properties(cdef, result)
            return result

        return None

    def r_html(self):
        o = []
        for code in [k for k in self.classes.keys() if k.isnumeric()]:
            cdef = self.classes.get(code)
            cdef.r_html(o, "table-warning")
            if not cdef.members:
                continue
            for mem in cdef.members.values():
                mem.r_html(o, "table-light")
        htmlutil.wrap_h(
            o, ['code', 'inherits', 'name', 'ndx', 'description', 'data_type', 'restriction',
                'ref', 'required', 'multiple', 'key', 'show', 'uri'], 'RDF Schema')

        o2 = []
        if self.errors:
            cnt = 0
            for e in self.errors:
                cnt += 1
                htmlutil.wrap_tr(o2, [cnt, ('class="table-danger"', e)])
            htmlutil.wrap_h(o2, ['No.', 'Error message'], 'Errors')
        return ''.join(o2 + o)


