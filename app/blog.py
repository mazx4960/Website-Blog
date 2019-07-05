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

from datetime import datetime, timedelta

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from app.auth import login_required, sign_in, error

bp = Blueprint('blog',__name__)

# BASE_URL = 'https://pure-atoll-42532.herokuapp.com'
BASE_URL = 'http://127.0.0.1:8080'
USERS_URL = '/user'
BLOGS_URL = '/blog'
COMMENTS_URL = '/comment'
FRIENDSHIPS_URL = '/friendship'

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "app/client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SCOPES = ['openid','https://www.googleapis.com/auth/calendar.readonly',\
            'https://www.googleapis.com/auth/userinfo.email',\
            'https://www.googleapis.com/auth/userinfo.profile']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


########################### Blog home pages ###########################

# time convertion function for home page
def timeIn12h(time):
    if int(time[:2]) == 12:
        return "{}:{} PM".format(time[:2],time[3:5])
    elif int(time[:2]) == 0:
        return "{}:{} AM".format('12',time[3:5])
    elif int(time[:2]) > 12:
        return "{}:{} PM".format((int(time[:2])-12),time[3:5])
    else:
        return "{}:{} AM".format(int(time[:2]),time[3:5])

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

@bp.route('/home')
@login_required
def home():

    # getting the users friend list
    parameters = { 'user_id':session['user_id'] }
    response = requests.get(BASE_URL + FRIENDSHIPS_URL, params=parameters)

    friends = json.loads(response.json())
    pending_req = []
    for friend in friends.keys():
        if friends[friend] == 'pending':
            pending_req.append(int(friend))

    # getting user details
    response = requests.get(BASE_URL + USERS_URL)

    users_data = json.loads(response.json())
    users = {}
    for user_data in users_data:
        users[user_data['user_id']] = user_data['username']

    # getting all the blogs posted by the current user
    response = requests.get(BASE_URL + BLOGS_URL,params={'blogger_id':session['user_id']})
    data = json.loads(response.json())

    user_posts = []
    timestamp = datetime.now().strftime('%Y-%m-%d')
    for post in data:
        if post['timestamp'][:10] == timestamp:
            user_posts.append(post)

    # Getting all the upcoming events for the day
    if 'credentials' not in session:
        # return flask.redirect('authorize') -> sign in button
        events = 'signed_out'
    else:
        # Load credentials from the session.
        credentials = google.oauth2.credentials.Credentials(
            **session['credentials'])

        calendar = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        # generating the start and end timestamp
        start = datetime.utcnow().date().isoformat() + 'T00:00:00Z' # 'Z' indicates UTC time
        end = (datetime.utcnow().date() + timedelta(days=1)).isoformat() + 'T00:00:00Z' # 'Z' indicates UTC time

        events_result = calendar.events().list(calendarId='primary', timeMin=start,
                                            timeMax=end, singleEvents=True,
                                            orderBy='startTime').execute()

        events = []
        for event in events_result.get('items', []):
            temp = {
                "summary"   :event['summary'],
                "location"  :event['location'] if 'location' in event.keys() else '',
                "start"     :timeIn12h(event['start'].get('dateTime')[11:19]),
                "end"       :timeIn12h(event['end'].get('dateTime')[11:19])
            }
            events.append(temp)

        # Save credentials back to session in case access token was refreshed.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        session['credentials'] = credentials_to_dict(credentials)

    return render_template('blog/home.html', events=events, session=session,
                    user_posts=user_posts, users=users, pending_req=pending_req)

