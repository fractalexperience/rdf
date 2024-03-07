import common.htmlutil as htmlutil

class RdfClass:
    def __init__(self, schema, parent, props):
        self.schema = schema
        self.parent = parent
        self.code = props.get('code')
        self.namespace = props.get('namespace')
        self.name = props.get('name')
        self.ndx = props.get('ndx')
        self.description = props.get('description')
        self.data_type = props.get('data_type')
        self.restriction = props.get('restriction')
        self.ref = props.get('ref')
        self.required = props.get('required')
        self.multiple = props.get('multiple')
        self.key = props.get('key')
        self.show = props.get('show')
        self.uri = props.get('uri')
        self.members = None  # By ndx
        self.members_by_name = None
        self.members_by_uri = None

    def add_member(self, mem):
        if self.members is None:
            self.members = {}
        if self.members_by_name is None:
            self.members_by_name = {}

        if mem.name in self.members_by_name:
            self.schema.errors.append(f'Duplicate property name <b>{mem.name}</b> for class <b>{self.name}</b>')
        else:
            self.members_by_name[mem.name] = mem

        if mem.ndx in self.members:
            self.schema.errors.append(f'Duplicate property index <b>{mem.ndx}</b> for property <b>{mem.name}</b> in class <b>{self.name}</b>')
        else:
            self.members[mem.ndx] = mem

    def r_html(self, o, html_class):
        attr = f'class="{html_class}" id="{self.code}"'
        htmlutil.wrap_tr(o, [
            ('style="text-align: right;"', self.code), self.name, self.ndx,
            self.description, self.data_type, ('style="color: Blue;"', f'<samp>{self.restriction}</samp>'),
            f'<a href="#{self.ref}">{self.ref}</a>', self.required, self.multiple, self.key, self.show, self.namespace
        ], attr)
