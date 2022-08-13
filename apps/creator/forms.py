# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField, DecimalField, TelField, SelectField, IntegerField
from wtforms.validators import Email, DataRequired, Optional


# create account
class NaturalPersonForm(FlaskForm):
    forename = StringField('Vorname',
                           id='forename',
                           validators=[DataRequired()])
    surname = StringField('Nachname',
                          id='surname',
                          validators=[DataRequired()])
    birth_date = DateField('Geburtstag',
                           id='birth_date',
                           format='%d/%m/%Y',
                           validators=[DataRequired()])
    birth_place = StringField('Geburtsort',
                              id='birth_place',
                              validators=[DataRequired()])
    citizenship = StringField('Nationalität',
                              id='citizenship',
                              validators=[DataRequired()])
    salutation = SelectField('Anrede',
                             id='salutation',
                             validators=[Optional()],
                             choices=['Herr', 'Frau', 'Divers'])
    phone = TelField('Telefonnummer',
                     id='phone',
                     validators=[Optional()])

    city = StringField('Stadt',
                       id='city',
                       validators=[DataRequired()])
    street = StringField('Straße',
                         id='street',
                         validators=[DataRequired()])
    number = IntegerField('Hausnummer',
                          id='number',
                          validators=[DataRequired()])
    country = SelectField('Land',
                          id='country',
                          validators=[DataRequired()],
                          choices=[' AU', 'DE', 'EN'])
    zip = IntegerField('Postleitzahl',
                       id='zip',
                       validators=[DataRequired()])


class InvestmentDataForm(FlaskForm):
    amount = IntegerField('Anzahl',
                          id='amount',
                          validators=[DataRequired()])


class IdentificationForm(FlaskForm):
    id_verified = IntegerField('ID Verified',
                               id='id_verified',
                               validators=[DataRequired()])


class SecuritiesDepositAccount(FlaskForm):
    account_holder = StringField('Kontoinhaber',
                                 id='account_holder',
                                 validators=[DataRequired()])
    account_number = StringField('Kontonummer',
                                 id='account_number',
                                 validators=[DataRequired()])
    bic = StringField('BIC',
                      id='bic',
                      validators=[DataRequired()])


class TaxInformationForm(FlaskForm):
    tax_identification_number = StringField('Steuer-Identifikationsnummer',
                                            id='tax_identification_number',
                                            validators=[DataRequired()])
    non_assessment_certificate = BooleanField('Nichtveranlagungs(NV)-Bescheinigung',
                                              id='non_assessment_certificate',
                                              validators=[DataRequired()])


class BankAccountForm(FlaskForm):
    account_holder = StringField('Kontoinhaber',
                                 id='account_holder',
                                 validators=[DataRequired()])
    bank = StringField('Bank',
                       id='bank',
                       validators=[DataRequired()])
    bic = StringField('BIC',
                      id='bic',
                      validators=[DataRequired()])
    country = SelectField('Land',
                          id='country',
                          validators=[DataRequired()],
                          choices=[' AU', 'DE', 'EN'])
    currency = SelectField('Währung',
                           id='currency',
                           validators=[DataRequired()],
                           choices=['EUR'])
    iban = StringField('IBAN',
                       id='iban',
                       validators=[DataRequired()])


class PostidentForm(FlaskForm):
    client_id = StringField('Postident Client ID',
                            id='client_id',
                            validators=[DataRequired()])


class ConfirmationForm(FlaskForm):
    accept = StringField('Aktzeptiere',
                         id='accept',
                         validators=[DataRequired()])