@bp.route('/authorize')
@login_required
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for('blog.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state
    print(authorization_url)

    return redirect(authorization_url)

@bp.route('/oauth2callback')
@login_required
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('blog.oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('blog.home'))

@bp.route('/revoke')
@login_required
def revoke():
    if 'credentials' not in session:
        return redirect(url_for('error'))

    credentials = google.oauth2.credentials.Credentials(
    **session['credentials'])

    revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        clear_credentials()
        return redirect(url_for('blog.home'))
    else:
        return redirect(url_for('auth.error'))

@bp.route('/clear')
@login_required
def clear_credentials():
    if 'credentials' in session:
        session.pop('credentials',None)
    return redirect(url_for('blog.home'))

@bp.route('/myposts')
@login_required
def myposts():

    # getting user details
    user_id = session['user_id']

    # getting all the blogs posted by the current user
    response = requests.get(BASE_URL + BLOGS_URL,params={'blogger_id':user_id})
    data = json.loads(response.json())

    user_posts = {}
    for post in data:
        temp = {
            'blog_id'   :post['blog_id'],
            'blogger_id':post['blogger_id'],
            'title'     :post['title'],
            'post'      :post['post'],
        }
        if post['timestamp'][:10] in user_posts.keys():
            user_posts[post['timestamp'][:10]].append(temp)
        else:
            user_posts[post['timestamp'][:10]] = [temp]

    return render_template('blog/myposts.html', user_posts=user_posts)

@bp.route('/posts')
@login_required
def posts():

    # storing the user id and the username in a dictionary
    response = requests.get(BASE_URL + USERS_URL)
    users_data = json.loads(response.json())

    users = {}
    for user_data in users_data:
        users[user_data['user_id']] = user_data['username']

    # getting the users friend list
    parameters = { 'user_id':session['user_id'] }
    response = requests.get(BASE_URL + FRIENDSHIPS_URL, params=parameters)

    friends_data = json.loads(response.json())
    friends = []
    for friend in friends_data.keys():
        if friends_data[friend] == 'accepted':
            friends.append(friend)

    # getting all the blogs posted
    response = requests.get(BASE_URL + BLOGS_URL)
    data = json.loads(response.json())

    user_posts = {}
    for post in data:
        if str(post['blogger_id']) not in friends or post['privacy'] == "myself":
            continue

        temp = {
            'blog_id'   :post['blog_id'],
            'blogger_id':post['blogger_id'],
            'title'     :post['title'],
            'post'      :post['post'],
            'privacy'   :post['privacy'],
            'blogger'   :users[post['blogger_id']]
        }
        if post['timestamp'][:10] in user_posts.keys():
            user_posts[post['timestamp'][:10]].append(temp)
        else:
            user_posts[post['timestamp'][:10]] = [temp]

    return render_template('blog/posts.html', user_posts=user_posts)

@bp.route('/view_post/<int:blog_id>/')
@login_required
def view_post(blog_id):

    # storing the user id and the username in a dictionary
    response = requests.get(BASE_URL + USERS_URL)
    users_data = json.loads(response.json())

    users = {}
    for user_data in users_data:
        users[user_data['user_id']] = user_data['username']

    # getting the specific blog data
    response = requests.get(BASE_URL + BLOGS_URL,params={'blog_id':blog_id})
    posts = json.loads(response.json())
    post = posts[0]
    post['blogger'] = users[post['blogger_id']]

    # getting all the comments associated with the blog
    response = requests.get(BASE_URL + COMMENTS_URL + '/' + str(blog_id))
    comments = json.loads(response.json())

    return render_template('blog/view_post.html', comments=comments, post=post, \
    users=users, session=session)

@bp.route('/view_profile/<int:user_id>/')
@login_required
def view_profile(user_id):

    # storing the user id and the username in a dictionary
    parameters = { 'user_id':user_id }
    response = requests.get(BASE_URL + USERS_URL, params=parameters)
    users = json.loads(response.json())
    user = users[0]

    # getting the users friend list
    parameters = { 'user_id':session['user_id'] }
    response = requests.get(BASE_URL + FRIENDSHIPS_URL, params=parameters)

    friends = json.loads(response.json())
    if str(user_id) in friends.keys():
        status = friends[str(user_id)]
    else:
        status = None

    # getting the specific blog data
    response = requests.get(BASE_URL + BLOGS_URL,params={'blogger_id':user_id})
    data = json.loads(response.json())

    posts = []
    for post in data:
        if str(post['blogger_id']) not in friends or post['privacy'] == "myself":
            continue

        temp = {
            'blog_id'   :post['blog_id'],
            'blogger_id':post['blogger_id'],
            'title'     :post['title'],
            'post'      :post['post'],
            'privacy'   :post['privacy']
        }
        posts.append(temp)

    return render_template('blog/view_profile.html', status=status, posts=posts, user=user, session=session)


######################## Getting friends list ########################


@bp.route('/friends')
@login_required
def friends():

    # getting the users friend list
    parameters = { 'user_id':session['user_id'] }
    response = requests.get(BASE_URL + FRIENDSHIPS_URL, params=parameters)

    friends = json.loads(response.json())
    pending_req = []
    sent_req = []
    accepted_req = []
    for friend in friends.keys():
        if friends[friend] == 'pending':
            pending_req.append(int(friend))
        elif friends[friend] == 'sent':
            sent_req.append(int(friend))
        elif friends[friend] == 'accepted':
            accepted_req.append(int(friend))

    # getting user details
    response = requests.get(BASE_URL + USERS_URL)

    users_data = json.loads(response.json())
    users = {}
    for user_data in users_data:
        users[user_data['user_id']] = user_data['username']

    return render_template('blog/friends.html', session=session,pending_req=pending_req,sent_req = sent_req, accepted_req=accepted_req, users=users)

@bp.route('/accept_friend/<int:friend_id>')
@login_required
def accept_friend(friend_id):

    # getting the users friend list
    parameters = {
        'user_id':session['user_id'],
        'friend_id':friend_id,
        'status':'accepted'
    }
    response = requests.put(BASE_URL + FRIENDSHIPS_URL, params=parameters)

    if response.status_code == 404:
        return error()

    return friends()

@bp.route('/search_results', methods=['POST'])
@login_required
def search_results():

    search_text = request.form.get('search_text')

    # getting user details
    response = requests.get(BASE_URL + USERS_URL)
    users_data = json.loads(response.json())

    # getting the users friend list
    parameters = { 'user_id':session['user_id'] }
    response = requests.get(BASE_URL + FRIENDSHIPS_URL, params=parameters)
    friends = json.loads(response.json())

    # results should be in the form of {'user_id':['username','status']}
    results = {}
    for user_data in users_data:
        if search_text in user_data['username']:
            results[user_data['user_id']] = [user_data['username']]
            if str(user_data['user_id']) in friends.keys():
                results[user_data['user_id']].append(friends[str(user_data['user_id'])])
            elif user_data['user_id'] == session['user_id']:
                results[user_data['user_id']].append('current user')
            else:
                results[user_data['user_id']].append('strangers')

    return render_template('blog/search_results.html', results=results)


######################## Adding comments or post or friends ########################


@bp.route('/add_post/', methods=['POST'])
@login_required
def add_post():

    title = request.form.get('title')
    post = request.form.get('post')
    privacy = request.form.get('privacy')

    if not title or not post or not privacy:
        return error()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    parameters = {
        'blogger_id':session['user_id'],
        'title':title,
        'post':post,
        'privacy':privacy,
        'timestamp':timestamp
    }
    response = requests.post(BASE_URL + BLOGS_URL, params=parameters)

    if response.status_code == 404:
        return error()

    return home()

@bp.route('/add_comment/<int:blog_id>/', methods=['POST'])
@login_required
def add_comment(blog_id):

    comment = request.form.get('comment')
    if not comment:
        return error()

    parameters = {'user_id':session['user_id'], 'comment':comment}
    response = requests.post(BASE_URL + COMMENTS_URL + '/' + str(blog_id), params = parameters)

    # The user posting the comment is not registered
    if response.status_code == 404:
        return error()

    return view_post(blog_id)

@bp.route('/add_friend/<int:friend_id>/')
@login_required
def add_friend(friend_id):

    # storing the user id and the username in a dictionary
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parameters = {
        'user_id':session['user_id'] ,
        'friend_id':friend_id,
        'timestamp':timestamp,
        'status':'pending'
        }
    response = requests.post(BASE_URL + FRIENDSHIPS_URL, params=parameters)

    if response.status_code == 400:
        return error()

    return view_profile(friend_id)
