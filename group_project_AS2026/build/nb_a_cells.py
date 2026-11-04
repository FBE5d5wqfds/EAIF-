# Cells for task (a), inserted between Section 5 and Section 6 of the starter notebook.
# Each entry: (cell_type, source)

CELLS = []
def md(s): CELLS.append(("markdown", s.strip("\n")))
def code(s): CELLS.append(("code", s.strip("\n")))

md(r'''
## Task (a): pipeline and data audit

*Everything from here to Section 6 is our own work. The given cells above are unchanged.*

**Approach.** First we audit the five files and measure what each problem does to one headline number. Then we build cleaned copies (`panel_c`, `returns_c`) and, from them, our own formation panel. The given data frames (`panel`, `returns`, `restated`, ...) stay untouched, so the given cells above still reproduce the starter's numbers.

**Run order.** The cells depend on each other: use *Runtime > Restart session and run all* instead of running single cells. Later cells stop with a clear message if an earlier one has not run.

**Treatments** follow the group's decisions from the coaching with the lecturer (any method is fine if it is applied consistently and explained): rescale the unit error, keep one row of each duplicated return month, exclude the column that carries future information, build everything on the full panel (never the survivors-only file), use the point-in-time scores and keep the restated file for the comparison in task (c), keep missing environmental metrics with a missing flag, and keep (and document) values at the bounds.
''')

code(r'''
# ---- (a) Step 1: structure checks on all five files ----
audit = {}   # the numbers collected here feed the audit table and results.json

def rank_corr(a, b):
    # Spearman rank correlation of two aligned series (rows with a missing value are dropped)
    return pd.concat([a, b], axis=1).dropna().corr(method="spearman").iloc[0, 1]

def rank_corr_within_year(df, a, b, year="Year"):
    # rank correlation computed inside each year and averaged over years (removes year-level drift in the scores)
    return float(np.mean([rank_corr(d[a], d[b]) for _, d in df.groupby(year)]))

pub = pd.to_datetime(panel["Publication_Date"])
window_ok = (pub >= pd.to_datetime((panel["Year"] + 1).astype(str) + "-03-31")) & \
            (pub <= pd.to_datetime((panel["Year"] + 1).astype(str) + "-05-31"))
ym = returns.drop_duplicates(["Company_ID", "Month"]).assign(
    m=lambda d: d["Month"].str[:4].astype(int) * 12 + d["Month"].str[5:].astype(int)).sort_values(["Company_ID", "m"])
gap_months = int((ym.groupby("Company_ID")["m"].diff().fillna(1) > 1).sum())

structure = pd.Series({
    "panel: duplicate (Company_ID, Year) keys": int(panel.duplicated(["Company_ID", "Year"]).sum()),
    "restated: duplicate (Company_ID, Year) keys": int(restated.duplicated(["Company_ID", "Year"]).sum()),
    "returns: duplicate (Company_ID, Month) keys": int(returns.duplicated(["Company_ID", "Month"]).sum()),
    "factors: duplicate months": int(factors["Month"].duplicated().sum()),
    "universe: duplicate firms": int(universe["Company_ID"].duplicated().sum()),
    "panel: firms whose Industry or Region changes over time": int(((panel.groupby("Company_ID")["Industry"].nunique() > 1) |
                                                                    (panel.groupby("Company_ID")["Region"].nunique() > 1)).sum()),
    "panel: rows published outside 31 Mar to 31 May of Year+1": int((~window_ok).sum()),
    "returns: months missing inside a firm's history": gap_months,
    "panel: Growth_Rate missing (first year of each firm = firms)": f"{int(panel['Growth_Rate'].isna().sum())} (= {panel['Company_ID'].nunique()} firms)",
})
print(structure.to_string())
print("\nOnly the returns file has duplicated keys (300). The structure checks on the other files are clean; the problems below are in the values.")
''')

