#!/usr/bin/env python3
"""
Database migration script to create Operations Copilot tables.
Run this script to add the new tables without affecting existing data.
"""

from sqlalchemy import create_engine, text
from app.db.models import Base
from app.db.session import DATABASE_URL

def create_copilot_tables():
    """Create the new tables for Operations Copilot"""
    engine = create_engine(DATABASE_URL)
    
    # Create only the new tables
    print("Creating Operations Copilot tables...")
    
    with engine.connect() as conn:
        # User Preferences table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR DEFAULT 'default',
                optimize_for VARCHAR DEFAULT 'balanced',
                service_level_priority VARCHAR DEFAULT 'medium',
                multi_location_aggressiveness VARCHAR DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Recommendation Feedback table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recommendation_feedback (
                id SERIAL PRIMARY KEY,
                recommendation_id VARCHAR,
                user_id VARCHAR DEFAULT 'default',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action VARCHAR,
                context_hash VARCHAR,
                action_type VARCHAR,
                action_parameters JSONB,
                risk_score NUMERIC
            );
        """))
        
        # News Events table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS news_events (
                id SERIAL PRIMARY KEY,
                event_date DATE,
                event_type VARCHAR,
                description VARCHAR,
                impact_stores JSONB,
                impact_skus JSONB,
                score_modifier NUMERIC DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Add risk_score column to batch_risk if it doesn't exist
        try:
            conn.execute(text("""
                ALTER TABLE batch_risk 
                ADD COLUMN IF NOT EXISTS risk_score NUMERIC;
            """))
        except Exception as e:
            print(f"Note: risk_score column may already exist: {e}")
        
        conn.commit()
    
    print("✅ Operations Copilot tables created successfully!")
    print("\nNew tables added:")
    print("- user_preferences: Store user optimization preferences")
    print("- recommendation_feedback: Track user feedback for learning")
    print("- news_events: Manual news events that affect scoring")
    print("- batch_risk.risk_score: Added risk score column if missing")

if __name__ == "__main__":
    create_copilot_tables()