"""B2: hostile CSV inputs, safe SQL, and sentiment edge cases."""
import csv, io, sqlite3, codecs

def read_csv_safely(text, delimiter=","):
    if not text.strip(): return [], "empty file"
    try:
        reader=csv.DictReader(io.StringIO(text), delimiter=delimiter)
        required={"station","date","pm25"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return [], "missing required column or wrong delimiter"
        return list(reader), "OK"
    except (csv.Error, UnicodeError) as e:
        return [], f"CSV error: {e}"

def run_sql_demo():
    readings=[("Adyar","2026-10-01",48.0),("Guindy","2026-10-01",95.0),
              ("Guindy","2026-10-03",121.0),("Adyar","2026-10-04",60.0)]
    con=sqlite3.connect(":memory:")
    con.execute("CREATE TABLE aq(station TEXT, day TEXT, pm25 REAL)")
    con.executemany("INSERT INTO aq VALUES(?,?,?)",readings); con.commit()
    def station_average(name):
        row=con.execute("SELECT AVG(pm25) FROM aq WHERE station = ?",(name,)).fetchone()
        return row[0]
    print("Averages:",station_average("Adyar"),station_average("Guindy"))
    print("Injection attempt:",station_average("Adyar' OR '1'='1"))
    # Demonstrate why concatenation is unsafe; never use this in real code.
    attack="Adyar' OR '1'='1"
    unsafe="SELECT AVG(pm25) FROM aq WHERE station = '"+attack+"'"
    print("Unsafe SQL text:",unsafe)
    try: print("Unsafe result:",con.execute(unsafe).fetchone()[0])
    except sqlite3.Error as e: print("Unsafe query error:",e)
    con.close()

POS={"good","clean","fast","improved","safe","helpful","excellent"}
NEG={"bad","smoke","dirty","slow","polluted","harmful","poor","unhelpful"}
NEGATORS={"not","never","no","n't"}
def sentiment(text):
    words=text.lower().replace(".","").replace(",","").replace("!","").split()
    score=0
    for i,w in enumerate(words):
        val=1 if w in POS else -1 if w in NEG else 0
        if i>0 and words[i-1] in NEGATORS: val=-val
        score+=val
    return score, "positive" if score>0 else "negative" if score<0 else "neutral"

if __name__=="__main__":
    cases={
      "missing column":"station,date\nAdyar,2026-10-01",
      "wrong delimiter":"station;date;pm25\nAdyar;2026-10-01;48",
      "valid utf-8":"station,date,pm25\nAdyar,2026-10-01,48",
      "empty":"",
    }
    for name,data in cases.items(): print(name,read_csv_safely(data))
    # A non-UTF-8 byte sequence illustrates decoding failure.
    bad=b"station,date,pm25\nAdyar,2026-10-01,48\n"+bytes([0xff])
    try: bad.decode("utf-8")
    except UnicodeDecodeError: print("encoding test: UnicodeDecodeError caught; decode using the known source encoding")
    run_sql_demo()
    for s in ["The service is not good","Not bad, service improved",
              "Great service, but the road is dirty","The traffic is not never bad"]:
        print(s,"=>",sentiment(s))