code(r'''
# ---- (a) Step 2: unit error in Revenue and Market_Cap ----
# Idea: carbon, water and energy scale with revenue within an industry. A firm whose revenue is 1,000 times too large
# looks like it emits 1,000 times too little for its size. The relation is fitted on clearly normal firms (Revenue < 100,000).
ENV = ["Carbon_Emissions", "Water_Usage", "Energy_Consumption"]
lp = panel.assign(l_rev=np.log10(panel["Revenue"]))
resid = pd.DataFrame(index=lp.index)
for c in ENV:
    lp["l_" + c] = np.log10(lp[c])
    normal = lp[(lp["Revenue"] < 1e5) & lp["Carbon_Emissions"].notna()]
    coef = {ind: np.polyfit(d["l_rev"], d["l_" + c], 1) for ind, d in normal.groupby("Industry")}
    slope = lp["Industry"].map({k: v[0] for k, v in coef.items()})
    icept = lp["Industry"].map({k: v[1] for k, v in coef.items()})
    resid[c] = lp["l_" + c] - (slope * lp["l_rev"] + icept)
lp["resid"] = resid.mean(axis=1)                      # missing where the environmental metrics are missing
lp["row_flag"] = lp["resid"] < -1.5                    # about 3 log10 units below the normal relation = factor 1,000
per_firm = lp.groupby("Company_ID").agg(flagged=("row_flag", "sum"), with_env=("resid", "count"))
unit_firms = sorted(per_firm.index[per_firm["flagged"] / per_firm["with_env"].replace(0, np.nan) > 0.5])
unit_mask = panel["Company_ID"].isin(unit_firms)

panel_c = panel.copy()                                 # cleaned copy used from here on
panel_c.loc[unit_mask, ["Revenue", "Market_Cap"]] = panel_c.loc[unit_mask, ["Revenue", "Market_Cap"]] / 1000

top100_before = panel.nlargest(100, "Market_Cap")["Company_ID"].isin(unit_firms).mean()
top100_after = panel_c.nlargest(100, "Market_Cap")["Company_ID"].isin(unit_firms).mean()
audit["unit"] = dict(firms=len(unit_firms), rows=int(unit_mask.sum()),
                     mc_before=panel["Market_Cap"].mean(), mc_after=panel_c["Market_Cap"].mean(),
                     rev_before=panel["Revenue"].mean(), rev_after=panel_c["Revenue"].mean(),
                     top100_before=top100_before, top100_after=top100_after)
print(f"{len(unit_firms)} firms ({int(unit_mask.sum())} firm-years) flagged: {unit_firms}")
print(f"Mean Market_Cap {panel['Market_Cap'].mean():,.0f} -> {panel_c['Market_Cap'].mean():,.0f} USD million; "
      f"mean Revenue {panel['Revenue'].mean():,.0f} -> {panel_c['Revenue'].mean():,.0f}")
print(f"Share of the 100 largest firm-years by market cap that belong to these firms: {top100_before:.0%} -> {top100_after:.0%}")

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
axes[0].hist(lp["resid"].dropna(), bins=80, color="steelblue")
axes[0].set_xlabel("Environmental metrics relative to revenue (log10 units, 0 = typical for the industry)")
axes[0].set_ylabel("Firm-years"); axes[0].set_title("Two clusters: the left one is about 1,000x (3 log10 units) off")
bins = np.linspace(1.4, 8, 100)                       # same bins for both histograms
axes[1].hist(np.log10(panel["Revenue"]), bins=bins, alpha=0.6, label="before the fix", color="grey")
axes[1].hist(np.log10(panel_c["Revenue"]), bins=bins, alpha=0.6, label="after the fix", color="steelblue")
axes[1].set_xlabel("log10 revenue (USD million)"); axes[1].set_ylabel("Firm-years"); axes[1].legend()
axes[1].set_title("Revenue: the second cluster disappears after dividing by 1,000")
plt.tight_layout(); plt.show()
''')

code(r'''
# ---- (a) Step 3: near-duplicate monthly returns ----
dups = returns[returns.duplicated(["Company_ID", "Month"], keep=False)]
spread = dups.groupby(["Company_ID", "Month"])["Return_Pct"].agg(lambda s: s.max() - s.min())
print(f"{len(spread)} company-months appear twice; the two values differ by {spread.mean():.4f} on average, at most {spread.max():.4f} percentage points")
print("Example:", dups[(dups["Company_ID"] == dups["Company_ID"].iloc[0]) & (dups["Month"] == dups["Month"].iloc[0])].to_dict("records"))

returns_c = returns.drop_duplicates(["Company_ID", "Month"], keep="first").reset_index(drop=True)   # treatment: keep the first row

# Effect, measured with the starter's own formation panel (the given function) on the otherwise unchanged panel
base_features = ["Growth_Rate", "Profit_Margin"] + SCORES
ml_before, _ = formation_panel(panel, returns, factors, base_features)
ml_after, _ = formation_panel(panel, returns_c, factors, base_features)
audit["dups"] = dict(keys=len(spread), max_spread=spread.max(),
                     over12_before=int((ml_before["Hold_Months"] > 12).sum()), over12_after=int((ml_after["Hold_Months"] > 12).sum()),
                     full12_before=int((ml_before["Hold_Months"] == 12).sum()), full12_after=int((ml_after["Hold_Months"] == 12).sum()))
print(f"Firm-years with 13 holding months (counted as 'not 12', so dropped by the starter): {audit['dups']['over12_before']} -> {audit['dups']['over12_after']}")
print(f"Firm-years with a full 12 holding months: {audit['dups']['full12_before']:,} -> {audit['dups']['full12_after']:,}")
''')

