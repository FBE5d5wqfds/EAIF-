"""Shared helpers for the Swiss health-insurance case notebooks (L1-L3).

The Lecture 1 notebooks write every step out in full. Later notebooks import the same steps from
this file so that they can focus on new ideas. Read the functions: nothing here is hidden magic.
"""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"


def load(table: str) -> pd.DataFrame:
    """Read one table of the case study (Parquet files in ./data)."""
    return pd.read_parquet(DATA / f"{table}.parquet")


# ------------------------------------------------------------------------------------------------
# Regression panel: one row per person and year t, target = gross OKP cost in year t+1
# ------------------------------------------------------------------------------------------------
CAT_REG = ["sex", "canton", "premium_region", "municipality_type", "language", "employment",
           "okp_insurer_next", "okp_model_next", "deductible_next", "accident_cover_next", "age_class_next"]
NUM_REG = ["age_next", "household_size", "income_band", "has_amb", "has_hosp_semi_priv", "n_vvg_reservations",
           "ra_hospital_prev_year_gt3_nights", "ra_pharma_cost_group", "log_cost_t", "log_cost_t1",
           "log_cost_t2", "n_gp_visits", "n_specialist_visits", "n_inpatient_stays", "inpatient_days",
           "n_accidents", "zero_cost_t"]


