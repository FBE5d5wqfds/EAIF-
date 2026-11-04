# Cells for task (d) (inserted after task (c)) and the final results.json cell (appended at the very end of the notebook).
CELLS = []
FINAL = []
def md(s): CELLS.append(("markdown", s.strip("\n")))
def code(s): CELLS.append(("code", s.strip("\n")))

md(r'''
## Task (d): backtest with costs and an ESG floor

**Design.**
- *Rule.* Each year on 1 July, rank the firms of the pool on the forecast of the model selected in task (b), hold the top decile equally weighted until 30 June, and charge 20 basis points per unit of one-way turnover (the starter's convention: the replaced share is sold and bought, 40 basis points on that share, charged in the first month of the holding year).
- *Walk-forward forecasts.* The forecast for formation year Y uses only formation years up to Y-1 (their holding periods end by 30 June of Y, so their outcomes are known on 1 July of Y); the model and its scaler are refitted every year. Formation years 2018 to 2024 (at least three earlier years to train on), 84 months. Formation year 2025 has only six months of returns and is left out.
- *Model.* The pre-set rule picks **linear regression** (lowest CV RMSE, a near-tie). **Gradient boosting** (settings tuned once on the training years of task b: a simplification, because the setting was chosen with years the early forecasts should not have seen, although no return value enters the tuning) is reported as a labelled robustness check, and so is a **linear variant** whose past 12-month return is standardised within each formation year (the pooled version carries year-level variation learned from only a few years).
- *ESG floor.* The pool is restricted to firms whose Environmental score is at or above the 50th, then the 80th percentile of that formation year (computed on the whole pool of that year). The top decile is 10% of the restricted pool, so the 80th-percentile floor holds only about 18 names, which makes it noisy.
- *Universe.* The full panel including the firms that left: forecasts are made for every firm with features (a later exit is unknown on 1 July), and a firm that leaves contributes its returns until its last month, the remaining names being re-weighted equally.
- *Benchmark.* Equal weight on all firms of the formation panel, no cost (as in the starter).
- *Uncertainty.* The Sharpe difference between the best rule and the benchmark is bootstrapped by resampling months (5,000 draws, fixed seed, the same months drawn for the rule and the benchmark).
''')

code(r'''
# ---- (d) Step 1: walk-forward forecasts for formation years 2018 to 2024 ----
assert all(k in globals() for k in ["ml_a", "model_data_a", "best_params", "feature_cols_a", "TARGET", "selected"]), "Run the cells above first (Runtime > Run all)."
BT_YEARS = list(range(2018, 2025))
ml_a["Past12_z"] = ml_a.groupby("Formation_Year")["Past12_Return_Pct"].transform(lambda s: (s - s.mean()) / s.std())
feats_var = ["Past12_z" if f == "Past12_Return_Pct" else f for f in feature_cols_a]
gb_params = dict(n_estimators=100, subsample=0.8, min_samples_leaf=20, random_state=42, **best_params["Gradient boosting"])
MODELS = {
    "Linear regression (selected)": (lambda: make_pipeline(StandardScaler(), LinearRegression()), feature_cols_a),
    "Gradient boosting (robustness check)": (lambda: GradientBoostingRegressor(**gb_params), feature_cols_a),
    "Linear, past return standardised within year (variant)": (lambda: make_pipeline(StandardScaler(), LinearRegression()), feats_var),
}
print("Model selected on cross-validation in task (b):", selected, "(the pre-set rule); the other two are labelled robustness checks.")

bt = ml_a[ml_a["Formation_Year"].isin(BT_YEARS)].copy()          # all firms with features, including firms that later leave
for name, (make, feats) in MODELS.items():
    bt[name] = np.nan
    for y in BT_YEARS:
        train = ml_a[(ml_a["Hold_Months"] == 12) & (ml_a["Formation_Year"] <= y - 1)]     # earlier formation years only
        assert train["Formation_Year"].max() <= y - 1 and len(train) > 0
        model = make().fit(train[feats], train[TARGET])
        rows_y = bt["Formation_Year"] == y
        bt.loc[rows_y, name] = model.predict(bt.loc[rows_y, feats])
print(f"Forecasts for {len(bt):,} firm-years, formation years {BT_YEARS[0]} to {BT_YEARS[-1]}; training years grow from {BT_YEARS[0] - ml_a['Formation_Year'].min()} to {BT_YEARS[-1] - ml_a['Formation_Year'].min()}.")

full12 = bt[bt["Hold_Months"] == 12]
ic = pd.DataFrame({name: {y: rank_corr(d[name], d[TARGET]) for y, d in full12.groupby("Formation_Year")} for name in MODELS})
ic.loc["average 2018-2021"] = ic.loc[2018:2021].mean(); ic.loc["average 2022-2024"] = ic.loc[2022:2024].mean(); ic.loc["average 2018-2024"] = ic.loc[2018:2024].mean()
print("Rank correlation between forecast and the realised 12-month return, by formation year (firms with a full 12 months):")
display(ic.round(3))
''')

