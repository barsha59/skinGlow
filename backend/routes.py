# routes.py - SKIN GLOW E-COMMERCE SITE
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import Product, Order, Review, User, Wishlist 
import stripe
import os
import traceback

print("✅ routes.py loaded - SkinGlow Store")

routes_bp = Blueprint("routes", __name__)

# Stripe secret key from .env
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
print("Stripe API Key loaded?", stripe.api_key is not None)

# ----------------------
# GET all products
# ----------------------
@routes_bp.route('/api/products', methods=['GET'])
def get_products():
    sort_by = request.args.get('sort')
    if sort_by == "price":
        products = Product.query.order_by(Product.price.asc()).all()
    elif sort_by == "rating":
        products = Product.query.order_by(Product.rating.desc()).all()
    else:
        products = Product.query.all()

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "rating": p.rating,
            "reviews": p.review_count,
            "category": p.category,
            "stock": p.stock,
            "image": p.image_url,
            "description": p.description
        }
        for p in products
    ])

@routes_bp.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "rating": product.rating,
        "reviews": product.review_count,
        "category": product.category,
        "stock": product.stock,
        "image_url": product.image_url,
        "description": product.description
    })


# ----------------------
# CREATE ORDER
# ----------------------
@routes_bp.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    customer_name = data.get("customer_name")
    address = data.get("address")
    phone = data.get("phone")
    cart_items = data.get("cart")  # [{"product_id":1,"quantity":2}, ...]

    if not customer_name or not address or not phone:
        return jsonify({"error": "Customer info is required"}), 400

    if not cart_items or not isinstance(cart_items, list):
        return jsonify({"error": "Cart is empty or invalid"}), 400

    orders_created = []

    for item in cart_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": f"Product ID {product_id} not found"}), 404

        if product.stock < quantity:
            return jsonify({"error": f"{product.name} out of stock"}), 400

        # Create one Order record per cart item
        order = Order(
            product_id=product.id,
            customer_name=customer_name,
            address=address,
            phone=phone,
            status="Pending"
        )
        db.session.add(order)
        orders_created.append(order)

        # Reduce product stock
        product.stock -= quantity

    db.session.commit()

    return jsonify({
        "message": "Orders placed successfully",
        "order_ids": [o.id for o in orders_created]
    })


# ----------------------
# ADD REVIEW
# ----------------------
@routes_bp.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.json
    product_id = data.get("product_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if product_id is None or rating is None:
        return jsonify({"error": "Product ID and rating are required"}), 400

    review = Review(product_id=product_id, rating=rating, comment=comment)
    db.session.add(review)

    product = Product.query.get(product_id)
    if product:
        all_reviews = Review.query.filter_by(product_id=product_id).all()
        product.review_count = len(all_reviews)
        product.rating = sum(r.rating for r in all_reviews) / len(all_reviews)

    db.session.commit()
    return jsonify({"message": "Review added successfully"})


# ----------------------
# STRIPE PAYMENT
# ----------------------
@routes_bp.route('/api/pay', methods=['POST'])
def create_payment():
    data = request.json
    amount = data.get("amount")  # in cents

    if not amount:
        return jsonify({"error": "Amount is required"}), 400

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency="usd",
            payment_method_types=["card"],
        )
        return jsonify({"client_secret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------
# CONFIRM ORDER PAYMENT
# ----------------------
@routes_bp.route('/api/orders/<int:order_id>/pay', methods=['POST'])
def confirm_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.status = "Paid"
    db.session.commit()
    return jsonify({"message": f"Order {order_id} marked as Paid"})


# ----------------------
# USER AUTHENTICATION
# ----------------------
@routes_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    
    if not email or not name or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400
    
    user = User(email=email, name=name)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": "User registered successfully",
        "user": {"id": user.id, "email": user.email, "name": user.name}
    })

@routes_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    return jsonify({
        "message": "Login successful",
        "user": {"id": user.id, "email": user.email, "name": user.name}
    })


