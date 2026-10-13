"""Synthetic daily step counts for the case study's step-bonus programme ("Move+", fictional).

Participants: people aged 20-79 who held supplementary outpatient cover (AMB) in 2023, observed from
1 January 2023 until they leave the portfolio or until 31 December 2026.

Each person's series is built from documented mechanisms, so that the course can show WHICH model
families can learn WHICH structure:
  * person-level level  : age, sex, chronic conditions, latent frailty, a random person effect
  * calendar            : person-specific weekday/weekend pattern, seasonality (summer high)
  * slow drift          : AR(1) fluctuation of the personal level (weeks to months)
  * holidays            : 1-3 per year, 5-21 days, abrupt change up or down
  * device not worn     : runs of zero days
  * accidents           : drop and recovery after injuries and fractures (dates from events)
  * short illnesses     : a few days of low activity followed by a FULL recovery (not predictive)
  * hospital stays      : near zero during the stay, recovery afterwards, and - for many stays -
                          warning signs BEFORE admission: one to three "flare-ups" (a sharp drop
                          for a few days followed by a SLOW and INCOMPLETE recovery), at times that
                          vary from 3 weeks to several months before admission.
The pre-admission decline is inspired by studies that detect illness from deviations of wearable
signals from a person's own baseline (e.g. Radin et al., 2020, Lancet Digital Health; Mishra et al.,
2020, Nature Biomedical Engineering).

usage: python generate_activity.py --data <folder with persons/person_years/events parquet> --seed 2026
"""
import argparse, math
from pathlib import Path
import numpy as np
import pandas as pd

START, END = pd.Timestamp("2023-01-01"), pd.Timestamp("2026-12-31")
NDAYS = (END - START).days + 1

# prodrome by reason for admission: (probability, min length, max length, min depth, max depth)
PRODROME = {"musculoskeletal": (.85, 45, 150, .3, .6), "orthopaedic": (.85, 45, 150, .3, .6), "surgery_elective": (.7, 30, 120, .25, .5),
            "cardiovascular": (.85, 30, 100, .3, .6), "respiratory": (.85, 30, 90, .3, .6), "diabetes": (.8, 30, 100, .25, .55),
            "cancer": (.9, 45, 120, .35, .7), "mental": (.75, 30, 90, .3, .6), "dementia": (.85, 45, 120, .3, .6),
            "digestive": (.7, 21, 75, .25, .55), "cardiac_acute": (.6, 14, 45, .3, .6), "infection": (.6, 10, 30, .3, .6),
            "end_of_life": (.95, 45, 120, .4, .8), "childbirth": (.9, 30, 70, .2, .45), "severe_injury": (0, 0, 0, 0, 0)}


