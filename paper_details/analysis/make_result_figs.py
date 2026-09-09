#!/usr/bin/env python3
"""Regenerate the three benchmark figures (ingestion latency, concurrency
averages and throughput, concurrency spread) with one palette and one font, so
cloud is always vermillion and on-premises is always blue, matching the TCO
figures. Data are the manuscript's Tables 3 and 4 (renumbered in this revision)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

plt.rcParams["font.family"] = "Georgia"
plt.rcParams["font.size"] = 10
C_CLOUD = "#D55E00"
C_ONPREM = "#0072B2"

# ---- Figure 5: batch ingestion latency -----------------------------------
scen = ["1 document", "2 documents\n(parallel)", "10 documents\n(parallel)"]
cloud = [33, 34, 38]
onprem = [44, 52, 261]
x = np.arange(len(scen)); w = 0.36
fig, ax = plt.subplots(figsize=(6.4, 4.1))
b1 = ax.bar(x - w / 2, cloud, w, color=C_CLOUD, label="Cloud")
b2 = ax.bar(x + w / 2, onprem, w, color=C_ONPREM, label="On-premises")
for bars in (b1, b2):
    for b in bars:
        ax.annotate(f"{b.get_height():.0f} s", (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", fontsize=10.5)
ax.set_xticks(x); ax.set_xticklabels(scen)
ax.set_ylabel("End-to-end response time (s)"); ax.set_ylim(0, 290)
ax.legend(frameon=False, loc="upper left"); ax.grid(axis="y", alpha=0.25); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("../figures/fig_ingest_latency.png", dpi=300); plt.close(fig)

# ---- Figure 6: concurrency averages and throughput -----------------------
users = ["20 users", "50 users"]
avg_cloud = [583.87, 1905.84]; avg_on = [501.85, 1695.85]
rps_cloud = [35.2, 26.6]; rps_on = [41.2, 29.9]
x = np.arange(2); w = 0.36
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.75))
for ax, c, o, ylab, title, fmt in [(a1, avg_cloud, avg_on, "Average response time (ms)", "Average response time", "{:.0f}"),
                                   (a2, rps_cloud, rps_on, "Throughput (requests/s)", "Throughput", "{:.1f}")]:
    b1 = ax.bar(x - w / 2, c, w, color=C_CLOUD, label="Cloud")
    b2 = ax.bar(x + w / 2, o, w, color=C_ONPREM, label="On-premises")
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(fmt.format(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=10.5)
    ax.set_xticks(x); ax.set_xticklabels(users); ax.set_ylabel(ylab); ax.set_title(title, fontsize=10)
    ax.grid(axis="y", alpha=0.25); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
a1.set_ylim(0, 2200); a2.set_ylim(0, 48)
a1.legend(frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig("../figures/fig_concurrency_avg_rps.png", dpi=300); plt.close(fig)

# ---- Figure 7: concurrency spread ----------------------------------------
data = [("Cloud", C_CLOUD, 0.85, 570, 1100, 583.87), ("On-premises", C_ONPREM, 1.35, 480, 850, 501.85),
        ("Cloud", C_CLOUD, 2.75, 1900, 3800, 1905.84), ("On-premises", C_ONPREM, 3.25, 1700, 3400, 1695.85)]
fig, ax = plt.subplots(figsize=(7.2, 4.5)); cap = 0.10
for dep, c, xx, med, p99, avg in data:
    ax.plot([xx, xx], [med, p99], color=c, lw=8, alpha=0.22, solid_capstyle="round", zorder=1)
    ax.plot([xx - cap, xx + cap], [med, med], color=c, lw=2.6, zorder=3)
    ax.plot([xx - cap, xx + cap], [p99, p99], color=c, lw=2.6, zorder=3)
    ax.plot(xx, avg, marker="o", color=c, ms=7.5, mfc="white", mew=1.8, zorder=4)
    side = -1 if dep == "Cloud" else 1; ha = "right" if side < 0 else "left"
    ax.annotate(f"p99 {p99:,}", (xx, p99), xytext=(side * 13, 0), textcoords="offset points", ha=ha, va="center", fontsize=9, color=c, fontweight="bold")
    ax.annotate(f"median {med:,}", (xx, med), xytext=(side * 13, 2), textcoords="offset points", ha=ha, va="bottom", fontsize=9, color=c)
ax.set_xticks([1.10, 3.00]); ax.set_xticklabels(["20 concurrent users", "50 concurrent users"], fontsize=10.5)
ax.set_ylabel("Response time (ms)", fontsize=11); ax.set_ylim(0, 4200); ax.set_xlim(0.35, 3.75)
ax.grid(axis="y", alpha=0.25); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
key = [Line2D([0], [0], color="#555", lw=8, alpha=0.22, label="median-to-p99 range"),
       Line2D([0], [0], color="#555", lw=2.6, label="median and 99th percentile"),
       Line2D([0], [0], marker="o", color="#555", mfc="white", mew=1.8, ls="", label="average"),
       Line2D([0], [0], color=C_CLOUD, lw=3, label="Cloud"),
       Line2D([0], [0], color=C_ONPREM, lw=3, label="On-premises")]
ax.legend(handles=key, fontsize=9.5, frameon=False, loc="upper left", ncol=2)
fig.tight_layout(); fig.savefig("../figures/fig_concurrency_spread.png", dpi=300); plt.close(fig)
print("written: fig_ingest_latency.png, fig_concurrency_avg_rps.png, fig_concurrency_spread.png")
