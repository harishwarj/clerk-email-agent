# generate_token.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the necessary scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets"
]

def main():
    """Generates a token.json file using the local server flow."""
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("Successfully created token.json file.")

if __name__ == '__main__':
    main()