def main(data: Path, seed: int):
    r = np.random.default_rng(seed)
    persons = pd.read_parquet(data / "persons.parquet").set_index("person_id")
    py = pd.read_parquet(data / "person_years.parquet")
    ev = pd.read_parquet(data / "events.parquet", columns=["person_id", "date", "care_type", "diagnosis_group", "los_days"])
    truth = pd.read_csv(data / "ground_truth" / "person_latent_truth.csv").set_index("person_id")

    cohort = py[(py.year == 2023) & py.has_amb & py.age.between(20, 79)].person_id.unique()
    ev = ev[ev.person_id.isin(cohort)].copy()
    ev["day"] = (pd.to_datetime(ev.date) - START).dt.days
    ev = ev[(ev.day > -120) & (ev.day < NDAYS)]
    doy = (np.arange(NDAYS) + START.dayofyear - 1) % 365
    dow = (np.arange(NDAYS) + START.dayofweek) % 7
    season = 1 + .12 * np.sin(2 * np.pi * (doy - 100) / 365)

    rows = []
    for pid in cohort:
        P = persons.loc[pid]; T = truth.loc[pid]
        exit_ = pd.Timestamp(P.exit_date) if isinstance(P.exit_date, str) and P.exit_date else END
        n = min(NDAYS, (min(exit_, END) - START).days + 1)
        if n < 200:
            continue
        age = 2023 - pd.Timestamp(P.birth_date).year
        n_cond = sum(1 for c in truth.columns if c.startswith("onset_") and not pd.isna(T[c]) and T[c] <= 2023)
        level = 8500 * math.exp(-.012 * max(0, age - 35)) * (.88 ** n_cond) * math.exp(-.15 * T.frailty) * r.lognormal(0, .35)
        week = np.ones(7); week[5:] = r.uniform(.65, 1.35, 2); week[:5] *= r.uniform(.9, 1.1, 5)
        # slow AR(1) drift of the personal level
        z = np.zeros(NDAYS); eps = r.normal(0, .03, NDAYS)
        for d in range(1, NDAYS):
            z[d] = .97 * z[d - 1] + eps[d]
        f = level * week[dow] * season * np.exp(z) * r.lognormal(0, .28, NDAYS)
        mult = np.ones(NDAYS)
        # holidays
        for y in range(4):
            for _ in range(r.integers(1, 4)):
                s = y * 365 + int(r.integers(0, 350)); L = int(r.integers(5, 22))
                mult[s:s + L] *= r.lognormal(0, .35)
        # short illnesses (flu, colds): drop for a few days, then FULL recovery - not predictive
        for _ in range(r.poisson(3.0 * 4)):
            t0 = int(r.integers(0, NDAYS)); dur = int(r.integers(2, 7)); drop = r.uniform(.5, .8); rec = int(r.integers(3, 8))
            for k in range(dur):
                if t0 + k < NDAYS: mult[t0 + k] *= 1 - drop
            for k in range(rec):
                if t0 + dur + k < NDAYS: mult[t0 + dur + k] *= 1 - drop * (1 - (k + 1) / rec)
        e = ev[ev.person_id == pid]
        # accidents
        for _, a in e[e.care_type == "accident_outpatient"].iterrows():
            d0 = int(a.day); fr = a.diagnosis_group == "fracture"
            R = int(r.integers(30, 61)) if fr else int(r.integers(3, 8)); depth = .65 if fr else .3
            for k in range(R):
                if 0 <= d0 + k < NDAYS: mult[d0 + k] *= 1 - depth * (1 - k / R)
        # hospital stays: prodrome, stay, recovery
        for _, s in e[e.care_type == "inpatient_stay"].iterrows():
            D = int(s.day); los = max(1, int(s.los_days))
            p, lmin, lmax, dmin, dmax = PRODROME.get(s.diagnosis_group, (.7, 21, 75, .25, .5))
            if r.random() < p:
                # (a) one to three flare-ups some weeks or months before admission: a sharp drop for a
                #     few days, then a SLOW and INCOMPLETE recovery (unlike a cold, which recovers fully
                #     within a week)
                for _ in range(1 + r.binomial(2, .4)):
                    t0 = D - int(r.integers(20, max(21, lmax)))
                    dur = int(r.integers(2, 6)); drop = r.uniform(.55, .8); rec = int(r.integers(10, 26)); keep = r.uniform(.85, .95)
                    for k in range(dur):
                        if 0 <= t0 + k < NDAYS: mult[t0 + k] *= 1 - drop
                    for k in range(rec):
                        if 0 <= t0 + dur + k < NDAYS: mult[t0 + dur + k] *= (1 - drop) + (keep - (1 - drop)) * (k + 1) / rec
                    for d in range(max(0, t0 + dur + rec), min(D, NDAYS)):
                        mult[d] *= keep
            for k in range(los):
                if 0 <= D + k < NDAYS: mult[D + k] *= .08
            R = int(r.integers(14, 57))
            for k in range(R):
                if 0 <= D + los + k < NDAYS: mult[D + los + k] *= .4 + .6 * k / R
        steps = f * mult
        # device not worn: runs of zero days
        p_off = r.uniform(.005, .04); d = 0
        while d < NDAYS:
            if r.random() < p_off:
                L = int(r.geometric(1 / 3)); steps[d:d + L] = 0; d += L
            d += 1
        steps = np.round(np.minimum(steps, 40000)).astype(np.int32)[:n]
        rows.append(pd.DataFrame({"person_id": pid, "day": np.arange(n, dtype=np.int16), "steps": steps}))
    out = pd.concat(rows, ignore_index=True)
    out["date"] = (START + pd.to_timedelta(out.day, unit="D")).dt.date
    out[["person_id", "date", "steps"]].to_parquet(data / "activity_daily.parquet", index=False, compression="zstd")
    print(f"{out.person_id.nunique():,} participants, {len(out):,} person-days -> {data / 'activity_daily.parquet'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="data"); ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args(); main(Path(a.data), a.seed)
