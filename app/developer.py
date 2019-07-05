from flask import (
    Blueprint, Flask, request, render_template, redirect, url_for
)
# sessions is built on top of cookies
# which is sent to the server the authenticate the user
from flask import session

from werkzeug.security import generate_password_hash, check_password_hash

import smtplib
import threading
import requests
import json

from app.developer_auth import login_required, sign_in, error

bp = Blueprint('developer',__name__, url_prefix='/developer')

# BASE_URL = 'https://pure-atoll-42532.herokuapp.com'
BASE_URL = 'http://127.0.0.1:8080'
USERS_URL = '/user'
BLOGS_URL = '/blog'
COMMENTS_URL = '/comment'
FRIENDSHIPS_URL = '/friendship'


########################### Admin dashboard ###########################

@bp.route('/home')
@login_required
def dashboard():
    if 'admin_id' not in session:
        return render_template('developer/dev_sign_in.html')

    # get all data
    response = requests.get(BASE_URL + USERS_URL)
    users = json.loads(response.json())

    usernames = {}
    for user in users:
        usernames[user['user_id']] = user['username']

    response = requests.get(BASE_URL + BLOGS_URL)
    user_posts = json.loads(response.json())

    return render_template('developer/dashboard.html', users=users, user_posts=user_posts, usernames=usernames)

@bp.route('/promote/<int:user_id>')
@login_required
def promote(user_id):
    if 'admin_id' not in session:
        return render_template('dev_sign_in.html')

    parameters = {'user_id':user_id, 'admin':'true'}
    response = requests.put(BASE_URL + USERS_URL, params=parameters)
    return dashboard()

@bp.route('/demote/<int:user_id>')
@login_required
def demote(user_id):
    if 'admin_id' not in session:
        return render_template('dev_sign_in.html')

    parameters = {'user_id':user_id, 'admin':'false'}
    response = requests.put(BASE_URL + USERS_URL, params=parameters)
    return dashboard()

@bp.route('/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if 'admin_id' not in session:
        return render_template('dev_sign_in.html')

    parameters = {'user_id':user_id}
    response = requests.delete(BASE_URL + USERS_URL, params=parameters)
    return dashboard()
