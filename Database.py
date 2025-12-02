import sqlite3
import pandas as pd

df = pd.read_csv("Tesla_Data.csv")   


conn = sqlite3.connect("ev_data.db")
cursor = conn.cursor()



cursor.execute("""
CREATE TABLE IF NOT EXISTS Date (
    date_id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month_name TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Region (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Model (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS EVMetrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id INTEGER NOT NULL,
    region_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    estimated_deliveries INTEGER,
    production_units INTEGER,
    avg_price_usd REAL,
    battery_capacity_kwh INTEGER,
    range_km INTEGER,
    co2_saved_tons REAL,
    charging_stations INTEGER,
    FOREIGN KEY (date_id) REFERENCES Date(date_id),
    FOREIGN KEY (region_id) REFERENCES Region(region_id),
    FOREIGN KEY (model_id) REFERENCES Model(model_id)
);
""")

conn.commit()



def get_or_create_date(year, month_name):
    cursor.execute("SELECT date_id FROM Date WHERE year=? AND month_name=?", (year, month_name))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO Date (year, month_name) VALUES (?, ?)", (year, month_name))
    conn.commit()
    return cursor.lastrowid


def get_or_create_region(region_name):
    cursor.execute("SELECT region_id FROM Region WHERE region_name=?", (region_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO Region (region_name) VALUES (?)", (region_name,))
    conn.commit()
    return cursor.lastrowid


def get_or_create_model(model_name):
    cursor.execute("SELECT model_id FROM Model WHERE model_name=?", (model_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO Model (model_name) VALUES (?)", (model_name,))
    conn.commit()
    return cursor.lastrowid




for row in df.itertuples(index=False):
    
    # Insert or get dimension keys
    date_id = get_or_create_date(row.Year, row.Month)
    region_id = get_or_create_region(row.Region)
    model_id = get_or_create_model(row.Model)

    # Insert fact row
    cursor.execute("""
        INSERT INTO EVMetrics (
            date_id, region_id, model_id,
            estimated_deliveries, production_units,
            avg_price_usd, battery_capacity_kwh, range_km,
            co2_saved_tons, charging_stations
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        date_id,
        region_id,
        model_id,
        int(row.Estimated_Deliveries),
        int(row.Production_Units),
        float(row.Avg_Price_USD),
        int(row.Battery_Capacity_kWh),
        int(row.Range_km),
        float(row.CO2_Saved_tons),
        int(row.Charging_Stations)
    ))

conn.commit()
conn.close()

print("Database successfully populated using Pandas DataFrame!")
