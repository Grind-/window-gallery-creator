'''
Created on 19.06.2022

@author: jhirte
'''
# from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields
from marshmallow_sqlalchemy.fields import Nested
from apps.user_information.models import NaturalPerson, CreateNaturalPerson


class NaturalPersonSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NaturalPerson
        include_relationships = False
        load_instance = True
        exclude = ("id", "time_created", "time_updated",)


class CreateNaturalPersonSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CreateNaturalPerson
        include_relationships = True
        load_instance = True
        include_fk = False
        exclude = ("id",)

    natural_person = fields.Nested(NaturalPersonSchema)