code(r'''
# ---- (d) Step 2: portfolios, costs and the results table ----
assert "bt" in globals(), "Run the cells above first (Runtime > Run all)."
rf_series = factors.set_index("Month")["Rf_Pct"]

def run_rule(picks, fm, cost_bp=20):
    # same mechanics as the given backtest(), but it returns the monthly return series (needed for the figure and the bootstrap)
    months, rets, turns, prev = [], [], [], set()
    for y in sorted(picks):
        held = set(picks[y])
        turn = 1.0 if not prev else len(held - prev) / max(len(held), 1)
        window = fm[fm["Company_ID"].isin(held) & (fm["Month"] >= f"{y}-07") & (fm["Month"] <= f"{y + 1}-06")]
        monthly = window.groupby("Month")["Return_Pct"].mean().copy()
        monthly.iloc[0] -= 2 * cost_bp / 100 * turn                 # sell and buy the replaced share
        months += list(monthly.index); rets += list(monthly.values); turns.append(turn); prev = held
    return pd.Series(rets, index=months), turns

def summarise(r, turns):
    ex = r - r.index.map(rf_series)
    return {"Annualised return (%)": 100 * ((1 + r / 100).prod() ** (12 / len(r)) - 1), "Annualised volatility (%)": r.std() * np.sqrt(12),
            "Sharpe ratio": ex.mean() / ex.std() * np.sqrt(12), "Mean one-way turnover": float(np.mean(turns)), "Months": len(r)}

FLOORS = {"no floor": None, "floor 50th pct": 0.5, "floor 80th pct": 0.8}
def picks_for(score_col, floor_q):
    out = {}
    for y in BT_YEARS:
        year_pool = bt[bt["Formation_Year"] == y]
        pool = year_pool if floor_q is None else year_pool[year_pool["Environmental_Score"] >= np.quantile(year_pool["Environmental_Score"], floor_q)]
        out[y] = pool.nlargest(max(int(0.1 * len(pool)), 1), score_col)["Company_ID"].tolist()
    return out

series, metrics, names_held = {}, {}, {}
for model in MODELS:
    for floor, q in FLOORS.items():
        picks = picks_for(model, q)
        series[(model, floor)], turns = run_rule(picks, returns_c)
        metrics[(model, floor)] = summarise(series[(model, floor)], turns)
        names_held[(model, floor)] = float(np.mean([len(v) for v in picks.values()]))
bench_picks = {y: bt.loc[bt["Formation_Year"] == y, "Company_ID"].tolist() for y in BT_YEARS}
series["bench"], bench_turns = run_rule(bench_picks, returns_c, cost_bp=0)
metrics["bench"] = summarise(series["bench"], bench_turns)

main_model = "Linear regression (selected)"
main_table = pd.DataFrame({**{f"{main_model}, {f}": metrics[(main_model, f)] for f in FLOORS}, "Equal-weight benchmark (all firms)": metrics["bench"]}).T
main_table["Names held (average)"] = [names_held[(main_model, f)] for f in FLOORS] + [float(np.mean([len(v) for v in bench_picks.values()]))]
print(f"Formation years {BT_YEARS[0]} to {BT_YEARS[-1]}, held July to June (84 months), 20 bp per unit of one-way turnover, full panel including firms that left:")
display(main_table.round(3))
b = metrics["bench"]
print("Difference to the benchmark (percentage points of annual return / Sharpe points): " + "; ".join(
    f"{f}: {metrics[(main_model, f)]['Annualised return (%)'] - b['Annualised return (%)']:+.2f} / {metrics[(main_model, f)]['Sharpe ratio'] - b['Sharpe ratio']:+.3f}" for f in FLOORS))
print("Cost of the floor against the same rule without a floor: " + "; ".join(
    f"{f}: {metrics[(main_model, f)]['Annualised return (%)'] - metrics[(main_model, 'no floor')]['Annualised return (%)']:+.2f} points of return, "
    f"{metrics[(main_model, f)]['Sharpe ratio'] - metrics[(main_model, 'no floor')]['Sharpe ratio']:+.3f} Sharpe" for f in ["floor 50th pct", "floor 80th pct"]))

print("Cost drag per year (mean one-way turnover x 40 bp): " + "; ".join(f"{f}: {0.4 * metrics[(main_model, f)]['Mean one-way turnover']:.2f} points" for f in FLOORS))
rob_rows = {f"{m}, {f}": metrics[(m, f)] for m in MODELS if m != main_model for f in FLOORS}
print("\nLabelled robustness checks (same design, other forecasts):")
display(pd.DataFrame(rob_rows).T.round(3))

late = lambda s: s[s.index >= "2022-07"]
late_rows = {f"{main_model}, {f}": summarise(late(series[(main_model, f)]), [np.nan]) for f in FLOORS}
late_rows["Equal-weight benchmark (all firms)"] = summarise(late(series["bench"]), [np.nan])
print("\nOnly the clean out-of-sample years (formation 2022 to 2024, July 2022 to June 2025, 36 months; turnover not shown):")
display(pd.DataFrame(late_rows).T.drop(columns="Mean one-way turnover").round(3))
''')

