from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/ledgerit')
            self._client = MongoClient(mongodb_uri)
            self._db = self._client.get_database()
            print("Connected to MongoDB successfully")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise e
    
    def get_db(self):
        return self._db
    
    def close(self):
        if self._client:
            self._client.close()

# Initialize database connection
db = Database().get_db()