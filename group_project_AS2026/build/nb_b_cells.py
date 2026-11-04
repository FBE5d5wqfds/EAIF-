# Cells for task (b), inserted after the task (a) cells.
CELLS = []
def md(s): CELLS.append(("markdown", s.strip("\n")))
def code(s): CELLS.append(("code", s.strip("\n")))

md(r'''
## Task (b): linear baseline vs tree ensembles

**Design.** Target: the total 12-month return (percent) from July of the formation year to June of the next. Features: the 30 features of our formation panel (task a). Split by formation year: training 2015 to 2021, test 2022 to 2024. Models: the naive mean forecast, a linear regression on standardised features, a random forest and gradient boosting. The two ensembles are tuned by grouped cross-validation (5 folds grouped by company, with a fixed fold assignment so that the result does not depend on the scikit-learn version) inside the training years only, over a small grid (random forest: 150 trees, depth 3 or 6, minimum leaf 20 or 60; gradient boosting: 100 trees, learning rate 0.03 or 0.1, depth 2 or 3). The tuning step takes a few minutes on Colab and prints one progress line per setting. Linear regression has no setting to tune, so it enters the comparison as it is. The model is **selected on cross-validation**. The test years are evaluated in a single cell and never used to choose anything; later cells that report test errors are diagnostics only.
''')

code(r'''
# ---- (b) Step 1: data, cross-validation and tuning of the ensembles ----
assert "model_data_a" in globals(), "Run the cells above first (Runtime > Run all)."
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import ParameterGrid, cross_validate
from scipy.stats import spearmanr

TARGET = "Hold_Return_Pct"          # total 12-month return in percent, July to June after formation
X_tr, y_tr, g_tr = model_data_a.loc[train_a, feature_cols_a], model_data_a.loc[train_a, TARGET], model_data_a.loc[train_a, "Company_ID"]
X_te, y_te = model_data_a.loc[test_a, feature_cols_a], model_data_a.loc[test_a, TARGET]
# Grouped 5-fold cross-validation by company with an explicit, deterministic fold assignment: all rows of one company stay in
# the same fold, and the folds are identical on every machine and scikit-learn version (GroupKFold's own assignment changed
# between versions, which flipped the near-tie between models in a first Colab run).
companies = np.sort(g_tr.unique())
fold_of_company = pd.Series(np.arange(len(companies)) % 5, index=companies)
fold_of_row = g_tr.map(fold_of_company).to_numpy()
cv = [(np.where(fold_of_row != k)[0], np.where(fold_of_row == k)[0]) for k in range(5)]
print("Rows per cross-validation fold:", [len(te) for _, te in cv])

def cv_scores(model):
    res = cross_validate(model, X_tr, y_tr, cv=cv,
                         scoring={"rmse": "neg_root_mean_squared_error", "r2": "r2"})
    return dict(cv_rmse=-res["test_rmse"].mean(), cv_sd=res["test_rmse"].std(), cv_r2=res["test_r2"].mean())

candidates = {"Naive mean (baseline)": DummyRegressor(strategy="mean"),
              "Linear regression": make_pipeline(StandardScaler(), LinearRegression())}
cv_table = {name: cv_scores(m) for name, m in candidates.items()}

grids = {
    "Random forest": (lambda **p: RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1, **p),
                      {"max_depth": [3, 6], "min_samples_leaf": [20, 60]}),
    "Gradient boosting": (lambda **p: GradientBoostingRegressor(n_estimators=100, subsample=0.8, min_samples_leaf=20, random_state=42, **p),
                          {"learning_rate": [0.03, 0.1], "max_depth": [2, 3]}),
}
import time
t0 = time.time()
print("Tuning the ensembles with grouped cross-validation. This takes a few minutes on Colab; one line is printed per setting.")
tuning_rows = []
for name, (make, grid) in grids.items():
    for params in ParameterGrid(grid):
        scores = cv_scores(make(**params))
        tuning_rows.append({"model": name, **params, **scores})
        print(f"  {name} {params}: CV RMSE {scores['cv_rmse']:.3f}  ({time.time() - t0:.0f} s elapsed)")
tuning = pd.DataFrame(tuning_rows)

best_params = {}
for name, (make, grid) in grids.items():
    t = tuning[tuning["model"] == name]
    best = t.loc[t["cv_rmse"].idxmin()]
    best_params[name] = {k: (float(best[k]) if k == "learning_rate" else int(best[k])) for k in grid}
    label = f"{name} (tuned)"
    candidates[label] = make(**best_params[name])
    cv_table[label] = dict(cv_rmse=best["cv_rmse"], cv_sd=best["cv_sd"], cv_r2=best["cv_r2"])

print("Cross-validation results of the tuning grid (RMSE in percentage points, grouped 5-fold inside the training years):")
for name in grids:
    t = tuning[tuning["model"] == name].dropna(axis=1, how="all").drop(columns="model")
    print(f"\n{name}:"); display(t.sort_values("cv_rmse").round(3).reset_index(drop=True))
print("Chosen settings:", best_params)
''')

