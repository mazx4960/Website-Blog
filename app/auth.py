import functools

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

# for testing purposes
import os

bp = Blueprint('auth',__name__)

# BASE_URL = 'https://pure-atoll-42532.herokuapp.com'
BASE_URL = 'http://127.0.0.1:8080'
USERS_URL = '/user'
BLOGS_URL = '/blog'
COMMENTS_URL = '/comment'
FRIENDSHIPS_URL = '/friendship'


########################### User login page ###########################

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args,**kwargs):
        if session.get('user_id') is None:
            return render_template('blog/sign_in.html')

        return view(*args,**kwargs)

    return wrapped_view

@bp.route('/', methods=['GET','POST'])
def sign_in():
    # log users out of the developer app
    session.clear()
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

        # all tests passed, adding the user_id to the session
        session['user_id'] = user[0]['user_id']
        return redirect(url_for('blog.home'))

    else:
        return render_template('blog/sign_in.html')

@bp.route('/sign_up/', methods=['GET','POST'])
def sign_up():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        recipient_email = request.form.get('email')

        # checking if the field is null
        if not username or not password or not recipient_email:
            return error()

        hashed_password = generate_password_hash(password)
        parameters = {
            'username':username,
            'password':hashed_password,
            'email':recipient_email,
            'admin':'false'
        }
        response = requests.post(BASE_URL + USERS_URL,params=parameters)

        # Checking if the user has registered before
        if response.status_code == 400:
            return error()

        # getting the user_id of the new user
        parameters = {'username':username}
        response = requests.get(BASE_URL + USERS_URL,params=parameters)

        # adding the user_id to the session
        user = json.loads(response.json())
        session['user_id'] = user[0]['user_id']

        # sending the confirmation email in the background thread
        msg = "You have been registered successfully!\n"
        msg += "Username: {0}\nPassword: {1}\n".format(username,password)

        thread = threading.Thread(target=sendEmail, args=(recipient_email,msg))
        thread.daemon = True
        thread.start()

        return redirect(url_for('blog.home'))
    else:
        return render_template('blog/sign_up.html')

def sendEmail(recipient_email, msg):
    sender_email = "noreply9874321@gmail.com"
    #password = input("Enter your password: ")
    password = "qazwsx!@#123"

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.ehlo()
    server.starttls()
    # Ensure that you have enabled less secure app access in your email account
    server.login(sender_email,password)
    server.sendmail(sender_email,recipient_email,msg)
    server.quit()

@bp.route('/log_out/')
def log_out():
    session.clear()
    return redirect(url_for('sign_in'))

# Handles all the exception cases
@bp.route('/error/')
def error():
    return render_template('blog/error.html')
