from __future__ import print_function

import os.path
import pandas as pd
import argparse
import socket

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of spreadsheet.
SPREADSHEET_ID = '1zc07-Sz4JmswkbFfCTMBgUNbJNBtXcKbw7IWvY1t63I'         # ISCA 2024 - SPEC 

def authenticate():
    creds = None
    if os.path.exists('./sheets_api/token.json'):
        print("Authenticating")
        creds = Credentials.from_authorized_user_file('./sheets_api/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './sheets_api/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('./sheets_api/token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    print("Successful")
    return service

def create_sheet(service, title):
    # create sheet if not present
    requests=[{
        "addSheet": {
            "properties": {
                "title": title,
                "index": 2,
                "gridProperties": {
                    "frozenRowCount": 1,
                    "frozenColumnCount": 1,
                }
            }
        }
    }]

    body = {
            'requests': requests
        }
    try:
        response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body).execute()
        print(f"Sheet title {title} created.")
    except HttpError as err:
        print("Sheet already exists!")


def write_to_sheet(service, df, title):  
    # write dataframe to sheet
    body = {
        'values': [df.columns.values.tolist()] + df.values.tolist()
    }

    try:
        result = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, range=title,
                valueInputOption='USER_ENTERED', body=body).execute()
        
        print(f"{title} sheet is updated. {result.get('updatedCells')} cells updated.")

    except HttpError as err:
        print(err)


def append(service, df, title, prefetcher, env):
    temp = df[df['Benchmarks'] == title].reset_index(drop=True) # select row where 'Benchmarks' == title
    temp = temp.drop('Benchmarks', axis=1)  # delete Benchmarks column and insert below two columns
    temp.insert(0, 'Environment', env)
    temp.insert(0, 'Prefetcher', prefetcher)

    body = {
        'values': temp.values.tolist()
    }

    try:
        result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID, range=title,
                valueInputOption='USER_ENTERED', body=body).execute()

        print(f"{title}s are updated. {(result.get('updates').get('updatedCells'))} cells appended.")

    except HttpError as err:
        print(err)


def main():
    parser = argparse.ArgumentParser(
                        prog = 'Extractor',
                        description = 'Extracts all datapoints for all traces of a given benchmark',
                        epilog = 'Use it well.')

    parser.add_argument('-b','--benchmark', metavar='spec', required=True,
                        help='Name of benchmark')
    parser.add_argument('-p','--prefetcher', metavar='ip_stride', required=True,
                        help='Name of prefetcher')
    parser.add_argument('-e','--environment', metavar='gm', required=True,
                        help='Environment to be used')

    args = parser.parse_args()

    df = pd.read_csv(f"../results-{socket.gethostname()}/{args.benchmark}/{args.prefetcher}-{args.environment}.csv")

    service = authenticate()
    
    create_sheet(service, f"{args.prefetcher} {args.environment}")
    write_to_sheet(service, df, f"{args.prefetcher} {args.environment}")
    append(service, df, 'Mean', args.prefetcher, args.environment)
    append(service, df, 'Geomean', args.prefetcher, args.environment)

if __name__ == '__main__':
    main()