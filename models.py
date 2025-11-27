from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from database.connector import connect_with_connector
import os

# Create the base class for our models
Base = declarative_base()


class Contact(Base):
    """Contact model for SQLAlchemy"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(500), nullable=False)

    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', address='{self.address}')>"

    def to_dict(self):
        """Convert contact to dictionary for easy template rendering"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address
        }

# Database setup


def get_engine():
    """Get database engine - uses Cloud SQL in production, SQLite for development"""
    try:
        if all(key in os.environ for key in [
            'CONTACTS_INSTANCE_CONNECTION_NAME',
            'CONTACTS_DB_USER',
            'CONTACTS_DB_PASS',
            'CONTACTS_DB_NAME'
        ]):
            # Production: Use Google Cloud SQL
            print("Using Google Cloud SQL database")
            return connect_with_connector()
        else:
            # Development: Use SQLite
            print("Using SQLite database for development")
            return create_engine('sqlite:///contacts.db', echo=True)
    except Exception as e:
        print(f"Error creating database engine: {e}")
        # Fallback to SQLite if Cloud SQL fails
        print("Falling back to SQLite database")
        return create_engine('sqlite:///contacts.db', echo=True)


# Create engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get database session"""
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.close()
        raise e


@contextmanager
def get_db_session_context():
    """Get database session with proper context management and retry logic"""
    global engine, SessionLocal

    session = None
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            session = SessionLocal()
            # Test the connection with a simple query to catch stale connections
            session.execute(text("SELECT 1"))
            break
        except Exception as e:
            if session is not None:
                session.close()
                session = None
            retry_count += 1
            if retry_count >= max_retries:
                print(
                    f"Database connection failed after {max_retries} retries: {e}")
                raise
            print(
                f"Database connection attempt {retry_count} failed, retrying...")
            # Reset the engine to clear stale connections
            if engine:
                engine.dispose()
                engine = get_engine()
                SessionLocal = sessionmaker(
                    autocommit=False, autoflush=False, bind=engine)

    if session is None:
        raise Exception("Failed to create database session")

    try:
        yield session
        session.commit()
    except Exception:
        if session is not None:
            session.rollback()
        raise
    finally:
        if session is not None:
            session.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def seed_database():
    """Add sample data if database is empty"""
    try:
        with get_db_session_context() as session:
            # Check if contacts already exist
            contact_count = session.query(Contact).count()

            if contact_count == 0:
                print("Seeding database with sample contacts...")
                sample_contacts = [
                    Contact(name="John Doe",
                            address="123 Main Street, New York, NY 10001"),
                    Contact(name="Jane Smith",
                            address="456 Oak Avenue, Los Angeles, CA 90210"),
                    Contact(name="Mike Johnson",
                            address="789 Pine Road, Chicago, IL 60601")
                ]

                for contact in sample_contacts:
                    session.add(contact)

                # Context manager handles commit automatically
                print("Sample contacts added successfully")
            else:
                print(f"Database already contains {contact_count} contacts")

    except Exception as e:
        print(f"Error seeding database: {e}")
