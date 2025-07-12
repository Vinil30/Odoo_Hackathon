from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import (
    insert_question,
    get_all_questions,
    get_question_by_id,
    insert_answer,
    get_answers_for_question,
    insert_user
)
from dotenv import load_dotenv
import os
from groq import Groq
from pymongo import MongoClient
from urllib.parse import quote_plus
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

username = quote_plus(os.getenv("DB_USER"))
password = quote_plus(os.getenv("DB_PASS"))

# Replace YOUR_CLUSTER.mongodb.net with your actual MongoDB Atlas cluster domain
uri = f"mongodb+srv://{username}:{password}@cluster0.uinxu1w.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri)
db = client["forum"]  # Or your actual DB name
questions_collection = db["questions"]
class Generator:
    def __init__(self, api_key=None, model="llama3-70b-8192"):
        self.api_key = api_key or os.environ.get("groq_api_key")
        self.model = model
        self.client = Groq(api_key=self.api_key)
        self.system_prompts = {
            "question_formatter": "You are an expert assistant in English Speaking. You are given a raw text which is a question by the user. Your job is to return a properly grammar-formatted version.",
            "tag_generator": "You are an expert tag generator. You will be given a question and your job is to generate relevant hashtags for easier search. \
                For example: Question: How to merge 2 tables in SQL \
                Output: #sql #dbms #database",
            "ai_answer": "You are an expert answering assistant. You will be given a question and need to answer it in a structured and detailed way, explaining your reasoning and approach."
        }

    def _call_model(self, system_prompt, user_prompt):
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return chat_completion.choices[0].message.content.strip()

    def format_question(self, raw_question: str) -> str:
        return self._call_model(self.system_prompts["question_formatter"], raw_question)

    def generate_tags(self, question: str) -> str:
        return self._call_model(self.system_prompts["tag_generator"], question)

    def answer_question(self, question: str) -> str:
        return self._call_model(self.system_prompts["ai_answer"], question)

generator = Generator()

@app.route('/')
def index():
    questions = questions_collection.find().sort('created_at', -1)
    return render_template('index.html', questions=questions)

@app.route('/ask', methods=['GET', 'POST'])
def ask_question():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form.get('tags', '').split(',')
        
        # In a real app, you'd have user authentication
        user = User.query.first() or User(username='anonymous', email='anon@example.com', password='password')
        db.session.add(user)
        db.session.commit()
        
        question = Question(title=title, content=content, user_id=user.id)
        
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                question.tags.append(tag)
        
        db.session.add(question)
        db.session.commit()
        
        flash('Your question has been posted!', 'success')
        return redirect(url_for('question_detail', question_id=question.id))
    
    return render_template('form.html')

@app.route('/question/<question_id>')
def question_detail(question_id):
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question:
        return "Question not found", 404
    return render_template('question.html', question=question)

@app.route('/generate-tags', methods=['POST'])
def generate_tags():
    question = request.json.get('question')
    tags = generator.generate_tags(question)
    return {'tags': tags}
@app.route('/generate-description', methods=['POST'])
def generate_description():
    question = request.json.get('question')
    formatted = generator.format_question(question)
    return {'description': formatted}

@app.route('/generate-answer', methods=['POST'])
def generate_answer():
    question = request.json.get('question')
    answer = generator.answer_question(question)
    return {'answer': answer}

@app.route("/submit-question", methods=["POST"])
def submit_question():
    from datetime import datetime
    title = request.form.get("title")
    description = request.form.get("description")
    tags = [tag.strip() for tag in request.form.get("tags", "").split(",")]

    question_doc = {
        "title": title,
        "content": description,
        "author": "anonymous",
        "tags": tags,
        "votes": 0,
        "answers": 0,
        "views": 0,
        "answered": False,
        "created_at": datetime.utcnow()
    }

    inserted = questions_collection.insert_one(question_doc)
    return redirect(f"/question/{inserted.inserted_id}")
@app.route("/api/questions")
def api_get_questions():
    questions = get_all_questions()
    return jsonify([serialize_question(q) for q in questions])
if __name__ == '__main__':
    app.run(debug=True)