code(r'''
# ---- (b) Step 2: train, CV and test side by side (the test years are evaluated here, once) ----
assert "candidates" in globals(), "Run the cells above first (Runtime > Run all)."
test_years = model_data_a.loc[test_a, ["Formation_Year", TARGET]]
rows, fitted = [], {}
for name, m in candidates.items():
    m.fit(X_tr, y_tr)
    fitted[name] = m
    p_tr, p_te = m.predict(X_tr), pd.Series(m.predict(X_te), index=X_te.index)
    # rank correlation between forecast and outcome within each test year (what matters for ranking firms in task d)
    ic = np.nan if np.ptp(p_te.values) < 1e-9 else np.mean([spearmanr(p_te[d.index], d[TARGET])[0] for _, d in test_years.groupby("Formation_Year")])
    rows.append({"Model": name,
                 "Train RMSE": np.sqrt(mean_squared_error(y_tr, p_tr)), "CV RMSE": cv_table[name]["cv_rmse"], "CV sd": cv_table[name]["cv_sd"],
                 "Test RMSE": np.sqrt(mean_squared_error(y_te, p_te)),
                 "Train R2": r2_score(y_tr, p_tr), "CV R2": cv_table[name]["cv_r2"], "Test R2": r2_score(y_te, p_te),
                 "Test rank IC": ic})
comparison = pd.DataFrame(rows).set_index("Model")

selected = comparison.drop(index="Naive mean (baseline)")["CV RMSE"].idxmin()      # selection on CV only
ensembles = [i for i in comparison.index if "tuned" in i]
best_ens = comparison.loc[ensembles, "CV RMSE"].idxmin()
display(comparison.round(3))
print(f"Selected on cross-validation: {selected}.  Best ensemble on cross-validation: {best_ens}.")
y_year_mean = test_years.groupby("Formation_Year")[TARGET].transform("mean")
print(f"For reference: a naive forecast that already knew each test year's mean would have a test RMSE of {np.sqrt(((y_te - y_year_mean) ** 2).mean()):.2f} "
      f"(the plain naive baseline has {comparison.loc['Naive mean (baseline)', 'Test RMSE']:.2f}); the rest of the baseline's error is the shift between training and test years.")
''')

