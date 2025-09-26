import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")

con = duckdb.connect(f"{DB_NAME}.duckdb")

# Weather table
con.execute("""
CREATE TABLE IF NOT EXISTS weather (
    id INTEGER,
    city VARCHAR,
    temperature FLOAT,
    condition VARCHAR
)
""")
con.execute("DELETE FROM weather")  # clear if re-running
con.execute("""
INSERT INTO weather VALUES
    (1, 'Seattle', 55.2, 'Cloudy'),
    (2, 'Phoenix', 88.9, 'Sunny'),
    (3, 'Miami', 82.3, 'Rainy')
""")

# Forecast table
con.execute("""
CREATE TABLE IF NOT EXISTS forecast (
    forecast_id INTEGER,
    city VARCHAR,
    date DATE,
    high FLOAT,
    low FLOAT,
    condition VARCHAR
)
""")
con.execute("DELETE FROM forecast")
con.execute("""
INSERT INTO forecast VALUES
    (1, 'Seattle', '2025-09-26', 60.0, 50.0, 'Rain'),
    (2, 'Phoenix', '2025-09-26', 95.0, 75.0, 'Sunny'),
    (3, 'Miami', '2025-09-26', 85.0, 78.0, 'Stormy')
""")

# Cities table
con.execute("""
CREATE TABLE IF NOT EXISTS cities (
    city VARCHAR,
    state VARCHAR,
    population INTEGER
)
""")
con.execute("DELETE FROM cities")
con.execute("""
INSERT INTO cities VALUES
    ('Seattle', 'WA', 750000),
    ('Phoenix', 'AZ', 1650000),
    ('Miami', 'FL', 470000)
""")

con.close()
print("Database initialized with test data ✅")
