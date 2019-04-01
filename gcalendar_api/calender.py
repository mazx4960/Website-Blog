from __future__ import print_function
from datetime import datetime, timedelta
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def timeIn12h(time):
    if int(time[:2]) == 12:
        return "{}:{} PM".format(time[:2],time[3:5])
    elif int(time[:2]) == 0:
        return "{}:{} AM".format('12',time[3:5])
    elif int(time[:2]) > 12:
        return "{}:{} PM".format((int(time[:2])-12),time[3:5])
    else:
        return "{}:{} AM".format(int(time[:2]),time[3:5])

def getEvents(user_id, period, start = datetime.utcnow().date()):
    if period == 'day':
        end = start + timedelta(days=1)
    elif period == 'week':
        end = start + timedelta(weeks=1)
    else:
        return []

    # Getting events from Google Calendar API

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('gcalendar_api/tokens/token_{}.pickle'.format(user_id)):
        with open('gcalendar_api/tokens/token_{}.pickle'.format(user_id), 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'gcalendar_api/credentials.json', SCOPES)
            #creds = flow.run_console()
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('gcalendar_api/tokens/token_{}.pickle'.format(user_id), 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    start = start.isoformat() + 'T00:00:00Z' # 'Z' indicates UTC time
    end = end.isoformat() + 'T00:00:00Z' # 'Z' indicates UTC time

    events_result = service.events().list(calendarId='primary', timeMin=start,
                                        timeMax=end, singleEvents=True,
                                        orderBy='startTime').execute()

    events = events_result.get('items', [])

    return events