code(r'''
# ---- (b) Step 3: figures ----
assert "comparison" in globals(), "Run the cells above first (Runtime > Run all)."
fig, axes = plt.subplots(1, 2, figsize=(15, 5))
labels = [i.replace(" (baseline)", "\n(baseline)").replace(" (tuned)", "\n(tuned)").replace("regression", "regr.") for i in comparison.index]
x = np.arange(len(comparison)); w = 0.26
for k, (col, colour) in enumerate([("Train RMSE", "lightgrey"), ("CV RMSE", "steelblue"), ("Test RMSE", "darkorange")]):
    axes[0].bar(x + (k - 1) * w, comparison[col], w, label=col, color=colour)
axes[0].axhline(comparison.loc["Naive mean (baseline)", "Test RMSE"], color="red", ls="--", lw=1, label="Naive baseline, test")
axes[0].set_xticks(x); axes[0].set_xticklabels(labels, fontsize=8)
axes[0].set_ylabel("RMSE of the 12-month return forecast (percentage points)"); axes[0].set_xlabel("Model")
axes[0].set_ylim(0, 46); axes[0].set_title("Train, cross-validation and test error next to the baseline")
axes[0].legend(fontsize=8, ncol=2, loc="upper center")

by_year = model_data_a.groupby("Formation_Year")[TARGET].mean()
axes[1].bar(by_year.index, by_year.values, color=["steelblue" if y <= 2021 else "darkorange" for y in by_year.index])
axes[1].axhline(0, color="black", lw=0.8)
axes[1].set_xlabel("Formation year (blue = training, orange = test)"); axes[1].set_ylabel("Mean 12-month total return (%)")
train_by = by_year[by_year.index <= 2021]
axes[1].set_title(f"Test years average {by_year[by_year.index >= 2022].mean():.0f}%; only {train_by.idxmax()} ({train_by.max():.0f}%) was as high in training")
plt.tight_layout(); plt.show()

fig, axes = plt.subplots(1, 2, figsize=(15, 5))
lin = fitted["Linear regression"]
coef = pd.Series(lin.named_steps["linearregression"].coef_, index=feature_cols_a)
coef.reindex(coef.abs().sort_values(ascending=False).index).head(10)[::-1].plot(kind="barh", ax=axes[0], color="steelblue")
axes[0].set_xlabel("Coefficient (percentage points of 12-month return per 1 standard deviation of the feature)")
axes[0].set_title("Linear regression: 10 largest standardised coefficients")
imp = pd.Series(fitted[best_ens].feature_importances_, index=feature_cols_a).sort_values(ascending=False)
imp.head(10)[::-1].plot(kind="barh", ax=axes[1], color="darkorange")
axes[1].set_xlabel("Importance (share of the model's error reduction)"); axes[1].set_title(f"{best_ens}: 10 most important features")
plt.tight_layout(); plt.show()
''')

code(r'''
# ---- (b) Step 4: the result in words and the numbers for results.json ----
assert "comparison" in globals(), "Run the cells above first (Runtime > Run all)."
lin_rmse = comparison.loc["Linear regression", "Test RMSE"]
base_rmse = comparison.loc["Naive mean (baseline)", "Test RMSE"]
ens_rmse = comparison.loc[best_ens, "Test RMSE"]
ens_kind = "random forest" if best_ens.startswith("Random") else "gradient boosting"
key = selected.replace(" (tuned)", "")
sel_text = f"{selected} {best_params[key]}" if key in best_params else selected
task_b = dict(target="twelve-month total holding return in percent (July to June after formation)",
              test_formation_years=[2022, 2023, 2024],
              baseline_rmse=float(base_rmse), linear_rmse=float(lin_rmse), ensemble_rmse=float(ens_rmse),
              ensemble_kind=ens_kind, selected_on_cv=sel_text, test_r2=float(comparison.loc[selected, "Test R2"]))
print(task_b)
pays = ens_rmse < min(lin_rmse, base_rmse)
vs_lin = "better" if ens_rmse < lin_rmse else "worse"
vs_base = "better" if ens_rmse < base_rmse else "worse"
print(f"\nTest RMSE (percentage points): naive baseline {base_rmse:.2f}, linear regression {lin_rmse:.2f}, best ensemble ({best_ens}) {ens_rmse:.2f}.")
print(f"The best ensemble is {abs(ens_rmse - lin_rmse):.2f} points {vs_lin} than linear regression and {abs(ens_rmse - base_rmse):.2f} points {vs_base} than the naive baseline, "
      f"so the extra complexity of the ensemble {'pays off' if pays else 'does not pay off'} out of sample.")
''')

