import functools

from flask import (
    Blueprint, g, Flask, request, render_template, redirect, url_for
)
# sessions is built on top of cookies
# which is sent to the server the authenticate the user
from flask import session

from werkzeug.security import generate_password_hash, check_password_hash

import smtplib
import threading
import requests
import json

bp = Blueprint('developer_auth',__name__, url_prefix='/developer')

# BASE_URL = 'https://pure-atoll-42532.herokuapp.com'
BASE_URL = 'http://127.0.0.1:8080'
USERS_URL = '/user'
BLOGS_URL = '/blog'
COMMENTS_URL = '/comment'
FRIENDSHIPS_URL = '/friendship'


########################### Admin dashboard ###########################

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('admin_id') is None:
            return redirect(url_for('sign_in'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/', methods=['GET','POST'])
def sign_in():
    # log users out of the main app
    session.clear()

    if 'admin_id' in session:
        return dashboard()

    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # checking if the fields are empty
        if not username or not password:
            return error()

        # checking if the username exists in the database
        parameters = { 'username': username }
        response = requests.get(BASE_URL + USERS_URL,params=parameters)

        if response.status_code == 404:
            return error()

        user = json.loads(response.json())

        # checking if the password matches the one provided
        if not check_password_hash(user[0]['password'], password):
            return error()

        # checking if the account is admin
        if user[0]['admin'] != 'true':
            return error()

        # all tests passed, adding the user_id to the session
        session['admin_id'] = user[0]['user_id']
        return redirect(url_for('developer.dashboard'))

    else:
        return render_template('developer/dev_sign_in.html')

@bp.route('/sign_up', methods=['GET','POST'])
def sign_up():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        recipient_email = request.form.get('email')

        # checking if the field is null
        if not username or not password or not recipient_email:
            return error()

        # Checking if the user has registered before
        hashed_password = generate_password_hash(password)
        parameters = {
            'username':username,
            'password':hashed_password,
            'email':recipient_email,
            'admin':'pending'
        }
        response = requests.post(BASE_URL + USERS_URL,params=parameters)

        if response.status_code == 400:
            return error()

        return render_template('developer/dev_sign_in.html')
    else:
        return render_template('developer/dev_sign_up.html')


@bp.route('/log_out')
def log_out():
    session.pop('admin_id', None)
    return redirect(url_for('developer_auth.sign_in'))

@bp.route('/error')
def error():
    return render_template('developer/dev_error.html')
