# Benchmark suite for the on-premises GroundX study

This directory holds the harness that turns the paper's single representative runs into a repeatable, dispersion-reporting benchmark. It exists so that the repeated trials, statistical tests, varied corpus, and additional endpoints that the paper lists as future work can be run without redesigning the protocol. Running these scripts against a live cloud and on-premises deployment yields the mean, standard deviation, confidence intervals, Mann-Whitney U test, varied-corpus results, and multi-endpoint results that the manuscript now identifies as the natural next study.

## Contents

- `repeat_ingest.py` runs the batch-ingestion benchmark many times per workload and reports the statistics. The orchestration and statistics are complete. One function, `ingest_documents()`, submits a batch to GroundX and blocks until ingestion finishes, and it carries a clear TODO so it can be wired to the real ingest and status endpoints.
- `locustfile_multi.py` extends the concurrency benchmark from one endpoint to five, covering document listing, retrieval, query answering, embedding, and document processing. The listing task matches the published benchmark so results stay comparable. The other routes are marked for confirmation against the running API.
- `corpus_manifest.json` specifies a small documented corpus that spans page counts and modalities, so ingestion can be tested on text-heavy, image-heavy, scanned, tabular, and mixed inputs instead of one reused single-page PDF.

## Protocol

The protocol matches Section 4.2 of the manuscript so the new runs are directly comparable to the reported ones.

1. Warm-up. Run two warm-up ingestions and discard them before timing, so first-request warm-up does not dominate.
2. Repetitions. Time each workload at least ten times. More repetitions tighten the confidence interval.
3. Isolation. Leave the deployment otherwise idle during a run, and add no caching layer beyond GroundX's defaults.
4. Symmetry. Apply the identical configuration to the cloud and on-premises deployments.
5. Recording. Keep the per-run CSV files. They are the raw logs the Data Availability statement commits to deposit.

## Running the ingestion benchmark

Populate `./corpus/` with real documents named as in `corpus_manifest.json`, wire `ingest_documents()` to your GroundX endpoints, then run one pass per deployment.

```
python repeat_ingest.py --base-url http://<cloud-host>:<port>  --label cloud  --corpus ./corpus --reps 10 --warmup 2 --out cloud_ingest.csv
python repeat_ingest.py --base-url http://<onprem-host>:<port> --label onprem --corpus ./corpus --reps 10 --warmup 2 --out onprem_ingest.csv
python repeat_ingest.py --compare cloud_ingest.csv onprem_ingest.csv
```

The first two commands write per-run latencies and print the mean, standard deviation, and 95 percent confidence interval per workload. The third prints the Mann-Whitney U statistic and an approximate p-value comparing the two deployments per workload. For an exact small-sample p-value, feed the same CSV columns to `scipy.stats.mannwhitneyu`.

## Running the concurrency benchmark

```
locust -f locustfile_multi.py --host http://<host>:<port> --users 20 --spawn-rate 20 --run-time 3m --headless --csv <label>_20u
locust -f locustfile_multi.py --host http://<host>:<port> --users 50 --spawn-rate 50 --run-time 3m --headless --csv <label>_50u
```

Locust writes per-endpoint statistics to the CSV files. Re-run each configuration several times to get the run-to-run dispersion, then plot the distributions or add error bars to the concurrency figure.

## What is real and what is a template

The statistics, the orchestration, the protocol, and the corpus specification are complete and tested. The deployment-specific pieces, the exact ingest and status endpoints and the four unconfirmed serving routes, are marked with TODO because they depend on the running GroundX API, and guessing them would produce a script that silently fails rather than one that runs. The manuscript does not report any number these scripts have not yet produced.
