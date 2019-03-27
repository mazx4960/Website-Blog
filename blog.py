import sqlite3
from flask import Flask, request, render_template, redirect, url_for
import smtplib

app = Flask(__name__)
session = {'logged_in':False, 'user_id':None}

def get_db():
    db = sqlite3.connect('blog.sqlite3')
    db.row_factory = sqlite3.Row
    return db

@app.route('/')
def sign_in():
    if session['logged_in']==False:
        return render_template('sign_in.html')
    else:
        return home()

@app.route('/log_out/')
def log_out():
    session['logged_in'] = False
    session['user_id'] = None
    return sign_in()

@app.route('/sign_in/submit/', methods=['POST'])
def sign_in_submit():
    username = request.form.get('username')
    password = request.form.get('password')
    db = get_db()
    user = db.execute('SELECT * FROM Users WHERE username=?',(username,)).fetchall()
    if user == [] or user[0][2] != password:
        return error()
    else:
        session['logged_in'] = True
        session['user_id'] = user[0][0]
        return redirect(url_for('home'))

@app.route('/sign_up/')
def sign_up():
    return render_template('sign_up.html')

@app.route('/sign_up/submit/', methods=['POST'])
def sign_up_submit():
    username = request.form.get('username')
    password = request.form.get('password')
    recipient_email = request.form.get('email')
    if not username or not password or not recipient_email:
        return error()
    else:
        db = get_db()
        if db.execute('SELECT * FROM Users WHERE username=?',(username,)).fetchall() != []:
            return error()
        else:
            db.execute('INSERT INTO Users (username,password) VALUES(?,?)', (username,password) )
            db.commit()
            session['logged_in'] = True
            id_row = db.execute('SELECT id FROM Users WHERE username=?',(username,)).fetchall()
            session['user_id'] = id_row[0][0]
            msg = "You have been registered successfully!\nUsername: {0}\nPassword: {1}\n".format(username,password)

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

            return redirect(url_for('home'))

@app.route('/error/')
def error():
    return render_template('error.html')

@app.route('/home/')
def home():
    if session['logged_in']==False:
        return redirect(url_for('sign_in'))
    else:
        user_id = session['user_id']
        db = get_db()
        user_posts = db.execute('SELECT * FROM Blogs WHERE blogger_id=?',(user_id,)).fetchall()
        user = db.execute('SELECT * FROM Users WHERE id=?',(user_id,)).fetchall()
        username = user[0][1]
        return render_template('home.html', user_posts=user_posts, username=username)

@app.route('/posts')
def posts():
    if session['logged_in']==False:
        return redirect(url_for('sign_in'))
    else:
        user_id = session['user_id']
        db = get_db()
        user_posts = db.execute('SELECT * FROM Blogs').fetchall()
        return render_template('posts.html', user_posts=user_posts)

@app.route('/view/<int:id>/')
def view(id):
    if session['logged_in']==False:
        return redirect(url_for('sign_in'))
    else:
        db = get_db()
        post_row = db.execute('SELECT * FROM Blogs WHERE id=?',(id,)).fetchall()
        comments = db.execute('SELECT * FROM Comments WHERE blog_id=?',(id,)).fetchall()
        users_data = db.execute('SELECT * FROM Users')
        users = {}
        for user_data in users_data:
            user = []
            users[user_data['id']] = user_data['username']
        post = {'blog_id':post_row[0][0],'question':post_row[0][2], 'blogger':users[post_row[0][1]]}
        print(post)
        return render_template('view.html', comments=comments, post=post, users=users, session=session)

@app.route('/add_post/', methods=['POST'])
def add_post():
    if session['logged_in']==False:
        return redirect(url_for('sign_in'))
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
    if session['logged_in']==False:
        return redirect(url_for('sign_in'))
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
