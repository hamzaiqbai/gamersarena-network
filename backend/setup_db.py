"""
Database Setup Script
Run this to test connection and create tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, Base, SessionLocal
from app.config import settings

# Import all models to register them with Base
from app.models.user import User
from app.models.wallet import Wallet
from app.models.tournament import Tournament, TokenBundle
from app.models.transaction import Transaction
from app.models.registration import Registration

def test_connection():
    """Test database connection"""
    print("=" * 50)
    print("GAN Database Setup")
    print("=" * 50)
    print(f"\nDatabase URL: {settings.DATABASE_URL[:50]}...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"\n✅ Connected successfully!")
            print(f"   PostgreSQL version: {version}")
            return True
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

def create_tables():
    """Create all database tables"""
    print("\n" + "-" * 50)
    print("Creating database tables...")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("\n✅ All tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📋 Tables in database:")
            for table in tables:
                print(f"   - {table}")
        
        return True
    except Exception as e:
        print(f"\n❌ Failed to create tables: {e}")
        return False

def seed_token_bundles():
    """Create initial token bundles"""
    print("\n" + "-" * 50)
    print("Seeding token bundles...")
    
    db = SessionLocal()
    try:
        # Check if bundles exist
        existing = db.query(TokenBundle).count()
        if existing > 0:
            print(f"   Token bundles already exist ({existing} bundles)")
            return True
        
        # Create default bundles
        bundles = [
            TokenBundle(
                name="Starter Pack",
                tokens=100,
                bonus_tokens=0,
                price_pkr=100,
                is_active=True,
                is_featured=False
            ),
            TokenBundle(
                name="Value Pack",
                tokens=250,
                bonus_tokens=25,
                price_pkr=225,
                is_active=True,
                is_featured=False
            ),
            TokenBundle(
                name="Popular Pack",
                tokens=500,
                bonus_tokens=75,
                price_pkr=400,
                is_active=True,
                is_featured=True,
                badge="POPULAR"
            ),
            TokenBundle(
                name="Pro Gamer",
                tokens=1000,
                bonus_tokens=200,
                price_pkr=750,
                is_active=True,
                is_featured=False,
                badge="BEST VALUE"
            ),
            TokenBundle(
                name="Ultimate Pack",
                tokens=2500,
                bonus_tokens=500,
                price_pkr=1750,
                is_active=True,
                is_featured=False
            )
        ]
        
        for bundle in bundles:
            db.add(bundle)
        
        db.commit()
        print(f"\n✅ Created {len(bundles)} token bundles!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to seed bundles: {e}")
        return False
    finally:
        db.close()

def seed_sample_tournament():
    """Create a sample tournament for testing"""
    print("\n" + "-" * 50)
    print("Creating sample tournament...")
    
    db = SessionLocal()
    try:
        # Check if tournaments exist
        existing = db.query(Tournament).count()
        if existing > 0:
            print(f"   Tournaments already exist ({existing} tournaments)")
            return True
        
        from datetime import datetime, timedelta
        
        # Create sample tournaments
        tournaments = [
            Tournament(
                title="Free Fire Friday Showdown",
                slug="free-fire-friday-showdown",
                description="Join the ultimate Free Fire battle! Compete against the best players and win amazing token rewards.",
                game="freefire",
                entry_fee=50,
                prize_pool=1000,
                first_place_reward=500,
                second_place_reward=300,
                third_place_reward=200,
                max_participants=100,
                start_date=datetime.utcnow() + timedelta(days=2),
                registration_end=datetime.utcnow() + timedelta(days=1, hours=20),
                status="registration_open",
                rules="1. No hacking or cheating\n2. Must check-in 30 mins before start\n3. Team kills are not allowed\n4. Follow all in-game rules"
            ),
            Tournament(
                title="PUBG Mobile Championship",
                slug="pubg-mobile-championship",
                description="Battle royale at its finest! Show your skills in this epic PUBG Mobile tournament.",
                game="pubg",
                entry_fee=100,
                prize_pool=2500,
                first_place_reward=1250,
                second_place_reward=750,
                third_place_reward=500,
                max_participants=64,
                start_date=datetime.utcnow() + timedelta(days=5),
                registration_end=datetime.utcnow() + timedelta(days=4),
                status="registration_open",
                rules="1. Squad mode only\n2. No teaming with enemies\n3. Respect all players\n4. Winners announced after final match"
            ),
            Tournament(
                title="COD Mobile Quick Match",
                slug="cod-mobile-quick-match",
                description="Fast-paced Call of Duty Mobile action! Quick matches, big rewards.",
                game="cod_mobile",
                entry_fee=25,
                prize_pool=500,
                first_place_reward=250,
                second_place_reward=150,
                third_place_reward=100,
                max_participants=32,
                start_date=datetime.utcnow() + timedelta(hours=12),
                registration_end=datetime.utcnow() + timedelta(hours=10),
                status="upcoming",
                rules="1. TDM mode\n2. Standard loadouts only\n3. Fair play required"
            )
        ]
        
        for tournament in tournaments:
            db.add(tournament)
        
        db.commit()
        print(f"\n✅ Created {len(tournaments)} sample tournaments!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to create tournaments: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n")
    
    # Test connection
    if not test_connection():
        print("\nExiting due to connection failure...")
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        print("\nExiting due to table creation failure...")
        sys.exit(1)
    
    # Seed data
    seed_token_bundles()
    seed_sample_tournament()
    
    print("\n" + "=" * 50)
    print("✅ Database setup complete!")
    print("=" * 50)
    print("\nYou can now run the backend with:")
    print("   uvicorn app.main:app --reload --port 8000")
    print("\n")
