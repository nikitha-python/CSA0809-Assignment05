import csv, io
RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
"""
def load_clean(text):
    rows=[]
    for row in csv.DictReader(io.StringIO(text)):
        value=(row["pm25"] or "").strip()
        if value.upper() in ("","NA"): continue
        pm=float(value)
        if pm < 0 or pm > 999: continue
        rows.append((row["station"].strip(),row["date"].strip(),pm))
    return rows
def min_max(values):
    if not values: return ()
    lo,hi=min(values),max(values)
    if hi==lo: return tuple(0.0 for _ in values)
    return tuple(round((v-lo)/(hi-lo),3) for v in values)
clean=load_clean(RAW)
print(clean)
print(min_max([pm for _,_,pm in clean]))
