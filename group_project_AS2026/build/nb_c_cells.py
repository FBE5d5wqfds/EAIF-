# Cells for task (c), inserted after the task (b) cells.
CELLS = []
def md(s): CELLS.append(("markdown", s.strip("\n")))
def code(s): CELLS.append(("code", s.strip("\n")))

md(r'''
## Task (c): where does ESG pay?

**Design.** For every firm and formation year we relate the **previous fiscal year's Environmental score** (standardised within each fiscal year across all firms: mean 0, standard deviation 1) to the **next twelve months' excess return** (total return minus the risk-free rate, July to June, percent). The coefficient is the change in 12-month excess return, in percentage points, for a firm that is one standard deviation higher on the Environmental score than its same-industry peers of that year.

*Sample.* Formation years 2013 to 2024, firms with a full twelve holding months. The Environmental score needs no past-return history, so the sample starts two years earlier than the model panel of tasks (b) and (d). Formation year 2025 has only six months of returns and is left out.

*Estimation.* One regression per region and period (before 2021 and from 2021, defined by formation year), with **industry-by-formation-year fixed effects** (every firm is compared with firms of the same industry in the same year) and standard errors **clustered by company** (one firm's years are not independent evidence). With 14 region-period cells, one "significant" cell can appear by chance, so we also report **Holm-adjusted** p-values across the 14 cells. We repeat everything with the restated scores.
''')

code(r'''
# ---- (c) Step 1: estimation sample ----
assert "panel_c" in globals() and "returns_c" in globals(), "Run the cells above first (Runtime > Run all)."
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

def z_within_year(values, years):
    # standardise within each fiscal year across all firms with a row that year
    g = values.groupby(years)
    return (values - g.transform("mean")) / g.transform("std")

sc = panel_c[["Company_ID", "Year", "Region", "Industry", "Environmental_Score"]].merge(
    restated[["Company_ID", "Year", "Environmental_Score"]].rename(columns={"Environmental_Score": "Env_restated"}), on=["Company_ID", "Year"])
sc["z_pit"] = z_within_year(sc["Environmental_Score"], sc["Year"])      # point-in-time score, as first published
sc["z_rest"] = z_within_year(sc["Env_restated"], sc["Year"])            # restated score, as a download today shows it

# next 12-month excess return: fiscal year Y -> formation July Y+1 -> held to June Y+2 (full 12 months only)
tgt = pd.concat([holding_returns(returns_c, factors, f).assign(Year=f - 1) for f in range(2013, 2025)])
tgt = tgt[tgt["Months"] == 12][["Company_ID", "Year", "Hold_Excess_Pct"]]
est = sc.merge(tgt, on=["Company_ID", "Year"]).assign(Formation_Year=lambda d: d["Year"] + 1)
est["Period"] = np.where(est["Formation_Year"] < 2021, "before 2021", "from 2021")
est["ind_year"] = est["Industry"] + "_" + est["Formation_Year"].astype(str)
REGIONS = sorted(est["Region"].unique()); PERIODS = ["before 2021", "from 2021"]

print(f"Estimation sample: {len(est):,} firm-years, {est['Company_ID'].nunique():,} firms, formation years {est['Formation_Year'].min()} to {est['Formation_Year'].max()}")
print("Firm-years by region and period:")
print(est.pivot_table(index="Region", columns="Period", values="Company_ID", aggfunc="size")[PERIODS].to_string())
print(f"Mean standardised score: point-in-time {est['z_pit'].mean():.3f}, restated {est['z_rest'].mean():.3f}; mean 12-month excess return {est['Hold_Excess_Pct'].mean():.2f}%")
''')

