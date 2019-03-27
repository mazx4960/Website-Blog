# Website-Blog

A simple blog website that allows you to post questions and comments on posts

# Notes

This website was designed for me to learn more about the basic functionality of flask.

This website was created using Flask. Flask is a lightweight `WSGI`_ web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around `Werkzeug`_
and `Jinja`_ and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.


Installing
----------

Install and update using `pip`_:

    pip install -U Flask
    
Running the website

    cd <path to the app directory>
    export FLASK_APP=blog.py
    flask run
    
    
# Features

* User Authentication (Basic Implementation)
* SQL database to store all the user data
* Flask to handle all the routing request

# Future enhancements

* background threading for sending the email and posting
* Private messaging function
* Allows you to view user profile
* More robust User authentication system
* Implementation of emails
    * notify you when you have registered for an account (done)   
    * reset your password if you have forgotten it
* Allow more than one session at a time (done)
* Password hashing instead of just plain text (done)
* Better UI through CSS preferrably using bootstrap (done)
* Validates the fields of inputs (done)