code(r'''
# ---- (d) Step 3: bootstrap of the Sharpe difference (months resampled, same months for rule and benchmark) ----
assert "series" in globals(), "Run the cells above first (Runtime > Run all)."
B, rng = 5000, np.random.default_rng(12345)
ex_bench = (series["bench"] - series["bench"].index.map(rf_series)).to_numpy()
n_months = len(ex_bench)
idx = rng.integers(0, n_months, size=(B, n_months))              # the same resampled months for every rule
sharpe_of = lambda ex: ex.mean(axis=-1) / ex.std(axis=-1, ddof=1) * np.sqrt(12)
boot = {}
for f in FLOORS:
    ex_rule = (series[(main_model, f)] - series[(main_model, f)].index.map(rf_series)).to_numpy()
    assert len(ex_rule) == n_months
    diffs = sharpe_of(ex_rule[idx]) - sharpe_of(ex_bench[idx])
    point = float(sharpe_of(ex_rule) - sharpe_of(ex_bench))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    boot[f] = dict(point=point, lo=float(lo), hi=float(hi), share_positive=float((diffs > 0).mean()))
boot_table = pd.DataFrame(boot).T
boot_table.index = [f"{main_model}, {f} minus benchmark" for f in boot_table.index]
print("Sharpe ratio difference (rule minus equal-weight benchmark), 95% percentile interval over 5,000 resamples of the 84 months:")
display(boot_table.round(3))
best_rule = max(FLOORS, key=lambda f: metrics[(main_model, f)]["Sharpe ratio"])
print(f"Best rule by Sharpe ratio: {main_model}, {best_rule}: difference {boot[best_rule]['point']:+.3f}, 95% interval {boot[best_rule]['lo']:+.3f} to {boot[best_rule]['hi']:+.3f}. "
      + ("The interval contains zero: the difference to the benchmark is not distinguishable from noise." if boot[best_rule]["lo"] <= 0 <= boot[best_rule]["hi"]
         else "The interval excludes zero."))
print("Caveats: choosing the best of three rules after seeing the results flatters it; resampling months independently ignores autocorrelation (Step 6 repeats the bootstrap with blocks of months); 84 months are few.")
''')