# ----------------------
# ADD SAMPLE SKINCARE PRODUCTS
# ----------------------
@routes_bp.route('/api/add-sample-products')
def add_sample_products():
    """Add sample skincare products to empty database"""
    try:
        current_count = Product.query.count()
        if current_count > 0:
            return jsonify({
                "status": "info",
                "message": f"Already have {current_count} products. No need to add samples."
            })
        
        sample_products = [
            {
                "name": "Hydrating Face Cream",
                "price": 29.99,
                "rating": 4.6,
                "review_count": 142,
                "category": "Moisturizers",
                "stock": 120,
                "image_url": "https://images.unsplash.com/photo-1592928307317-8f1f3e8b97d5?w=400&h=400&fit=crop",
                "description": "Lightweight cream, deeply hydrates and nourishes skin"
            },
            {
                "name": "Vitamin C Serum",
                "price": 39.99,
                "rating": 4.8,
                "review_count": 210,
                "category": "Serums",
                "stock": 80,
                "image_url": "https://images.unsplash.com/photo-1598514983276-5678e0b46b70?w=400&h=400&fit=crop",
                "description": "Brightens skin, reduces dark spots, antioxidant-rich"
            },
            {
                "name": "Gentle Foaming Cleanser",
                "price": 19.99,
                "rating": 4.5,
                "review_count": 95,
                "category": "Cleansers",
                "stock": 150,
                "image_url": "https://images.unsplash.com/photo-1596461404969-5f0aa2b0c9d5?w=400&h=400&fit=crop",
                "description": "Removes impurities and makeup without drying"
            },
            {
                "name": "Sunscreen SPF 50",
                "price": 24.99,
                "rating": 4.7,
                "review_count": 132,
                "category": "Sun Care",
                "stock": 100,
                "image_url": "https://images.unsplash.com/photo-1596060179351-91b7aa42969b?w=400&h=400&fit=crop",
                "description": "Broad-spectrum protection, lightweight, non-greasy"
            },
            {
                "name": "Exfoliating Face Scrub",
                "price": 21.99,
                "rating": 4.3,
                "review_count": 78,
                "category": "Exfoliators",
                "stock": 60,
                "image_url": "https://images.unsplash.com/photo-1600185361775-f1c18b9286c3?w=400&h=400&fit=crop",
                "description": "Gently removes dead skin cells, smoothens texture"
            },
            {
                "name": "Night Repair Cream",
                "price": 34.99,
                "rating": 4.6,
                "review_count": 110,
                "category": "Night Care",
                "stock": 90,
                "image_url": "https://images.unsplash.com/photo-1600185361633-4c3d7f1b30c8?w=400&h=400&fit=crop",
                "description": "Rich night cream, repairs skin while you sleep"
            },
            {
                "name": "Eye Gel for Dark Circles",
                "price": 27.99,
                "rating": 4.4,
                "review_count": 65,
                "category": "Eye Care",
                "stock": 70,
                "image_url": "https://images.unsplash.com/photo-1600185361595-c8c0c18c4b1f?w=400&h=400&fit=crop",
                "description": "Reduces puffiness and dark circles, cooling effect"
            },
            {
                "name": "Aloe Vera Face Mask",
                "price": 22.99,
                "rating": 4.7,
                "review_count": 140,
                "category": "Masks",
                "stock": 50,
                "image_url": "https://images.unsplash.com/photo-1598514983286-5678e0b46b70?w=400&h=400&fit=crop",
                "description": "Soothes and hydrates, ideal for sensitive skin"
            }
        ]

        added_count = 0
        for prod_data in sample_products:
            product = Product(
                name=prod_data["name"],
                price=prod_data["price"],
                rating=prod_data["rating"],
                review_count=prod_data["review_count"],
                category=prod_data["category"],
                stock=prod_data["stock"],
                image_url=prod_data["image_url"],
                description=prod_data["description"]
            )
            db.session.add(product)
            added_count += 1

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Added {added_count} skincare products to database",
            "products_added": [p["name"] for p in sample_products]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ----------------------
# DEBUG INFO
# ----------------------
@routes_bp.route('/api/debug-info')
def debug_info():
    import os
    return jsonify({
        "backend_running": True,
        "store_type": "SkinGlow E-commerce",
        "database_url_exists": bool(os.environ.get('DATABASE_URL')),
        "total_products": Product.query.count(),
        "total_users": User.query.count(),
        "total_orders": Order.query.count(),
        "environment": "production"
    })


# ----------------------
# DATABASE INITIALIZATION
# ----------------------
@routes_bp.route('/api/init-db')
def init_database():
    try:
        db.create_all()
        return jsonify({
            "success": True,
            "message": "Database tables created successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc() if traceback else None
        }), 500