code(r'''
# ---- (a) Step 4: Analyst_Outlook carries information from the future ----
# Diagnostic only: the test years are used here to measure the size of an effect, never to choose a model, a feature or a setting.
assert "panel_c" in globals() and "returns_c" in globals(), "Run the cells above first (Runtime > Run all)."
# Formation panel on the cleaned data, built with the given function (used only for the audit)
ml_c, _ = formation_panel(panel_c, returns_c, factors, base_features + ["Analyst_Outlook"])
rows = []
for label, offset in [("Next 12 months after formation (Jul Y+1 to Jun Y+2): the target", 1),
                      ("12 months before formation (Jul Y to Jun Y+1)", 0),
                      ("The 12 months before that (Jul Y-1 to Jun Y)", -1)]:
    w = pd.concat([holding_returns(returns_c, factors, fy + offset).assign(Year=fy) for fy in range(2012, 2026)])
    w = w[w["Months"] == 12].merge(panel_c[["Company_ID", "Year", "Analyst_Outlook"]], on=["Company_ID", "Year"])
    rows.append((label, rank_corr(w["Analyst_Outlook"], w["Hold_Return_Pct"])))
leak = pd.DataFrame(rows, columns=["12-month window (Y = fiscal year of the row)", "Rank correlation with Analyst_Outlook"])
print(leak.round(3).to_string(index=False))

from sklearn.ensemble import RandomForestRegressor
def rf_test_rmse(features):
    d, ft = formation_panel(panel_c, returns_c, factors, features)
    d = d[d["Hold_Months"] == 12]
    tr, te = d[d["Formation_Year"] <= 2021], d[d["Formation_Year"] >= 2022]
    rf = RandomForestRegressor(n_estimators=300, max_depth=3, min_samples_leaf=20, random_state=42, n_jobs=-1).fit(tr[ft], tr["Hold_Return_Pct"])
    return (np.sqrt(mean_squared_error(te["Hold_Return_Pct"], rf.predict(te[ft]))),
            np.sqrt(mean_squared_error(te["Hold_Return_Pct"], np.full(len(te), tr["Hold_Return_Pct"].mean()))))
rmse_without, rmse_base = rf_test_rmse(base_features)
rmse_with, _ = rf_test_rmse(base_features + ["Analyst_Outlook"])
audit["leak"] = dict(rho_next=leak.iloc[0, 1], rho_before=leak.iloc[1, 1], rho_before2=leak.iloc[2, 1],
                     rmse_without=rmse_without, rmse_with=rmse_with, rmse_base=rmse_base)
print(f"\nRandom forest test RMSE (percentage points): without Analyst_Outlook {rmse_without:.2f}, WITH it {rmse_with:.2f}, naive baseline {rmse_base:.2f}")
print("A column that makes the model look this good, and is related to no other window, behaves as if it was stamped with future information. Excluded.")
''')

code(r'''
# ---- (a) Step 5: survivorship (the universe file holds survivors only) ----
assert "ml_c" in globals(), "Run the cells above first (Runtime > Run all)."
last_year = panel.groupby("Company_ID")["Year"].max()
n_exit = int((last_year < 2025).sum())
survivor_ids = set(universe["Company_ID"])
fyears = sorted(y for y in ml_c["Formation_Year"].unique() if y >= 2015)
all_firms = {y: ml_c.loc[ml_c["Formation_Year"] == y, "Company_ID"].tolist() for y in fyears}
survivors = {y: [c for c in all_firms[y] if c in survivor_ids] for y in fyears}
bench_full = backtest(all_firms, returns_c, factors, cost_bp=0)
bench_surv = backtest(survivors, returns_c, factors, cost_bp=0)
short_exit = int(((ml_c["Hold_Months"] < 12) & (ml_c["Formation_Year"] <= 2024)).sum())   # firm-years of exiting firms with fewer than 12 holding months
censored_2025 = int((ml_c["Formation_Year"] == 2025).sum())                                 # formation 2025: returns end in December 2025
audit["surv"] = dict(exits=n_exit, universe=len(survivor_ids), firms=panel["Company_ID"].nunique(), short_exit=short_exit, censored_2025=censored_2025,
                     ret_full=bench_full["Annualised return (%)"], ret_surv=bench_surv["Annualised return (%)"],
                     sharpe_full=bench_full["Sharpe ratio"], sharpe_surv=bench_surv["Sharpe ratio"])
print(f"{panel['Company_ID'].nunique():,} firms in the panel, {len(survivor_ids)} in universe_current.csv, {n_exit} exited before 2025")
print(pd.DataFrame({"Full panel (incl. exits)": bench_full, "Survivors only": bench_surv}).T.round(3).to_string())
''')

