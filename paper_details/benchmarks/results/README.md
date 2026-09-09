# Benchmark results

`table4_ingestion_latency.csv` holds the end-to-end ingestion times of Table 4 in the paper, in seconds, for one, two, and ten parallel submissions of the same single-page PDF, on the hosted cloud service and on the on-premises deployment. Each value is a single representative run taken after the cluster reached a steady state.

`table5_concurrency.csv` holds the Locust statistics of Table 5, one row per load session, for the document-list endpoint at 20 and 50 concurrent users. Locust drove the project's Django backend on the workstation, which forwarded each call to GroundX, at the Minikube tunnel address for the on-premises runs and at the hosted service's default endpoint for the cloud runs. Users were all spawned at the start of each session and sent requests with no think time between them.

`locust_summary_screens.pdf` is the Locust statistics view captured at the end of each session, which is the source of the Table 5 values.

## What was retained

The per-request Locust exports of the four load sessions were not retained, so the two CSV files and the captured statistics views above are the record of the benchmarks, and the paper's Data Availability statement says so. If the timing records of the six ingestion runs (submission and completion timestamps) are still held, add them here as a CSV.
