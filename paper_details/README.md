# Paper artifacts

This section accompanies the paper "Rethinking Multimodal System Deployment: Cost-Effective On-Premises Framework for Predictable Non-Real-Time Applications, a GroundX Case Study" (Academia.edu Journals, AI and Applications, revised September 2026). Append it to the repository README or keep it as a separate file linked from the README.

## What the paper uses from this repository

The deployment configuration, the Minikube provisioning script (`environment/on-premise/setup-minikube`), and the autoscaling notes (`hpa_notes.md`, `autoscaling_notes.md`) are the archived configuration the paper reports. The paper was produced against GroundX On-Prem at commit 59148d0 (full hash 59148d04455f6ff4ce79d96d90bab45f12f8ce7c, committed June 19, 2025), and the environment was set up and benchmarked in June 2025. The full archived configuration, including tool versions, hardware, the two cloud baselines, and the network conditions of the benchmarks, is recorded in `doc/paper_configuration.md`.

## Layout of the added material

- `analysis/tco_model_v2.py` is the total-cost-of-ownership model behind Section 5.1, Tables 2 and 3, and Figures 3 and 4 of the paper. It prints every number quoted in the paper, writes them to `figures/tco_v2_summary.json`, and regenerates the two cost figures.
- `analysis/make_result_figs.py` regenerates the three benchmark figures (Figures 5, 6, and 7) from the values in `benchmarks/results/`.
- `figures/` holds the five data figures as they appear in the paper.
- `benchmarks/` holds the load test that produced Table 5 (`locustfile_list.py`, the `ListTester` class), the repeated-trial ingestion harness (`repeat_ingest.py`), the multimodal corpus manifest (`corpus_manifest.json`), and the multi-endpoint Locust file (`locustfile_multi.py`) that the paper's Table 6 names for the experiments it leaves to future work. `benchmarks/README.md` gives the protocol.
- `benchmarks/results/` holds the values behind Tables 4 and 5 and the raw logs behind them. See the README in that folder for what is expected there.

## Reproducing the figures

Run from the `analysis` directory with Python 3.10 or later, NumPy, and Matplotlib installed. The scripts write into `../figures/`.

```
cd analysis
python tco_model_v2.py
python make_result_figs.py
```

The model reads no external data. Every parameter, with its baseline and range, sits at the top of `tco_model_v2.py`, so a reader with different electricity prices, staffing, or cloud rates can change the values and rerun.