code(r'''
# ---- (a) Step 6: restated scores behave as if they contain hindsight ----
assert "ml_c" in globals(), "Run the cells above first (Runtime > Run all)."
pit_vs_rest = panel[["Company_ID", "Year", "Environmental_Score"]].merge(
    restated[["Company_ID", "Year", "Environmental_Score"]], on=["Company_ID", "Year"], suffixes=("", "_r"))
pit_vs_rest["d"] = pit_vs_rest["Environmental_Score_r"] - pit_vs_rest["Environmental_Score"]
pit_vs_rest["changed"] = pit_vs_rest["d"].abs() > 0.01
share_changed = pit_vs_rest.groupby("Company_ID")["changed"].mean()
mdl_c = ml_c[ml_c["Hold_Months"] == 12][["Company_ID", "Formation_Year", "Hold_Excess_Pct"]].assign(Year=lambda d: d["Formation_Year"] - 1)
z = pit_vs_rest.merge(mdl_c, on=["Company_ID", "Year"])
overlap = []
for y, d in z.groupby("Year"):
    n = max(int(0.1 * len(d)), 1)
    overlap.append(len(set(d.nlargest(n, "Environmental_Score")["Company_ID"]) & set(d.nlargest(n, "Environmental_Score_r")["Company_ID"])) / n)
audit["restated"] = dict(firms_all_changed=int((share_changed == 1).sum()), firms_none=int((share_changed == 0).sum()),
                         mean_abs_change=pit_vs_rest.loc[pit_vs_rest["changed"], "d"].abs().mean(),
                         rho_pit=rank_corr_within_year(z, "Environmental_Score", "Hold_Excess_Pct"),
                         rho_rest=rank_corr_within_year(z, "Environmental_Score_r", "Hold_Excess_Pct"),
                         rho_change=rank_corr_within_year(z[z["changed"]], "d", "Hold_Excess_Pct"),
                         top_decile_overlap=float(np.mean(overlap)))
a = audit["restated"]
print(f"Firms with every Environmental score changed: {a['firms_all_changed']}; with none changed: {a['firms_none']}; mean absolute change among changed rows: {a['mean_abs_change']:.1f} points")
print(f"Rank correlation (within each year, averaged over years) of the Environmental score with the next 12-month excess return: point-in-time {a['rho_pit']:.3f}, restated {a['rho_rest']:.3f}")
print(f"Same measure for the change itself (restated minus point-in-time), changed rows only: {a['rho_change']:.3f}")
print(f"Mean overlap of the top-decile Environmental names, point-in-time vs restated: {a['top_decile_overlap']:.0%}")
''')

code(r'''
# ---- (a) Step 7: missing environmental metrics, and values at the bounds ----
assert "ml_c" in globals(), "Run the cells above first (Runtime > Run all)."
mdl_all = ml_c[ml_c["Hold_Months"] == 12]
miss = mdl_all["Carbon_Emissions"].isna()
together = bool((panel["Carbon_Emissions"].isna() == panel["Water_Usage"].isna()).all() and
                (panel["Carbon_Emissions"].isna() == panel["Energy_Consumption"].isna()).all())
by_region = mdl_all.assign(miss=miss).groupby("Region")["miss"].mean().round(3)
audit["missing"] = dict(rows=int(panel["Carbon_Emissions"].isna().sum()), share=float(miss.mean()), together=together,
                        env_missing=mdl_all.loc[miss, "Environmental_Score"].mean(), env_present=mdl_all.loc[~miss, "Environmental_Score"].mean(),
                        env_all=float(mdl_all["Environmental_Score"].mean()),
                        europe=float(by_region["Europe"]), others_min=float(by_region.drop("Europe").min()), others_max=float(by_region.drop("Europe").max()))
m_ = audit["missing"]
print(f"Carbon, water and energy are missing in {m_['rows']:,} panel rows, always together: {m_['together']} ({m_['share']:.1%} of the formation rows)")
print(f"Share missing by region (formation rows):\n{by_region.to_string()}")
print(f"Mean Environmental score: rows with the metrics missing {m_['env_missing']:.1f} vs present {m_['env_present']:.1f}")

S3 = ["Environmental_Score", "Social_Score", "Governance_Score"]
audit["bounds"] = dict(env_rows=int(panel["Environmental_Score"].isin([0, 100]).sum()), social_rows=int(panel["Social_Score"].isin([0, 100]).sum()),
                       gov_rows=int(panel["Governance_Score"].isin([0, 100]).sum()), any_rows=int(panel[S3].isin([0, 100]).any(axis=1).sum()),
                       env_europe=int((panel.loc[panel["Environmental_Score"].isin([0, 100]), "Region"] == "Europe").sum()),
                       restated_env_rows=int(restated["Environmental_Score"].isin([0, 100]).sum()),
                       return_rows=int((returns["Return_Pct"] == -95).sum()),
                       return_rows_not_last=int((returns.loc[returns["Return_Pct"] == -95].merge(
                           returns.groupby("Company_ID")["Month"].max().rename("last"), on="Company_ID").eval("Month != last")).sum()))
b_ = audit["bounds"]
print(f"\nScores exactly 0 or 100 in the panel: Environmental {b_['env_rows']}, Social {b_['social_rows']}, Governance {b_['gov_rows']}; "
      f"{b_['any_rows']} rows ({b_['any_rows'] / len(panel):.1%}) have at least one; {b_['env_europe']} of the Environmental ones are in Europe; restated file: Environmental {b_['restated_env_rows']}.")
print(f"Monthly returns exactly -95%: {b_['return_rows']} rows ({b_['return_rows_not_last']} of them not in the firm's last month). "
      "Kept and documented: the scores look clipped (censored) at the bounds, and we cannot tell clipped returns from real ones.")
''')


