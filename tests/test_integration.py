import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from models import get_engine, init_db, seed_database, Contact, get_db_session_context
from sqlalchemy import create_engine


class TestDatabaseConfiguration:
    """Tests for database configuration and environment detection"""

    def test_sqlite_database_detection(self):
        """Test SQLite database is used when no Cloud SQL env vars"""
        # Ensure no Cloud SQL environment variables are set
        env_vars = [
            'CONTACTS_INSTANCE_CONNECTION_NAME',
            'CONTACTS_DB_USER',
            'CONTACTS_DB_PASS',
            'CONTACTS_DB_NAME'
        ]

        with patch.dict(os.environ, {}, clear=True):
            # Clear all environment variables
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]

            engine = get_engine()
            assert 'sqlite' in str(engine.url)

    @patch('models.connect_with_connector')
    def test_cloud_sql_database_detection(self, mock_connector):
        """Test Cloud SQL is used when environment variables are set"""
        mock_engine = MagicMock()
        mock_connector.return_value = mock_engine

        env_vars = {
            'CONTACTS_INSTANCE_CONNECTION_NAME': 'test-project:region:instance',
            'CONTACTS_DB_USER': 'test-user',
            'CONTACTS_DB_PASS': 'test-pass',
            'CONTACTS_DB_NAME': 'test-db'
        }

        with patch.dict(os.environ, env_vars):
            engine = get_engine()
            mock_connector.assert_called_once()
            assert engine == mock_engine


class TestDatabaseInitialization:
    """Tests for database initialization functions"""

    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up isolated test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.test_engine = create_engine(
            f'sqlite:///{self.db_path}', echo=False)

        # Override global engine
        import models
        self.original_engine = models.engine
        models.engine = self.test_engine

        yield

        # Restore original engine and clean up properly
        models.engine = self.original_engine
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

    def test_init_db_creates_tables(self):
        """Test that init_db creates the necessary tables"""
        # Tables should not exist initially
        from sqlalchemy import inspect
        inspector = inspect(self.test_engine)
        initial_tables = inspector.get_table_names()
        assert 'contacts' not in initial_tables

        # Initialize database
        init_db()

        # Tables should now exist
        inspector = inspect(self.test_engine)
        tables = inspector.get_table_names()
        assert 'contacts' in tables

    def test_seed_database_empty_db(self):
        """Test seeding empty database"""
        # Initialize tables first
        init_db()

        # Update SessionLocal to use test engine
        import models
        from sqlalchemy.orm import sessionmaker
        models.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine)

        # Seed the database
        seed_database()

        # Check that contacts were created
        with get_db_session_context() as session:
            contacts = session.query(Contact).all()
            assert len(contacts) == 3

            names = [c.name for c in contacts]
            assert 'John Doe' in names
            assert 'Jane Smith' in names
            assert 'Mike Johnson' in names

    def test_seed_database_existing_contacts(self):
        """Test that seeding doesn't duplicate existing contacts"""
        # Initialize tables and create a contact
        init_db()

        import models
        from sqlalchemy.orm import sessionmaker
        models.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine)

        with get_db_session_context() as session:
            existing_contact = Contact(
                name='Existing Contact', address='Existing Address')
            session.add(existing_contact)

        # Now try to seed
        seed_database()

        # Should still only have 1 contact (the existing one)
        with get_db_session_context() as session:
            contacts = session.query(Contact).all()
            assert len(contacts) == 1
            assert contacts[0] is not None
            assert getattr(contacts[0], 'name') == 'Existing Contact'


class TestApplicationConfiguration:
    """Tests for Flask application configuration"""

    def test_app_secret_key_from_environment(self):
        """Test that secret key is read from environment"""
        test_secret = 'test-secret-key-from-env'

        with patch.dict(os.environ, {'SECRET_KEY': test_secret}):
            # Re-import to get the updated configuration
            import importlib
            import main
            importlib.reload(main)

            assert main.app.secret_key == test_secret

    def test_app_secret_key_fallback(self):
        """Test fallback secret key when environment variable is not set"""
        with patch.dict(os.environ, {}, clear=True):
            if 'SECRET_KEY' in os.environ:
                del os.environ['SECRET_KEY']

            # Re-import to get the updated configuration
            import importlib
            import main
            importlib.reload(main)

            assert main.app.secret_key == 'fallback-dev-key'