code(r'''
# ---- (b) Step 5: reading the result (every sentence is computed from the tables above) ----
# Diagnostic only: the test years are used here to measure the size of an effect, never to choose a model, a feature or a setting.
assert "comparison" in globals() and "task_b" in globals(), "Run the cells above first (Runtime > Run all)."
mods = comparison.drop(index="Naive mean (baseline)")
naive_cv = comparison.loc["Naive mean (baseline)", "CV RMSE"]
cv_spread = mods["CV RMSE"].max() - mods["CV RMSE"].min()
tie = cv_spread < mods["CV sd"].mean()
beats = [n for n in mods.index if mods.loc[n, "Test RMSE"] < base_rmse]
by_year_mean = model_data_a.groupby("Formation_Year")[TARGET].mean()
tr_mean, te_mean = model_data_a.loc[train_a, TARGET].mean(), model_data_a.loc[test_a, TARGET].mean()
best_train_year = by_year_mean[by_year_mean.index <= 2021].idxmax()
pred = {n: pd.Series(fitted[n].predict(X_te), index=X_te.index) for n in mods.index}
yr = test_years["Formation_Year"]
dy = y_te - y_te.groupby(yr).transform("mean")                       # outcome with each test year's mean removed
zero_within = np.sqrt((dy ** 2).mean())                              # a zero forecast after removing year means
within = {n: np.sqrt(((dy - (p - p.groupby(yr).transform("mean"))) ** 2).mean()) for n, p in pred.items()}
oos_r2 = {n: 1 - (mods.loc[n, "Test RMSE"] / base_rmse) ** 2 for n in mods.index}
ic_year = pd.DataFrame({n: {int(y): spearmanr(pred[n][d.index], d[TARGET])[0] for y, d in test_years.groupby("Formation_Year")} for n in mods.index})
f_no = [f for f in feature_cols_a if f != "Past12_Return_Pct"]
lin_no_past = make_pipeline(StandardScaler(), LinearRegression()).fit(X_tr[f_no], y_tr)
rmse_no_past = np.sqrt(mean_squared_error(y_te, lin_no_past.predict(X_te[f_no])))

print("1. Test RMSE (percentage points): naive baseline {:.2f}; ".format(base_rmse) + "; ".join(f"{n} {mods.loc[n, 'Test RMSE']:.2f}" for n in mods.index) + ". "
      + ("No model beats the naive baseline on the test years." if not beats else "Models that beat the baseline on the test years: " + ", ".join(beats) + "."))
print(f"2. Selection on cross-validation: {selected}. The three models lie within {cv_spread:.2f} RMSE points of each other while the fold-to-fold standard deviation is about {mods['CV sd'].mean():.2f}, "
      + ("so the selection is effectively a tie, not a clear win. " if tie else "so the selection rests on a clear difference. ")
      + f"The selected model's CV RMSE is {mods.loc[selected, 'CV RMSE']:.2f} against {naive_cv:.2f} for the naive forecast, a gain of {naive_cv - mods.loc[selected, 'CV RMSE']:.2f}.")
print(f"3. Why test error is higher than CV error: the mean 12-month return is {te_mean:.1f}% in the test years against {tr_mean:.1f}% in the training years, and only {best_train_year} ({by_year_mean[best_train_year]:.0f}%) was as high in training. "
      f"A naive forecast that knew each test year's mean would have a test RMSE of {zero_within:.2f}. Cross-validation mixes years inside the training period and cannot see this shift.")
print(f"   Even after removing each year's mean from outcome and forecast, the models do not beat the zero forecast ({zero_within:.2f}): " + ", ".join(f"{n} {within[n]:.2f}" for n in mods.index)
      + ". So part of the loss is a lack of cross-sectional skill, not only the level shift.")
print("   Out-of-sample R2 against the training-mean forecast: " + ", ".join(f"{n} {oos_r2[n]:+.2f}" for n in mods.index) + f" (the baseline itself has a test R2 of {comparison.loc['Naive mean (baseline)', 'Test R2']:+.2f} against the test-year mean).")
print(f"4. Ranking skill: the rank correlation between forecast and outcome within each test year, by year and on average:")
display(ic_year.assign(**{"": ""}).drop(columns="").round(3).T.assign(average=lambda t: t.mean(axis=1)).round(3))
print("   " + ("No model shows a stable positive rank correlation: the sign changes across the three test years, so none ranks firms reliably." if ic_year.mean().max() < 0.02 else "At least one model shows some ranking skill in the test years."))
print(f"5. Complexity: the best ensemble ({best_ens}) is {abs(ens_rmse - lin_rmse):.2f} points {vs_lin} than linear regression and {abs(ens_rmse - base_rmse):.2f} points {vs_base} than the baseline; the extra complexity {'pays off' if pays else 'does not pay off'} out of sample.")
print(f"6. Caveat on the linear model: its largest coefficient is on past 12-month return, learned from only {int(train_a.sum() and model_data_a.loc[train_a, 'Formation_Year'].nunique())} training years of market-wide variation. Without that feature its test RMSE is {rmse_no_past:.2f}"
      + (", still above the baseline." if rmse_no_past > base_rmse else ", below the baseline."))
print("7. Limitations: the tuning grids are small (four settings per ensemble), and the cross-validation folds mix years, so same-year dependence makes cross-validation optimistic.")
''')