code(r'''
# ---- (d) Step 4: figure: cumulative return series ----
assert "series" in globals(), "Run the cells above first (Runtime > Run all)."
cum = lambda s: (1 + s / 100).cumprod()
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
for f, colour in zip(FLOORS, ["steelblue", "darkorange", "seagreen"]):
    axes[0].plot(cum(series[(main_model, f)]).values, label=f"{main_model}, {f}", color=colour)
axes[0].plot(cum(series["bench"]).values, color="black", ls="--", label="Equal-weight benchmark (all firms)")
axes[0].set_title("Selected model (linear regression) with and without the ESG floor")
for (m, colour) in zip([m for m in MODELS if m != main_model], ["purple", "firebrick"]):
    axes[1].plot(cum(series[(m, "no floor")]).values, label=f"{m}, no floor", color=colour)
axes[1].plot(cum(series[(main_model, "no floor")]).values, label=f"{main_model}, no floor", color="steelblue")
axes[1].plot(cum(series["bench"]).values, color="black", ls="--", label="Equal-weight benchmark (all firms)")
axes[1].set_title("Labelled robustness checks (no floor)")
months = list(series["bench"].index)
for ax in axes:
    ax.set_xticks(range(0, len(months), 12)); ax.set_xticklabels([months[i] for i in range(0, len(months), 12)], rotation=45)
    ax.axvline(months.index("2022-07"), color="grey", ls=":", lw=1)
    ax.set_xlabel("Month (July 2018 to June 2025; dotted line: start of the 2022 to 2024 formation years)"); ax.legend(fontsize=8, loc="upper left")
axes[0].set_ylabel("Cumulative value of 1 invested in July 2018 (after costs)")
plt.tight_layout(); plt.show()
''')

code(r'''
# ---- (d) Step 5: the numbers for results.json ----
assert "boot" in globals(), "Run the cells above first (Runtime > Run all)."
def rule_row(name, m):
    return dict(name=name, ann_return_pct=float(m["Annualised return (%)"]), ann_vol_pct=float(m["Annualised volatility (%)"]),
                sharpe=float(m["Sharpe ratio"]), turnover=float(m["Mean one-way turnover"]))
task_d = dict(
    rules=[rule_row(f"{main_model}, {f}", metrics[(main_model, f)]) for f in FLOORS] + [rule_row("Equal-weight benchmark (all firms)", metrics["bench"])],
    bootstrap=dict(statistic=f"Sharpe ratio difference, {main_model}, {best_rule} minus equal-weight benchmark; 84 months resampled with replacement, 5,000 draws, seed 12345, 95% percentile interval",
                   point=boot[best_rule]["point"], lo=boot[best_rule]["lo"], hi=boot[best_rule]["hi"]),
    universe="full panel including firms that left")
for r_ in task_d["rules"]:
    print(r_)
print(task_d["bootstrap"])
''')

