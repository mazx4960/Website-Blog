from flask import Flask, request, render_template, redirect, url_for

# sessions is built on top of cookies
# which is sent to the server the authenticate the user
from flask import session

from werkzeug.security import generate_password_hash, check_password_hash

import smtplib
import threading
import requests
import json

# SECRETY_KET is needed in order to store sessions
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'

# BASE_URL = 'https://pure-atoll-42532.herokuapp.com'
BASE_URL = 'http://127.0.0.1:8080'
USERS_URL = '/user'
BLOGS_URL = '/blog'
COMMENTS_URL = '/comment'


########################### User login page ###########################


@app.route('/', methods=['GET','POST'])
def sign_in():
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
        return redirect(url_for('home'))

    else:
        return render_template('sign_in.html')

@app.route('/sign_up/', methods=['GET','POST'])
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


########################### Admin dashboard ###########################


@app.route('/developer/', methods=['GET','POST'])
def dev_sign_in():
    # log users out of the main app
    session.pop('user_id', None)

    if 'admin_id' in session:
        return dev_dashboard()

    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # checking if the fields are empty
        if not username or not password:
            return dev_error()

        # checking if the username exists in the database
        parameters = { 'username': username }
        response = requests.get(BASE_URL + USERS_URL,params=parameters)

        if response.status_code == 404:
            return dev_error()

        user = json.loads(response.json())

        # checking if the password matches the one provided
        if not check_password_hash(user[0]['password'], password):
            return error()

        # checking if the account is admin
        if user[0]['admin'] != 'true':
            return dev_error()

        # all tests passed, adding the user_id to the session
        session['admin_id'] = user[0]['user_id']
        return redirect(url_for('dev_dashboard'))

    else:
        return render_template('dev_sign_in.html')

@app.route('/developer/sign_up/', methods=['GET','POST'])
def dev_sign_up():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        recipient_email = request.form.get('email')

        # checking if the field is null
        if not username or not password or not recipient_email:
            return dev_error()

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
            return dev_error()

        return render_template('dev_sign_in.html')
    else:
        return render_template('dev_sign_up.html')

@app.route('/developer/home/')
def dev_dashboard():
    if 'admin_id' not in session:
        return render_template('sign_in.html')

    # get all data
    response = requests.get(BASE_URL + USERS_URL)
    users = json.loads(response.json())

    usernames = {}
    for user in users:
        usernames[user['user_id']] = user['username']

    response = requests.get(BASE_URL + BLOGS_URL)
    user_posts = json.loads(response.json())

    return render_template('dashboard.html', users=users, user_posts=user_posts, usernames=usernames)

@app.route('/developer/promote/<int:user_id>')
def dev_promote(user_id):
    if 'admin_id' not in session:
        return render_template('sign_in.html')

    parameters = {'user_id':user_id, 'admin':'true'}
    response = requests.put(BASE_URL + USERS_URL, params=parameters)
    return dev_dashboard()

@app.route('/developer/demote/<int:user_id>')
def dev_demote(user_id):
    if 'admin_id' not in session:
        return render_template('sign_in.html')

    parameters = {'user_id':user_id, 'admin':'false'}
    response = requests.put(BASE_URL + USERS_URL, params=parameters)
    return dev_dashboard()

@app.route('/developer/log_out/')
def dev_log_out():
    session.pop('admin_id', None)
    return dev_sign_in()

@app.route('/developer/error/')
def dev_error():
    return render_template('dev_error.html')


########################### Blog home pages ###########################


# Handles all the exception cases
@app.route('/error/')
def error():
    return render_template('error.html')

@app.route('/home/')
def home():
    if 'user_id' not in session:
        return render_template('sign_in.html')

    # getting user details
    user_id = session['user_id']
    parameters = {'user_id':user_id}
    response = requests.get(BASE_URL + USERS_URL,params=parameters)

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

    # getting all the blogs posted
    response = requests.get(BASE_URL + BLOGS_URL)
    user_posts = json.loads(response.json())

    return render_template('posts.html', user_posts=user_posts)

@app.route('/view_post/<int:blog_id>/')
def view_post(blog_id):
    if 'user_id' not in session:
        return render_template('sign_in.html')

    # storing the user id and the username in a dictionary
    response = requests.get(BASE_URL + USERS_URL)
    users_data = json.loads(response.json())

    users = {}
    for user_data in users_data:
        users[user_data['user_id']] = user_data['username']

    # getting the specific blog data
    response = requests.get(BASE_URL + BLOGS_URL,params={'blog_id':blog_id})
    post_row = json.loads(response.json())

    post = {
        'blogger_id':post_row[0]['blogger_id'],
        'blog_id':post_row[0]['blog_id'],
        'post':post_row[0]['post'],
        'blogger':users[post_row[0]['blogger_id']]
    }

    # getting all the comments associated with the blog
    response = requests.get(BASE_URL + COMMENTS_URL + '/' + str(blog_id))
    comments = json.loads(response.json())

    return render_template('view_post.html', comments=comments, post=post, \
    users=users, session=session)

@app.route('/view_profile/<int:user_id>/')
def view_profile(user_id):
    if 'user_id' not in session:
        return render_template('sign_in.html')

    # storing the user id and the username in a dictionary
    parameters = { 'user_id':user_id }
    response = requests.get(BASE_URL + USERS_URL, params=parameters)
    users = json.loads(response.json())
    user = users[0]

    # getting the specific blog data
    response = requests.get(BASE_URL + BLOGS_URL,params={'blogger_id':user_id})
    posts = json.loads(response.json())

    return render_template('view_profile.html', posts=posts, user=user)


########################### Adding comments or post ###########################


@app.route('/add_post/', methods=['POST'])
def add_post():
    if 'user_id' not in session:
        return render_template('sign_in.html')

    post = request.form.get('post')
    if not post:
        return error()

    parameters = {'blogger_id':session['user_id'], 'post':post}
    response = requests.post(BASE_URL + BLOGS_URL, params=parameters)

    if response.status_code == 404:
        return error()

    return home()

@app.route('/add_comment/<int:blog_id>/', methods=['POST'])
def add_comment(blog_id):
    if 'user_id' not in session:
        return render_template('sign_in.html')

    comment = request.form.get('comment')
    if not comment:
        return error()

    parameters = {'user_id':session['user_id'], 'comment':comment}
    response = requests.post(BASE_URL + COMMENTS_URL + '/' + str(blog_id), params = parameters)

    # The user posting the comment is not registered
    if response.status_code == 404:
        return error()

    return view_post(blog_id)


########################### End of file ###########################
