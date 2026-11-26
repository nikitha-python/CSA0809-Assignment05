"""B3: Compare loop, pandas and SQLite group-by methods; benchmark and profile."""
import csv, io, sqlite3, time, cProfile, pstats, random
from datetime import date, timedelta
from collections import defaultdict
from pathlib import Path

def make_csv(stations, days=365, path="data/generated.csv"):
    Path(path).parent.mkdir(exist_ok=True)
    with open(path,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["station","date","pm25"])
        for s in range(stations):
            for d in range(days):
                # deterministic synthetic readings, one per day/station
                w.writerow([f"S{s+1:03d}",(date(2025,1,1)+timedelta(days=d)).isoformat(),round(20+(s*7+d%31)%100/2,2)])
    return path

def loop_means(path):
    sums=defaultdict(float); counts=defaultdict(int)
    with open(path,newline="") as f:
        for r in csv.DictReader(f):
            key=(r["station"],r["date"])
            sums[key]+=float(r["pm25"]); counts[key]+=1
    return {k:sums[k]/counts[k] for k in sums}

def pandas_means(path):
    import pandas as pd
    df=pd.read_csv(path)
    result=df.groupby(["station","date"])["pm25"].mean()
    return result.to_dict()

def sql_means(path):
    con=sqlite3.connect(":memory:")
    con.execute("CREATE TABLE r(station TEXT, day TEXT, pm25 REAL)")
    with open(path,newline="") as f:
        rows=[(r["station"],r["date"],float(r["pm25"])) for r in csv.DictReader(f)]
    con.executemany("INSERT INTO r VALUES(?,?,?)",rows)
    result={(s,d):v for s,d,v in con.execute("SELECT station,day,AVG(pm25) FROM r GROUP BY station,day")}
    con.close(); return result

def timed(fn,path):
    start=time.perf_counter(); result=fn(path); return time.perf_counter()-start,result

if __name__=="__main__":
    small=make_csv(2,days=10,path="data/small.csv")
    a=loop_means(small); b=pandas_means(small); c=sql_means(small)
    print("All methods agree:",a.keys()==b.keys()==c.keys() and all(abs(a[k]-b[k])<1e-9 and abs(a[k]-c[k])<1e-9 for k in a))
    print("Benchmark seconds (actual values from this computer):")
    for n in (1,12,120):
        path=make_csv(n)
        print(f"Stations={n}, rows={n*365}")
        for fn in (loop_means,pandas_means,sql_means):
            try:
                sec,_=timed(fn,path); print(fn.__name__,round(sec,4))
            except ImportError: print("pandas_means: install pandas to run")
    print("\\nProfiler for loop method:")
    prof=cProfile.Profile(); prof.enable(); loop_means("data/generated.csv"); prof.disable()
    pstats.Stats(prof).sort_stats("cumulative").print_stats(8)
