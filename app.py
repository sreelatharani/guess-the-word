# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_app, db
from models import User, Word, Game, Guess
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime, date

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash("You must be an admin to access this page.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# 1️⃣ Create the Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # for session management
init_app(app)

# 2️⃣ Add the root route AFTER app is created
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------- USER REGISTRATION -------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 5:
            flash("Username must be at least 5 characters")
            return redirect(url_for('register'))

        if len(password) < 5 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password) or not any(c in '$%*@' for c in password):
            flash("Password must be at least 5 chars, include letters, digits and one special ($ % * @)")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        user = User(username=username, password_hash=hashed, is_admin=False)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------- USER LOGIN -------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash("Login successful!")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
            return redirect(url_for('login'))

    return render_template('login.html')


# ------------------- DASHBOARD -------------------
# ------------------- DASHBOARD -------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    else:
        # Player dashboard
        user_id = session['user_id']
        today = date.today()
        games_today = Game.query.filter(
            Game.user_id == user_id,
            db.func.date(Game.started_at) == today
        ).count()
        remaining_games = max(0, 3 - games_today)
        return render_template('dashboard.html', remaining_games=remaining_games)





# ------------------- LOGOUT -------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for('login'))

# ------------------- START GAME -------------------
# ------------------- START GAME -------------------
from datetime import datetime, date

@app.route('/start_game')
def start_game():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    # Count games started today by this user
    games_today = Game.query.filter(
        Game.user_id == user_id,
        db.func.date(Game.started_at) == today
    ).count()

    max_games_per_day = 3

    if games_today >= max_games_per_day:
        flash("You have reached your 3 games limit for today. Try again tomorrow!")
        return render_template('limit_reached.html')

    # Pick a random word
    all_words = Word.query.all()
    if not all_words:
        flash("No words available. Contact admin.")
        return redirect(url_for('dashboard'))

    word = random.choice(all_words)

    # Create a new game and set started_at
    game = Game(
        user_id=user_id,
        word_id=word.id,
        finished=False,
        won=False,
        attempts=0,
        started_at=datetime.now()  # <-- important
    )
    db.session.add(game)
    db.session.commit()

    return redirect(url_for('play_game', game_id=game.id))


# ------------------- PLAY GAME -------------------
# ------------------- PLAY GAME -------------------
@app.route('/game/<int:game_id>', methods=['GET', 'POST'])
def play_game(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    game = Game.query.get_or_404(game_id)
    word = game.word.value
    max_attempts = 5
    remaining_attempts = max_attempts - game.attempts
    message = None
    error = None
    celebration = False
    failure = False

    if request.method == 'POST':
        guess_text = request.form['guess']

        # Uppercase-only check
        if not guess_text.isupper():
            error = "⚠️ Please enter letters in UPPER CASE only!"
        elif len(guess_text) != 5:
            error = "Enter exactly 5 letters!"
        elif game.finished:
            error = "Game already finished. Press OK to go back."
        else:
            # Feedback calculation
            feedback = ""
            for i in range(5):
                if guess_text[i] == word[i]:
                    feedback += "G"  # Green
                elif guess_text[i] in word:
                    feedback += "O"  # Orange
                else:
                    feedback += "X"  # Grey

            # Save guess
            guess = Guess(game_id=game.id, guess_text=guess_text, correct_positions=feedback)
            db.session.add(guess)
            game.attempts += 1

            # Win check
            if guess_text == word:
                game.won = True
                game.finished = True
                db.session.commit()
                celebration = True
                message = f"🎉 Congratulations! You guessed '{word}' correctly!"
                return render_template('game.html', game=game, guesses=[guess],
                                       remaining_attempts=0, success=True,
                                       message=message, celebration=celebration)

            # Max attempts reached
            if game.attempts >= max_attempts:
                game.finished = True
                db.session.commit()
                guesses = Guess.query.filter_by(game_id=game.id).all()
                failure = True
                message = f"😢 Better luck next time! The word was '{word}'."
                return render_template('game.html', game=game, guesses=guesses,
                                       remaining_attempts=0, failure=True,
                                       message=message, celebration=celebration)

            db.session.commit()
            remaining_attempts = max_attempts - game.attempts
            message = f"Attempt {game.attempts}/{max_attempts} - {feedback} 😊 Remaining attempts: {remaining_attempts}"

    guesses = Guess.query.filter_by(game_id=game.id).all()
    return render_template('game.html', game=game, guesses=guesses,
                           remaining_attempts=remaining_attempts, message=message,
                           error=error, celebration=celebration, failure=failure)



# ------------------- ADMIN REPORT -------------------
@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    today = date.today()
    total_users = User.query.count()
    total_games = Game.query.filter(db.func.date(Game.started_at) == today).count()
    correct_guesses = Game.query.filter(
        Game.won == True,
        db.func.date(Game.started_at) == today
    ).count()

    return render_template(
        'admin_report.html',
        today=today,
        total_users=total_users,
        total_games=total_games,
        correct_guesses=correct_guesses
    )


# ------------------- ADMIN REPORT PER USER -------------------
# ------------------- ADMIN REPORT PER USER -------------------
@app.route('/admin_user_report', methods=['GET', 'POST'])
def admin_user_report():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    # Fetch only non-admin users
    users = User.query.filter_by(is_admin=False).all()

    report_data = None
    selected_user = None
    no_games_played = False  # Flag for no games

    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        selected_user = User.query.get(user_id)

        # Get all games for this user
        games = Game.query.filter_by(user_id=user_id).order_by(Game.started_at).all()
        
        if not games:
            no_games_played = True  # User hasn't played any games
        else:
            report_data = []
            for g in games:
                correct_guesses = Guess.query.filter_by(game_id=g.id).filter(Guess.guess_text == g.word.value).count()
                report_data.append({
                    'date': g.started_at.date().isoformat(),
                    'word': g.word.value,
                    'attempts': g.attempts,
                    'won': g.won,
                    'correct_guesses': correct_guesses
                })

    return render_template(
        'admin_user_report.html',
        users=users,
        report_data=report_data,
        selected_user=selected_user,
        no_games_played=no_games_played  # Pass flag to template
    )


# ------------------- RUN APP -------------------
if __name__ == '__main__':
    app.run(debug=True)
