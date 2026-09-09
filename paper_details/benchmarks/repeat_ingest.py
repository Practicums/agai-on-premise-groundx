#!/usr/bin/env python3
"""
Repeated-trial ingestion benchmark for GroundX, cloud vs on-premises.

This harness produces the statistics the reviewers asked for and that the paper
now defers to future work: per-run latencies, mean, standard deviation, a 95%
confidence interval, and a Mann-Whitney U test comparing the cloud and
on-premises latency distributions per workload. It replaces the single
representative runs in Table 2 with a repeatable, dispersion-reporting protocol.

The statistics and orchestration are complete. The only deployment-specific
piece is `ingest_documents()`, which submits a batch of documents to a running
GroundX deployment and blocks until ingestion finishes. Wire it to the exact
GroundX ingest endpoint and completion signal for your deployment; the TODO
markers show where. Nothing else needs editing.

Usage:
  python repeat_ingest.py --base-url http://<host>:<port> --label cloud \
      --corpus ./corpus --reps 10 --warmup 2 --out cloud_ingest.csv
  python repeat_ingest.py --base-url http://localhost:<port> --label onprem \
      --corpus ./corpus --reps 10 --warmup 2 --out onprem_ingest.csv
  python repeat_ingest.py --compare cloud_ingest.csv onprem_ingest.csv

Protocol (matches Section 4.2 of the manuscript):
  - Warm-up runs are executed and discarded before timed runs begin.
  - Each workload (1, 2, 10 parallel documents) is timed `reps` times.
  - The deployment is left otherwise idle; no extra caching layer is added.
  - Wall-clock end-to-end latency is recorded per run.
"""
import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

# Workloads to time: (label, number_of_parallel_documents)
WORKLOADS = [("1 document", 1), ("2 documents", 2), ("10 documents", 10)]


def ingest_documents(base_url, doc_paths):
    """Submit `doc_paths` to GroundX for ingestion and block until all finish.

    TODO(author): replace the body with the real call for your deployment.
    Typical shape:
        1. POST each file to the GroundX ingest endpoint (e.g. /api/v1/ingest),
           capturing the returned process/ingest id.
        2. Poll the status endpoint until every id reports 'complete'.
    Keep the function synchronous: it must return only after ingestion is done,
    so the wall-clock timing around it measures end-to-end ingestion.
    Raise on any non-success status so failed runs are visible, not silently
    counted as fast.
    """
    raise NotImplementedError(
        "Wire ingest_documents() to your GroundX ingest + status endpoints. "
        "See the TODO in this function."
    )


def time_workload(base_url, doc_paths):
    t0 = time.perf_counter()
    ingest_documents(base_url, doc_paths)
    return time.perf_counter() - t0


def pick_docs(corpus_dir, n):
    docs = sorted(p for p in Path(corpus_dir).iterdir() if p.is_file())
    if not docs:
        sys.exit(f"No documents found in {corpus_dir}")
    # Reuse the corpus cyclically so n can exceed the corpus size, matching the
    # paper's reused-corpus protocol. Swap in distinct documents to test a
    # varied corpus (see corpus_manifest.json).
    return [docs[i % len(docs)] for i in range(n)]


def run(args):
    warm = pick_docs(args.corpus, 1)
    for _ in range(args.warmup):
        try:
            time_workload(args.base_url, warm)
        except NotImplementedError:
            sys.exit("ingest_documents() is not wired up yet; see the TODO.")
    rows = []
    for name, n in WORKLOADS:
        docs = pick_docs(args.corpus, n)
        for rep in range(args.reps):
            latency = time_workload(args.base_url, docs)
            rows.append({"label": args.label, "workload": name,
                         "n_docs": n, "rep": rep, "latency_s": round(latency, 3)})
            print(f"{args.label} | {name} | rep {rep+1}/{args.reps} | {latency:.2f}s")
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nWrote {len(rows)} timed runs to {args.out}")
    _summ(rows)


def _ci95(xs):
    """95% confidence interval half-width for a small sample (t-approx)."""
    if len(xs) < 2:
        return 0.0
    sd = statistics.stdev(xs)
    # t critical for common small n; falls back to 1.96 for larger n.
    tcrit = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45,
             8: 2.36, 9: 2.31, 10: 2.26}.get(len(xs), 1.96)
    return tcrit * sd / (len(xs) ** 0.5)


def _summ(rows):
    print("\nworkload            mean(s)   sd(s)   95% CI half-width   n")
    by = {}
    for r in rows:
        by.setdefault(r["workload"], []).append(r["latency_s"])
    for name, xs in by.items():
        m = statistics.mean(xs)
        sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
        print(f"{name:<18} {m:>8.2f} {sd:>7.2f} {_ci95(xs):>17.2f} {len(xs):>4}")


def _mannwhitney_u(a, b):
    """Two-sided Mann-Whitney U with a normal approximation (no SciPy needed).
    Returns (U, z, approx_p). Use SciPy for exact small-sample p-values."""
    import math
    n1, n2 = len(a), len(b)
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    # rank with ties averaged
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j+1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r1 = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sigma if sigma else 0.0
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return u, z, p


def compare(f_cloud, f_onprem):
    def load(f):
        by = {}
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                by.setdefault(r["workload"], []).append(float(r["latency_s"]))
        return by
    c, o = load(f_cloud), load(f_onprem)
    print("workload            cloud mean   onprem mean   U      z      p(approx)   significant(0.05)")
    for name in [w[0] for w in WORKLOADS]:
        if name in c and name in o:
            u, z, p = _mannwhitney_u(c[name], o[name])
            sig = "yes" if p < 0.05 else "no"
            print(f"{name:<18} {statistics.mean(c[name]):>10.2f} {statistics.mean(o[name]):>13.2f}"
                  f" {u:>6.1f} {z:>6.2f} {p:>11.4f}   {sig}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url"); ap.add_argument("--label", default="run")
    ap.add_argument("--corpus", default="./corpus")
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--out", default="ingest_results.csv")
    ap.add_argument("--compare", nargs=2, metavar=("CLOUD_CSV", "ONPREM_CSV"))
    args = ap.parse_args()
    if args.compare:
        compare(*args.compare)
    elif args.base_url:
        run(args)
    else:
        ap.error("provide --base-url to run a benchmark, or --compare two CSVs")


if __name__ == "__main__":
    main()
