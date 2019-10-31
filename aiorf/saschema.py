import sqlalchemy
from marshmallow import Schema, validate, post_load, fields, pre_dump
from marshmallow.schema import SchemaMeta

translation_table = {
    sqlalchemy.types.Integer: fields.Int,
    sqlalchemy.types.Float: fields.Float,
    sqlalchemy.types.DECIMAL: fields.Decimal,
    sqlalchemy.types.String: fields.String,
    sqlalchemy.types.DateTime: fields.DateTime,
    sqlalchemy.types.Date: fields.Date,
    sqlalchemy.types.Time: fields.Time,
    sqlalchemy.types.TIMESTAMP: fields.Int,
    sqlalchemy.types.Boolean: fields.Boolean,
}


class ModelSchemaMeta(SchemaMeta):
    def __new__(cls, clsname, superclasses, attributedict):
        if 'Meta' not in attributedict:
            return super().__new__(cls, clsname, superclasses, attributedict)
        model_fields = {}
        if not attributedict['Meta'].table:
            raise AssertionError('Meta.table is required')
        for name, column in attributedict['Meta'].table.columns.items():
            for dbtype, schematype in translation_table.items():
                if not hasattr(attributedict['Meta'], 'fields') or name in attributedict['Meta'].fields:
                    if isinstance(column.type, dbtype):
                        params = {}
                        if column.primary_key:
                            params['dump_only'] = True
                        if hasattr(column.type, 'length'):
                            params['validite'] = validate.Length(max=column.type.length)
                        params['allow_none'] = column.nullable
                        params['default'] = column.default
                        model_fields[name] = schematype(**params)
                        break
        new_attributedict = {}
        new_attributedict.update(model_fields)
        new_attributedict.update(attributedict)
        return super().__new__(cls, clsname, superclasses, new_attributedict)


class ModelSchema(Schema, metaclass=ModelSchemaMeta):
    @post_load(pass_many=True)
    def make_object(self, data, many, **kwargs):
        if not data:
            return None
        if self._instance:
            for k, v in data.items():
                setattr(self._instance, k, v)
            return self.Meta.table.update().where(self.Meta.table.primary_key==data[self.Meta.table.primary_key.name]).values(**data)
        else:
            return self.Meta.table.update(**data)

    def load(self, data, *, instance=None, **kwargs):
        self._instance = instance
        super().load(data, **kwargs)

#     @pre_dump
#     def dump_relations(self, data, pass_many=False):
#         for k, v in self.declared_fields.items():
#             if isinstance(v, ForeignKey):
#
#
#
#
# class ForeignKey(fields.Nested):
#     def __init__(self, nested, field_name, **kwargs):
#         super().__init__(nested, **kwargs)
#         self.field_name = field_name
