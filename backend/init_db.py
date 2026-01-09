"""
Database initialization script
Creates all tables and sets up the initial schema
"""
from app import create_app, db
from app.models import UserProfile, TrustedContact, ActionPolicy, AuditLog

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")

if __name__ == '__main__':
    init_database()