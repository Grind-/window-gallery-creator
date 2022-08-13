# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from copy import deepcopy
from datetime import datetime
from json import dump, dumps

from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from flask_login import login_required
from jinja2 import TemplateNotFound
from sqlalchemy import update
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from apps import db, login_manager
from apps.authentication.models import User
from apps.user_information.models import NaturalPerson
from apps.user_information.schemas import CreateNaturalPerson, CreateNaturalPersonSchema,\
    NaturalPersonSchema
from apps.creator import blueprint
from apps.creator.forms import NaturalPersonForm
from flask.wrappers import Response
from apps.creator.functions import gen_frames


@blueprint.route('/creator/<template>', methods=['GET', 'POST'])
@login_required
def creator_template(template):

    # Detect the current page
    segment = get_segment(request)

    if 'personal-data' in request.form:
        natural_person = NaturalPerson(**request.form, user_id=current_user.id)
        add_or_update_db(NaturalPerson, natural_person)
        segment = template = 'personal-data'

    if 'creator' in request.form:
        natural_person = NaturalPerson(**request.form, user_id=current_user.id)
        # add_or_update_db(NaturalPerson, natural_person)
        segment = template = 'creator'

    try:

        if not template.endswith('.html'):
            template += '.html'
            
        if segment == 'creator':
            query = db.session.query(NaturalPerson).filter_by(user_id=current_user.id).first()
            if query:
                form = NaturalPersonForm(obj=query)
            else:
                form = NaturalPersonForm(request.form)

        if segment == 'personal-data':
            query = db.session.query(NaturalPerson).filter_by(user_id=current_user.id).first()
            if query:
                form = NaturalPersonForm(obj=query)
            else:
                form = NaturalPersonForm(request.form)

        return render_template("creator/" + template, segment=segment,
                               form=form, username='username')

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500

# def gen_frames():  
#     while True:
#         success, frame = camera.read()  # read the camera frame
#         if not success:
#             break
#         else:
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@blueprint.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@blueprint.route('/nac-uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        return redirect(url_for('creator_blueprint.creator_template', template='tax-information'))


# Helper - Extract current page name from request
def get_segment(request):

    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None


def add_or_update_db(model, form):
    form_dict = vars(form)
    for key, value in form_dict.items():
        if key in vars(model) and hasattr(vars(model)[key], 'type') and str(vars(model)[key].type) == str(db.DateTime()):  # undefinedVariable
            setattr(form, key, datetime.strptime(value, '%Y-%m-%d'))
    if db.session.query(db.exists().where(model.user_id == current_user.id)).scalar():
        form_dict = vars(deepcopy(form))
        del form_dict['_sa_instance_state']
        db.session.query(model).filter_by(user_id=current_user.id).update(form_dict)
    else:
        db.session.add_all([form])
    db.session.commit()


def send_to_api():
    natural_person = db.session.query(NaturalPerson).filter_by(user_id=current_user.id).first()
    bank_account = db.session.query(BankAccount).filter_by(user_id=current_user.id).first()
    tax_information = db.session.query(TaxInformation).filter_by(user_id=current_user.id).first()
    create_natural_person = CreateNaturalPerson(is_beneficiary=True,
                                                pep_status=False,
                                                non_assessment_certificate=True,
                                                account_setup_accepted_at=natural_person.time_created,
                                                natural_person=natural_person,
                                                bank_account=bank_account,
                                                tax_information=tax_information)
    dump_data = CreateNaturalPersonSchema().dump(create_natural_person)
    db.session.query(User).filter_by(id=current_user.id).update({'investor_id': investor_id})
    db.session.commit()
