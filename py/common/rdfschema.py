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
            'thumbnail', 'db_table', 'lang')
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