code(r'''
# ---- (d) Step 6: checks on what drives the backtest result (each check answers one question a reader will ask) ----
assert "series" in globals() and "boot" in globals(), "Run the cells above first (Runtime > Run all)."
# Check 1: would a random selection of the same size have done as well? Each draw picks, in every formation year, as many
# names as the rule holds, at random from the same pool (after the same floor), with the same cost convention.
ret_mat = {}
for y in BT_YEARS:
    w = returns_c[(returns_c["Month"] >= f"{y}-07") & (returns_c["Month"] <= f"{y + 1}-06")].pivot_table(index="Month", columns="Company_ID", values="Return_Pct")
    ret_mat[y] = w
def random_rule_returns(floor_q, draws=1000, seed=2026):
    rng_r = np.random.default_rng(seed)
    pools = {}
    for y in BT_YEARS:
        p = bt[bt["Formation_Year"] == y]
        if floor_q is not None:
            p = p[p["Environmental_Score"] >= np.quantile(p["Environmental_Score"], floor_q)]
        ids = p["Company_ID"].to_numpy()
        pools[y] = (ids, max(int(0.1 * len(ids)), 1), ret_mat[y].reindex(columns=ids).to_numpy())
    out = np.empty(draws)
    for b_ in range(draws):
        monthly, prev = [], set()
        for y in BT_YEARS:
            ids, k, R = pools[y]
            pick = rng_r.choice(len(ids), k, replace=False)
            held = set(ids[pick])
            turn = 1.0 if not prev else len(held - prev) / k
            m = np.nanmean(R[:, pick], axis=1)
            m[0] -= 2 * 20 / 100 * turn
            monthly.append(m); prev = held
        r_ = np.concatenate(monthly) / 100
        out[b_] = 100 * ((1 + r_).prod() ** (12 / len(r_)) - 1)
    return out
rand_rows = {}
for f, q in FLOORS.items():
    a = random_rule_returns(q)
    v = metrics[(main_model, f)]["Annualised return (%)"]
    rand_rows[f"{main_model}, {f}"] = {"Rule (%)": v, "Random: median (%)": np.median(a), "Random: 5th pct (%)": np.percentile(a, 5),
                                      "Random: 95th pct (%)": np.percentile(a, 95), "Share of random draws at least as good": (a >= v).mean()}
rand_table = pd.DataFrame(rand_rows).T
print("Check 1: the rules against 1,000 random selections of the same size from the same pool (annualised return after costs):")
display(rand_table.round(3))
print(f"Between {rand_table['Share of random draws at least as good'].min():.0%} and {rand_table['Share of random draws at least as good'].max():.0%} of random selections do at least as well as the rules: "
      "the rules' results are within what an unskilled selection of the same size produces.")

# Check 2: where does the floor result come from? (a) all firms above the floor at equal weight, no forecast; (b) year by year; (c) without formation year 2022
floor_only = {}
for f, q in FLOORS.items():
    if q is None:
        continue
    pk = {y: bt[(bt["Formation_Year"] == y) & (bt["Environmental_Score"] >= np.quantile(bt.loc[bt["Formation_Year"] == y, "Environmental_Score"], q))]["Company_ID"].tolist() for y in BT_YEARS}
    s_, t_ = run_rule(pk, returns_c)
    floor_only[f"All firms above the {f[6:]}, equal weight"] = summarise(s_, t_)
floor_only["Equal-weight benchmark (all firms)"] = metrics["bench"]
print("\nCheck 2a: holding every firm above the floor at equal weight (no forecast, same cost convention):")
display(pd.DataFrame(floor_only).T[["Annualised return (%)", "Annualised volatility (%)", "Sharpe ratio"]].round(3))
year_ret = lambda s_, y: 100 * ((1 + s_[(s_.index >= f"{y}-07") & (s_.index <= f"{y + 1}-06")] / 100).prod() - 1)
yearly = pd.DataFrame({**{f: {y: year_ret(series[(main_model, f)], y) for y in BT_YEARS} for f in FLOORS}, "benchmark": {y: year_ret(series["bench"], y) for y in BT_YEARS}})
print("Check 2b: return of each holding year (July to June, %), by formation year:")
display(yearly.round(1))
drop22 = lambda s_: s_[~((s_.index >= "2022-07") & (s_.index <= "2023-06"))]
no22 = {f"{main_model}, {f}": summarise(drop22(series[(main_model, f)]), [np.nan]) for f in FLOORS}
no22["Equal-weight benchmark (all firms)"] = summarise(drop22(series["bench"]), [np.nan])
print("Check 2c: the same backtest without formation year 2022 (72 months):")
display(pd.DataFrame(no22).T[["Annualised return (%)", "Sharpe ratio"]].round(3))

# Check 3: survivors-only benchmark on the same 2018 to 2024 window (task a measured the effect over formation years 2015 to 2025)
surv_picks = {y: [c for c in bench_picks[y] if c in survivor_ids] for y in BT_YEARS}
s_, t_ = run_rule(surv_picks, returns_c, cost_bp=0)
surv_ret = summarise(s_, t_)["Annualised return (%)"]
print(f"\nCheck 3: equal-weight benchmark 2018 to 2024 on survivors only {surv_ret:.2f}% against {metrics['bench']['Annualised return (%)']:.2f}% on the full panel "
      f"({surv_ret - metrics['bench']['Annualised return (%)']:+.2f} points a year).")

# Check 4: formation year 2025 has only six months of returns (July to December 2025) and is left out. What if it were included?
Y25 = BT_YEARS + [2025]
bt25 = ml_a[ml_a["Formation_Year"].isin(Y25)].copy()
make_lin, feats_lin = MODELS[main_model]
bt25["forecast"] = np.nan
for y in Y25:
    train = ml_a[(ml_a["Hold_Months"] == 12) & (ml_a["Formation_Year"] <= y - 1)]
    rows_y = bt25["Formation_Year"] == y
    bt25.loc[rows_y, "forecast"] = make_lin().fit(train[feats_lin], train[TARGET]).predict(bt25.loc[rows_y, feats_lin])
with25 = {}
for f, q in FLOORS.items():
    pk = {}
    for y in Y25:
        p = bt25[bt25["Formation_Year"] == y]
        if q is not None:
            p = p[p["Environmental_Score"] >= np.quantile(p["Environmental_Score"], q)]
        pk[y] = p.nlargest(max(int(0.1 * len(p)), 1), "forecast")["Company_ID"].tolist()
    s_, t_ = run_rule(pk, returns_c)
    with25[f"{main_model}, {f}"] = summarise(s_, t_)
s_, t_ = run_rule({y: bt25.loc[bt25["Formation_Year"] == y, "Company_ID"].tolist() for y in Y25}, returns_c, cost_bp=0)
with25["Equal-weight benchmark (all firms)"] = summarise(s_, t_)
w25 = pd.DataFrame(with25).T[["Annualised return (%)", "Sharpe ratio", "Months"]]
w25["Without 2025 (%)"] = [metrics[(main_model, f)]["Annualised return (%)"] for f in FLOORS] + [metrics["bench"]["Annualised return (%)"]]
print("\nCheck 4: including formation year 2025 (six months):")
display(w25.round(3))
same_order = list(w25["Annualised return (%)"].sort_values().index) == list(w25["Without 2025 (%)"].sort_values().index)
print(f"Including it lowers every rule and the benchmark by {(w25['Without 2025 (%)'] - w25['Annualised return (%)']).min():.1f} to {(w25['Without 2025 (%)'] - w25['Annualised return (%)']).max():.1f} points a year; "
      + ("the ranking of the rules is unchanged." if same_order else "the ranking of the rules changes."))

# Check 5: the bootstrap with blocks of consecutive months (circular block bootstrap), which keeps short-run dependence between months
ex_best = (series[(main_model, best_rule)] - series[(main_model, best_rule)].index.map(rf_series)).to_numpy()
block_rows = {"1 month (Step 3)": dict(lo=boot[best_rule]["lo"], hi=boot[best_rule]["hi"])}
for L in [3, 6, 12]:
    rng_b = np.random.default_rng(12345)
    starts = rng_b.integers(0, n_months, size=(B, int(np.ceil(n_months / L))))
    ii = ((starts[:, :, None] + np.arange(L)) % n_months).reshape(B, -1)[:, :n_months]
    d_ = sharpe_of(ex_best[ii]) - sharpe_of(ex_bench[ii])
    block_rows[f"{L} months"] = dict(lo=np.percentile(d_, 2.5), hi=np.percentile(d_, 97.5))
print(f"\nCheck 5: 95% interval of the Sharpe difference ({main_model}, {best_rule} minus benchmark) by block length:")
display(pd.DataFrame(block_rows).T.round(3))
blk = pd.DataFrame(block_rows).T
widths = blk["hi"] - blk["lo"]
print(("Keeping blocks of months together does not widen the interval here (the independent resampling is, if anything, conservative). " if (widths.iloc[1:] <= widths.iloc[0] + 1e-9).all()
       else "Keeping blocks of months together widens the interval for at least one block length. ")
      + ("Every interval contains zero." if ((blk["lo"] <= 0) & (blk["hi"] >= 0)).all() else "At least one interval excludes zero."))
''')

