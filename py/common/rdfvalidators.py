import json
import os.path
import datetime
import re

import pandas as pd
import common.util as util
import common.htmlutil as htmlutil


class RdfValidators:
    """ Implements validators for some known RDF objects with complex content """
    def __init__(self, rdfengine):
        self.rdfeng = rdfengine

        self.class_validators = {
            'user': self.v_user,
        }
        self.property_validators = {
            'email': self.v_email,
        }

        self.delete_validators = {
            'org' : self.v_del_org
        }

        self.success_message = 'Success'

    def v_generic(self, tn, cdef, data):
        if not cdef.members:
            return True, self.success_message
        for ndx, mem in cdef.members.items():
            mdef = self.rdfeng.schema.get_class(mem.ref)
            if not mdef:
                return False, f'Property not found: {cdef.name}.{mem.ref}'
            value = data.get(mem.name)
            if mem.required and not value:
                return False, f'Property is required: {mem.name}'
            method = self.property_validators.get(mdef.data_type)
            if method:
                success, message = method(value)
                if not success:
                    return success, message

        return True, self.success_message

    def v_user(self, tn, cdef, data):
        username = data.get('Username')
        email = data.get('Email')
        success, message = self.v_username(username)  # Check if user name is an NC name
        if not success:
            return success, message
        # Check if user name is unique
        # WARNING - property name and object code ar hard coded - TO IMPROVE!
        q = f"SELECT count(*) FROM {tn} WHERE v = '{email}' AND s in (SELECT id FROM root WHERE s = 101) AND p = 1"
        cnt = self.rdfeng.cms.sqleng.exec_scalar(q)
        if cnt:
            return False, 'User email already exists in database. It must be unique.'
        q = f"SELECT count(*) FROM {tn} WHERE v = '{username}' AND s in (SELECT id FROM root WHERE s = 101) AND p = 3"
        cnt = self.rdfeng.cms.sqleng.exec_scalar(q)
        if cnt:
            return False, 'Username already exists in database. It must be unique.'

        return True, self.success_message

    # Plain value validators -------------------------------------------------------------------------------------------
    def v_email(self, value):
        valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value)
        return (True, self.success_message) if valid else (False, 'Invalid email address')

    def v_username(self, value):
        if not value:
            return False, 'Empty user name'
        valid = re.match(r'^[a-zA-Z_][\w.-]*$', value)
        return (True, self.success_message) if valid else (False, 'Invalid user name')

    # On delete validators - whether an object can be deleted
    def v_del_org(self, value):

        return False, f'Organization {value} cannot be deleted!'