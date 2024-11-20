from flask_login import UserMixin
from pymongo import MongoClient

db = MongoClient('localhost', 27017)['users']

class User(UserMixin):
    def __init__(self, db: MongoClient):
        self.db = db
        self.id = db.Column(db.Integer, primary_key=True)
