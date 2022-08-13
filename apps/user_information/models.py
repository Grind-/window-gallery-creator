# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json

from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from apps import db


Base = declarative_base()


class Secrets(db.Model):

    __tablename__ = 'secrets'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(64), unique=True)
    client_secret = db.Column(db.String(255), unique=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            if hasattr(self, key):
                setattr(self, key, value)

    user = relationship("User", back_populates="secrets")

    def __repr__(self):
        return str(self.username)


class NaturalPerson(db.Model):

    __tablename__ = 'natural_person'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    street = db.Column(db.String(64), unique=False)
    salutation = db.Column(db.String(64), unique=False)
    forename = db.Column(db.String(64), unique=False)
    surname = db.Column(db.String(64), unique=False)
    birth_date = db.Column(db.DateTime(timezone=True), unique=False)
    birth_place = db.Column(db.String(64), unique=False)
    citizenship = db.Column(db.String(64), unique=False)
    street = db.Column(db.String(64), unique=False)
    number = db.Column(db.Integer, unique=False)
    city = db.Column(db.String(64), unique=False)
    zip = db.Column(db.String(64), unique=False)
    country = db.Column(db.String(64), unique=False)
    phone = db.Column(db.String(64), unique=False)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return str(self.forename + ' ' + self.surname)

    user = relationship("User", back_populates="natural_person")



class CreateNaturalPerson(db.Model):

    __tablename__ = 'create_natural_person'

    id = db.Column(db.Integer, primary_key=True)
    natural_person_user_id = db.Column(db.Integer, ForeignKey("natural_person.user_id"))
    is_beneficiary = db.Column(db.Boolean(64), unique=False)
    pep_status = db.Column(db.Boolean(64), unique=False)
    account_setup_accepted_at = db.Column(db.DateTime)
    non_assessment_certificate = db.Column(db.Boolean(64), unique=False)

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return str(self.natural_person)

    natural_person = relationship("NaturalPerson", backref="create_natural_person")

