from flask import Flask, render_template, request, redirect, url_for, flash
import os
from models import Contact, get_db_session, init_db, seed_database
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'fallback-dev-key'

# Initialize database on app startup
init_db()
# seed_database()


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
    elif len(address.strip()) < 5:
        errors['address'] = 'Address must be at least 5 characters long'

    return errors


@app.route('/')
def homepage():
    """Homepage showing contacts list"""
    session = get_db_session()

    try:
        contacts = session.query(Contact).all()
        # Convert to dict for template compatibility
        contacts_data = [contact.to_dict() for contact in contacts]
        return render_template('homepage.html', contacts=contacts_data)
    except SQLAlchemyError as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('homepage.html', contacts=[])
    finally:
        session.close()


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

        # Save to database
        session = get_db_session()
        try:
            new_contact = Contact(name=name, address=address)
            session.add(new_contact)
            session.commit()

            print(f"New contact saved to database:")
            print(f"ID: {new_contact.id}, Name: {name}, Address: {address}")

            flash('Contact created successfully!', 'success')
            return redirect(url_for('homepage'))

        except SQLAlchemyError as e:
            session.rollback()
            flash(f'Error saving contact: {str(e)}', 'error')
            return render_template('create_contact.html',
                                   errors={},
                                   name=name,
                                   address=address)
        finally:
            session.close()

    # GET request - show empty form
    return render_template('create_contact.html', errors={})


@app.route('/delete-contact/<int:contact_id>', methods=['POST'])
def delete_contact(contact_id):
    """Delete contact"""
    session = get_db_session()
    try:
        # Find the contact in database
        contact = session.query(Contact).filter(
            Contact.id == contact_id).first()

        if contact:
            contact_name = contact.name
            session.delete(contact)
            session.commit()

            print(
                f"Deleted contact from database: ID {contact_id}, Name: {contact_name}")
            flash('Contact deleted successfully!', 'success')
        else:
            print(f"Contact with ID {contact_id} not found")
            flash('Contact not found!', 'error')

    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Error deleting contact: {str(e)}', 'error')
        print(f"Database error during deletion: {e}")
    finally:
        session.close()

    return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)
