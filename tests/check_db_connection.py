import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(database_url)

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT current_database(), current_user;")
    )

    database, user = result.one()

    print(f"Connected to database: {database}")
    print(f"Connected as user: {user}")