code(r'''
# ---- (c) Step 2: one regression per region and period, point-in-time and restated scores ----
assert "est" in globals(), "Run the cells above first (Runtime > Run all)."

def one_cell(d, zcol):
    # excess return on the standardised score, with industry-by-year fixed effects, standard errors clustered by company
    m = smf.ols(f"Hold_Excess_Pct ~ {zcol} + C(ind_year)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["Company_ID"])[0]})
    lo, hi = m.conf_int().loc[zcol]
    return dict(coef=m.params[zcol], se=m.bse[zcol], p=m.pvalues[zcol], lo=lo, hi=hi, n=int(m.nobs), firms=int(d["Company_ID"].nunique()))

rows = []
for version, zcol in [("point-in-time", "z_pit"), ("restated", "z_rest")]:
    for period in PERIODS:
        for region in REGIONS + ["All regions"]:
            d = est[(est["Period"] == period) & ((est["Region"] == region) | (region == "All regions"))]
            rows.append(dict(version=version, region=region, period=period, **one_cell(d, zcol)))
est_table = pd.DataFrame(rows)

# Holm adjustment across the 14 region-period cells, separately for each version (the 'All regions' rows are reference only)
est_table["p_holm"] = np.nan
for version in ["point-in-time", "restated"]:
    mask = (est_table["version"] == version) & (est_table["region"] != "All regions")
    est_table.loc[mask, "p_holm"] = multipletests(est_table.loc[mask, "p"], method="holm")[1]

def fmt(r):
    star = " **" if r["p_holm"] < 0.05 else (" *" if r["p"] < 0.05 else "")
    return f"{r['coef']:+.2f} ({r['se']:.2f}){star}"
wide = {}
for version in ["point-in-time", "restated"]:
    t = est_table[est_table["version"] == version].copy()
    t["cell"] = t.apply(fmt, axis=1)
    wide[version] = t.pivot(index="region", columns="period", values="cell")[PERIODS]
summary_c = pd.concat(wide, axis=1).reindex(REGIONS + ["All regions"])
summary_c.columns = [f"{v}, {p}" for v, p in summary_c.columns]
print("Coefficient in percentage points of 12-month excess return per 1 standard deviation of the Environmental score (standard error in brackets).")
print("* = p < 0.05 for that cell;  ** = still p < 0.05 after the Holm correction across the 14 region-period cells.\n")
display(summary_c)

det = est_table[(est_table["region"] != "All regions")].copy()
print("\nDetail for the point-in-time scores (95% interval, p-values; n = firm-years):")
display(det[det["version"] == "point-in-time"][["region", "period", "coef", "se", "lo", "hi", "p", "p_holm", "n", "firms"]].round(3).reset_index(drop=True))
''')

code(r'''
# ---- (c) Step 3: figure ----
assert "est_table" in globals(), "Run the cells above first (Runtime > Run all)."
fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharex=True, sharey=True)
ypos = np.arange(len(REGIONS))[::-1]
for ax, period in zip(axes, PERIODS):
    for k, (version, colour) in enumerate([("point-in-time", "steelblue"), ("restated", "darkorange")]):
        t = est_table[(est_table["version"] == version) & (est_table["period"] == period)].set_index("region").reindex(REGIONS)
        off = (-0.15 if k == 0 else 0.15)
        ax.errorbar(t["coef"], ypos + off, xerr=[t["coef"] - t["lo"], t["hi"] - t["coef"]], fmt="o", color=colour, capsize=3, label=version)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(ypos); ax.set_yticklabels(REGIONS)
    ax.set_title(f"Formation years {period}")
    ax.set_xlabel("Percentage points of 12-month excess return per 1 standard deviation of the Environmental score\n(95% interval, standard errors clustered by company)")
axes[0].set_ylabel("Region"); axes[0].legend(title="Score used")
fig.suptitle("Intervals are not adjusted for the 14 cells; only Europe from 2021 stays significant after the Holm correction (point-in-time scores)", fontsize=10)
plt.tight_layout(); plt.show()
''')

