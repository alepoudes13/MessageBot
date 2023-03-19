import os

#BOT:
TOKEN = os.environ['SECRET_TOKEN']  # Bot token

ADMIN = None
DIR = "" 

#DEV API AND HASH
API_ID = int(os.environ['SECRET_ID'])
API_HASH = os.environ['SECRET_HASH']

#Setup a chat for bot logs
DUMP_ID = int(os.environ['SECRET_DUMP_ID'])
