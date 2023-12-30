class RdfClass:
    def __init__(self, schema, props):
        self.schema = schema
        self.code = props.get('code')
        self.name = props.get('name')
        self.description = props.get('description')
        self.data_type = props.get('data_type')
        self.restriction = props.get('restriction')
        self.ref = props.get('ref')
        self.required = props.get('required')
        self.multiple = props.get('multiple')
        self.key = props.get('key')
        self.uri = props.get('uri')
        self.members = None

    def add_member(self, mem):
        if self.members is None:
            self.members = {}
        self.members[mem.name] = mem
