"""
Multi-endpoint Locust load test for GroundX serving.

The paper's concurrency benchmark (Table 3) tested one endpoint,
/api/documents/list. Reviewer 1 asked for coverage of retrieval, query
answering, embedding, and document-processing endpoints. This file adds a task
per endpoint so the serving path is exercised more representatively. The
document-list task mirrors the published benchmark so results stay comparable.

Each task carries the same spawn-all-at-start protocol used in the paper: run
with `--users N --spawn-rate N` so all users start together, against the same
configuration on cloud and on-premises.

Run:
  locust -f locustfile_multi.py --host http://<host>:<port> \
      --users 20 --spawn-rate 20 --run-time 3m --headless \
      --csv onprem_20u
  locust -f locustfile_multi.py --host http://<host>:<port> \
      --users 50 --spawn-rate 50 --run-time 3m --headless --csv onprem_50u

Locust writes per-endpoint statistics (median, 95th/99th percentile, RPS,
failures) to the CSV files, which become the raw logs deposited per the Data
Availability statement. Re-run each configuration several times to obtain the
run-to-run dispersion the reviewers requested.

TODO(author): confirm each endpoint path and payload against your GroundX API.
The list endpoint is known from the paper; the others are marked and should be
set to the real routes. Tasks whose route is unconfirmed are given a low weight
so an accidental 404 does not dominate the run; raise the weights once the
routes are set.
"""
from locust import HttpUser, task, between


class GroundXUser(HttpUser):
    # Small think time between requests; set to `constant(0)` to reproduce the
    # paper's back-to-back load exactly.
    wait_time = between(0.1, 0.5)

    @task(5)
    def list_documents(self):
        # Published benchmark endpoint (Table 3). Weighted highest for comparability.
        self.client.get("/api/documents/list", name="documents/list")

    @task(2)
    def retrieve(self):
        # TODO(author): set the retrieval route and query payload.
        self.client.post("/api/search", json={"query": "benchmark probe query", "top_k": 5},
                         name="search/retrieve")

    @task(2)
    def query_answer(self):
        # TODO(author): set the RAG query-answering route.
        self.client.post("/api/query", json={"question": "benchmark probe question"},
                         name="query/answer")

    @task(1)
    def embed(self):
        # TODO(author): set the embedding route and payload.
        self.client.post("/api/embeddings", json={"input": "benchmark probe text"},
                         name="embeddings")

    @task(1)
    def document_status(self):
        # TODO(author): set the document-processing status route; DOC_ID placeholder.
        self.client.get("/api/documents/DOC_ID/status", name="documents/status")
