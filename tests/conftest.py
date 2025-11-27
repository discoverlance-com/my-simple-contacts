import pytest
import os
import tempfile
from main import app
from models import Contact, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestConfig:
    """Test configuration class"""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False


@pytest.fixture(scope='function')
def test_app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()

    # Configure test app
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    # Override the database engine for testing
    test_engine = create_engine(f'sqlite:///{db_path}', echo=False)

    # Monkey patch the models to use test database
    import models
    models.engine = test_engine
    models.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine)

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    with app.app_context():
        yield app

    # Clean up - dispose of all connections first
    test_engine.dispose()
    # Close any remaining sessions
    models.SessionLocal.close_all()
    os.close(db_fd)
    # Small delay to ensure connections are closed on Windows
    import time
    time.sleep(0.1)
    try:
        os.unlink(db_path)
    except PermissionError:
        # Retry once more after a longer delay
        time.sleep(0.5)
        os.unlink(db_path)


@pytest.fixture
def client(test_app):
    """A test client for the app."""
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    """A test runner for the app's Click commands."""
    return test_app.test_cli_runner()


@pytest.fixture
def sample_contact_data():
    """Sample contact data for testing"""
    return {
        'name': 'John Doe',
        'address': '123 Main Street, New York, NY 10001'
    }


@pytest.fixture
def create_sample_contact(test_app):
    """Create a sample contact in the database"""
    from models import get_db_session_context

    with get_db_session_context() as session:
        contact = Contact(
            name='Jane Smith',
            address='456 Oak Avenue, Los Angeles, CA 90210'
        )
        session.add(contact)
        session.commit()
        session.refresh(contact)
        # Store the ID to avoid DetachedInstanceError
        contact_id = contact.id
        # Create a simple object with the ID that won't cause session issues

        class ContactStub:
            def __init__(self, id, name, address):
                self.id = id
                self.name = name
                self.address = address

        return ContactStub(contact_id, contact.name, contact.address)