md(r'''
**Reading the result of task (d).**

*Does the selected rule beat the benchmark?* Not in a way that can be told apart from chance. Linear regression, no floor, earned 9.4% a year after costs against 8.8% for the equal-weight benchmark (+0.6 points; Sharpe ratio 0.46 against 0.42). The forecast itself has almost no ranking skill: the rank correlation with the realised return averages +0.01 over 2018 to 2024 (+0.03 in 2018 to 2021, -0.02 in 2022 to 2024). The strategy holds about 94 names against about 945 for the benchmark, and 16% of random selections of the same size from the same pool do at least as well (Step 6, check 1), so a difference of this size is within what an unskilled selection of names produces. In the clean out-of-sample years (formation 2022 to 2024, a strong market) the picture is the same: 21.9% against 21.4%.

*What the floor does.* In this sample the floor did **not** cost return: the 50th-percentile floor earned 9.6% (+0.2 points against no floor), the 80th-percentile floor 11.4% (+2.0 points; Sharpe 0.53). What it costs is concentration and trading: about 47 and 19 names instead of 94, volatility of 17.1% and 18.4% instead of 16.8%, and one-way turnover of 0.76 and 0.82 instead of 0.70, that is a cost drag of 0.31 and 0.33 points a year (0.28 without a floor). The 80th-percentile result should not be read as an ESG effect (Step 6, check 2). Holding every firm above the 80th percentile at equal weight earns 8.9% a year, about the benchmark's 8.8%, so the floor itself adds nothing; the gap comes from the about 19 names the model picked, mostly in one year: for formation year 2022 the rule earned +45% against +22% for the benchmark. Without formation year 2022 every rule trails the benchmark (6.0%, 6.2% and 6.6% a year against 6.7%). In random draws of 19 names from the same pool, 11% do at least as well as the rule.

*Is the difference to the benchmark distinguishable from noise?* No. For the best rule (80th-percentile floor) the Sharpe difference is +0.11 with a 95% interval from -0.16 to +0.38; the intervals of the other two rules also contain zero (-0.16 to +0.23 and -0.18 to +0.26). Choosing the best of three rules after seeing the results flatters it, and 84 months are few. Resampling blocks of 3, 6 or 12 consecutive months instead of single months gives intervals that are no wider (12-month blocks: -0.07 to +0.31), so the independent resampling is not what makes the interval include zero.

*Robustness checks (labelled, not chosen on cross-validation).* Gradient boosting without a floor earned 8.1% (Sharpe 0.39), below the benchmark. The linear variant with past return standardised within year earned 11.5% (Sharpe 0.57), the highest no-floor result, but it was not the model selected in task (b), and picking it now because it looks best would be selecting on the test period.

*Two design choices.* Formation year 2025 has only six months of returns and is left out; including it lowers every rule and the benchmark by 1.6 to 2.3 points a year and leaves the ranking unchanged (Step 6, check 4). The benchmark uses the full panel including firms that left; on survivors only it would have earned 9.2% instead of 8.8% (+0.46 points a year, check 3).
''')

FINAL.append(("code", r'''
# ---- Final cell: fill results.json from the numbers computed above (run this last) ----
GROUP_NAME = "Group_8"
MEMBERS = ["Beyeler Fabian", "Lussi Laurin", "Griessen Jan"]
assert all(k in globals() for k in ["audit_entries", "task_b", "task_c", "task_d"]), "Run the cells above first (Runtime > Run all)."

def all_finite(x):
    # results.json must contain no NaN or infinity (they would produce invalid JSON)
    if isinstance(x, dict):
        return all(all_finite(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return all(all_finite(v) for v in x)
    if isinstance(x, (int, float, np.integer, np.floating)) and not isinstance(x, bool):
        return bool(np.isfinite(x))
    return True

results_final = dict(group=GROUP_NAME, members=MEMBERS, audit=audit_entries, task_b=task_b, task_c=task_c, task_d=task_d)
assert all_finite(results_final), "results.json would contain NaN or infinity"
if not GROUP_NAME:
    print("Reminder: GROUP_NAME is still empty; set it in this cell before the final submission run.")
write_results(results_final)
print("In Colab the file is written to /content/results.json: download it from the file browser on the left.")
'''))
