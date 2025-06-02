"""Database initialization and migration script for LocPlat"""

import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.field_config import create_tables, Base


def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    # Extract database name from URL
    db_url_parts = settings.DATABASE_URL.split('/')
    db_name = db_url_parts[-1]
    base_url = '/'.join(db_url_parts[:-1])
    
    # Connect to postgres database to create our database
    postgres_url = f"{base_url}/postgres"
    
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as connection:
            # Check if database exists
            result = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Create database
                connection.execute(text("COMMIT"))  # End any transaction
                connection.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Created database: {db_name}")
            else:
                print(f"Database {db_name} already exists")
                
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Make sure PostgreSQL is running and connection settings are correct")
        return False
    
    return True


def initialize_field_mapping_tables():
    """Initialize field mapping tables in the database."""
    try:
        # Create engine and session
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        create_tables(engine)
        print("Field mapping tables created successfully")
        
        # Test the connection and tables
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test query
        result = session.execute(text("SELECT COUNT(*) FROM field_configs"))
        count = result.scalar()
        print(f"Field configs table ready (current count: {count})")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error initializing tables: {e}")
        return False


def main():
    """Main initialization function."""
    print("Initializing LocPlat Field Mapping Database...")
    
    # Step 1: Create database if needed
    if not create_database_if_not_exists():
        sys.exit(1)
    
    # Step 2: Create tables
    if not initialize_field_mapping_tables():
        sys.exit(1)
    
    print("✅ Field mapping database initialization complete!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Use the field mapping API endpoints to configure collections")


if __name__ == "__main__":
    main()
