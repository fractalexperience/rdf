class RdfClass:
    def __init__(self, schema, props):
        self.schema = schema
        self.code = props.get('code')
        self.namespace = props.get('namespace')
        self.name = props.get('name')
        self.description = props.get('description')
        self.data_type = props.get('data_type')
        self.restriction = props.get('restriction')
        self.ref = props.get('ref')
        self.required = props.get('required')
        self.multiple = props.get('multiple')
        self.key = props.get('key')
        self.show = props.get('show')
        self.uri = props.get('uri')
        self.members = None

    def add_member(self, mem):
        if self.members is None:
            self.members = {}
        self.members[mem.name] = mem

    def to_html(self, o, html_class):
        o.append(
            f'<tr class="{html_class}" id="{self.code}">'
            f'<td style="text-align: right;">{self.code}</td>'
            f'<td>{self.name}</td>'
            f'<td>{self.description}</td>'
            f'<td>{self.data_type}</td>'
            f'<td style="color: Blue;"><tt>{self.restriction}</tt></td>'
            f'<td><a href="#{self.ref}">{self.ref}</a></td>'
            f'<td>{self.required}</td>'
            f'<td>{self.multiple}</td>'
            f'<td>{self.key}</td>'
            f'<td>{self.show}</td>'
            f'<td>{self.namespace}/{self.uri}</td>'
            f'</tr>')
