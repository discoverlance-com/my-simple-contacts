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
        # Register cleanup function
        atexit.register(cleanup_connector)
    return _connector


def cleanup_connector():
    """Clean up connector on application shutdown"""
    global _connector
    if _connector:
        try:
            _connector.close()
        except Exception as e:
            print(f"Error closing connector: {e}")
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

    # Create engine with proper connection pool settings
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
        pool_recycle=1800,  # Recycle connections every 30 minutes
        connect_args={
            "connect_timeout": 60,
            "read_timeout": 60,
            "write_timeout": 60,
        }
    )
    return pool