class TestErrorHandling:
    """Tests for error handling in various scenarios"""

    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.test_engine = create_engine(
            f'sqlite:///{self.db_path}', echo=False)

        import models
        from sqlalchemy.orm import sessionmaker
        self.original_engine = models.engine
        self.original_sessionlocal = models.SessionLocal
        models.engine = self.test_engine
        models.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine)

        # Initialize database
        from models import Base
        Base.metadata.create_all(bind=self.test_engine)

        yield

        # Proper cleanup with connection disposal
        models.engine = self.original_engine
        models.SessionLocal = self.original_sessionlocal
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

    def test_database_session_error_handling(self):
        """Test that database errors are properly handled"""
        # This test ensures that even if an error occurs, the session is properly closed
        session_was_closed = False

        try:
            with get_db_session_context() as session:
                # Create a valid contact first
                contact = Contact(name='Test', address='Test Address')
                session.add(contact)

                # Now force an error by trying to access non-existent attribute
                _ = contact.nonexistent_attribute
        except AttributeError:
            # Error is expected
            session_was_closed = True

        # Verify that we can still use the database (session was properly closed)
        with get_db_session_context() as session:
            contacts = session.query(Contact).all()
            # Should be empty because the transaction was rolled back
            assert len(contacts) == 0


class TestIntegrationScenarios:
    """Integration tests for common user scenarios"""

    @pytest.fixture(autouse=True)
    def setup_test_app(self):
        """Set up complete test application"""
        from main import app

        self.db_fd, self.db_path = tempfile.mkstemp()
        self.test_engine = create_engine(
            f'sqlite:///{self.db_path}', echo=False)

        app.config['TESTING'] = True

        # Override database
        import models
        from sqlalchemy.orm import sessionmaker
        self.original_engine = models.engine
        self.original_sessionlocal = models.SessionLocal
        models.engine = self.test_engine
        models.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine)

        # Initialize database
        init_db()

        self.client = app.test_client()

        yield

        # Proper cleanup with connection disposal
        models.engine = self.original_engine
        models.SessionLocal = self.original_sessionlocal
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

    def test_complete_contact_lifecycle(self):
        """Test creating, viewing, and deleting a contact"""
        # Start with empty database
        response = self.client.get('/')
        assert b'No contacts found' in response.data

        # Create a new contact
        contact_data = {
            'name': 'Integration Test User',
            'address': '123 Integration Test Street, Test City, TC 12345'
        }
        response = self.client.post(
            '/create-contact', data=contact_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Contact created successfully!' in response.data
        assert b'Integration Test User' in response.data

        # Verify contact appears on homepage
        response = self.client.get('/')
        assert b'Integration Test User' in response.data
        assert b'123 Integration Test Street' in response.data

        # Get the contact ID from the database for deletion
        with get_db_session_context() as session:
            contact = session.query(Contact).filter_by(
                name='Integration Test User').first()
            assert contact is not None, "Contact not found in database"
            contact_id = contact.id

        # Delete the contact
        response = self.client.post(
            f'/delete-contact/{contact_id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'Contact deleted successfully!' in response.data
        assert b'Integration Test User' not in response.data

    def test_form_validation_persistence(self):
        """Test that form data persists through validation errors"""
        # Submit invalid data
        invalid_data = {
            'name': 'A',  # Too short
            'address': '123 Very Long Address That Should Be Valid'
        }
        response = self.client.post('/create-contact', data=invalid_data)

        # Should show validation error but preserve address
        assert response.status_code == 200
        assert b'Name must be at least 2 characters' in response.data
        assert b'123 Very Long Address That Should Be Valid' in response.data

    def test_multiple_contacts_management(self):
        """Test managing multiple contacts"""
        contacts = [
            {'name': 'Contact One', 'address': 'Address One'},
            {'name': 'Contact Two', 'address': 'Address Two'},
            {'name': 'Contact Three', 'address': 'Address Three'}
        ]

        # Create multiple contacts
        for contact in contacts:
            response = self.client.post(
                '/create-contact', data=contact, follow_redirects=True)
            assert response.status_code == 200

        # Verify all contacts appear on homepage
        response = self.client.get('/')
        for contact in contacts:
            assert contact['name'].encode() in response.data

        # Delete one contact
        with get_db_session_context() as session:
            contact_to_delete = session.query(
                Contact).filter_by(name='Contact Two').first()
            assert contact_to_delete is not None, "Contact Two not found in database"
            contact_id = contact_to_delete.id

        response = self.client.post(
            f'/delete-contact/{contact_id}', follow_redirects=True)
        assert response.status_code == 200

        # Verify correct contact was deleted
        response = self.client.get('/')
        assert b'Contact One' in response.data
        assert b'Contact Two' not in response.data
        assert b'Contact Three' in response.data