code(r'''
# ---- (c) Step 4: why do the restated scores give different estimates? ----
assert "est" in globals(), "Run the cells above first (Runtime > Run all)."
est["dz"] = est["z_rest"] - est["z_pit"]            # what the restatement added to the standardised score
est["dz_std"] = est["dz"] / est["dz"].std()          # the same, in standard deviations of the restatement itself
print(f"Rank correlation (within each year, averaged over years) with the next 12-month excess return: point-in-time score {rank_corr_within_year(est, 'z_pit', 'Hold_Excess_Pct'):.3f}, "
      f"restated score {rank_corr_within_year(est, 'z_rest', 'Hold_Excess_Pct'):.3f}, the restatement itself (restated minus point-in-time) {rank_corr_within_year(est, 'dz', 'Hold_Excess_Pct'):.3f}")
both = smf.ols("Hold_Excess_Pct ~ z_pit + dz_std + C(ind_year)", data=est).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(est["Company_ID"])[0]})
print(f"Joint regression with industry-by-year effects (all regions, all years): point-in-time score {both.params['z_pit']:+.2f} (se {both.bse['z_pit']:.2f}), "
      f"restatement part (per 1 standard deviation of the restatement) {both.params['dz_std']:+.2f} (se {both.bse['dz_std']:.2f})")
print(f"The restatement changed {((est['Env_restated'] - est['Environmental_Score']).abs() > 0.01).mean():.0%} of the scores, and what it added is itself related to the return that followed: the restated score behaves as if it contains hindsight (inference from this correlation).")
diff = (est_table[est_table["version"] == "restated"].set_index(["region", "period"])["coef"]
        - est_table[est_table["version"] == "point-in-time"].set_index(["region", "period"])["coef"]).unstack()[PERIODS]
print("\nRestated minus point-in-time coefficient, by region and period (percentage points):")
display(diff.round(2))
''')

code(r'''
# ---- (c) Step 5: the one cell that stands out, in more detail (exploratory: chosen after looking at the 14 cells) ----
assert "est" in globals(), "Run the cells above first (Runtime > Run all)."
eu = est[est["Region"] == "Europe"].copy()
eu["from21"] = (eu["Period"] == "from 2021").astype(int)
inter = smf.ols("Hold_Excess_Pct ~ z_pit + z_pit:from21 + C(ind_year)", data=eu).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(eu["Company_ID"])[0]})
print(f"Europe: is the relation from 2021 different from before 2021? Extra coefficient from 2021 {inter.params['z_pit:from21']:+.2f} (se {inter.bse['z_pit:from21']:.2f}, p = {inter.pvalues['z_pit:from21']:.3f})")

by_year = []
for fy, d in eu.groupby("Formation_Year"):
    m = smf.ols("Hold_Excess_Pct ~ z_pit + C(Industry)", data=d).fit(cov_type="HC1")        # one year: a firm appears once, so robust errors
    lo, hi = m.conf_int().loc["z_pit"]
    by_year.append(dict(formation_year=fy, coef=m.params["z_pit"], se=m.bse["z_pit"], lo=lo, hi=hi, n=int(m.nobs)))
by_year = pd.DataFrame(by_year)
display(by_year.round(2).set_index("formation_year"))
from scipy import stats
late = by_year[by_year["formation_year"] >= 2021]
fm_t = late["coef"].mean() / (late["coef"].std() / np.sqrt(len(late)))
fm_p = 2 * stats.t.sf(abs(fm_t), df=len(late) - 1)
print(f"Europe, from 2021, with years as the unit (Fama-MacBeth over the {len(late)} yearly slopes): mean {late['coef'].mean():+.2f}, t = {fm_t:.2f}, p = {fm_p:.3f} with {len(late) - 1} degrees of freedom. "
      "The firm-clustered p-value of the main table treats firms, not years, as independent.")
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.errorbar(by_year["formation_year"], by_year["coef"], yerr=[by_year["coef"] - by_year["lo"], by_year["hi"] - by_year["coef"]], fmt="o", color="steelblue", capsize=3)
ax.axhline(0, color="black", lw=0.8); ax.axvline(2020.5, color="grey", ls="--", lw=1)
ax.set_xlabel("Formation year (dashed line: start of the 'from 2021' period)")
ax.set_ylabel("Percentage points of 12-month excess return\nper 1 standard deviation of the Environmental score")
ax.set_title("Europe: the estimate year by year (95% interval, industry effects)")
plt.tight_layout(); plt.show()
''')

