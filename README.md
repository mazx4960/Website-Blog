# Website-Blog

A simple blog website that allows you to post questions and comments on posts

# About this project

This website was designed for me to learn more about the basic functionality of flask. It started off as a simple blogging website which allows users to post questions and comments. However, over the course of this project, I learnt more than what I expected to and encountered several road blocks. However, as I got more into this project, I envision it to be greater than just a simple blogging website.

In the future, this project could be expanded to become a one stop daily planner for everyone and also allows them to document all of their activities and experiences. This could serve as a one stop portal for users to do regular reflections and also plan out their daily commute and activities. 

# Notes

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
* Server side data implemented using RESTful API

# Future enhancements

### Priority updates
* Separating Blog title and Blog Content
* Setting a blog post to be seen by: myself, friends or everyone
* Deleting and editing Posts and Comments - only the ones written by you
* Updating the current location based on current time
* Tagging the blog post to the location

### Minor updates
* Tidy up the code using blueprints
* Add time stamp to comments
* Private messaging function
* Add API token authentication
* More robust User authentication system

### Completed updates
* Adding google calendar API support to pull data about your daily schedule
* Display day scehdule on home page 
* Change the home page interface: displaying only the daily schedule and adding new post while collapsing the posts today as well as the notifications
* Allow the searching of users
* Added collapsible navigation bar
* Allows you to add friends (done)
* Adding a new tab to the nav bar : (Today/Home, My Posts) replacing Home (done)
* Add time stamp to the blogs (done)
* Allows you to view user profile (done)
* Admin login dashboard to see all the users and activities (done)
* Implementation of emails
    * notify you when you have registered for an account (done)   
    * reset your password if you have forgotten it
* Migration of database to another server (done)
* Allow more than one session at a time (done)
* Password hashing instead of just plain text (done)
* Better UI through CSS preferrably using bootstrap (done)
* Validates the fields of inputs (done)
* background threading for sending the email and posting (done)
