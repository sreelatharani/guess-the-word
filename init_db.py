from flask import Flask
from database import init_app, db
from models import Word

def seed_words():
    words = [
        'APPLE','BRAVE','CRANE','DRIVE','EPOCH','EAGLE',
        'FABLE','GHOST','HUMAN','INNER','JOKER','CABLE',
        'KNIFE','LIGHT','MIGHT','NERVE','OCEAN',
        'PLANT','QUERY','RIVER','SHADE','TRUST',
    ]
    for w in words:
        if not Word.query.filter_by(value=w).first():
            db.session.add(Word(value=w))
    db.session.commit()

if __name__ == "__main__":
    app = Flask(__name__)
    init_app(app)
    with app.app_context():
        db.drop_all()     # clears existing (for development only)
        db.create_all()   # create tables
        seed_words()
        
        # ✅ Print all words to check
        all_words = [w.value for w in Word.query.all()]
        print("Words in database:", all_words)
        print("Database initialized with 20 words.")
