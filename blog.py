import sqlite3

from flask import Flask, request, render_template, redirect, url_for
# sessions is built on top of cookies which is sent to the server the authenticate the user
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

import smtplib
import threading
import requests
import json

# SECRETY_KET is needed in order to store sessions
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'

BASE_URL = 'https://pure-atoll-42532.herokuapp.com'
USERS_URL = '/user'
BLOGS_URL = '/blog'
COMMENTS_URL = '/comment'

@app.route('/', methods=['GET','POST'])
def sign_in():
    if request.method=='POST':
        username, password = request.form.get('username'), request.form.get('password')

        # checking if the username exists in the database
        response = requests.get(BASE_URL + USERS_URL,params={'username':username})
        if response.status_code == 404:
            return error()

        user = json.loads(response.json())

        # checking if the password matches the one provided
        if not check_password_hash(user[0]['password'], password):
            return error()

        session['user_id'] = user[0]['user_id']
        return redirect(url_for('home'))

    else:
        return render_template('sign_in.html')

@app.route('/sign_up/', methods=['GET','POST'])
def sign_up():
    if request.method=='POST':
        username, password = request.form.get('username'), request.form.get('password')
        recipient_email = request.form.get('email')

        # checking if the field is null
        if not username or not password or not recipient_email:
            return error()
        else:
            # Checking if the user has registered before
            hashed_password = generate_password_hash(password)
            parameters = {'username':username, 'password':hashed_password}
            response = requests.post(BASE_URL + USERS_URL,params=parameters)
            if response.status_code == 400:
                return error()

            # getting the user_id of the new user
            response = requests.get(BASE_URL + USERS_URL,params={'username':username})
            user = json.loads(response.json())
            session['user_id'] = user[0]['user_id']

            # sending the confirmation email in the background thread
            msg = "You have been registered successfully!\nUsername: {0}\nPassword: {1}\n".format(username,password)
            thread = threading.Thread(target=sendEmail, args=(recipient_email,msg))
            thread.daemon = True
            thread.start()

            return redirect(url_for('home'))
    else:
        return render_template('sign_up.html')

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

@app.route('/log_out/')
def log_out():
    session.pop('user_id', None)
    return sign_in()

# Handles all the exception cases
@app.route('/error/')
def error():
    return render_template('error.html')

@app.route('/home/')
def home():
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        # getting user details
        user_id = session['user_id']
        response = requests.get(BASE_URL + USERS_URL,params={'user_id':user_id})
        user = json.loads(response.json())
        username = user[0]['username']

        # getting all the blogs posted by the current user
        response = requests.get(BASE_URL + BLOGS_URL,params={'blogger_id':user_id})
        user_posts = json.loads(response.json())

        return render_template('home.html', user_posts=user_posts, username=username)

@app.route('/posts')
def posts():
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        # getting all the blogs posted
        response = requests.get(BASE_URL + BLOGS_URL)
        user_posts = json.loads(response.json())

        return render_template('posts.html', user_posts=user_posts)

@app.route('/view/<int:blog_id>/')
def view(blog_id):
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        # storing the user id and the username in a dictionary
        response = requests.get(BASE_URL + USERS_URL)
        users_data = json.loads(response.json())

        users = {}
        for user_data in users_data:
            user = []
            users[user_data['user_id']] = user_data['username']

        # getting the specific blog data
        response = requests.get(BASE_URL + BLOGS_URL,params={'blog_id':blog_id})
        post_row = json.loads(response.json())

        post = {'blog_id':post_row[0]['blog_id'],'question':post_row[0]['post'], 'blogger':users[post_row[0]['blogger_id']]}

        # getting all the comments associated with the blog
        response = requests.get(BASE_URL + COMMENTS_URL + '/' + str(blog_id))
        comments = json.loads(response.json())

        return render_template('view.html', comments=comments, post=post, users=users, session=session)

@app.route('/add_post/', methods=['POST'])
def add_post():
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        post = request.form.get('post')
        if not post:
            return error()
        else:
            parameters = {'blogger_id':session['user_id'], 'post':post}
            response = requests.post(BASE_URL + BLOGS_URL, params=parameters)
            if response.status_code == 404:
                return error()

            return home()

@app.route('/add_comment/<int:blog_id>/', methods=['POST'])
def add_comment(blog_id):
    # TODO add a comment to a post
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        comment = request.form.get('comment')
        if not comment:
            return error()
        else:
            parameters = {'user_id':session['user_id'], 'comment':comment}
            response = requests.post(BASE_URL + COMMENTS_URL + '/' + str(blog_id), params = parameters)

            return view(blog_id)
