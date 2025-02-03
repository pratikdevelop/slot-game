from flask import Flask, render_template, request, jsonify

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scores.db'
db = SQLAlchemy(app)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, nullable=False)

@app.route('/')
def index():
    return render_template('index_v1.html')

@app.route('/build_transaction', methods=['POST'])
def build_transaction():
    data = request.get_json()
    # Process the data and build the transaction
    return jsonify({"status": "success", "data": data})



@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.get_json()
    new_score = Score(username=data['username'], score=data['score'])
    db.session.add(new_score)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    scores = Score.query.order_by(Score.score.desc()).limit(10).all()
    return jsonify([{"username": score.username, "score": score.score} for score in scores])

if __name__ == '__main__':
    app.run(debug=True)