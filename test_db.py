#!/usr/bin/env python3
"""
Database connection test script
Run this to verify your database configuration is working correctly.
"""

import os
import sys
from models import get_db_session_context, Contact


def test_database_connection():
    """Test database connection and basic operations"""
    print("Testing database connection...")

    try:
        with get_db_session_context() as session:
            # Test basic query
            contact_count = session.query(Contact).count()
            print(f"✅ Database connection successful!")
            print(f"📊 Current contacts in database: {contact_count}")

            # Test if we can fetch a contact
            if contact_count > 0:
                first_contact = session.query(Contact).first()
                print(
                    f"📧 First contact: {first_contact.name if first_contact else 'No contacts found'}")

            return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_environment():
    """Check environment configuration"""
    print("\n🔍 Environment Check:")

    cloud_sql_vars = [
        'CONTACTS_INSTANCE_CONNECTION_NAME',
        'CONTACTS_DB_USER',
        'CONTACTS_DB_PASS',
        'CONTACTS_DB_NAME'
    ]

    has_cloud_sql = all(var in os.environ for var in cloud_sql_vars)

    if has_cloud_sql:
        print("☁️ Google Cloud SQL configuration detected")
        print(
            f"   Instance: {os.environ.get('CONTACTS_INSTANCE_CONNECTION_NAME')}")
        print(f"   Database: {os.environ.get('CONTACTS_DB_NAME')}")
        print(f"   User: {os.environ.get('CONTACTS_DB_USER')}")
    else:
        print("💾 SQLite configuration (development mode)")
        print("   Database: contacts.db")

    return has_cloud_sql


if __name__ == "__main__":
    print("🧪 Simple Contacts - Database Test\n")

    # Check environment
    is_cloud_sql = check_environment()

    # Test connection
    success = test_database_connection()

    if success:
        print("\n✅ All tests passed! Database is ready.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! Check your database configuration.")
        sys.exit(1)