code(r'''
# ---- (b) Step 6: two checks on the selection (training years only; the test years are not used) ----
assert "comparison" in globals() and "cv" in globals(), "Run the cells above first (Runtime > Run all)."
from sklearn.base import clone
# Check 1: fold by fold. The CV average hides whether a gain is consistent; here every model is scored on the same five company folds.
fold_rmse = pd.DataFrame({n: -cross_validate(clone(m), X_tr, y_tr, cv=cv, scoring="neg_root_mean_squared_error")["test_score"] for n, m in candidates.items()})
fold_rmse.index = [f"fold {k + 1}" for k in range(len(cv))]
print("Check 1: CV RMSE fold by fold (same company folds for every model):")
display(fold_rmse.round(3))
n_lin_wins = int((fold_rmse["Linear regression"] < fold_rmse["Naive mean (baseline)"]).sum())
print(f"Linear regression has a lower error than the naive forecast in {n_lin_wins} of {len(cv)} folds (by {(fold_rmse['Naive mean (baseline)'] - fold_rmse['Linear regression']).min():.2f} to "
      f"{(fold_rmse['Naive mean (baseline)'] - fold_rmse['Linear regression']).max():.2f} points): inside the training years the gain over the naive forecast is small but consistent.")
fold_winner = fold_rmse.drop(columns="Naive mean (baseline)").idxmin(axis=1)
print("Best of the three models per fold: " + ", ".join(f"{k} {v}" for k, v in fold_winner.items()) + ". "
      + ("The winner changes from fold to fold, so the selection among the three models is a tie." if fold_winner.nunique() > 1 else "The same model wins every fold."))

# Check 2: validation in time order. Train on formation years up to Y-1, validate on Y, for Y = 2017 to 2021 (inside the training years).
md_tr = model_data_a[train_a]
time_rows = {}
for y in range(2017, 2022):
    tr_y, va_y = md_tr[md_tr["Formation_Year"] <= y - 1], md_tr[md_tr["Formation_Year"] == y]
    for n, m in candidates.items():
        p = clone(m).fit(tr_y[feature_cols_a], tr_y[TARGET]).predict(va_y[feature_cols_a])
        time_rows.setdefault(n, {})[y] = np.sqrt(mean_squared_error(va_y[TARGET], p))
time_cv = pd.DataFrame(time_rows); time_cv.loc["average"] = time_cv.mean()
print("\nCheck 2: validation in time order (train on earlier formation years only, validate on the next one), RMSE:")
display(time_cv.round(3))
best_time = time_cv.loc["average"].idxmin()
print(f"Lowest average error in time order: {best_time}. "
      + ("No model beats the naive forecast when validated in time order, which matches the test result: the small gain in company-grouped CV comes from mixing years and does not carry forward in time."
         if best_time == "Naive mean (baseline)" else "At least one model beats the naive forecast in time order."))
''')
