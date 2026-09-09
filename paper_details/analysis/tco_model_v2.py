#!/usr/bin/env python3
"""
Total-cost-of-ownership (TCO) and break-even model, second revision.

Extends Revision/analysis/tco_model.py with the categories Reviewer 1 asked for
(maintenance, hardware replacement risk, useful life and depreciation, residual
value, physical infrastructure) and the scenario and probability view Reviewer 3
asked for (a scenario table plus a Monte Carlo over the parameter ranges).

Every parameter carries a stated baseline and a low/high range. Break-even is
reported as a baseline, a scenario table, and a sampled distribution, never as a
single point. All monetary values are USD.

Break-even convention: hardware capex is paid at month 0 and the cloud bill is
paid monthly, so break-even is the month at which cumulative cloud spend equals
capex plus cumulative on-premises recurring spend. The refresh reserve is NOT
added to the recurring line during the first useful-life cycle, because that
would count the same hardware twice (capex up front and again as depreciation).
Useful life and residual value instead enter (a) the amortized monthly-equivalent
cost of ownership and (b) the multi-year cumulative comparison, where the
replacement purchase is booked at the end of the useful life.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Georgia"
plt.rcParams["font.size"] = 8.5

# Okabe-Ito, same assignment as every other data figure in the manuscript
C_CLOUD = "#D55E00"      # cloud = vermillion
C_ONPREM = "#0072B2"     # on-premises = blue
C_ONPREM0 = "#56B4E9"    # on-premises compute-only = sky blue
C_ACCENT = "#009E73"     # green

CLOUD_MONTHLY = 2576.89  # AWS Pricing Calculator estimate a5cfe90e (US East Ohio, on-demand): 1x m6a.xlarge, 4x t3a.medium, 1x g4dn.xlarge, 1x g4dn.2xlarge, 1x g6e.xlarge, 300 GB gp2
HW_CAPEX = 9600.0        # one-time on-premises hardware cost

PARAMS = {
    "system_power_kW":     dict(base=0.50,  low=0.30, high=0.80,  unit="kW",    label="Avg system power"),
    "PUE":                 dict(base=1.30,  low=1.10, high=1.60,  unit="x",     label="PUE (cooling overhead)"),
    "electricity_per_kWh": dict(base=0.13,  low=0.08, high=0.25,  unit="$/kWh", label="Electricity price"),
    "admin_monthly":       dict(base=150.0, low=0.0,  high=500.0, unit="$/mo",  label="Admin overhead"),
    "other_monthly":       dict(base=50.0,  low=0.0,  high=150.0, unit="$/mo",  label="Network/backup/security"),
    # New in this revision
    "maintenance_monthly": dict(base=25.0,  low=0.0,  high=100.0, unit="$/mo",  label="Maintenance/support"),
    "physical_monthly":    dict(base=25.0,  low=0.0,  high=100.0, unit="$/mo",  label="Space/power protection"),
}
# Life-cycle parameters (do not enter the first-cycle break-even; see docstring)
USEFUL_LIFE_MONTHS = dict(base=60, low=36, high=72)      # 5 years baseline, 3 to 6 years
RESIDUAL_FRACTION = dict(base=0.10, low=0.00, high=0.25)  # fraction of capex recovered at end of life

HOURS_PER_MONTH = 24 * 30  # 720


def power_cost_monthly(kw, pue, price):
    return kw * pue * HOURS_PER_MONTH * price


def recurring_monthly(p):
    return (power_cost_monthly(p["system_power_kW"], p["PUE"], p["electricity_per_kWh"])
            + p["admin_monthly"] + p["other_monthly"]
            + p["maintenance_monthly"] + p["physical_monthly"])


def breakeven_months(recurring, capex=HW_CAPEX):
    denom = CLOUD_MONTHLY - recurring
    return np.inf if denom <= 0 else capex / denom


def base_params():
    return {k: v["base"] for k, v in PARAMS.items()}


def amortized_monthly(life_months, residual_fraction):
    """Monthly-equivalent depreciation charge for the hardware."""
    return HW_CAPEX * (1.0 - residual_fraction) / life_months


def cumulative_onprem(months, rec, life_months, residual_fraction):
    """Cumulative on-prem cost with a replacement purchase at the end of each useful life,
    net of residual value recovered on the retired unit."""
    out = HW_CAPEX + rec * months
    n_replacements = np.floor(months / life_months)
    out = out + n_replacements * (HW_CAPEX - HW_CAPEX * residual_fraction)
    return out


def main():
    rng = np.random.default_rng(20260908)
    base = base_params()
    rec_base = recurring_monthly(base)
    be_base = breakeven_months(rec_base)
    be_compute_only = HW_CAPEX / CLOUD_MONTHLY
    power_base = power_cost_monthly(base["system_power_kW"], base["PUE"], base["electricity_per_kWh"])

    low = {k: v["low"] for k, v in PARAMS.items()}
    high = {k: v["high"] for k, v in PARAMS.items()}
    rec_low, rec_high = recurring_monthly(low), recurring_monthly(high)
    be_low, be_high = breakeven_months(rec_low), breakeven_months(rec_high)

    # ---- scenario table ------------------------------------------------------
    scenarios = []
    scenarios.append(("Compute only (original comparison)", 0.0, be_compute_only, None))
    scenarios.append(("All parameters favorable", rec_low, be_low, None))
    scenarios.append(("Baseline", rec_base, be_base, None))
    heavy = base_params(); heavy["admin_monthly"] = 500.0
    scenarios.append(("Baseline with heavy administration (500 USD/mo)", recurring_monthly(heavy), breakeven_months(recurring_monthly(heavy)), None))
    exp = base_params(); exp["electricity_per_kWh"] = 0.25
    scenarios.append(("Baseline with expensive electricity (0.25 USD/kWh)", recurring_monthly(exp), breakeven_months(recurring_monthly(exp)), None))
    scenarios.append(("All parameters adverse", rec_high, be_high, None))
    # early hardware failure outside warranty: second purchase at month 36, baseline recurring
    be_fail = breakeven_months(rec_base, capex=2 * HW_CAPEX)
    scenarios.append(("Baseline plus one full hardware replacement (failure risk)", rec_base, be_fail, None))

    # ---- one-at-a-time sensitivity (tornado) --------------------------------
    labels, lo_be, hi_be, swings = [], [], [], []
    for k, v in PARAMS.items():
        p_lo = base_params(); p_lo[k] = v["low"]
        p_hi = base_params(); p_hi[k] = v["high"]
        l, h = breakeven_months(recurring_monthly(p_lo)), breakeven_months(recurring_monthly(p_hi))
        labels.append(f"{v['label']}\n({v['low']:g} to {v['high']:g} {v['unit']})")
        lo_be.append(l); hi_be.append(h); swings.append(abs(h - l))
    order = np.argsort(swings)

    # ---- Monte Carlo over triangular distributions --------------------------
    N = 100_000
    samples = {}
    for k, v in PARAMS.items():
        samples[k] = rng.triangular(v["low"], v["base"], v["high"], N)
    rec_mc = (samples["system_power_kW"] * samples["PUE"] * HOURS_PER_MONTH * samples["electricity_per_kWh"]
              + samples["admin_monthly"] + samples["other_monthly"]
              + samples["maintenance_monthly"] + samples["physical_monthly"])
    be_mc = HW_CAPEX / (CLOUD_MONTHLY - rec_mc)
    q = np.percentile(be_mc, [5, 10, 25, 50, 75, 90, 95])
    p12 = float(np.mean(be_mc <= 5)); p18 = float(np.mean(be_mc <= 6)); p24 = float(np.mean(be_mc <= 7))

    # ---- life-cycle view ------------------------------------------------------
    amort_base = amortized_monthly(USEFUL_LIFE_MONTHS["base"], RESIDUAL_FRACTION["base"])
    amort_worst = amortized_monthly(USEFUL_LIFE_MONTHS["low"], RESIDUAL_FRACTION["low"])
    amort_best = amortized_monthly(USEFUL_LIFE_MONTHS["high"], RESIDUAL_FRACTION["high"])
    monthly_equiv_base = amort_base + rec_base
    monthly_equiv_worst = amort_worst + rec_high
    monthly_equiv_best = amort_best + rec_low
    m36 = 36; m60 = 60
    cloud36, cloud60 = CLOUD_MONTHLY * m36, CLOUD_MONTHLY * m60
    onp36 = float(cumulative_onprem(m36, rec_base, USEFUL_LIFE_MONTHS["base"], RESIDUAL_FRACTION["base"]))
    onp60 = float(cumulative_onprem(m60, rec_base, USEFUL_LIFE_MONTHS["base"], RESIDUAL_FRACTION["base"]))
    onp36_adv = float(cumulative_onprem(m36, rec_high, USEFUL_LIFE_MONTHS["low"], RESIDUAL_FRACTION["low"]))
    onp60_adv = float(cumulative_onprem(m60, rec_high, USEFUL_LIFE_MONTHS["low"], RESIDUAL_FRACTION["low"]))

    summary = dict(
        power_base=round(power_base, 2), rec_base=round(rec_base, 2), be_base=round(be_base, 2),
        be_compute_only=round(be_compute_only, 2), rec_low=round(rec_low, 2), rec_high=round(rec_high, 2),
        be_low=round(be_low, 2), be_high=round(be_high, 2),
        scenarios=[(n, round(r, 1), round(b, 1)) for n, r, b, _ in scenarios],
        tornado=[(labels[i].replace("\n", " "), round(lo_be[i], 2), round(hi_be[i], 2), round(swings[i], 2)) for i in order[::-1]],
        mc_percentiles=dict(zip(["p5", "p10", "p25", "p50", "p75", "p90", "p95"], [round(float(x), 2) for x in q])),
        mc_p_le_5=round(p12, 4), mc_p_le_6=round(p18, 4), mc_p_le_7=round(p24, 4), mc_mean=round(float(be_mc.mean()), 2),
        amortized=dict(base=round(amort_base, 2), worst=round(amort_worst, 2), best=round(amort_best, 2)),
        monthly_equiv=dict(base=round(monthly_equiv_base, 2), worst=round(monthly_equiv_worst, 2), best=round(monthly_equiv_best, 2)),
        cumulative=dict(cloud36=cloud36, cloud60=cloud60, onp36=onp36, onp60=onp60, onp36_adv=onp36_adv, onp60_adv=onp60_adv),
    )
    print(json.dumps(summary, indent=1))
    with open("../figures/tco_v2_summary.json", "w") as f:
        json.dump(summary, f, indent=1)

    # ---- Figure 3: cumulative cost curves -----------------------------------
    months = np.arange(0, 37)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(months, CLOUD_MONTHLY * months / 1000, color=C_CLOUD, lw=2.2, label="Cloud (recurring)")
    ax.plot(months, (HW_CAPEX + 0 * months) / 1000, color=C_ONPREM0, lw=1.8, ls="--", label="On-premises, compute only")
    ax.plot(months, (HW_CAPEX + rec_base * months) / 1000, color=C_ONPREM, lw=2.2, label="On-premises, full TCO (baseline)")
    ax.plot(months, (HW_CAPEX + rec_high * months) / 1000, color=C_ONPREM, lw=1.4, ls=":", label="On-premises, full TCO (all adverse)")
    for be, c in [(be_compute_only, C_ONPREM0), (be_base, C_ONPREM)]:
        ax.axvline(be, color=c, lw=0.8, alpha=0.6)
    ax.annotate(f"{be_compute_only:.1f} mo", (be_compute_only, 30.0), color=C_ONPREM0, fontsize=8, ha="right", xytext=(-3, 0), textcoords="offset points")
    ax.annotate(f"{be_base:.1f} mo", (be_base, 42.0), color=C_ONPREM, fontsize=8, ha="left", xytext=(3, 0), textcoords="offset points")
    ax.set_xlabel("Months of operation"); ax.set_ylabel("Cumulative cost (thousand USD)")
    ax.set_xlim(0, 36); ax.set_ylim(0, 100)
    ax.legend(fontsize=8, loc="center left", bbox_to_anchor=(0.16, 0.72), frameon=False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig("../figures/fig_tco_cumulative.png", dpi=300); plt.close(fig)

    # ---- Figure 4: two panels, tornado (a) and Monte Carlo CDF (b) ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.4), gridspec_kw=dict(width_ratios=[1.3, 1.0]))
    y = np.arange(len(labels))
    for j, i in enumerate(order):
        left, right = sorted([lo_be[i], hi_be[i]])
        ax1.barh(y[j], right - left, left=left, color=C_ONPREM, alpha=0.75, height=0.55)
    ax1.axvline(be_base, color=C_ACCENT, lw=1.6, label=f"Baseline {be_base:.1f} mo")
    ax1.set_yticks(y); ax1.set_yticklabels([labels[i] for i in order], fontsize=8)
    ax1.set_xlabel("Break-even (months)"); ax1.legend(fontsize=8, frameon=False, loc="lower right")
    ax1.grid(axis="x", alpha=0.25); ax1.set_title("(a) One-at-a-time sensitivity", fontsize=9.5)

    xs = np.sort(be_mc); cdf = np.arange(1, N + 1) / N
    ax2.plot(xs, cdf, color=C_ONPREM, lw=2.0)
    for m, ls in [(5, "--"), (6, ":"), (7, "-.")]:
        pm = float(np.mean(be_mc <= m))
        ax2.axvline(m, color="#666666", lw=0.8, ls=ls)
        ax2.annotate(f"P(≤{m} mo) = {pm:.2f}", (m, 0.06 + 0.12 * ([5, 6, 7].index(m))), fontsize=8, color="#333333", ha="left", xytext=(3, 0), textcoords="offset points")
    ax2.axvline(q[3], color=C_ACCENT, lw=1.2); ax2.annotate(f"median {q[3]:.1f} mo", (q[3], 0.52), fontsize=8, color=C_ACCENT, xytext=(3, 0), textcoords="offset points")
    ax2.set_xlim(3, 8); ax2.set_ylim(0, 1)
    ax2.set_xlabel("Break-even (months)"); ax2.set_ylabel("Cumulative probability")
    ax2.grid(alpha=0.25); ax2.set_title("(b) Monte Carlo over parameter ranges", fontsize=9.5)
    fig.tight_layout(); fig.savefig("../figures/fig_tco_tornado.png", dpi=300); plt.close(fig)
    print("figures written: fig_tco_cumulative.png, fig_tco_tornado.png")


if __name__ == "__main__":
    main()
