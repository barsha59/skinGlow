# models.py - UPDATED VERSION
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ---------------------- USER MODEL ----------------------
class User(db.Model):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password helpers
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ---------------------- PRODUCT MODEL ----------------------
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review_count = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")

    # Convert to dictionary for frontend
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "rating": self.rating,
            "reviews": self.reviews,
            "category": self.category,
            "stock": self.stock,
            "image": self.image_url,
            "image_url": self.image_url,
            "description": self.description
        }

# ---------------------- ORDER MODEL ----------------------
class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(120))
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------------- REVIEW MODEL ----------------------
class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------------- WISHLIST MODEL ----------------------
class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Prevent duplicate wishlist entries
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),
    )
