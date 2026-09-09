# Cost model and figure scripts

`tco_model_v2.py` is an analytical model rather than a measurement. It compares the monthly cost of the AWS footprint that GroundX recommends, priced with the saved AWS Pricing Calculator estimate cited in the paper (2,576.89 USD per month at on-demand rates in US East, Ohio, for one m6a.xlarge, four t3a.medium, one g4dn.xlarge, one g4dn.2xlarge, one g6e.xlarge, and 300 GB of gp2 storage), against a one-time 9,600 USD workstation purchase plus modeled recurring costs.

The recurring on-premises terms are electricity and cooling (average system power times a PUE factor times hours times price), administration, networking with backup and security monitoring, maintenance and support beyond the bundled warranty, and physical space with power protection. Each carries a baseline and a low-to-high range. Useful life and residual value enter only the amortized view, because the purchase is already counted at month zero in the break-even calculation, and counting it again as depreciation would double count.

The script reports the baseline break-even, a scenario table, a one-at-a-time sensitivity, and a Monte Carlo over the parameter ranges with each parameter drawn from a triangular distribution over its low, baseline, and high values (100,000 draws, fixed seed 20260908). It writes `../figures/fig_tco_cumulative.png`, `../figures/fig_tco_tornado.png`, and `../figures/tco_v2_summary.json`.

`make_result_figs.py` redraws the ingestion-latency figure, the concurrency average and throughput figure, and the concurrency spread figure from the values in `../benchmarks/results/`, using one palette (cloud in vermillion, on-premises in blue) and one typeface so the figures match the cost figures.

Both scripts need Python 3.10 or later with NumPy and Matplotlib and are run from this directory.
