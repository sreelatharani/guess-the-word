from database import db, init_app
from models import Word
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_app(app)

with app.app_context():
    words = Word.query.all()
    if not words:
        print("⚠️ No words found in database!")
    else:
        print("✅ Words in database:")
        for w in words:
            print(w.id, w.value)
