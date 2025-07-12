from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
# from models import db, User, Question, Answer, Tag 

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["forum"]

questions_collection = db["questions"]
answers_collection = db["answers"]
users_collection = db["users"]

# ------------------------------
# Question-related helpers
# ------------------------------

def get_all_questions():
    return questions_collection.find().sort("created_at", -1)

def get_question_by_id(question_id):
    return questions_collection.find_one({"_id": ObjectId(question_id)})

def insert_question(title, content, tags, author="anonymous"):
    return questions_collection.insert_one({
        "title": title,
        "content": content,
        "tags": tags,
        "author": author,
        "votes": 0,
        "views": 0,
        "answered": False,
        "created_at": datetime.utcnow()
    })

# ------------------------------
# Answer-related helpers
# ------------------------------

def insert_answer(question_id, content, author="anonymous"):
    return answers_collection.insert_one({
        "question_id": ObjectId(question_id),
        "content": content,
        "author": author,
        "votes": 0,
        "created_at": datetime.utcnow()
    })

def get_answers_for_question(question_id):
    return answers_collection.find({"question_id": ObjectId(question_id)}).sort("created_at", 1)

# ------------------------------
# User-related (optional)
# ------------------------------

def insert_user(username, email):
    return users_collection.insert_one({
        "username": username,
        "email": email,
        "joined": datetime.utcnow()
    })