md(r'''
### Formation panel and features

The decision-time rule is the same as in the worked model: portfolios are formed on 1 July of the formation year; every feature comes from the fiscal-year row published before that date (fiscal year = formation year - 1) or from returns up to June of the formation year; the target is the total return over the following twelve months. The split is by formation year (train up to 2021, test 2022 to 2024).

Six features are new compared with the worked model. Each passes the rule: it is in a file that existed on 1 July, with the value it had then.
''')

code(r'''
# ---- (a) Step 8: our own formation panel (cleaned data, new dated features) ----
assert "panel_c" in globals() and "returns_c" in globals(), "Run the cells above first (Runtime > Run all)."
NEW_FEATURES = ["Env_Change", "Margin_Change", "log_MC_to_Rev", "log_Carbon_Int", "Carbon_Missing", "Past_Vol_Pct"]

def past_window(fm, y):
    # the 12 months before formation: July of y-1 to June of y (returns up to June of the formation year)
    w = fm[(fm["Month"] >= f"{y - 1}-07") & (fm["Month"] <= f"{y}-06")].copy()
    w["gross"] = 1 + w["Return_Pct"] / 100
    g = w.groupby("Company_ID")
    return pd.DataFrame({"Past12_Return_Pct": 100 * (g["gross"].prod() - 1), "Past_Months": g.size(),
                         "Past_Vol_Pct": g["Return_Pct"].std()}).reset_index()

def formation_panel_a(fy, fm, factors):
    fy = fy.sort_values(["Company_ID", "Year"]).copy()
    assert (fy.groupby("Company_ID")["Year"].diff().dropna() == 1).all()      # consecutive years, so shift(1) is the previous year
    g = fy.groupby("Company_ID")
    fy["Growth_Lag1"] = g["Growth_Rate"].shift(1)
    fy["Env_Change"] = fy["Environmental_Score"] - g["Environmental_Score"].shift(1)     # ESG momentum
    fy["Margin_Change"] = fy["Profit_Margin"] - g["Profit_Margin"].shift(1)
    fy["log_Revenue"], fy["log_Market_Cap"] = np.log(fy["Revenue"]), np.log(fy["Market_Cap"])
    fy["log_MC_to_Rev"] = np.log(fy["Market_Cap"] / fy["Revenue"])                       # valuation relative to sales
    fy["log_Carbon_Int"] = np.log(fy["Carbon_Emissions"] / fy["Revenue"])                # carbon per USD million revenue
    fy["Carbon_Missing"] = fy["Carbon_Emissions"].isna().astype(int)
    # gap fill: median of the same fiscal year and industry (all rows of fiscal year t are published before 1 July t+1)
    fy["log_Carbon_Int"] = fy["log_Carbon_Int"].fillna(fy.groupby(["Year", "Industry"])["log_Carbon_Int"].transform("median"))
    fy["Formation_Year"] = fy["Year"] + 1
    pub_ok = pd.to_datetime(fy["Publication_Date"]) < pd.to_datetime(fy["Formation_Year"].astype(str) + f"-{FORMATION_MONTH:02d}-01")
    assert pub_ok.all(), "a row would be used before it was published"
    years = sorted(fy["Formation_Year"].unique())
    past = pd.concat([past_window(fm, y).assign(Formation_Year=y) for y in years])
    past = past[past["Past_Months"] == 12]                                               # require a full 12 months of history
    tgt = pd.concat([holding_returns(fm, factors, y).assign(Formation_Year=y) for y in years]).rename(columns={"Months": "Hold_Months"})
    out = (fy.merge(past.drop(columns="Past_Months"), on=["Company_ID", "Formation_Year"], how="left")
             .merge(tgt[["Company_ID", "Formation_Year", "Hold_Return_Pct", "Hold_Excess_Pct", "Hold_Months"]], on=["Company_ID", "Formation_Year"], how="inner"))
    dummies = pd.get_dummies(out[["Industry", "Region"]], drop_first=True, dtype=int)
    out = pd.concat([out, dummies], axis=1)
    features = (["Growth_Rate", "Profit_Margin"] + SCORES + ["Growth_Lag1", "log_Revenue", "log_Market_Cap", "Past12_Return_Pct"]
                + NEW_FEATURES + list(dummies.columns))
    return out.dropna(subset=features + ["Hold_Return_Pct"]).reset_index(drop=True), features

ml_a, feature_cols_a = formation_panel_a(panel_c, returns_c, factors)
model_data_a = ml_a[ml_a["Hold_Months"] == 12]            # a full twelve holding months: the rows models are fitted and tested on
train_a, test_a = model_data_a["Formation_Year"] <= 2021, model_data_a["Formation_Year"] >= 2022

# decision-time checks that must hold for every row
assert (ml_a["Formation_Year"] == ml_a["Year"] + 1).all()
assert (pd.to_datetime(ml_a["Publication_Date"]) < pd.to_datetime(ml_a["Formation_Year"].astype(str) + "-07-01")).all()
assert "Analyst_Outlook" not in feature_cols_a

print(f"Formation rows: {len(ml_a):,} ({len(model_data_a):,} with a full twelve holding months), formation years {ml_a['Formation_Year'].min()}-{ml_a['Formation_Year'].max()}")
print(f"Features ({len(feature_cols_a)}): {feature_cols_a}")
print(f"Training rows (formation years <= 2021): {int(train_a.sum()):,}; test rows (2022-2024): {int(test_a.sum()):,}")
print(f"Naive baseline: training mean {model_data_a.loc[train_a, 'Hold_Return_Pct'].mean():.2f}%, test RMSE "
      f"{np.sqrt(mean_squared_error(model_data_a.loc[test_a, 'Hold_Return_Pct'], np.full(int(test_a.sum()), model_data_a.loc[train_a, 'Hold_Return_Pct'].mean()))):.3f}")
print(f"Mean 12-month return: training years {model_data_a.loc[train_a, 'Hold_Return_Pct'].mean():.1f}%, test years {model_data_a.loc[test_a, 'Hold_Return_Pct'].mean():.1f}% "
      "(the test years are strong years, not a downturn)")
''')

