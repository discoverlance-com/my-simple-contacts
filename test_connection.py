#!/usr/bin/env python3
"""
Cloud SQL Connection Monitor
Simple script to test database connectivity and diagnose connection issues.
"""

import os
import sys
import time
from contextlib import contextmanager


def test_basic_connection():
    """Test basic database connectivity without our retry logic"""
    print("Testing basic database connection...")

    # Check if we're in Cloud SQL mode
    is_cloud_sql = all(key in os.environ for key in [
        'CONTACTS_INSTANCE_CONNECTION_NAME',
        'CONTACTS_DB_USER',
        'CONTACTS_DB_PASS',
        'CONTACTS_DB_NAME'
    ])

    if is_cloud_sql:
        print("📡 Cloud SQL mode detected")
        try:
            from database.connector import connect_with_connector
            engine = connect_with_connector()

            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1")).scalar()
                print(f"✅ Cloud SQL connection successful: {result}")
                conn.close()

            engine.dispose()
            return True

        except Exception as e:
            print(f"❌ Cloud SQL connection failed: {e}")
            return False
    else:
        print("💾 SQLite mode detected")
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine('sqlite:///contacts.db')

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                print(f"✅ SQLite connection successful: {result}")
                conn.close()

            engine.dispose()
            return True

        except Exception as e:
            print(f"❌ SQLite connection failed: {e}")
            return False


def test_application_context():
    """Test the application's database context manager"""
    print("\\nTesting application database context...")

    try:
        from models import get_db_session_context, Contact
        from sqlalchemy import text

        with get_db_session_context() as session:
            # Test basic query
            result = session.execute(text("SELECT 1")).scalar()
            print(f"✅ Context manager test successful: {result}")

            # Test contact count
            count = session.query(Contact).count()
            print(f"📊 Contact count: {count}")

        return True

    except Exception as e:
        print(f"❌ Context manager test failed: {e}")
        return False


def test_health_endpoint():
    """Test the health check endpoint"""
    print("\\nTesting health check endpoint...")

    try:
        from main import app

        with app.test_client() as client:
            response = client.get('/health')

            if response.status_code == 200:
                print(f"✅ Health check passed: {response.get_json()}")
                return True
            else:
                print(
                    f"❌ Health check failed: {response.status_code} - {response.get_json()}")
                return False

    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def main():
    print("🔍 Cloud SQL Connection Diagnostics")
    print("=" * 50)

    tests = [
        ("Basic Connection", test_basic_connection),
        ("Application Context", test_application_context),
        ("Health Endpoint", test_health_endpoint)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\\n🧪 Running {test_name} Test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\\n" + "=" * 50)
    print("📋 Test Summary:")

    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False

    if all_passed:
        print("\\n🎉 All tests passed! Database connectivity looks good.")
        return 0
    else:
        print("\\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