code(r'''
# ---- (c) Step 6: the numbers and the one-sentence conclusion for results.json ----
assert "est_table" in globals(), "Run the cells above first (Runtime > Run all)."
def rows_for(version):
    t = est_table[(est_table["version"] == version) & (est_table["region"] != "All regions")]
    return [dict(region=r.region, period=r.period, coef=float(r.coef), se=float(r.se), n=int(r.n)) for r in t.itertuples()]
pit = est_table[(est_table["version"] == "point-in-time") & (est_table["region"] != "All regions")]
hits_adj = pit[pit["p_holm"] < 0.05]
hits_raw = pit[(pit["p"] < 0.05) & (pit["p_holm"] >= 0.05)]
def n_years(region, period):
    return int(est[(est["Region"] == region) & (est["Period"] == period)]["Formation_Year"].nunique())
def years_as_unit_p(region, period):
    # Fama-MacBeth: one slope per formation year (industry effects), then a t-test across the yearly slopes
    d = est[(est["Region"] == region) & (est["Period"] == period)]
    slopes = np.array([smf.ols("Hold_Excess_Pct ~ z_pit + C(Industry)", data=g).fit().params["z_pit"] for _, g in d.groupby("Formation_Year")])
    t = slopes.mean() / (slopes.std(ddof=1) / np.sqrt(len(slopes)))
    return float(2 * stats.t.sf(abs(t), df=len(slopes) - 1))
if len(hits_adj):
    conclusion = ("An investor could have earned an ESG premium only in "
                  + " and in ".join(f"firms in {r.region}, {r.period} (+{r.coef:.1f} points of 12-month excess return per standard deviation of the Environmental score; "
                                    f"Holm-adjusted p = {r.p_holm:.3f} with errors clustered by company, but p = {years_as_unit_p(r.region, r.period):.2f} with its {n_years(r.region, r.period)} formation years as the unit)"
                                    for r in hits_adj.itertuples())
                  + "; no other region or period is distinguishable from zero, so this is a plausible, not a proven, premium, and it is a cross-sectional association, not a return shown to be tradable after costs.")
else:
    conclusion = "No region-period cell is distinguishable from zero after the Holm correction across the 14 cells, so an investor could not have earned an ESG premium in any of them."
task_c = dict(estimates=rows_for("point-in-time"), restated=rows_for("restated"), conclusion=conclusion)
print(conclusion)
print(f"{len(task_c['estimates'])} point-in-time cells and {len(task_c['restated'])} restated cells stored for results.json")
''')

md(r'''
**Reading the result of task (c).**

*Pooled over all regions* the relation between the point-in-time Environmental score and the next 12-month excess return is indistinguishable from zero: -0.12 points per standard deviation before 2021 (standard error 0.28) and +0.63 from 2021 (standard error 0.43). A ranking on the global score would therefore bury whatever exists.

*Region by region, exactly one cell stands out:* **Europe, from 2021**: +3.08 percentage points of 12-month excess return per standard deviation of the score (standard error 0.96, 95% interval 1.20 to 4.96, p = 0.0013, **p = 0.018 after the Holm correction** across the 14 cells). No other cell is distinguishable from zero after the correction; the next closest is Latin America from 2021 at -2.94 (p = 0.077, Holm-adjusted 0.995). Europe before 2021 is +0.47 (standard error 0.65), and the extra effect from 2021 is +2.61 (standard error 1.26, p = 0.038, an exploratory test run after the cell was singled out).

*How firm is it?* The evidence rests on four formation years (2021 to 2024): the yearly slopes are +0.3, +5.9, +1.8 and +4.2, and with years as the unit (Fama-MacBeth) p is about 0.09. The firm-clustered p-value of 0.0013 treats firms, not years, as independent. The premium therefore appears from 2022. With 14 cells and 12 yearly estimates examined, we treat it as a plausible premium for European firms from 2021, not as proven; the intervals in the figure are not adjusted for the 14 cells. For an investor: a European firm 17 points above the average of its year (about one standard deviation) was associated with about 3 percentage points more 12-month excess return than industry peers of the same year (a cross-sectional association, not a tradable return); whether it could be harvested after costs is not established by this table.

*Restated scores.* They give higher coefficients in every region and period (by 0.9 to 2.5 points) and, before the Holm correction, make more cells look significant, including Europe before 2021 (+1.59) and Asia from 2021 (+1.95), where the point-in-time scores show nothing; after the correction only Europe from 2021 remains (+4.88 with restated scores). The restated score behaves as if it carries hindsight: what the restatement added is itself related to the return that followed (within-year rank correlation 0.16; in a joint regression +5.3 points per standard deviation of the restatement). An investor on 1 July would have seen only the point-in-time score.
''')
