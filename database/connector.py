import os
import atexit
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

# Global connector instance for proper cleanup
_connector = None


def get_connector():
    """Get or create global connector instance"""
    global _connector
    if _connector is None:
        ip_type = IPTypes.PRIVATE if os.environ.get(
            "PRIVATE_IP") else IPTypes.PUBLIC
        _connector = Connector(ip_type=ip_type, refresh_strategy="LAZY")
        # Don't register cleanup for Cloud Run - let the platform handle it
        # atexit.register(cleanup_connector)
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

    # Create engine with robust connection pool settings for Cloud Run
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        pool_size=3,  # Smaller pool for Cloud Run
        max_overflow=1,  # Reduced overflow
        pool_pre_ping=True,  # Test connections before use
        # Recycle connections every 10 minutes (shorter than Cloud SQL idle timeout)
        pool_recycle=600,
        pool_reset_on_return='commit',  # Clean state on return
        connect_args={
            "connect_timeout": 30,  # Shorter connection timeout
            "read_timeout": 30,
            "write_timeout": 30,
            "autocommit": True,  # Enable autocommit for connection health
        }
    )
    return pool
