# backend/app.py
from flask import Flask
from flask_cors import CORS
from extensions import db
from routes import routes_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
print("Stripe key loaded:", stripe.api_key)  # for debug

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------- SQLITE DATABASE CONFIG ----------
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")
os.makedirs(instance_path, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_path, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

# Initialize DB
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()
    print("✅ SQLite database & tables created")

# Register routes
app.register_blueprint(routes_bp)

@app.route("/")
def home():
    return {"message": "SkinGlow Website API Running"}

# ---------- RUN APP ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))  # Use PORT from env or default
    app.run(host="0.0.0.0", port=port, debug=True)