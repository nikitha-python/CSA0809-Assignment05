"""B1: Cleaning pipeline, SQLite storage, queries and visualisation."""
import csv, io, sqlite3, statistics, logging
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

RAW = """station,date,hour,pm25,pm10,no,temperature,temp_unit
Adyar,2026-10-01,08:00,48,82,12,30,C
Adyar,2026-10-02,08:00,NA,75,10,31,C
Adyar,2026-10-03,08:00,,79,11,89.6,F
Guindy,2026-10-01,08:00,95,140,22,95,F
Guindy,2026-10-02,08:00,-5,130,18,96,F
Guindy,2026-10-03,08:00,121,160,25,34,C
Velachery,2026-10-01,08:00,55,90,15,32,C
Velachery,2026-10-02,08:00,62,96,17,33,C
"""

def load_and_clean(text):
    reader = csv.DictReader(io.StringIO(text))
    required = {"station","date","hour","pm25","pm10","no","temperature","temp_unit"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValueError("CSV is missing one or more required columns")
    cleaned, seen = [], set()
    for row in reader:
        try:
            station = row["station"].strip().title()
            day = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date().isoformat()
            hour = row["hour"].strip()
            if not station or not hour: 
                continue
            vals = {}
            for col, upper in [("pm25",999),("pm10",2000),("no",1000)]:
                raw = (row[col] or "").strip()
                if raw.upper() in ("", "NA", "N/A", "NULL"):
                    vals[col] = None
                else:
                    v = float(raw)
                    vals[col] = v if 0 <= v <= upper else None
            temp = float(row["temperature"])
            unit = row["temp_unit"].strip().upper()
            if unit == "F":
                temp = (temp - 32) * 5/9
            elif unit != "C":
                raise ValueError("Unknown temperature unit")
            key = (station, day, hour)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append((station, day, hour, vals["pm25"], vals["pm10"], vals["no"], round(temp,2)))
        except (ValueError, TypeError, KeyError):
            logging.warning("Skipping invalid row: %r", row)
    # Fill missing PM2.5 by station median; if no station values, leave missing.
    by_station = {}
    for r in cleaned:
        if r[3] is not None: by_station.setdefault(r[0], []).append(r[3])
    medians = {s: statistics.median(v) for s,v in by_station.items()}
    out=[]
    for r in cleaned:
        pm = r[3] if r[3] is not None else medians.get(r[0])
        if pm is not None:
            out.append((r[0],r[1],r[2],pm,r[4],r[5],r[6]))
    return out

def create_db(rows, db_path="air_quality.db"):
    con=sqlite3.connect(db_path)
    con.execute("""CREATE TABLE IF NOT EXISTS readings(
        station TEXT NOT NULL, day TEXT NOT NULL, hour TEXT NOT NULL,
        pm25 REAL NOT NULL, pm10 REAL, no REAL, temperature_c REAL,
        PRIMARY KEY(station,day,hour))""")
    con.executemany("INSERT OR REPLACE INTO readings VALUES(?,?,?,?,?,?,?)", rows)
    con.execute("CREATE INDEX IF NOT EXISTS idx_station_day ON readings(station,day)")
    con.commit()
    return con

def make_charts(con):
    daily=con.execute("""SELECT day, AVG(pm25) FROM readings
                         GROUP BY day ORDER BY day""").fetchall()
    stations=con.execute("""SELECT station, AVG(pm25) FROM readings
                            GROUP BY station ORDER BY station""").fetchall()
    hours=con.execute("""SELECT hour, AVG(pm25) FROM readings
                         GROUP BY hour ORDER BY hour""").fetchall()
    if daily:
        plt.figure(); plt.plot([x[0] for x in daily],[x[1] for x in daily],marker="o")
        plt.title("Daily PM2.5 Trend"); plt.xlabel("Date"); plt.ylabel("PM2.5"); plt.xticks(rotation=30); plt.tight_layout(); plt.savefig("outputs/daily_trend.png"); plt.close()
    if stations:
        plt.figure(); plt.bar([x[0] for x in stations],[x[1] for x in stations])
        plt.title("Average PM2.5 by Station"); plt.xlabel("Station"); plt.ylabel("Mean PM2.5"); plt.tight_layout(); plt.savefig("outputs/station_comparison.png"); plt.close()
    if hours:
        plt.figure(); plt.bar([x[0] for x in hours],[x[1] for x in hours])
        plt.title("Average PM2.5 by Hour"); plt.xlabel("Hour"); plt.ylabel("Mean PM2.5"); plt.tight_layout(); plt.savefig("outputs/hourly_pollution.png"); plt.close()

if __name__=="__main__":
    logging.basicConfig(level=logging.WARNING)
    rows=load_and_clean(RAW)
    print("CLEANED ROWS:")
    for row in rows: print(row)
    con=create_db(rows)
    print("\nOctober station averages:")
    print(con.execute("SELECT station, AVG(pm25) FROM readings WHERE day LIKE '2026-10-%' GROUP BY station").fetchall())
    print("Daily summary:")
    print(con.execute("SELECT station,day,MIN(pm25),MAX(pm25),AVG(pm25),COUNT(pm25) FROM readings GROUP BY station,day").fetchall())
    make_charts(con); con.close()
    print("Charts saved in outputs/.")
