import peewee
from marshmallow import Schema, validate, post_load, fields, pre_dump
from marshmallow.schema import SchemaMeta


translation_table = {
    peewee.IntegerField: fields.Int,
    peewee.FloatField: fields.Float,
    peewee.DecimalField: fields.Decimal,
    peewee.CharField: fields.String,
    peewee.TextField: fields.String,
    peewee.UUIDField: fields.UUID,
    peewee.DateTimeField: fields.DateTime,
    peewee.DateField: fields.Date,
    peewee.TimeField: fields.Time,
    peewee.TimestampField: fields.Int,
    peewee.BooleanField: fields.Boolean,
}


class ModelSchemaMeta(SchemaMeta):
    def __new__(cls, clsname, superclasses, attributedict):
        if 'Meta' not in attributedict:
            return super().__new__(cls, clsname, superclasses, attributedict)
        model_fields = {}
        if not attributedict['Meta'].model:
            raise AssertionError('Meta.model is required')
        for name, field in attributedict['Meta'].model._meta.fields.items():
            for dbtype, schematype in translation_table.items():
                if not hasattr(attributedict['Meta'], 'fields') or name in attributedict['Meta'].fields:
                    if isinstance(field, dbtype):
                        params = {}
                        if isinstance(field, peewee.PrimaryKeyField):
                            params['dump_only'] = True
                        if hasattr(field, 'max_length'):
                            params['validate'] = validate.Length(max=field.max_length)
                        params['allow_none'] = field.null
                        params['default'] = field.default
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
            return self._instance
        else:
            return self.Meta.model(**data)

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
