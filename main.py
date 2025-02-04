from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Integer, default=1000)
    high_score = db.Column(db.Integer, default=0)
    total_bet = db.Column(db.Integer, default=0)
    terms=db.Column(db.String(10), nullable=False)
    total_wins = db.Column(db.Integer, default=0)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())


class GameTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'bet' or 'win'
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Check if it's a normal form POST (from the form submission) or a fetch API request (JSON)
        if request.is_json:  # Handling fetch API call
            data = request.get_json()

            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            terms = data.get('terms', False)

            if not terms:
                return jsonify({"success": False, "message": "You must agree to the terms and conditions"}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({"success": False, "message": "Username already exists"}), 400

            if User.query.filter_by(email=email).first():
                return jsonify({"success": False, "message": "Email already registered"}), 400

            if password != confirm_password:
                return jsonify({"success": False, "message": "Passwords do not match"}), 400

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password, terms=terms,
                            balance=1000,  # Initial balance
                            high_score=1000)  # Initial high score

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return jsonify({"success": True, "message": "Account created successfully!"}), 200

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if the request is coming from a normal form submission or AJAX (fetch)
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            user = User.query.filter_by(email=email).first()
            
            if user:
                login_user(user)
                return jsonify({"success": True, "message": "Login successful"}), 200

            return jsonify({"success": False, "message": "Invalid username or password"}), 401
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/api/bet', methods=['POST'])
@login_required
def place_bet():
    data = request.get_json()
    bet_amount = data.get('amount')
    
    if not bet_amount or bet_amount <= 0:
        return jsonify({"status": "error", "message": "Invalid bet amount"}), 400
        
    if current_user.balance < bet_amount:
        return jsonify({"status": "error", "message": "Insufficient balance"}), 400

    try:
        current_user.balance -= bet_amount
        current_user.total_bet += bet_amount
        
        transaction = GameTransaction(
            user_id=current_user.id,
            amount=bet_amount,
            transaction_type='bet'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "new_balance": current_user.balance,
            "total_bet": current_user.total_bet
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/win', methods=['POST'])
@login_required
def register_win():
    data = request.get_json()
    win_amount = data.get('amount')
    
    if not win_amount or win_amount <= 0:
        return jsonify({"status": "error", "message": "Invalid win amount"}), 400

    try:
        current_user.balance += win_amount
        current_user.total_wins += win_amount
        
        # Update high score if current balance exceeds it
        if current_user.balance > current_user.high_score:
            current_user.high_score = current_user.balance
            
        transaction = GameTransaction(
            user_id=current_user.id,
            amount=win_amount,
            transaction_type='win'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "new_balance": current_user.balance,
            "new_high_score": current_user.high_score,
            "total_wins": current_user.total_wins
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    return jsonify({
        "username": current_user.username,
        "balance": current_user.balance,
        "high_score": current_user.high_score,
        "total_bet": current_user.total_bet,
        "total_wins": current_user.total_wins
    })

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    leaderboard_type = request.args.get('type', 'high_score')
    
    if leaderboard_type == 'high_score':
        users = User.query.order_by(User.high_score.desc()).limit(10).all()
    elif leaderboard_type == 'balance':
        users = User.query.order_by(User.balance.desc()).limit(10).all()
    else:
        return jsonify({"status": "error", "message": "Invalid leaderboard type"}), 400
    
    leaderboard_data = [{
        "username": user.username,
        "value": user.high_score if leaderboard_type == 'high_score' else user.balance,
        "type": leaderboard_type
    } for user in users]
    
    return jsonify(leaderboard_data)

@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    transactions = GameTransaction.query.filter_by(user_id=current_user.id)\
        .order_by(GameTransaction.timestamp.desc()).limit(10).all()
        
    return jsonify([{
        "amount": t.amount,
        "type": t.transaction_type,
        "timestamp": t.timestamp.isoformat()
    } for t in transactions])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
