import json
from rdf.py.common.rdfclass import RdfClass


class RdfSchema:
    def __init__(self, location):
        self.base = 'http://fractalexperience.com/rdf'
        self.location = location
        self.classes = None
        self.allowed_types = ('string', 'integer', 'float', 'boolean', 'date', 'object', 'property', 'ref')
        self.errors = None

        self.init()
        self.check()

    def init(self):
        try:
            with open(self.location, 'r') as f:
                sh_raw = json.load(f)
                self.classes = {}
                self.errors = []
                current_class = None
                for props in sh_raw:
                    code = props.get('code')
                    name = props.get('name')
                    if not name:
                        continue
                    if not code and current_class is None:
                        continue
                    cls = RdfClass(self, props)
                    if code:
                        self.classes[code] = cls
                        current_class = cls
                        continue
                    if current_class:
                        current_class.add_member(cls)

        except Exception as ex:
            print(ex)

    def check(self):
        if self.classes is None:
            return True  # Nothing to check
        for name, cls in self.classes.items():
            # If the class does not have members, check if there is a valid data type
            self.check_part(cls)
            if cls.members:
                for name, mem in cls.members.items():
                    self.check_part(mem)

    def check_part(self, part):
        if part.data_type not in self.allowed_types:
            self.errors.append(f'Unknown data type: {part.data_type} for [{part.code}] {part.name}')
        if part.code and not part.uri:
            self.errors.append(f'Missing uri for [{part.code}]')
        if not part.code and not part.ref:
            self.errors.append(f'Missing class reference for [{part.code}]')
        if not part.code and part.ref and part.ref not in self.classes:
            self.errors.append(f'Reference to unexisting class for [{part.code}]')
