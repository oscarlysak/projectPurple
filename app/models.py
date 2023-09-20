from datetime import datetime
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    NFTno = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    current_threshold = db.Column(db.Integer, default=500)
    reset_threshold = db.Column(db.Integer, default=500)
    adventures = db.relationship('Adventure', backref='adventurer', lazy=True)

class Adventure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rng_score = db.Column(db.Integer, nullable=False)
    material = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(120), nullable=False, default="In Progress")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class LootBox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rarity = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class PrizeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    rarity = db.Column(db.String(120), nullable=False)
    quanity = db.Column(db.Integer, nullable=False)
    number_claimed = db.Column(db.Integer, nullable=False, default=0)
    
class Prize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prize_type_id = db.Column(db.Integer, db.ForeignKey('prize_type.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)