code(r'''
# ---- (a) Step 9: feature table, with the date from which each feature is known ----
assert "ml_a" in globals(), "Run the cells above first (Runtime > Run all)."
PANEL_DATE = "Row of fiscal year Y published 31 Mar to 31 May of Y+1, so known before 1 July of Y+1"
RET_DATE = "Returns through 30 June of the formation year, so known on 1 July"
feature_table = pd.DataFrame([
    ("Growth_Rate", "panel", "Revenue growth of fiscal year Y", PANEL_DATE, "given"),
    ("Profit_Margin", "panel", "Profit margin of fiscal year Y (percent)", PANEL_DATE, "given"),
    ("ESG_Score, Environmental_Score, Social_Score, Governance_Score", "panel (point-in-time)", "Scores of fiscal year Y as first published", PANEL_DATE, "given"),
    ("Growth_Lag1", "panel", "Growth_Rate of fiscal year Y-1", PANEL_DATE, "given"),
    ("log_Revenue, log_Market_Cap", "panel (unit-corrected)", "Natural log of revenue and market cap, fiscal year Y", PANEL_DATE, "given"),
    ("Past12_Return_Pct", "returns", "Total return July Y to June Y+1 (the 12 months before formation)", RET_DATE, "given"),
    ("Industry and Region dummies", "panel", "One-hot encoding of fixed firm attributes", "Constant over time, known always", "given"),
    ("Env_Change", "panel", "Environmental_Score of Y minus that of Y-1 (ESG momentum)", PANEL_DATE, "NEW"),
    ("Margin_Change", "panel", "Profit_Margin of Y minus that of Y-1", PANEL_DATE, "NEW"),
    ("log_MC_to_Rev", "panel (unit-corrected)", "Log of market cap divided by revenue (valuation relative to sales)", PANEL_DATE, "NEW"),
    ("log_Carbon_Int", "panel (unit-corrected)", "Log of carbon emissions per USD million revenue; gaps filled with the median of the same fiscal year and industry", PANEL_DATE, "NEW"),
    ("Carbon_Missing", "panel", "1 if carbon, water and energy are missing in that row", PANEL_DATE, "NEW"),
    ("Past_Vol_Pct", "returns", "Standard deviation of the 12 monthly returns before formation", RET_DATE, "NEW"),
    ("Analyst_Outlook", "panel", "EXCLUDED: related to the next 12-month return (see audit)", "Not usable: carries future information", "excluded"),
], columns=["Feature", "Source", "Definition", "Known from", "Status"])
pd.set_option("display.max_colwidth", None)      # show the full text of the 'Known from' column
display(feature_table)
print(f"{len(ml_a):,} formation rows remain after requiring a full 12-month history for the two return-based features (the starter keeps the same number).")
''')

