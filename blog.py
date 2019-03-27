import sqlite3

from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

import smtplib

import threading

# SECRETY_KET is needed in order to store sessions
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'

def get_db():
    db = sqlite3.connect('blog.sqlite3')
    db.row_factory = sqlite3.Row
    return db

@app.route('/', methods=['GET','POST'])
def sign_in():
    if request.method=='POST':
        username, password = request.form.get('username'), request.form.get('password')

        # checking if the username exists in the database
        db = get_db()
        user = db.execute('SELECT * FROM Users WHERE username=?',(username,)).fetchall()

        # checking if the password matches the one provided
        if user == [] or not check_password_hash(user[0][2], password):
            return error()
        else:
            session['user_id'] = user[0][0]
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
            db = get_db()
            if db.execute('SELECT * FROM Users WHERE username=?',(username,)).fetchall() != []:
                return error()
            else:
                hashed_password = generate_password_hash(password)
                db.execute('INSERT INTO Users (username,password) VALUES(?,?)', (username,hashed_password) )
                db.commit()

                # getting the user_id of the new user
                user_data = db.execute('SELECT id FROM Users WHERE username=?',(username,)).fetchall()
                session['user_id'] = user_data[0][0]

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
        # getting all the blogs posted by the current user
        user_id = session['user_id']
        db = get_db()
        user_posts = db.execute('SELECT * FROM Blogs WHERE blogger_id=?',(user_id,)).fetchall()
        user = db.execute('SELECT * FROM Users WHERE id=?',(user_id,)).fetchall()
        username = user[0][1]
        return render_template('home.html', user_posts=user_posts, username=username)

@app.route('/posts')
def posts():
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        # getting all the blogs posted
        db = get_db()
        user_posts = db.execute('SELECT * FROM Blogs').fetchall()
        return render_template('posts.html', user_posts=user_posts)

@app.route('/view/<int:id>/')
def view(id):
    if 'user_id' not in session:
        return render_template('sign_in.html')
    else:
        db = get_db()

        # storing the user id and the username in a dictionary
        users_data = db.execute('SELECT * FROM Users')
        users = {}
        for user_data in users_data:
            user = []
            users[user_data['id']] = user_data['username']

        # getting the specific blog data
        post_row = db.execute('SELECT * FROM Blogs WHERE id=?',(id,)).fetchall()
        post = {'blog_id':post_row[0][0],'question':post_row[0][2], 'blogger':users[post_row[0][1]]}

        # getting all the comments associated with the blog
        comments = db.execute('SELECT * FROM Comments WHERE blog_id=?',(id,)).fetchall()

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
            db = get_db()
            db.execute('INSERT INTO Blogs (blogger_id,post) VALUES (?, ?)' , (session['user_id'], post))
            db.commit()
            db.close()
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
            db = get_db()
            blog_row = db.execute('SELECT * FROM Blogs WHERE id=?',(blog_id,)).fetchall()
            db.execute('INSERT INTO Comments (user_id, comment, blog_id) \
            VALUES (?, ?, ?)' , (session['user_id'], comment, blog_row[0][0]))
            db.commit()
            db.close()
            return view(blog_id)
