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

from apps import db, login_manager
from apps.authentication.util import hash_pass


Base = declarative_base()


class User(db.Model, UserMixin):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    role = db.Column(db.String(64), unique=True)
    investor_id = db.Column(db.String(64), unique=True)

    natural_person = relationship(
        "NaturalPerson", back_populates="user", cascade="all, delete-orphan"
    )

    secrets = relationship(
        "Secrets", back_populates="user", cascade="all, delete-orphan"
    )
    communication = relationship(
        "Communication", back_populates="user", cascade="all, delete-orphan"
    )



    # create_natural_person = relationship(
    #     "CreateNaturalPerson", back_populates="user", cascade="all, delete-orphan"
    # )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if key == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return str(self.username)


class Communication(db.Model):

    __tablename__ = 'communication'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"), nullable=False)
    email = db.Column(db.String(64), unique=False)
    email_confirmed = db.Column(db.Boolean(), unique=False)

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return str(self.forename + ' ' + self.surname)

    user = relationship("User", back_populates="communication")


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
