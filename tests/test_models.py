import pytest
import tempfile
import os
from sqlalchemy import create_engine
from models import Contact, Base, get_db_session_context, SessionLocal
from sqlalchemy.orm import sessionmaker


class TestContactModel:
    """Tests for the Contact model"""

    def test_contact_creation(self):
        """Test creating a new contact"""
        contact = Contact(name="John Doe", address="123 Main St")

        assert getattr(contact, 'name') == "John Doe"
        assert getattr(contact, 'address') == "123 Main St"
        assert contact.id is None  # Should be None before saving

    def test_contact_repr(self):
        """Test contact string representation"""
        contact = Contact(id=1, name="John Doe", address="123 Main St")

        expected = "<Contact(id=1, name='John Doe', address='123 Main St')>"
        assert repr(contact) == expected

    def test_contact_to_dict(self):
        """Test converting contact to dictionary"""
        contact = Contact(id=1, name="John Doe", address="123 Main St")

        expected = {
            'id': 1,
            'name': 'John Doe',
            'address': '123 Main St'
        }
        assert contact.to_dict() == expected

    def test_contact_to_dict_no_id(self):
        """Test converting unsaved contact to dictionary"""
        contact = Contact(name="John Doe", address="123 Main St")

        result = contact.to_dict()
        assert result['name'] == 'John Doe'
        assert result['address'] == '123 Main St'
        assert result['id'] is None


class TestDatabaseOperations:
    """Tests for database operations"""

    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up a test database for each test"""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Create test engine
        self.test_engine = create_engine(
            f'sqlite:///{self.db_path}', echo=False)

        # Override the global engine and session
        import models
        self.original_engine = models.engine
        self.original_session = models.SessionLocal

        models.engine = self.test_engine
        models.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine)

        # Create tables
        Base.metadata.create_all(bind=self.test_engine)

        yield

        # Clean up properly
        models.engine = self.original_engine
        models.SessionLocal = self.original_session
        # Dispose of test engine to close all connections
        self.test_engine.dispose()
        os.close(self.db_fd)
        # Small delay to ensure connections are closed on Windows
        import time
        time.sleep(0.1)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            # Retry once more after a longer delay
            time.sleep(0.5)
            os.unlink(self.db_path)

    def test_database_session_context_manager(self):
        """Test the database session context manager"""
        contact_data = {'name': 'Test User', 'address': 'Test Address'}

        # Create a contact using context manager
        with get_db_session_context() as session:
            contact = Contact(**contact_data)
            session.add(contact)
            # Commit should happen automatically

        # Verify contact was saved
        with get_db_session_context() as session:
            saved_contact = session.query(
                Contact).filter_by(name='Test User').first()
            assert saved_contact is not None
            assert getattr(saved_contact, 'name') == 'Test User'
            assert getattr(saved_contact, 'address') == 'Test Address'

    def test_database_session_rollback_on_error(self):
        """Test that database session rolls back on error"""
        # First, create a contact
        with get_db_session_context() as session:
            contact = Contact(name='Valid Contact', address='Valid Address')
            session.add(contact)

        # Now try to create a contact that will cause an error
        try:
            with get_db_session_context() as session:
                contact = Contact(name='Test User', address='Test Address')
                session.add(contact)
                # Force an error by trying to access a non-existent attribute
                _ = contact.nonexistent_attribute
        except AttributeError:
            pass

        # Verify that only the first contact exists
        with get_db_session_context() as session:
            contacts = session.query(Contact).all()
            assert len(contacts) == 1
            assert contacts[0] is not None
            assert getattr(contacts[0], 'name') == 'Valid Contact'

    def test_database_multiple_contacts(self):
        """Test creating multiple contacts"""
        contacts_data = [
            {'name': 'User 1', 'address': 'Address 1'},
            {'name': 'User 2', 'address': 'Address 2'},
            {'name': 'User 3', 'address': 'Address 3'}
        ]

        # Create multiple contacts
        with get_db_session_context() as session:
            for data in contacts_data:
                contact = Contact(**data)
                session.add(contact)

        # Verify all contacts were saved
        with get_db_session_context() as session:
            saved_contacts = session.query(Contact).all()
            assert len(saved_contacts) == 3

            names = [c.name for c in saved_contacts]
            assert 'User 1' in names
            assert 'User 2' in names
            assert 'User 3' in names

    def test_database_update_contact(self):
        """Test updating a contact"""
        # Create a contact
        with get_db_session_context() as session:
            contact = Contact(name='Original Name', address='Original Address')
            session.add(contact)
            session.flush()  # Get the ID
            contact_id = contact.id

        # Update the contact
        with get_db_session_context() as session:
            contact = session.query(Contact).get(contact_id)
            assert contact is not None
            contact.name = 'Updated Name'
            contact.address = 'Updated Address'

        # Verify the update
        with get_db_session_context() as session:
            updated_contact = session.query(Contact).get(contact_id)
            assert updated_contact is not None
            assert getattr(updated_contact, 'name') == 'Updated Name'
            assert getattr(updated_contact, 'address') == 'Updated Address'

    def test_database_delete_contact(self):
        """Test deleting a contact"""
        # Create a contact
        with get_db_session_context() as session:
            contact = Contact(name='To Delete', address='Delete Address')
            session.add(contact)
            session.flush()
            contact_id = contact.id

        # Delete the contact
        with get_db_session_context() as session:
            contact = session.query(Contact).get(contact_id)
            session.delete(contact)

        # Verify deletion
        with get_db_session_context() as session:
            deleted_contact = session.query(Contact).get(contact_id)
            assert deleted_contact is None

    def test_database_query_filtering(self):
        """Test querying contacts with filters"""
        # Create test contacts
        with get_db_session_context() as session:
            contacts = [
                Contact(name='John Doe', address='New York'),
                Contact(name='Jane Smith', address='Los Angeles'),
                Contact(name='John Smith', address='Chicago')
            ]
            for contact in contacts:
                session.add(contact)

        # Test filtering by name
        with get_db_session_context() as session:
            johns = session.query(Contact).filter(
                Contact.name.like('John%')).all()
            assert len(johns) == 2

            # Test filtering by address
            ny_contacts = session.query(Contact).filter(
                Contact.address.like('%New York%')).all()
            assert len(ny_contacts) == 1
            assert ny_contacts[0] is not None
            # Use getattr to avoid linter issues with SQLAlchemy attributes
            assert getattr(ny_contacts[0], 'name') == 'John Doe'


class TestDatabaseErrors:
    """Tests for database error handling"""

    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up a test database for each test"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.test_engine = create_engine(
            f'sqlite:///{self.db_path}', echo=False)

        import models
        self.original_engine = models.engine
        self.original_session = models.SessionLocal

        models.engine = self.test_engine
        models.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine)

        Base.metadata.create_all(bind=self.test_engine)

        yield

        # Proper cleanup with connection disposal
        models.engine = self.original_engine
        models.SessionLocal = self.original_session
        # Dispose of test engine to close all connections
        self.test_engine.dispose()
        os.close(self.db_fd)
        # Small delay to ensure connections are closed on Windows
        import time
        time.sleep(0.1)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            # Retry once more after a longer delay
            time.sleep(0.5)
            os.unlink(self.db_path)

    def test_database_constraint_violation(self):
        """Test handling database constraint violations"""
        # This test depends on your specific database constraints
        # For SQLite, we can test NULL constraints

        with pytest.raises(Exception):  # Should raise an exception for NULL name
            with get_db_session_context() as session:
                contact = Contact(name=None, address='Some address')
                session.add(contact)
                session.flush()  # Force the constraint check
