"""B4.1: sentiment scorer + extractive summariser on 60 complaints; agreement with my labels."""
import csv, re, time
from collections import Counter

POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}
STOP = set("the is a an and of to in it i my we our are was were for on at this that they them he she with "
           "from by as be been me you your please thank thanks there here am do does did has have had will "
           "would can could so but or if when which where what who all any".split())

def score(text):                      # same code as complete_the_code.py
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0
    for i, w in enumerate(words):
        value = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if i > 0 and words[i - 1] in NEGATORS:
            value = -value
        total += value
    return total

def label(text):
    s = score(text)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"

def sentences(text):
    return [s for s in re.split(r"(?<=[.?!])\s+", text.strip()) if s]

def words_of(s):
    return [w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP]

def summarise(text, k=1):
    """Pick the k sentences with the largest sum of word frequencies (frequency counted inside the complaint)."""
    sents = sentences(text)
    freq = Counter(w for s in sents for w in words_of(s))
    scores = [sum(freq[w] for w in words_of(s)) for s in sents]
    top = sorted(range(len(sents)), key=lambda i: (-scores[i], i))[:k]
    return [sents[i] for i in sorted(top)], sorted(i + 1 for i in top)

def first_k(text, k=1):
    return sentences(text)[:k]

rows = list(csv.DictReader(open("complaints.csv", encoding="utf-8")))
print("=== Sentiment: scorer vs my labels ===")
wrong = []
for r in rows:
    got = label(r["complaint"])
    if got != r["my_label"]:
        wrong.append(r)
        print(f"id {r['id']:>2}: scorer={got:8} mine={r['my_label']:8} score={score(r['complaint']):+d} | {r['complaint']}")
agree = len(rows) - len(wrong)
print(f"\nAgreement: {agree}/{len(rows)} = {agree / len(rows):.1%}")
pred_wrong = {21, 22, 25, 26, 27, 28, 30, 39, 45, 53, 60}
actual_wrong = {int(r["id"]) for r in wrong}
print("Predicted wrong ids :", sorted(pred_wrong))
print("Actual wrong ids    :", sorted(actual_wrong))
print("Predicted but right :", sorted(pred_wrong - actual_wrong), "| Wrong but not predicted:", sorted(actual_wrong - pred_wrong))

print("\nConfusion (rows = my label, columns = scorer):")
cats = ["positive", "negative", "neutral"]
cm = Counter((r["my_label"], label(r["complaint"])) for r in rows)
print(f"{'':10}" + "".join(f"{c:>10}" for c in cats))
for a in cats:
    print(f"{a:10}" + "".join(f"{cm[(a, b)]:>10}" for b in cats))

print("\n=== Summariser: does k=1 pick the sentence I marked as the key one? ===")
hit_freq = hit_first = 0
for r in rows:
    _, idx = summarise(r["complaint"], 1)
    hit_freq += idx[0] == int(r["key_sentence"])
    hit_first += 1 == int(r["key_sentence"])
n = len(rows)
print(f"frequent-word summariser: {hit_freq}/{n} = {hit_freq / n:.1%}")
print(f"first-sentence baseline : {hit_first}/{n} = {hit_first / n:.1%}")
print("\nExamples (id, frequent-word pick, first-sentence pick, my key sentence):")
for r in rows[:6]:
    pick, idx = summarise(r["complaint"], 1)
    print(f"id {r['id']}: freq -> sentence {idx[0]}: {pick[0]!r}; first -> sentence 1; key -> {r['key_sentence']}")

print("\n=== Time per complaint (all 60 complaints, repeated 2000 times) ===")
texts = [r["complaint"] for r in rows]
t = time.perf_counter()
for _ in range(2000):
    for x in texts: label(x)
t_sent = (time.perf_counter() - t) / (2000 * len(texts))
t = time.perf_counter()
for _ in range(2000):
    for x in texts: summarise(x, 1)
t_sum = (time.perf_counter() - t) / (2000 * len(texts))
t = time.perf_counter()
for _ in range(2000):
    for x in texts: first_k(x, 1)
t_first = (time.perf_counter() - t) / (2000 * len(texts))
print(f"sentiment score + label: {t_sent * 1e6:.1f} microseconds per complaint")
print(f"frequent-word summary  : {t_sum * 1e6:.1f} microseconds per complaint")
print(f"first-k summary        : {t_first * 1e6:.1f} microseconds per complaint")
print(f"50,000 complaints a month, sentiment + summary: about {(t_sent + t_sum) * 50000:.1f} seconds in total")
