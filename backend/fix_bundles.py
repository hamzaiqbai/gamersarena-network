"""
Fix and seed token bundles
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.tournament import TokenBundle

def fix_and_seed():
    """Fix token_bundles table and seed data"""
    
    # First, alter the table to make price_usd nullable
    print("Fixing token_bundles table...")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE token_bundles ALTER COLUMN price_usd DROP NOT NULL"))
        conn.commit()
    print("✅ Made price_usd nullable")
    
    # Now seed the bundles
    print("\nSeeding token bundles...")
    db = SessionLocal()
    try:
        # Check if bundles exist
        existing = db.query(TokenBundle).count()
        if existing > 0:
            print(f"   Token bundles already exist ({existing} bundles)")
            return
        
        # Create default bundles
        bundles = [
            TokenBundle(
                name="Starter Pack",
                tokens=100,
                bonus_tokens=0,
                price_pkr=100,
                price_usd=0.35,
                is_active=True,
                is_featured=False
            ),
            TokenBundle(
                name="Value Pack",
                tokens=250,
                bonus_tokens=25,
                price_pkr=225,
                price_usd=0.80,
                is_active=True,
                is_featured=False
            ),
            TokenBundle(
                name="Popular Pack",
                tokens=500,
                bonus_tokens=75,
                price_pkr=400,
                price_usd=1.40,
                is_active=True,
                is_featured=True,
                badge="POPULAR"
            ),
            TokenBundle(
                name="Pro Gamer",
                tokens=1000,
                bonus_tokens=200,
                price_pkr=750,
                price_usd=2.60,
                is_active=True,
                is_featured=False,
                badge="BEST VALUE"
            ),
            TokenBundle(
                name="Ultimate Pack",
                tokens=2500,
                bonus_tokens=500,
                price_pkr=1750,
                price_usd=6.20,
                is_active=True,
                is_featured=False
            )
        ]
        
        for bundle in bundles:
            db.add(bundle)
        
        db.commit()
        print(f"\n✅ Created {len(bundles)} token bundles!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to seed bundles: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_and_seed()
