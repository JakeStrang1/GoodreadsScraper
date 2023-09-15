import os
from dotenv import load_dotenv

class Config:
    def __init__(self, username, password, db_name):
        self.goodreads_username = username
        self.goodreads_password = password
        self.mongo_db_name = db_name

def loadConfig():
    load_dotenv()
    return Config(os.getenv('GOODREADS_USERNAME'), os.getenv('GOODREADS_PASSWORD'), os.getenv('MONGO_DB_NAME'))