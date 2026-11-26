"""B4: complaint sentiment, extractive summary, agreement, indexed-query timing."""
import re, sqlite3, time, statistics
from collections import Counter

POS={"clean","fast","good","safe","improved","helpful","excellent","beautiful","fresh"}
NEG={"smoke","bad","dirty","slow","polluted","harmful","poor","unhelpful","waste"}
NEGATORS={"not","never","no","n't"}
STOP={"the","is","a","an","and","or","to","of","in","on","it","was","are","we","i","this","that","with","for"}

def score(text):
    words=re.findall(r"[a-z']+",text.lower())
    total=0
    for i,w in enumerate(words):
        v=1 if w in POS else -1 if w in NEG else 0
        if i>0 and words[i-1] in NEGATORS: v=-v
        total+=v
    return total

def label(text):
    s=score(text)
    return "positive" if s>0 else "negative" if s<0 else "neutral"

def summarise(text, k=2):
    sentences=[s.strip() for s in re.split(r"(?<=[.!?])\\s+",text) if s.strip()]
    words=[w for w in re.findall(r"[a-z']+",text.lower()) if w not in STOP]
    freq=Counter(words)
    ranked=sorted(enumerate(sentences),key=lambda p:sum(freq[w] for w in re.findall(r"[a-z']+",p[1].lower())),reverse=True)
    chosen=sorted(ranked[:k],key=lambda p:p[0])
    return " ".join(s for _,s in chosen)

COMPLAINTS=[
"Roads are clean and the bus was fast.","Smoke from the factory, air is bad.",
"The staff were not helpful.","Not bad, service improved.",
"The street is dirty and full of waste.","The park is beautiful and clean.",
"Traffic is slow and pollution is harmful.","Water is clean and safe.",
"The drains smell bad.","The air is fresh today."
]*5

def database_index_experiment():
    con=sqlite3.connect(":memory:")
    con.execute("CREATE TABLE readings(station TEXT, day TEXT, pm25 REAL)")
    rows=[(f"Station{i%120}",f"2026-10-{i%28+1:02d}",float(i%150)) for i in range(120000)]
    con.executemany("INSERT INTO readings VALUES(?,?,?)",rows); con.commit()
    query=("SELECT AVG(pm25) FROM readings WHERE station=? AND day=?")
    params=("Station42","2026-10-15")
    t=time.perf_counter()
    for _ in range(200): con.execute(query,params).fetchone()
    before=(time.perf_counter()-t)/200
    con.execute("CREATE INDEX idx_station_day ON readings(station,day)"); con.commit()
    t=time.perf_counter()
    for _ in range(200): con.execute(query,params).fetchone()
    after=(time.perf_counter()-t)/200
    con.close()
    return before,after

if __name__=="__main__":
    # After independently reading the 50 complaints, enter one human label
    # (positive/negative/neutral) per complaint in this list.
    HUMAN_LABELS = []
    if len(HUMAN_LABELS) == len(COMPLAINTS):
        agreed=sum(label(c)==h for c,h in zip(COMPLAINTS,HUMAN_LABELS))
        print(f"Human agreement: {agreed}/{len(COMPLAINTS)} ({100*agreed/len(COMPLAINTS):.1f}%)")
    else:
        print(f"Human agreement not calculated: review {len(COMPLAINTS)} complaints and fill HUMAN_LABELS.")
    print("Example summary:",summarise(" ".join(COMPLAINTS[:4]),2))
    before,after=database_index_experiment()
    print(f"Average indexed-query test: before={before:.6f}s, after={after:.6f}s")
    print("Decision: retain SQLite with indexes; batch ingestion; validate and clean at input;")
    print("use lexicon as a transparent baseline and evaluate a trained classifier on labelled local complaints.")
