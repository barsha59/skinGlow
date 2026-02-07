from app import app
from models import db, Product

def seed_database():
    with app.app_context():
        db.create_all()  # creates tables fresh
        products = [
            Product(
                name="Aloe Vera Face Cream",
                price=499.0,
                rating=4.5,
                review_count=12,
                category="Skin Care",
                stock=20,
                image_url="https://example.com/images/aloe_cream.jpg",
                description="Moisturizes and soothes skin"
            ),
            Product(
                name="Vitamin C Serum",
                price=699.0,
                rating=4.7,
                review_count=8,
                category="Skin Care",
                stock=15,
                image_url="https://example.com/images/vitc_serum.jpg",
                description="Brightens your skin"
            ),
            # Add more products here
        ]
        db.session.bulk_save_objects(products)
        db.session.commit()
        print(f"✅ Seeded {len(products)} products")

if __name__ == "__main__":
    seed_database()
