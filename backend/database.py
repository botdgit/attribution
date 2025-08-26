from sqlalchemy import create_engine
from google.cloud.sql.connector import Connector


def connect_with_connector(instance_connection_string: str, user: str, password: str):
    # Returns a SQLAlchemy engine connected via the Cloud SQL Python Connector.
    connector = Connector()

    def getconn():
        conn = connector.connect(
            instance_connection_string,
            "pg8000",
            user=user,
            password=password,
            db="postgres",
        )
        return conn

    engine = create_engine("postgresql+pg8000://", creator=getconn)
    return engine