def build_regression_panel(py: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return one row per (person, year t) with features known at the end of year t and the
    target `cost_next` = gross OKP cost in year t+1 (CHF), plus `exposure_next` in years."""
    if py is None:
        py = load("person_years")
    py = py.sort_values(["person_id", "year"]).copy()
    g = py.groupby("person_id")
    py["log_cost_t"] = np.log1p(py["okp_gross_cost"])
    py["log_cost_t1"] = np.log1p(g["okp_gross_cost"].shift(1)).fillna(-1.0)   # -1 marks "no history"
    py["log_cost_t2"] = np.log1p(g["okp_gross_cost"].shift(2)).fillna(-1.0)
    py["zero_cost_t"] = (py["okp_gross_cost"] == 0).astype(int)
    py["has_hosp_semi_priv"] = (py["has_hosp_semi"] | py["has_hosp_priv"]).astype(int)
    py["has_amb"] = py["has_amb"].astype(int)
    # next-year contract (chosen at renewal, so known when the price is set) and next-year outcome
    nxt = py[["person_id", "year", "age", "age_class", "okp_insurer", "okp_model", "deductible",
              "accident_cover", "okp_gross_cost", "insured_days"]].copy()
    nxt["year"] -= 1
    nxt = nxt.rename(columns={"age": "age_next", "age_class": "age_class_next", "okp_insurer": "okp_insurer_next",
                              "okp_model": "okp_model_next", "deductible": "deductible_next",
                              "accident_cover": "accident_cover_next", "okp_gross_cost": "cost_next",
                              "insured_days": "days_next"})
    df = py.merge(nxt, on=["person_id", "year"], how="inner")
    df = df[(df["insured_days"] >= 360)].copy()            # a full year of history in year t
    df["exposure_next"] = df["days_next"] / 365.0
    df["accident_cover_next"] = df["accident_cover_next"].astype(str)
    df["deductible_next"] = df["deductible_next"].astype(str)
    df["premium_region"] = df["premium_region"].astype(str)
    return df.reset_index(drop=True)


# ------------------------------------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------------------------------------
def tweedie_deviance(y, mu, p=1.5, w=None):
    """Mean Tweedie deviance (power p in (1,2)); lower is better. y, mu in the same unit."""
    y, mu = np.asarray(y, float), np.clip(np.asarray(mu, float), 1e-8, None)
    d = 2 * (np.power(np.maximum(y, 0), 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p)
             + np.power(mu, 2 - p) / (2 - p))
    return float(np.average(d, weights=w))


def gini(y, pred, w=None):
    """Normalised Gini of an ordering: how well `pred` ranks the actual costs `y` (1 = perfect)."""
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    w = np.ones_like(y) if w is None else np.asarray(w, float)

    def _g(order_by):
        o = np.argsort(-order_by, kind="mergesort")
        cw, cy = np.cumsum(w[o]) / w.sum(), np.cumsum((y * w)[o]) / (y * w).sum()
        return float(np.trapezoid(cy, cw) - 0.5)
    return _g(pred) / _g(y)


def lorenz_curve(y, pred):
    o = np.argsort(-np.asarray(pred), kind="mergesort")
    share_people = np.arange(1, len(o) + 1) / len(o)
    share_cost = np.cumsum(np.asarray(y)[o]) / np.sum(y)
    return share_people, share_cost


# ------------------------------------------------------------------------------------------------
# OKP tariff helpers (used by the classification and agent notebooks)
# ------------------------------------------------------------------------------------------------
FR_ADULT = [300, 500, 1000, 1500, 2000, 2500]
FR_CHILD = [0, 100, 200, 300, 400, 500, 600]


def deductible_rebate(fr: int, age_class: str, rebate_share: float) -> float:
    """Monthly rebate (CHF) granted for a deductible above the minimum. Swiss law caps it at 70% of
    the extra risk taken; each insurer grants a share `rebate_share` of that maximum."""
    base = 0 if age_class == "child" else 300
    return 0.70 * (fr - base) / 12.0 * rebate_share


def okp_premium(tariffs, rules, year, insurer, canton, region, age_class, deductible, model, accident=True):
    """Monthly OKP premium for one cover, rebuilt from the published tariff tables."""
    t = tariffs[(tariffs.year == year) & (tariffs.insurer == insurer) & (tariffs.canton == canton)
                & (tariffs.premium_region == region) & (tariffs.age_class == age_class)]
    if t.empty:
        raise ValueError("no tariff for this cell")
    r = rules.set_index("insurer").loc[insurer]
    base = float(t["premium_standard_lowest_deductible"].iloc[0])
    p = base * float(r[f"model_factor_{model}"])
    if not accident:
        p *= float(r["accident_excluded_factor"])
    rebate = deductible_rebate(int(deductible), age_class, float(r["deductible_rebate_share_of_max"]))
    return round(max(p - rebate, 0.5 * p), 2)          # the rebate may never exceed half the premium


INSURER_CODES = ["ARV", "BRQ", "LEM", "NRW", "SOR", "TLW", "UST", "VIR"]


def quote_all_insurers(frame: pd.DataFrame, tariffs: pd.DataFrame, rules: pd.DataFrame, year_col="year",
                       age_class_col="age_class", deductible_col="deductible", model_col="okp_model",
                       accident_col="accident_cover") -> pd.DataFrame:
    """Vectorised version of `okp_premium`: the monthly premium that EVERY insurer charges for the
    cover described in each row of `frame`. Returns one column per insurer code, same index as frame."""
    out = pd.DataFrame(index=frame.index)
    rr = rules.set_index("insurer")
    key = frame[[year_col, "canton", "premium_region", age_class_col]].copy()
    key.columns = ["year", "canton", "premium_region", "age_class"]
    key["premium_region"] = key["premium_region"].astype(int)
    for ins in INSURER_CODES:
        t = tariffs[tariffs.insurer == ins].drop(columns="insurer")
        base = key.merge(t, on=["year", "canton", "premium_region", "age_class"], how="left")[
            "premium_standard_lowest_deductible"].to_numpy()
        mf = frame[model_col].map(lambda m: rr.loc[ins, f"model_factor_{m}"]).to_numpy(float)
        af = np.where(frame[accident_col].astype(str) == "True", 1.0, rr.loc[ins, "accident_excluded_factor"])
        p = base * mf * af
        fr = frame[deductible_col].astype(int).to_numpy()
        child = (key["age_class"] == "child").to_numpy()
        reb = 0.70 * np.where(child, fr, np.maximum(fr, 300) - 300) / 12 * rr.loc[ins, "deductible_rebate_share_of_max"]
        out[ins] = np.round(np.maximum(p - reb, 0.5 * p), 2)
    return out


# ------------------------------------------------------------------------------------------------
# Switching panel: one row per household and renewal (decision in November t for 1 January t+1)
# ------------------------------------------------------------------------------------------------
def _household_rows(cur: pd.DataFrame, T: pd.DataFrame, R: pd.DataFrame) -> pd.DataFrame:
    """`cur` holds one row per person insured in year t (cover of year t) with columns
    year, year_next, age_class, age_class_next. Returns household-level price and tie features."""
    cur = cur.copy()
    q_now = quote_all_insurers(cur, T, R)
    q_next = quote_all_insurers(cur, T, R, year_col="year_next", age_class_col="age_class_next")
    for k in INSURER_CODES:
        cur[f"q_{k}"] = 12 * q_next[k]
    pos = cur["okp_insurer"].map({k: i for i, k in enumerate(INSURER_CODES)}).to_numpy()
    cur["own_now"] = 12 * q_now.to_numpy()[np.arange(len(cur)), pos]
    cur["hosp_tie"] = ((cur["has_hosp_semi"] | cur["has_hosp_priv"] | cur["has_hosp_gen"])
                       & (cur["vvg_insurer"] == cur["okp_insurer"])).astype(int)
    cur["any_vvg_tie"] = ((cur["vvg_products"].fillna("") != "") & (cur["vvg_insurer"] == cur["okp_insurer"])).astype(int)
    cur["chronic"] = (cur["ra_pharma_cost_group"] > 0).astype(int)
    agg = {f"q_{k}": "sum" for k in INSURER_CODES}
    agg.update(own_now="sum", hosp_tie="max", any_vvg_tie="max", chronic="max", age="max", person_id="size",
               okp_insurer="first", canton="first", language="first", income_band="first", premium_region="first",
               municipality_type="first", deductible="mean", okp_gross_cost="sum")
    cur = cur.sort_values(["household_id", "age"], ascending=[True, False])     # oldest member first = head
    h = cur.groupby(["household_id", "year"]).agg(agg).reset_index()
    h = h.rename(columns={"age": "age_head", "person_id": "n_members", "okp_gross_cost": "hh_cost_t",
                          "deductible": "mean_deductible"})
    qcols = [f"q_{k}" for k in INSURER_CODES]
    pos = h["okp_insurer"].map({k: i for i, k in enumerate(INSURER_CODES)}).to_numpy()
    h["own_next"] = h[qcols].to_numpy()[np.arange(len(h)), pos]
    h["own_increase"] = h["own_next"] / h["own_now"] - 1                  # what the household sees in its letter
    h["savings"] = 1 - h[qcols].min(axis=1) / h["own_next"]                # share it could save by switching
    h["cheapest"] = h[qcols].idxmin(axis=1).str[2:]
    h["own_rank"] = h[qcols].rank(axis=1).to_numpy()[np.arange(len(h)), pos]
    # market-wide increase in the canton (mean over insurers, same households)
    h["mkt_increase"] = h.groupby(["canton", "year"])["own_increase"].transform("mean")
    h["log_hh_cost_t"] = np.log1p(h["hh_cost_t"])
    return h


def build_switching_panel():
    """Households x renewals 2015..2026 (label from person_years) and the live renewal 2027."""
    py = load("person_years").sort_values(["person_id", "year"])
    T, R = load("tariffs_okp"), load("tariff_rules")
    g = py.groupby("person_id")
    py["ins_next"], py["year_n"] = g["okp_insurer"].shift(-1), g["year"].shift(-1)
    py["age_class_next"] = g["age_class"].shift(-1)
    hist = py[(py["year_n"] == py["year"] + 1) & (py["year"] <= 2025)].copy()
    hist["year_next"] = hist["year"] + 1
    hist["moved"] = (hist["ins_next"] != hist["okp_insurer"]).astype(int)
    H = _household_rows(hist, T, R)
    lab = hist.groupby(["household_id", "year"])["moved"].mean().rename("frac_moved")
    H = H.join(lab, on=["household_id", "year"])
    H["switched"] = (H["frac_moved"] >= 0.5).astype(int)
    # live renewal 2027: cover of 2026 + labels from renewal_2027
    ren = load("renewal_2027")
    cur = py[(py["year"] == 2026) & py["person_id"].isin(ren["person_id"])].copy()
    cur["year_next"] = 2027
    cur["age_class_next"] = np.select([cur["age"] + 1 <= 18, cur["age"] + 1 <= 25], ["child", "young_adult"], "adult")
    L = _household_rows(cur, T, R)
    lab = ren.groupby("household_id")["label_switched_okp_insurer"].mean().rename("frac_moved")
    L = L.join(lab, on="household_id")
    L["switched"] = (L["frac_moved"] >= 0.5).astype(int)
    return H.drop(columns="frac_moved"), L.drop(columns="frac_moved")


# ------------------------------------------------------------------------------------------------
# Forecast rows: the same features as the regression panel, for everyone who renews into `year`+1
# ------------------------------------------------------------------------------------------------
def build_forecast_rows(year: int = 2026) -> pd.DataFrame:
    """One row per person insured at the renewal into `year`+1 (people in `renewal_2027` for 2026),
    with the features of `build_regression_panel` computed at the end of `year`. The contract for
    `year`+1 is assumed unchanged (same insurer, model, deductible, accident cover)."""
    py = load("person_years").sort_values(["person_id", "year"]).copy()
    g = py.groupby("person_id")
    py["log_cost_t"] = np.log1p(py["okp_gross_cost"])
    py["log_cost_t1"] = np.log1p(g["okp_gross_cost"].shift(1)).fillna(-1.0)
    py["log_cost_t2"] = np.log1p(g["okp_gross_cost"].shift(2)).fillna(-1.0)
    py["zero_cost_t"] = (py["okp_gross_cost"] == 0).astype(int)
    py["has_hosp_semi_priv"] = (py["has_hosp_semi"] | py["has_hosp_priv"]).astype(int)
    py["has_amb"] = py["has_amb"].astype(int)
    keep = load("renewal_2027").person_id if year == 2026 else py[py.year == year + 1].person_id
    f = py[(py.year == year) & py.person_id.isin(keep)].copy()
    f["age_next"] = f["age"] + 1
    f["age_class_next"] = np.select([f.age_next <= 18, f.age_next <= 25], ["child", "young_adult"], "adult")
    f["okp_insurer_next"], f["okp_model_next"] = f["okp_insurer"], f["okp_model"]
    f["deductible_next"] = f["deductible"].astype(str)
    f["accident_cover_next"] = f["accident_cover"].astype(str)
    f["premium_region"] = f["premium_region"].astype(str)
    return f.reset_index(drop=True)


# ------------------------------------------------------------------------------------------------
# Monthly cost series (Lecture 2, Practical 3: forecasting with a pretrained foundation model)
# ------------------------------------------------------------------------------------------------
CARE_TYPES_TS = ["gp_visit", "specialist_visit", "outpatient_hospital", "inpatient_stay", "medication",
                 "nursing_home_care", "physiotherapy", "psychotherapy"]


def monthly_cost_series() -> pd.DataFrame:
    """Monthly basic-insurance (OKP) gross cost per insured person and month, in CHF, 2014-01 … 2026-12.
    Returns a long table: series_id, group, month (Timestamp, first day), value.
    Series: the whole portfolio, 8 care types, 26 cantons and 8 insurers (43 series).
    Exposure: insured person-months, i.e. the insured person-years of the calendar year spread evenly
    over its months (the BAG reports the same quantity: CHF 391 per insured and month in 2024)."""
    ev = load("events")[["person_id", "date", "year", "care_type", "okp_gross", "insurer_okp"]]
    ev = ev[ev.okp_gross > 0].copy()
    ev["month"] = pd.to_datetime(ev["date"]).dt.to_period("M").dt.to_timestamp()
    py = load("person_years")[["person_id", "year", "canton", "okp_insurer", "insured_days"]]
    ev = ev.merge(py[["person_id", "year", "canton"]], on=["person_id", "year"], how="left")
    months = pd.date_range("2014-01-01", "2026-12-01", freq="MS")
    frac = pd.Series(months.days_in_month / np.where(months.is_leap_year, 366, 365), index=months)

    def per_insured(cost, expo_year, sid, group):
        # cost: Series indexed by month; expo_year: Series indexed by year (person-years)
        expo = expo_year.reindex(months.year).values * frac.values * 12      # person-months
        v = cost.reindex(months, fill_value=0.0).values / expo
        return pd.DataFrame({"series_id": sid, "group": group, "month": months, "value": v})

    out = []
    expo_all = py.groupby("year").insured_days.sum() / 365.0
    out.append(per_insured(ev.groupby("month").okp_gross.sum(), expo_all, "total", "portfolio"))
    for c in CARE_TYPES_TS:
        out.append(per_insured(ev[ev.care_type == c].groupby("month").okp_gross.sum(), expo_all, f"care:{c}", "care type"))
    for k, gcol, ecol in [("canton", "canton", "canton"), ("insurer", "insurer_okp", "okp_insurer")]:
        expo_g = py.groupby([ecol, "year"]).insured_days.sum() / 365.0
        for g in sorted(py[ecol].unique()):
            out.append(per_insured(ev[ev[gcol] == g].groupby("month").okp_gross.sum(), expo_g.loc[g], f"{k}:{g}", k))
    return pd.concat(out, ignore_index=True)


def individual_monthly_series(person_ids, last_month="2025-12") -> pd.DataFrame:
    """Monthly OKP gross cost (CHF) of each person from 2014-01 to `last_month`.
    Months of calendar years in which the person was not insured are NaN (before entry, for example)."""
    ids = pd.Index(np.unique(person_ids))
    months = pd.date_range("2014-01-01", pd.Period(last_month).to_timestamp(), freq="MS")
    ev = load("events")[["person_id", "date", "okp_gross"]]
    ev = ev[ev.person_id.isin(ids) & (ev.okp_gross > 0)].copy()
    ev["month"] = pd.to_datetime(ev["date"]).dt.to_period("M").dt.to_timestamp()
    m = ev.groupby(["person_id", "month"]).okp_gross.sum().unstack().reindex(index=ids, columns=months).fillna(0.0)
    py = load("person_years")[["person_id", "year"]]
    insured = py[py.person_id.isin(ids)].assign(on=1).pivot_table(index="person_id", columns="year", values="on").reindex(ids)
    mask = insured.reindex(columns=months.year).values == 1
    m = m.where(mask)
    m.columns.name = "month"
    m.index.name = "person_id"
    return m
