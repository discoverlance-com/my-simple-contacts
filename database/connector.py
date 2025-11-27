import os
import atexit
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

# Global connector instance for proper cleanup
_connector = None


def get_connector():
    """Get or create global connector instance with proper cleanup"""
    global _connector
    if _connector is None:
        ip_type = IPTypes.PRIVATE if os.environ.get(
            "PRIVATE_IP") else IPTypes.PUBLIC
        _connector = Connector(
            ip_type=ip_type,
            refresh_strategy="LAZY"
        )
        # Register cleanup for proper session management
        atexit.register(cleanup_connector)
    return _connector


def cleanup_connector():
    """Clean up connector on application shutdown"""
    global _connector
    if _connector:
        try:
            _connector.close()
            print("Connector closed successfully")
        except Exception as e:
            print(f"Error closing connector: {e}")
            # Ignore the error and continue shutdown
            pass
        finally:
            _connector = None


def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.
    Uses the Cloud SQL Python Connector package with proper connection management.
    """
    instance_connection_name = os.environ["CONTACTS_INSTANCE_CONNECTION_NAME"]
    db_user = os.environ["CONTACTS_DB_USER"]
    db_pass = os.environ["CONTACTS_DB_PASS"]
    db_name = os.environ["CONTACTS_DB_NAME"]

    connector = get_connector()

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    # Create engine optimized for Cloud Run with aggressive connection management
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        pool_size=2,  # Very small pool for Cloud Run
        max_overflow=0,  # No overflow to limit connections
        pool_pre_ping=False,  # Disable pre-ping to avoid InvalidatePoolError
        pool_recycle=300,  # More aggressive recycle (5 minutes)
        pool_reset_on_return='commit',  # Clean state on return
        pool_timeout=10,  # Short timeout for getting connections
        connect_args={
            "connect_timeout": 20,  # Reduced connection timeout
            "read_timeout": 20,
            "write_timeout": 20,
            "autocommit": False,  # Disable autocommit for better control
        },
        # Additional engine options for stability
        echo=False,  # Disable SQL logging in production
        future=True  # Use SQLAlchemy 2.0 style
    )
    return pool