code(r'''
# ---- (a) Step 10: the audit table (one row per problem, numbers computed above) ----
# Diagnostic only: the test years are used here to measure the size of an effect, never to choose a model, a feature or a setting.
assert all(k in audit for k in ["unit", "dups", "leak", "surv", "restated", "missing", "bounds"]) and "model_data_a" in globals(), "Run the cells above first (Runtime > Run all)."
# two effects that need the model panel: linear-model test RMSE without the carbon features, and without rows that have a clipped score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
def linear_test_rmse(features, keep_train=None):
    tr, te = model_data_a[train_a], model_data_a[test_a]
    if keep_train is not None:
        tr = tr[keep_train(tr)]
    m = make_pipeline(StandardScaler(), LinearRegression()).fit(tr[features], tr["Hold_Return_Pct"])
    return float(np.sqrt(mean_squared_error(te["Hold_Return_Pct"], m.predict(te[features]))))
not_clipped = lambda d: ~d[["Environmental_Score", "Social_Score", "Governance_Score"]].isin([0, 100]).any(axis=1)
audit["missing"].update(rmse_full=linear_test_rmse(feature_cols_a), rmse_no_carbon=linear_test_rmse([f for f in feature_cols_a if f not in ("log_Carbon_Int", "Carbon_Missing")]))
audit["bounds"].update(rmse_noclip=linear_test_rmse(feature_cols_a, not_clipped), n_clip_train=int((~not_clipped(model_data_a[train_a])).sum()))
u, d, l, s, r, ms, bd = (audit[k] for k in ["unit", "dups", "leak", "surv", "restated", "missing", "bounds"])
audit_entries = [
    dict(issue="Wrong unit: revenue and market cap about 1,000 times too large for some firms", file="firm_year_panel.csv",
         detected_by="Carbon, water and energy scale with revenue within an industry; these firms sit about 1,000x below that relation",
         treatment="Divide Revenue and Market_Cap by 1,000 for every row of the flagged firms",
         affected_ids=[int(i) for i in unit_firms], affected_count=u["rows"],
         effect=f"Mean market cap {u['mc_before']:,.0f} -> {u['mc_after']:,.0f} USD million; share of the 100 largest firm-years held by these firms {u['top100_before']:.0%} -> {u['top100_after']:.0%}"),
    dict(issue="Near-duplicate monthly returns (two rows per company-month, values differ by at most 0.01)", file="stock_returns_monthly.csv",
         detected_by="Duplicate (Company_ID, Month) keys; no exact duplicates",
         treatment="Keep the first row per company-month",
         affected_ids=[], affected_count=d["keys"],
         effect=f"Firm-years with a full 12 holding months {d['full12_before']:,} -> {d['full12_after']:,} ({d['over12_before']} firm-years had 13 months and were dropped)"),
    dict(issue="Analyst_Outlook behaves as if stamped with future information (related to the next 12-month return)", file="firm_year_panel.csv",
         detected_by="Rank correlation with the return in three 12-month windows: only the next window is non-zero",
         treatment="Exclude from every model; listed in the feature table as excluded",
         affected_ids=[], affected_count=int(panel.shape[0]),
         effect=f"Rank correlation with the next 12-month return {l['rho_next']:.2f} (other windows {l['rho_before']:.2f}, {l['rho_before2']:.2f}); random forest test RMSE {l['rmse_without']:.2f} without vs {l['rmse_with']:.2f} with it (baseline {l['rmse_base']:.2f})"),
    dict(issue="Survivorship: universe_current.csv lists survivors only", file="universe_current.csv",
         detected_by=f"{s['universe']} firms in the file vs {s['firms']:,} in the panel; {s['exits']} firms have a last fiscal year before 2025",
         treatment="Build every sample and the benchmark on the full panel and hold exiting firms until their last month in the backtest (model fitting needs the full 12 months)",
         affected_ids=[], affected_count=s["exits"],
         effect=f"Equal-weight benchmark: {s['ret_full']:.2f}% a year on the full panel vs {s['ret_surv']:.2f}% on survivors only (Sharpe {s['sharpe_full']:.3f} vs {s['sharpe_surv']:.3f}); the model samples also drop {s['short_exit']} firm-years of exiting firms (fewer than 12 holding months), plus {s['censored_2025']} rows of formation year 2025 with only 6 months of returns"),
    dict(issue="Restated scores behave as if they contain hindsight (not point-in-time)", file="esg_scores_restated.csv",
         detected_by="Compared with the point-in-time scores; the changes correlate with later returns (inference: hindsight)",
         treatment="Use the point-in-time scores everywhere; use the restated file only for the comparison in task (c)",
         affected_ids=[], affected_count=r["firms_all_changed"],
         effect=f"{r['firms_all_changed']} firms have every score changed (mean {r['mean_abs_change']:.1f} points); within-year rank correlation of the Environmental score with the next excess return {r['rho_pit']:.3f} (point-in-time) vs {r['rho_rest']:.3f} (restated); {1 - r['top_decile_overlap']:.0%} of the top-decile names change"),
    dict(issue="Carbon, water and energy missing together, not at random", file="firm_year_panel.csv",
         detected_by="Missing share by region and by Environmental score",
         treatment="Keep all rows; carbon intensity filled with the industry-year median plus a missing flag; raw water and energy not used",
         affected_ids=[], affected_count=ms["rows"],
         effect=f"{ms['share']:.1%} of formation rows; Europe {ms['europe']:.1%} vs {ms['others_min']:.1%} to {ms['others_max']:.1%} elsewhere; mean Environmental score {ms['env_missing']:.1f} (missing) vs {ms['env_present']:.1f}; dropping the carbon features changes the linear test RMSE {ms['rmse_full']:.2f} -> {ms['rmse_no_carbon']:.2f}; dropping the rows with gaps would lose {ms['share']:.1%} of the sample and lift its mean Environmental score {ms['env_all']:.1f} -> {ms['env_present']:.1f}"),
    dict(issue="Values at the bounds: scores of exactly 0 or 100 (censoring) and monthly returns of exactly -95%", file="firm_year_panel.csv; stock_returns_monthly.csv",
         detected_by="Counts of values at the minimum and maximum, for all three score components and in the restated file",
         treatment="Kept and documented; cannot be told apart from real values",
         affected_ids=[], affected_count=bd["any_rows"] + bd["return_rows"],
         effect=f"Environmental {bd['env_rows']}, Social {bd['social_rows']}, Governance {bd['gov_rows']} scores at 0 or 100 ({bd['any_rows']} panel rows, {bd['any_rows'] / len(panel):.1%}, have at least one), {bd['return_rows']} returns at -95%; removing the {bd['n_clip_train']} training rows with a clipped score changes the linear test RMSE {ms['rmse_full']:.2f} -> {bd['rmse_noclip']:.2f}"),
]
audit_table = pd.DataFrame([{"Issue": e["issue"], "File": e["file"], "How detected": e["detected_by"], "Treatment": e["treatment"],
                             "Effect on one headline number": e["effect"]} for e in audit_entries])
pd.set_option("display.max_colwidth", None)
display(audit_table)
print("Each effect was measured one problem at a time, on the data as it stood before the other fixes, so the effects do not add up.")
''')

md(r'''
**Reading the result of task (a).** Seven problems were found and treated (table above). Three of them change numbers a reader would notice: the unit error moves the mean market cap from about 213,000 to about 14,000 USD million, the duplicated months silently removed 181 firm-years from the model data, and `Analyst_Outlook` would cut the test error from about 37.6 to 29.1 percentage points while carrying no information that was available on 1 July. Survivorship matters for any comparison: a test on survivors alone makes the equal-weight benchmark look about 0.6 percentage points a year (about 12%) better than it was over formation years 2015 to 2025 (about 0.46 points over the 2018 to 2024 backtest window of task d). The restated scores are only weakly related to later returns, but what the restatement added is related to them, so it behaves as if it contains hindsight, which is why task (c) compares both versions.
''')
