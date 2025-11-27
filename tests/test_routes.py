import pytest
from models import Contact


class TestHomepage:
    """Tests for the homepage route"""

    def test_homepage_empty_database(self, client):
        """Test homepage with no contacts"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'Simple Contacts' in response.data
        assert b'No contacts found' in response.data
        assert b'Create your first contact!' in response.data

    def test_homepage_with_contacts(self, client, create_sample_contact):
        """Test homepage displaying contacts"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'Simple Contacts' in response.data
        assert b'Jane Smith' in response.data
        assert b'456 Oak Avenue' in response.data
        assert b'Delete' in response.data

    def test_homepage_create_button(self, client):
        """Test that create contact button is present"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'Create New Contact' in response.data
        assert b'/create-contact' in response.data

    def test_homepage_flash_messages(self, client):
        """Test flash messages display correctly"""
        with client.session_transaction() as sess:
            sess['_flashes'] = [('success', 'Test message')]

        response = client.get('/')
        assert b'Test message' in response.data


class TestCreateContact:
    """Tests for the create contact functionality"""

    def test_create_contact_get(self, client):
        """Test GET request to create contact page"""
        response = client.get('/create-contact')

        assert response.status_code == 200
        assert b'Create New Contact' in response.data
        assert b'<form' in response.data
        assert b'name="name"' in response.data
        assert b'name="address"' in response.data
        assert b'Cancel' in response.data

    def test_create_contact_valid_data(self, client, sample_contact_data):
        """Test creating contact with valid data"""
        response = client.post(
            '/create-contact', data=sample_contact_data, follow_redirects=True)

        assert response.status_code == 200
        assert b'Contact created successfully!' in response.data
        assert b'John Doe' in response.data
        assert b'123 Main Street' in response.data

    def test_create_contact_empty_name(self, client):
        """Test creating contact with empty name"""
        data = {'name': '', 'address': '123 Main Street'}
        response = client.post('/create-contact', data=data)

        assert response.status_code == 200
        assert b'Name is required' in response.data
        assert b'Create New Contact' in response.data

    def test_create_contact_empty_address(self, client):
        """Test creating contact with empty address"""
        data = {'name': 'John Doe', 'address': ''}
        response = client.post('/create-contact', data=data)

        assert response.status_code == 200
        assert b'Address is required' in response.data
        assert b'Create New Contact' in response.data

    def test_create_contact_short_name(self, client):
        """Test creating contact with name too short"""
        data = {'name': 'J', 'address': '123 Main Street, New York, NY'}
        response = client.post('/create-contact', data=data)

        assert response.status_code == 200
        assert b'Name must be at least 2 characters' in response.data

    def test_create_contact_short_address(self, client):
        """Test creating contact with address too short"""
        data = {'name': 'John Doe', 'address': 'NYC'}
        response = client.post('/create-contact', data=data)

        assert response.status_code == 200
        assert b'Address must be at least 5 characters' in response.data

    def test_create_contact_whitespace_handling(self, client):
        """Test that whitespace is properly trimmed"""
        data = {'name': '  John Doe  ', 'address': '  123 Main Street  '}
        response = client.post(
            '/create-contact', data=data, follow_redirects=True)

        assert response.status_code == 200
        assert b'Contact created successfully!' in response.data
        assert b'John Doe' in response.data

    def test_create_contact_form_persistence(self, client):
        """Test that form data persists on validation error"""
        data = {'name': 'John Doe', 'address': 'NY'}  # Address too short
        response = client.post('/create-contact', data=data)

        assert response.status_code == 200
        assert b'value="John Doe"' in response.data  # Name should be preserved
        assert b'NY' in response.data  # Address should be preserved


class TestDeleteContact:
    """Tests for delete contact functionality"""

    def test_delete_existing_contact(self, client, create_sample_contact):
        """Test deleting an existing contact"""
        contact = create_sample_contact
        response = client.post(
            f'/delete-contact/{contact.id}', follow_redirects=True)

        assert response.status_code == 200
        assert b'Contact deleted successfully!' in response.data
        # Should not see the contact anymore
        assert b'Jane Smith' not in response.data

    def test_delete_nonexistent_contact(self, client):
        """Test deleting a contact that doesn't exist"""
        response = client.post('/delete-contact/999', follow_redirects=True)

        assert response.status_code == 200
        assert b'Contact not found!' in response.data

    def test_delete_contact_get_method_not_allowed(self, client, create_sample_contact):
        """Test that GET method is not allowed for delete"""
        contact = create_sample_contact
        response = client.get(f'/delete-contact/{contact.id}')

        assert response.status_code == 405  # Method Not Allowed


class TestFormValidation:
    """Tests for form validation logic"""

    def test_validation_function_empty_inputs(self):
        """Test validation function with empty inputs"""
        from main import validate_contact

        errors = validate_contact('', '')
        assert 'name' in errors
        assert 'address' in errors
        assert errors['name'] == 'Name is required'
        assert errors['address'] == 'Address is required'

    def test_validation_function_whitespace_inputs(self):
        """Test validation function with whitespace inputs"""
        from main import validate_contact

        errors = validate_contact('   ', '   ')
        assert 'name' in errors
        assert 'address' in errors

    def test_validation_function_valid_inputs(self):
        """Test validation function with valid inputs"""
        from main import validate_contact

        errors = validate_contact('John Doe', '123 Main Street, NY')
        assert len(errors) == 0

    def test_validation_function_edge_cases(self):
        """Test validation function edge cases"""
        from main import validate_contact

        # Minimum valid lengths
        errors = validate_contact('Jo', '12345')
        assert len(errors) == 0

        # Just below minimum
        errors = validate_contact('J', '1234')
        assert 'name' in errors
        assert 'address' in errors


class TestResponseHeaders:
    """Tests for HTTP response headers and status codes"""

    def test_homepage_headers(self, client):
        """Test homepage response headers"""
        response = client.get('/')

        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_create_contact_headers(self, client):
        """Test create contact page headers"""
        response = client.get('/create-contact')

        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_nonexistent_route(self, client):
        """Test accessing nonexistent route"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
