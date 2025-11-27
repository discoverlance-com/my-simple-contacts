from flask import Flask, render_template, request, redirect, url_for, flash
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Sample contacts data
sample_contacts = [
    {"id": 1, "name": "John Doe", "address": "123 Main Street, New York, NY 10001"},
    {"id": 2, "name": "Jane Smith", "address": "456 Oak Avenue, Los Angeles, CA 90210"},
    {"id": 3, "name": "Mike Johnson", "address": "789 Pine Road, Chicago, IL 60601"}
]


def validate_contact(name, address):
    """Validate contact form data"""
    errors = {}

    # Validate name
    if not name or not name.strip():
        errors['name'] = 'Name is required'
    elif len(name.strip()) < 2:
        errors['name'] = 'Name must be at least 2 characters long'

    # Validate address
    if not address or not address.strip():
        errors['address'] = 'Address is required'
    elif len(address.strip()) < 10:
        errors['address'] = 'Address must be at least 10 characters long'

    return errors


@app.route('/')
def homepage():
    """Homepage showing contacts list"""
    return render_template('homepage.html', contacts=sample_contacts)


@app.route('/create-contact', methods=['GET', 'POST'])
def create_contact():
    """Create new contact page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()

        # Validate form data
        errors = validate_contact(name, address)

        if errors:
            # Return form with errors
            return render_template('create_contact.html',
                                   errors=errors,
                                   name=name,
                                   address=address)

        # Log the validated contact details
        print(f"New contact created:")
        print(f"Name: {name}")
        print(f"Address: {address}")

        flash('Contact created successfully!', 'success')
        return redirect(url_for('homepage'))

    # GET request - show empty form
    return render_template('create_contact.html')


@app.route('/delete-contact/<int:contact_id>', methods=['POST'])
def delete_contact(contact_id):
    """Delete contact"""
    # Log the delete action
    print(f"Delete contact requested for ID: {contact_id}")

    # Find the contact name for better logging
    contact = next((c for c in sample_contacts if c['id'] == contact_id), None)
    if contact:
        print(f"Deleting contact: {contact['name']}")
    else:
        print(f"Contact with ID {contact_id} not found")

    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run(debug=True)
