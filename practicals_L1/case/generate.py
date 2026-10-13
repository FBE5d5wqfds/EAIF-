"""Synthetic Swiss health-insurance panel: basic (OKP/KVG) + supplementary (VVG) cover, 2014-2026,
plus the 1 January 2027 renewal.  Run:  python generate.py --out data --households 3000 --seed 7

Design: households live in cantons and premium regions; each person has latent health (frailty, chronic
conditions with onsets, pregnancies, accidents, death).  Each year (1) insurers publish OKP and VVG tariffs,
(2) households decide on insurer, deductible, model, accident cover and supplementary products,
(3) insurers underwrite VVG applications, (4) health events generate invoices that are split between
OKP, canton, VVG, accident insurance (UVG) and the patient, (5) insurers settle risk equalisation and
adjust next year's prices.  All amounts in CHF.
"""
import argparse, math, os, datetime as dt
import numpy as np, pandas as pd
from params import *

D = dt.date
def sig(x): return 1 / (1 + math.exp(-x))
def dayofyear_date(y, doy): return D(y, 1, 1) + dt.timedelta(days=int(min(max(doy, 0), 364)))
CANTON_LIST = list(CANTONS)
FLU_W = np.array([1.5, 1.4, 1.2, 1, .9, .8, .7, .7, .9, 1, 1.1, 1.4]); FLU_W = FLU_W / FLU_W.sum()
SPORT_W = np.array([3, 3, 2.5, 1, 1, 1.5, 2, 2, 1.2, .8, .7, 1.8]); SPORT_W = SPORT_W / SPORT_W.sum()
INS = list(INSURERS)
LANG = {c: v[2] for c, v in CANTONS.items()}

def age_class(age):
    return "child" if age <= 18 else ("young_adult" if age <= 25 else "adult")
def age_band(age):
    for i, (a, b) in enumerate(AGE_BANDS):
        if a <= age <= b: return i
    return len(AGE_BANDS) - 1
def band_label(i): a, b = AGE_BANDS[i]; return f"{a}-{b}" if b < 120 else f"{a}+"

# national adult mean premium path, then canton paths (back-cast from 2026 with national growth)
def canton_adult_mean(c, y):
    if y == 2027: return CANTONS[c][5]
    v = CANTONS[c][4]
    for yy in range(2026, y, -1): v /= (1 + PREMIUM_GROWTH[yy])
    return v
COST_INDEX = {c: (CANTONS[c][4] / NATIONAL_ADULT_2026) for c in CANTONS}   # canton cost level ~ premium level


class World:
    def __init__(self, n_households, seed):
        self.r = np.random.default_rng(seed)
        self.pid = 0; self.hid = 0; self.polid = 0; self.appid = 0; self.evid = 0
        self.dyn_hist = {}; self.K_hist = {}; self.vvg_dev_hist = {}
        self.persons = {}; self.households = {}
        self.events = []; self.person_years = []; self.policies = {}; self.applications = []
        self.tariff_okp = []; self.tariff_vvg = []; self.fin = []; self.renewal = []
        r = self.r
        # insurer static pricing structure
        self.u = {i: {c: r.normal(0, .04) for c in CANTONS} for i in INS}        # canton-specific position
        self.dyn = {i: 0.0 for i in INS}                                         # dynamic level (loss-ratio feedback)
        self.fr_rate = {i: r.uniform(.85, 1.0) for i in INS}                      # share of the max deductible rebate granted
        self.model_noise = {i: {m: (1.0 if m == "standard" else r.uniform(.98, 1.02)) for m in MODEL_FACTOR} for i in INS}
        self.vvg_dev = {i: {p: 1.0 for p in VVG_PRODUCTS} for i in INS}          # insurer deviation from the market tariff path
        self.vvg_region = {i: {c: (COST_INDEX[c] ** .8) * r.uniform(.95, 1.05) for c in CANTONS} for i in INS}
        self.K = {c: 1.30 for c in CANTONS}                                        # calibration: tariff -> realised mean
        self.cost_scale = 1.0
        self.okp_cache = {}
        for _ in range(n_households): self.new_household(2014, D(2014, 1, 1), "portfolio_2014")

    # ------------------------------------------------------------------ population
    def new_person(self, hid, sex, birth, entry, reason):
        r = self.r; self.pid += 1
        P = dict(pid=self.pid, hid=hid, sex=sex, birth=birth, entry=entry, entry_reason=reason, exit=None, exit_reason=None,
                 smoker=bool(r.random() < (.27 if sex == "M" else .21)) if birth.year < 2000 else False,
                 bmi=float(np.clip(r.normal(25.5 if sex == "M" else 24.3, 4.2), 16, 48)),
                 frailty=float(r.normal()), risk_av=float(r.normal()), altmed=float(r.normal()),
                 dental_poor=bool(r.random() < .15), ortho_need=bool(r.random() < .3), ortho_done=False,
                 emp_prop=float(r.normal()), cond={}, active={}, undisclosed=set(), nursing_home=False,
                 alive=True, okp=None, vvg={}, bonus={}, last_glasses=-9, educ=bool(r.random() < .45))
        self.persons[P["pid"]] = P
        if reason != "birth":                       # past health history up to the entry year
            for yy in range(birth.year + 1, entry.year): self.onsets(P, yy)
        return P

    def new_household(self, y, date, reason, canton=None):
        r = self.r; self.hid += 1; h = self.hid
        if canton is None:
            w = np.array([CANTONS[c][1] for c in CANTON_LIST]); canton = CANTON_LIST[r.choice(len(w), p=w / w.sum())]
        nreg = CANTONS[canton][3]
        region = int(r.choice(range(1, nreg + 1), p=[.5, .3, .2][:nreg] / np.sum([.5, .3, .2][:nreg])))
        mtype = r.choice(["urban", "suburban", "rural"], p=[[.7, .25, .05], [.25, .5, .25], [.05, .35, .6]][region - 1])
        typ = r.choice(["single", "couple", "family", "single_parent"], p=[.38, .34, .23, .05])
        if reason == "immigration": typ = r.choice(["single", "couple", "family"], p=[.45, .25, .30])
        def bdate(age):
            yy = y - int(age); return D(yy, int(r.integers(1, 13)), int(r.integers(1, 29)))
        members = []
        if reason == "immigration": a1 = r.uniform(22, 48)
        elif typ == "single": a1 = float(np.clip(r.choice([r.uniform(20, 45), r.uniform(50, 97)], p=[.38, .62]), 20, 99))
        elif typ == "couple": a1 = float(np.clip(r.choice([r.uniform(24, 45), r.uniform(52, 93)], p=[.25, .75]), 20, 96))
        else: a1 = r.uniform(27, 54)
        s1 = r.choice(["F", "M"])
        members.append(self.new_person(h, s1, bdate(a1), date, reason))
        if typ in ("couple", "family"):
            members.append(self.new_person(h, "M" if s1 == "F" else "F", bdate(np.clip(a1 + r.normal(0, 3), 19, 99)), date, reason))
        if typ in ("family", "single_parent"):
            nk = int(r.choice([1, 2, 3, 4], p=[.42, .43, .12, .03]))
            for k in range(nk):
                ka = np.clip(a1 - r.uniform(24, 40), 1, 22)
                members.append(self.new_person(h, r.choice(["F", "M"]), bdate(ka), date, reason))
        inc = int(r.choice([1, 2, 3, 4], p=[.2, .28, .32, .2]))
        if a1 < 27 or a1 > 70: inc = max(1, inc - int(r.random() < .5))
        self.households[h] = dict(canton=canton, region=region, mtype=str(mtype), income=inc, members=[m["pid"] for m in members],
                                  hist=[])
        for P in members:
            self.init_cover(P, y, date, new=(reason != "portfolio_2014"))
        return h

    def age(self, P, y): return y - P["birth"].year
    def hh(self, P): return self.households[P["hid"]]

    def employment(self, P, y):
        a = self.age(P, y)
        if a < 16: return "child"
        if a <= 25 and P["educ"] and a <= 18 + 6 * (P["emp_prop"] < .3): return "student"
        ret = 64 if (P["sex"] == "F" and P["birth"].year < 1961) else 65
        if a >= ret: return "retired"
        p = sig(1.6 + .8 * P["emp_prop"] - (.4 if P["sex"] == "F" else 0) - .03 * max(0, a - 55) * 3)
        return "employed" if self.r.random() < p else "not_employed"

    # ------------------------------------------------------------------ tariffs
    def ins_factor(self, i, c, y):
        key = (i, c, y)
        if key not in self.okp_cache:
            raw = {j: 1 + INSURERS[j]["level"] + self.u[j][c] + self.dyn_hist.get((j, y), 0) for j in INS}
            w = {j: INSURERS[j]["share"] * INSURERS[j]["affinity"][LANG[c]] for j in INS}
            m = sum(raw[j] * w[j] for j in INS) / sum(w.values())
            for j in INS: self.okp_cache[(j, c, y)] = raw[j] / m
        return self.okp_cache[key]

    def okp_premium(self, i, c, reg, ac, y, model, accident, fr):
        """Monthly OKP premium for a given cover configuration."""
        fr = min(fr, 600) if ac == "child" else max(fr, 300)
        nreg = CANTONS[c][3]
        wts = [.5, .3, .2][:nreg]; rf = REGION_FACTOR[reg] / (sum(REGION_FACTOR[k + 1] * wts[k] for k in range(nreg)) / sum(wts))
        base = canton_adult_mean(c, y) * self.K_hist.get((c, y), self.K[c]) * rf * self.ins_factor(i, c, y) * AGE_CLASS_FACTOR[ac]
        p = base * MODEL_FACTOR[model] * self.model_noise[i][model] * (1.0 if accident else ACCIDENT_EXCLUDED_FACTOR)
        reb = self.fr_rate[i] * .7 * ((fr - 300) if ac != "child" else fr) / 12
        return round(max(p - reb, .5 * p), 2)

    def vvg_premium(self, i, prod, P, y, c, start=None):
        a = self.age(P, y); b = age_band(a)
        if INSURERS[i]["entry_age_tariff"] and a >= 50 and start is not None and self.age(P, start.year) < 50:
            b = age_band(50)                               # entry-age tariff from 50 for long-standing customers
        p = VVG_BASE_2026[prod][b] * (1 + VVG_INDEX_GROWTH[prod]) ** (y - 2026)
        p *= self.vvg_dev_hist.get((i, prod, y), self.vvg_dev[i][prod])
        p *= INSURERS[i]["vvg_level"] * self.vvg_region[i][c]
        if prod.startswith("HOSP") and P["sex"] == "F" and 19 <= a <= 45: p *= INSURERS[i]["sex_rated"]
        return p

    # ------------------------------------------------------------------ cover initialisation
    def choose_insurer(self, c, exclude=None, prices=None, beta=25):
        w = []
        for i in INS:
            v = INSURERS[i]["share"] * INSURERS[i]["affinity"][LANG[c]]
            if prices is not None:
                v = v * math.exp(-beta * (prices[i] / np.mean(list(prices.values())) - 1)) if i in prices else 0
            w.append(0 if i == exclude else v)
        w = np.array(w); return INS[self.r.choice(len(INS), p=w / w.sum())]

    def init_cover(self, P, y, date, new):
        r = self.r; H = self.hh(P); a = self.age(P, y)
        head = self.persons[H["members"][0]]
        ins = head["okp"]["insurer"] if (head is not P and head.get("okp")) else self.choose_insurer(
            H["canton"], prices={i: self.ins_factor(i, H["canton"], y) for i in INS}, beta=12)
        if a < 0: return
        model = "standard" if r.random() < (.45 if y < 2018 else .3) else r.choice(["family_doctor", "telmed", "hmo"], p=[.45, .35, .2])
        if model == "hmo" and H["mtype"] == "rural": model = "family_doctor"
        emp = self.employment(P, y); P["emp_y"] = emp
        fr = self.pick_franchise(P, y, ins, H, model, emp != "employed", initial=True)
        P["okp"] = dict(insurer=ins, model=str(model), franchise=fr, accident=(emp != "employed") or (r.random() < .3),
                        start=date, policy=self.open_policy(P, "OKP", ins, date))
        # supplementary portfolio (for 2014 stock: contracts started in the past; for newcomers: applications)
        if not new:
            self.init_vvg_stock(P, y, date)
        elif P["entry_reason"] == "immigration":
            for prod, p in [("AMB", .35), ("HOSP_SEMI", .06), ("DENT", .10)]:
                if r.random() < p: self.apply_vvg(P, prod, ins if r.random() < .8 else self.choose_insurer(H["canton"]), date, "new_resident")

    def init_vvg_stock(self, P, y, date):
        r = self.r; a = self.age(P, y); H = self.hh(P); inc = H["income"]
        ins = P["okp"]["insurer"] if r.random() < .85 else self.choose_insurer(H["canton"])
        probs = {"AMB": sig(.6 + .3 * (inc - 2.5) + (.5 if a <= 18 else 0) + (.3 if P["sex"] == "F" else 0)),
                 "DENT": .35 if a <= 18 else .16,
                 "HOSP_PRIV": sig(-3.3 + .55 * (inc - 2.5) + .03 * max(0, a - 30)) if a >= 19 else .03,
                 "HOSP_SEMI": sig(-1.45 + .45 * (inc - 2.5) + .02 * max(0, a - 30)) if a >= 19 else .14,
                 "HOSP_GEN": .22}
        held_hosp = False
        for prod in ["AMB", "DENT", "HOSP_PRIV", "HOSP_SEMI", "HOSP_GEN"]:
            if prod.startswith("HOSP") and held_hosp: continue
            if r.random() < probs[prod]:
                since = max(P["birth"].year, y - int(r.integers(1, max(2, min(a, 40) + 1))))
                start = D(since, 1, 1)
                if since <= P["birth"].year: start = P["birth"]
                res = None
                if r.random() < .12 and a > 25:
                    res = (r.choice(["musculoskeletal", "mental", "respiratory"]), since + 5)
                self.add_vvg(P, prod, ins, start, res, tariff_start=start)
                held_hosp |= prod.startswith("HOSP")

    def open_policy(self, P, line, ins, start, res=None):
        self.polid += 1
        self.policies[self.polid] = dict(policy_id=self.polid, person_id=P["pid"], line=line, insurer=ins, start_date=start,
                                         end_date=None, end_reason="active",
                                         reservation_condition=res[0] if res else None,
                                         reservation_until=res[1] if res else None)
        return self.polid

    def close_policy(self, pol, date, reason):
        p = self.policies[pol]
        if p["end_date"] is None: p["end_date"] = date; p["end_reason"] = reason

    def add_vvg(self, P, prod, ins, start, res, tariff_start):
        pol = self.open_policy(P, prod, ins, start, res)
        P["vvg"][prod] = dict(insurer=ins, start=start, policy=pol, res=res, tariff_start=tariff_start)
        if INSURERS[ins]["bonus"] == "ladder": P["bonus"][prod] = .8
        elif INSURERS[ins]["bonus"] == "two_level25": P["bonus"][prod] = .75
        elif INSURERS[ins]["bonus"] == "claimfree20": P["bonus"][prod] = 1.0

    # ------------------------------------------------------------------ underwriting
    def apply_vvg(self, P, prod, ins, date, channel):
        r = self.r; y = date.year; a = self.age(P, y)
        if prod in P["vvg"]: return
        I = INSURERS[ins]
        declared = [c for c in P["cond"] if P["cond"][c] <= y and c not in P["undisclosed"]
                    and (c != "cancer" or y - P["cond"][c] <= 10)]
        hidden = [c for c in P["cond"] if P["cond"][c] <= y and c not in declared and c != "dementia"]
        for c in list(declared):
            if c in ("mental", "musculoskeletal", "respiratory") and r.random() < .07:   # applicant omits a condition
                declared.remove(c); hidden.append(c); P["undisclosed"].add(c)
        pts = {"cardiovascular": 2, "diabetes": 2.5, "respiratory": 1.5, "mental": 2, "musculoskeletal": 1.5, "cancer": 5, "dementia": 10}
        score = sum(pts[c] for c in declared) + (1 if P["bmi"] > 32 else 0) + (.5 if P["smoker"] else 0)
        decision, res = "accepted", None
        if channel == "prenatal":
            decision = "accepted"
        elif prod.startswith("HOSP"):
            score += .1 * max(0, a - 50)
            if a > I["max_entry_hosp"]: decision = "declined_age_limit"
            elif score >= 4.5 - 1.5 * I["strict"]: decision = "declined"
            elif declared and score >= 1.5:
                worst = max(declared, key=lambda c: pts[c]); decision = "accepted_with_reservation"
                res = (worst, 9999 if worst in ("cancer", "diabetes") else y + 5)
        elif prod == "AMB":
            if a > 75 or score >= 6: decision = "declined"
            elif any(c in declared for c in ("mental", "musculoskeletal")):
                decision = "accepted_with_reservation"; res = ([c for c in declared if c in ("mental", "musculoskeletal")][0], y + 5)
        elif prod == "DENT":
            if a >= 19 and P["dental_poor"] and r.random() < .7: decision = "declined"
            elif a >= 10 and P["ortho_need"] and not P["ortho_done"]: decision = "accepted_with_reservation"; res = ("orthodontics", 9999)
        self.appid += 1
        h_cm = float(np.clip(r.normal(178 if P["sex"] == "M" else 165, 7), 140, 205)) if a >= 16 else None
        self.applications.append(dict(application_id=self.appid, person_id=P["pid"], date=date, insurer=ins, product=prod,
            channel=channel, age=a, sex=P["sex"], canton=self.hh(P)["canton"],
            height_cm=round(h_cm) if h_cm else None, weight_kg=round(P["bmi"] * (h_cm / 100) ** 2) if h_cm else None,
            smoker=P["smoker"] if a >= 16 else None, declared_conditions=";".join(sorted(declared)) if channel != "prenatal" else "",
            n_declared=len(declared) if channel != "prenatal" else 0, decision=decision,
            reservation_condition=res[0] if res else None, reservation_until=res[1] if res else None))
        if decision.startswith("accepted"):
            start = D(y + 1, 1, 1) if channel in ("existing_customer", "new_customer") and date.month >= 10 else date
            self.add_vvg(P, prod, ins, start, res, tariff_start=start)

    # ------------------------------------------------------------------ choices at 1 January
    def expected_cost(self, P, y):
        a = self.age(P, y)
        base = 1300 if a <= 18 else (1800 + 60 * max(0, a - 25) + 4 * max(0, a - 60) ** 2)
        base *= (1 + .7 * sum(1 for c in P["cond"] if P["cond"][c] <= y)) * math.exp(.25 * P["frailty"])
        last = P.get("last_okp_cost")
        return .5 * base + .5 * last if last is not None else base

    def pick_franchise(self, P, y, ins, H, model, accident, initial=False):
        r = self.r; a = self.age(P, y); ac = age_class(a)
        if ac == "child":
            return 0 if r.random() < .93 else int(r.choice(FRANCHISES_CHILD[1:]))
        ec = self.expected_cost(P, y) * self.cost_scale
        best, utils = None, []
        for f in FRANCHISES_ADULT:
            prem = 12 * self.okp_premium(ins, H["canton"], H["region"], ac, y, model, accident, f)
            share = 0
            for q in (.1, .4, .8, 1.5, 3.2):
                cst = ec * q; share += min(cst, f) + min(.1 * max(cst - f, 0), COINS_CAP_ADULT)
            utils.append(-(prem + share / 5) - 120 * (P["risk_av"] + .6) * (f - 300) / 1000)
        u = np.array(utils) / 110.0; p = np.exp(u - u.max()); p /= p.sum()
        return int(FRANCHISES_ADULT[r.choice(len(p), p=p)])

    def yearly_choices(self, y, renewal=False):
        """Decisions effective 1 January of year y (made in November y-1)."""
        r = self.r; nat = PREMIUM_GROWTH.get(y, .03); out = {}
        for h, H in self.households.items():
            mem = [self.persons[p] for p in H["members"] if self.persons[p]["alive"] and self.persons[p]["exit"] is None]
            if not mem: continue
            adults = [P for P in mem if self.age(P, y) >= 19] or mem
            head = max(adults, key=lambda P: (self.age(P, y) < 80, self.age(P, y)))
            c, reg = H["canton"], H["region"]
            cur = head["okp"]["insurer"]
            def hh_cost(i):
                return sum(12 * self.okp_premium(i, c, reg, age_class(self.age(P, y)), y, P["okp"]["model"], P["okp"]["accident"],
                                                  P["okp"]["franchise"] if age_class(self.age(P, y)) != "child" or P["okp"]["franchise"] <= 600 else 0) for P in mem)
            prices = {i: hh_cost(i) for i in INS}
            prev = sum(12 * self.okp_premium(cur, c, reg, age_class(self.age(P, y - 1)), y - 1, P["okp"]["model"], P["okp"]["accident"],
                                              P["okp"]["franchise"]) for P in mem if self.age(P, y - 1) >= 0)
            inc = prices[cur] / prev - 1 if prev > 0 else 0
            save = (prices[cur] - min(prices.values())) / prices[cur]
            chronic = any(P["cond"] for P in mem)
            vvg_tie = any(k.startswith("HOSP") and v["insurer"] == cur for P in mem for k, v in P["vvg"].items())
            amb_tie = any(v["insurer"] == cur for P in mem for v in P["vvg"].values())
            age_h = self.age(head, y)
            logit = (-2.45 + 9 * save + 5 * max(0, inc - nat) + 10 * nat - .025 * max(0, age_h - 35)
                     - .45 * chronic - .9 * vvg_tie - .35 * amb_tie + .25 * (H["income"] == 1))
            switch = r.random() < sig(logit)
            new_ins = cur
            if switch:
                cheaper = {i: v for i, v in prices.items() if i != cur}
                new_ins = self.choose_insurer(c, exclude=cur, prices=cheaper, beta=30)
            info = dict(hh_premium_current=prices[cur], hh_premium_cheapest=min(prices.values()), premium_change=inc,
                        cheapest_insurer=min(prices, key=prices.get), switch_prob=sig(logit))
            for P in mem:
                if self.age(P, y) < 0: continue
                follow = switch and (r.random() < .9 or P is head or self.age(P, y) <= 18)
                emp = self.employment(P, y); P["emp_y"] = emp
                o = P["okp"]; old = dict(o)
                if follow and o["insurer"] != new_ins:
                    if not renewal:
                        self.close_policy(o["policy"], D(y - 1, 12, 31), "switch_insurer")
                        o["policy"] = self.open_policy(P, "OKP", new_ins, D(y, 1, 1)); o["start"] = D(y, 1, 1)
                    o["insurer"] = new_ins
                # model
                if r.random() < (.08 + .2 * follow):
                    trend = sig(-0.2 + .22 * (y - 2014))
                    if o["model"] == "standard" and r.random() < trend:
                        o["model"] = str(r.choice(["family_doctor", "telmed", "hmo"], p=[.45, .35, .2]))
                        if o["model"] == "hmo" and H["mtype"] == "rural": o["model"] = "family_doctor"
                    elif o["model"] != "standard" and r.random() < .05: o["model"] = "standard"
                # accident cover follows employment
                o["accident"] = True if emp != "employed" else (o["accident"] if r.random() < .9 else r.random() < .3)
                # deductible
                ac = age_class(self.age(P, y))
                if ac == "child":
                    if o["franchise"] > 600: o["franchise"] = 0
                elif o["franchise"] < 300 or age_class(self.age(P, y - 1)) == "child" or r.random() < (.1 + .3 * (abs(inc) > .06) + .2 * follow):
                    o["franchise"] = self.pick_franchise(P, y, o["insurer"], H, o["model"], o["accident"])
                out[P["pid"]] = dict(old=old, new=dict(o), switched=o["insurer"] != old["insurer"], info=info)
                # supplementary lapses / downgrades (customer can cancel from the 3rd contract year, 3 months' notice)
                for prod in list(P["vvg"]):
                    v = P["vvg"][prod]
                    if (D(y, 1, 1) - v["start"]).days < 2 * 365: continue
                    pn = self.vvg_premium(v["insurer"], prod, P, y, c, v["tariff_start"])
                    po = self.vvg_premium(v["insurer"], prod, P, y - 1, c, v["tariff_start"])
                    pi = pn / po - 1
                    a = self.age(P, y)
                    lg = (-4.3 + 7 * pi + .8 * (H["income"] == 1) + .5 * (emp == "retired" and P.get("emp_prev") != "retired")
                          + (1.2 if (prod in ("HOSP_PRIV", "HOSP_SEMI") and a >= 58 and H["income"] <= 2) else 0)
                          - .9 * bool(P["cond"]) + (.6 if (prod == "DENT" and a >= 19) else 0) + (.5 if follow else 0))
                    if r.random() < sig(lg):
                        down = {"HOSP_PRIV": "HOSP_SEMI", "HOSP_SEMI": "HOSP_GEN"}.get(prod)
                        if renewal:
                            out[P["pid"]].setdefault("vvg_changes", []).append((prod, "downgrade" if down and r.random() < .5 else "cancel"))
                            continue
                        if down and r.random() < .5:
                            self.close_policy(v["policy"], D(y - 1, 12, 31), "downgrade")
                            res = v["res"]; del P["vvg"][prod]
                            self.add_vvg(P, down, v["insurer"], D(y, 1, 1), res, tariff_start=v["tariff_start"])
                        else:
                            self.close_policy(v["policy"], D(y - 1, 12, 31), "cancelled_by_customer"); del P["vvg"][prod]
                            P["bonus"].pop(prod, None)
                P["emp_prev"] = emp
        return out

    # ------------------------------------------------------------------ health
    def onsets(self, P, y):
        r = self.r; a = self.age(P, y); fz = math.exp(.35 * P["frailty"]); F = P["sex"] == "F"
        hz = {"cardiovascular": .0006 * math.exp(.075 * (a - 20)) * (1 + .5 * P["smoker"]) * (0.8 if F else 1.0),
              "diabetes": .0003 * math.exp(.06 * (a - 20)) * (1 + 2 * (P["bmi"] > 30)),
              "respiratory": (.006 if 2 <= a <= 12 else .0002 * math.exp(.06 * max(0, a - 30)) * (1 + 3 * P["smoker"]) + .0008),
              "mental": (.014 * (1.6 if F else 1.0) if 15 <= a <= 65 else .004),
              "musculoskeletal": .004 * math.exp(.03 * max(0, a - 20)) * (1 + .5 * (P["bmi"] > 30)),
              "cancer": .0004 * math.exp(.075 * max(0, a - 30)) * (1 + 1.5 * P["smoker"]),
              "dementia": (.006 * math.exp(.13 * (a - 75)) if a >= 70 else 0)}
        for c, h in hz.items():
            if (c not in P["cond"] or (c == "mental" and not P["active"].get(c))) and r.random() < min(.5, h * fz):
                if c not in P["cond"]: P["cond"][c] = y
                P["active"][c] = y + (int(r.integers(1, 3)) if c == "cancer" else 999)
        if P["active"].get("mental", 0) >= y and r.random() < .3 and P["cond"].get("mental", y) < y: P["active"]["mental"] = y - 1
        if "dementia" in P["cond"] and not P["nursing_home"] and r.random() < .35: P["nursing_home"] = True

    def qx(self, P, y):
        a = self.age(P, y)
        q = .003 if a == 0 else math.exp(-13.0 + .1 * a) * (1.25 if P["sex"] == "M" else .85)
        q *= math.exp(.3 * P["frailty"])
        act = lambda c: c in P["cond"] and P["active"].get(c, 0) >= y
        q *= (6 if act("cancer") else 1.4 if "cancer" in P["cond"] else 1) * (3 if "dementia" in P["cond"] else 1) \
             * (1.4 if "cardiovascular" in P["cond"] else 1) * (1.3 if "diabetes" in P["cond"] else 1) * (1.5 if P["smoker"] and a > 50 else 1)
        return min(q, .6)

    def ev(self, P, y, doy, care, prov, diag, cost, cond=None, acc=None, ward=None, los=0, okp_eligible=True, extra=None):
        self.evid += 1
        e = dict(event_id=self.evid, person_id=P["pid"], date=dayofyear_date(y, doy), year=y, care_type=care, provider=prov,
                 diagnosis_group=diag, condition=cond, accident_context=acc, ward=ward, los_days=los,
                 gross_cost=float(cost), okp_eligible=okp_eligible)
        if extra: e.update(extra)
        return e

    def simulate_health(self, P, y, H, start_doy, end_doy):
        """Generate the year's events (amounts in 2024 CHF, rescaled later)."""
        r = self.r; a = self.age(P, y); F = P["sex"] == "F"; ex = max(1, end_doy - start_doy) / 365
        fz = math.exp(.45 * P["frailty"]) * (.8 if P["okp"]["franchise"] >= 1500 else 1.0); ci = COST_INDEX[H["canton"]] ** .6
        act = [c for c in P["cond"] if P["active"].get(c, 0) >= y]
        hist = [c for c in P["cond"] if c not in act]
        evs = []
        def d(): return int(r.integers(start_doy, max(start_doy + 1, end_doy)))
        def d_flu():
            m = r.choice(12, p=FLU_W)
            dd = int(m * 30.4 + r.integers(0, 30)); return min(max(dd, start_doy), max(start_doy, end_doy - 1))
        diag_acute = ["respiratory_infection", "digestive", "skin", "musculoskeletal_acute", "ent", "urogenital", "checkup"]
        lam_gp = (1.3 + (2.0 if a < 6 else 0) + .035 * max(0, a - 40) + (.8 if F and 18 <= a <= 50 else 0) + 1.2 * len(act) + .3 * len(hist)) * fz * ex
        for _ in range(r.poisson(lam_gp)):
            evs.append(self.ev(P, y, d_flu(), "gp_visit", "physician_gp", r.choice(diag_acute), max(48, r.lognormal(math.log(105), .7)) * ci))
        lam_sp = (.3 + (.85 if F and 18 <= a <= 60 else 0) + .02 * max(0, a - 40) + 1.4 * len(act) + .4 * len(hist)) * fz * ex
        for _ in range(r.poisson(lam_sp)):
            cond = r.choice(act) if act and r.random() < .7 else None
            evs.append(self.ev(P, y, d(), "specialist_visit", "physician_specialist", cond or r.choice(diag_acute), max(85, r.lognormal(math.log(200), 1.05)) * ci, cond=cond))
        for _ in range(r.poisson((.35 + .008 * a + .6 * len(act)) * fz * ex)):
            cond = r.choice(act) if act and r.random() < .6 else None
            evs.append(self.ev(P, y, d(), "outpatient_hospital", "hospital_outpatient", cond or r.choice(diag_acute), max(90, r.lognormal(math.log(320), 1.2)) * ci, cond=cond))
        medq = {"cardiovascular": 160, "diabetes": 420, "respiratory": 210, "mental": 230, "musculoskeletal": 110, "cancer": 5200, "dementia": 220}
        for cnd in P["cond"]:
            if cnd in act or cnd in ("cardiovascular", "diabetes", "respiratory") or (cnd == "cancer" and r.random() < .3):
                amt = medq[cnd] * (.5 if cnd == "cancer" and cnd not in act else 1)
                for q in range(4):
                    dq = q * 91 + int(r.integers(0, 30))
                    if start_doy <= dq < end_doy:
                        evs.append(self.ev(P, y, dq, "medication", "pharmacy", cnd, amt * r.lognormal(0, .25), cond=cnd))
        if any(c in act for c in ("musculoskeletal", "respiratory")) and P["frailty"] > 1.6:     # biologics: rare, very expensive
            for q in range(4):
                dq = q * 91 + 10
                if start_doy <= dq < end_doy: evs.append(self.ev(P, y, dq, "medication", "pharmacy", "specialty_drug", 4200 * r.lognormal(0, .2)))
        if "mental" in act and r.random() < .6:
            for q in range(4):
                dq = q * 91 + 60
                if start_doy <= dq < end_doy:
                    evs.append(self.ev(P, y, dq, "psychotherapy", "psychologist", "mental", r.lognormal(math.log(1100), .4), cond="mental"))
        if "musculoskeletal" in act and r.random() < .45:
            evs.append(self.ev(P, y, d(), "physiotherapy", "physiotherapist", "musculoskeletal", 9 * 68 * r.uniform(.6, 1.8), cond="musculoskeletal"))
        # inpatient stays
        p_in = .62 * (.07 if a == 0 else .04 if a <= 18 else .06 if a <= 44 else .10 if a <= 64 else .17 if a <= 74 else .24 if a <= 84 else .30)
        lam_in = p_in * (1.5 ** len(act)) * (2.5 if "cancer" in act else 1) * fz * ex
        for _ in range(r.poisson(lam_in)):
            cond = r.choice(act) if act and r.random() < .65 else None
            los = 1 + r.poisson(2.5 + .06 * max(0, a - 40) + (4 if cond == "cancer" else 0))
            cost = 2500 * (los ** .8) * r.lognormal(0, 1.0) * ci * (1.5 if cond == "cancer" else 1)
            elective = r.random() < .45
            evs.append(self.ev(P, y, d(), "inpatient_stay", "hospital_inpatient", cond or r.choice(["surgery_elective", "cardiac_acute", "digestive", "infection", "orthopaedic"]),
                               cost, cond=cond, los=los, extra=dict(elective=elective, out_of_canton=elective and r.random() < .1)))
        if a >= 80 and (P["frailty"] > .8 or "dementia" in P["cond"]) and not P["nursing_home"] and r.random() < .4:
            for q in range(4):
                dq = q * 91 + 20
                if start_doy <= dq < end_doy: evs.append(self.ev(P, y, dq, "home_care", "spitex", "frailty", 1600 * r.lognormal(0, .3)))
        if P["nursing_home"]:
            for q in range(4):
                dq = q * 91 + 5
                if start_doy <= dq < end_doy: evs.append(self.ev(P, y, dq, "nursing_home_care", "nursing_home", "dementia" if "dementia" in P["cond"] else "frailty", 5200 * r.lognormal(0, .2)))
        # maternity (no cost sharing); newborn handled by caller
        birth = None
        if F and 18 <= a <= 45 and P.get("hh_couple"):
            pp = .13 * math.exp(-((a - 32.5) / 5.5) ** 2) * (1.0 if self.count_children(H) < 3 else .3)
            if r.random() < pp and end_doy > 200:
                bd = int(r.integers(max(start_doy + 60, 100), max(start_doy + 61, min(end_doy, 364))))
                for k in range(6):
                    evs.append(self.ev(P, y, max(start_doy, bd - 200 + 30 * k), "maternity_care", "physician_specialist", "pregnancy", r.lognormal(math.log(260), .3), extra=dict(maternity=True)))
                cs = r.random() < .33
                evs.append(self.ev(P, y, bd, "inpatient_stay", "hospital_inpatient", "childbirth", (7800 if not cs else 11000) * r.lognormal(0, .2) * ci,
                                   los=4 + cs, extra=dict(maternity=True, elective=False)))
                birth = dayofyear_date(y, bd)
        # accidents
        lam_acc = (.08 if a <= 15 else (.17 if not F else .11) if a <= 30 else .09 if a <= 64 else .06 + .004 * max(0, a - 70)) * ex
        for _ in range(r.poisson(lam_acc)):
            ctx = r.choice(["sport", "home_leisure", "traffic", "work"], p=[.42, .38, .10, .10] if P.get("emp_y") == "employed" else [.47, .43, .10, 0])
            if ctx == "sport":
                m = r.choice(12, p=SPORT_W); dd = int(m * 30.4 + r.integers(0, 30))
            else: dd = d()
            dd = min(max(dd, start_doy), max(start_doy, end_doy - 1))
            sev = r.choice(["minor", "moderate", "severe"], p=[.84, .13, .03] if a < 70 else [.7, .2, .1])
            if sev == "minor": evs.append(self.ev(P, y, dd, "accident_outpatient", "hospital_outpatient", "injury", r.lognormal(math.log(600), .7), acc=ctx))
            elif sev == "moderate":
                evs.append(self.ev(P, y, dd, "accident_outpatient", "hospital_outpatient", "fracture", r.lognormal(math.log(2500), .5), acc=ctx))
                evs.append(self.ev(P, y, min(dd + 40, 364), "physiotherapy", "physiotherapist", "injury_rehab", 9 * 68 * r.uniform(.8, 1.6), acc=ctx))
            else:
                los = 3 + r.poisson(6)
                evs.append(self.ev(P, y, dd, "inpatient_stay", "hospital_inpatient", "severe_injury", 4500 * los ** .7 * r.lognormal(0, .4), acc=ctx, los=los,
                                   extra=dict(elective=False)))
                evs.append(self.ev(P, y, dd, "rescue_transport", "ambulance", "severe_injury", r.lognormal(math.log(1400), .5), acc=ctx))
        # non-OKP / partly-covered services
        if a >= 3:
            if r.random() < (.8 if a <= 18 else .62) * ex: evs.append(self.ev(P, y, d(), "dental_checkup", "dentist", "dental", r.lognormal(math.log(190 if a <= 18 else 230), .25), okp_eligible=False))
            if r.random() < (.18 + .35 * P["dental_poor"] + .002 * a) * ex: evs.append(self.ev(P, y, d(), "dental_treatment", "dentist", "dental", r.lognormal(math.log(850), .9), okp_eligible=False))
            if P["ortho_need"] and not P["ortho_done"] and 9 <= a <= 13 and r.random() < .35:
                P["ortho_done"] = True; P["ortho_years"] = (y, y + 1)
            if P.get("ortho_years") and y in P["ortho_years"]:
                for k in (40, 220): evs.append(self.ev(P, y, k, "orthodontics", "dentist", "orthodontics", r.uniform(1300, 1900), okp_eligible=False))
        if r.random() < (.15 if a <= 18 else .2 if a > 45 else .1) * ex:
            evs.append(self.ev(P, y, d(), "glasses", "optician", "vision", r.lognormal(math.log(330 if a <= 18 else 520), .35), okp_eligible=a <= 18))
        if a >= 16 and r.random() < sig(-2.1 + 1.1 * P["altmed"] + .6 * F + .7 * ("AMB" in P["vvg"]) + .4 * bool(act)) * ex:
            evs.append(self.ev(P, y, d(), "complementary_therapy", "therapist_nonphysician", r.choice(["musculoskeletal_acute", "mental", "checkup"]),
                               int(r.integers(3, 13)) * 118, okp_eligible=False))
        if "AMB" in P["vvg"] and a >= 16 and r.random() < .22 * ex:
            evs.append(self.ev(P, y, d(), "fitness_prevention", "fitness_centre", "prevention", r.uniform(600, 1100), okp_eligible=False))
        if r.random() < .015 * ex:
            evs.append(self.ev(P, y, d(), "emergency_abroad", "hospital_abroad", r.choice(["injury", "digestive", "infection"]), r.lognormal(math.log(2500), .9),
                               extra=dict(abroad=True)))
        return evs, birth

    def terminal_events(self, P, y, H, death_doy):
        r = self.r; ci = COST_INDEX[H["canton"]] ** .6; evs = []
        if not P["nursing_home"]:
            for k in range(int(r.integers(1, 3))):
                los = 5 + r.poisson(6)
                evs.append(self.ev(P, y, max(0, death_doy - 30 * k - int(r.integers(0, 20))), "inpatient_stay", "hospital_inpatient", "end_of_life",
                                   3800 * los ** .7 * r.lognormal(0, .3) * ci, los=los, extra=dict(elective=False)))
            evs.append(self.ev(P, y, max(0, death_doy - 15), "specialist_visit", "physician_specialist", "end_of_life", 900 * r.lognormal(0, .5)))
        return evs

    def count_children(self, H): return sum(1 for p in H["members"] if self.persons[p]["alive"] and self.persons[p]["exit"] is None and self.persons[p]["birth"].year >= 2000 and self.age(self.persons[p], 2026) <= 18)

    # ------------------------------------------------------------------ settlement of a person-year
    def settle(self, P, y, evs, H):
        r = self.r; a = self.age(P, y); ac = age_class(a); scale = self.cost_scale
        fr = P["okp"]["franchise"]; cap = COINS_CAP_CHILD if ac == "child" else COINS_CAP_ADULT
        used_fr = 0.0; used_co = 0.0
        vvg_used = {k: 0.0 for k in VVG_PRODUCTS}
        emp_full = P.get("emp_y") == "employed"
        evs.sort(key=lambda e: e["date"])
        hosp_prod = next((k for k in ("HOSP_PRIV", "HOSP_SEMI", "HOSP_GEN") if k in P["vvg"]), None)
        def res_blocks(prod, cond):
            v = P["vvg"].get(prod)
            return v is not None and v["res"] is not None and cond is not None and v["res"][0] == cond and v["res"][1] >= y
        for e in evs:
            if e["care_type"] not in ("dental_checkup", "dental_treatment", "orthodontics", "complementary_therapy", "fitness_prevention", "glasses"):
                e["gross_cost"] *= scale
            else:
                e["gross_cost"] *= (1.012) ** (y - 2024)
            g = e["gross_cost"]; e.update(insurer_okp=P["okp"]["insurer"], paid_okp=0.0, paid_canton=0.0, paid_uvg=0.0, paid_vvg=0.0,
                                         vvg_product=None, vvg_insurer=None, cost_share_franchise=0.0, cost_share_coinsurance=0.0,
                                         hospital_contribution=0.0, paid_patient_uncovered=0.0, vvg_rejection=None, submitted_to_insurer=True)
            cond = e.get("condition") or (e["diagnosis_group"] if e["diagnosis_group"] in CONDITIONS else None)
            # accident insurance (UVG) for employed persons: not visible in the health insurer's own claims
            if e.get("accident_context") and emp_full:
                e["paid_uvg"] = g; e["visible_to_health_insurer"] = False; e["okp_gross"] = 0.0; continue
            e["visible_to_health_insurer"] = True
            okp_part = 0.0
            e["submitted_to_insurer"] = True
            # small invoices below a high deductible are often never sent to the insurer
            if (e.get("okp_eligible") and e["care_type"] in ("gp_visit", "specialist_visit", "medication", "outpatient_hospital")
                    and fr >= 1000 and used_fr + g < fr and g < 400 and r.random() < .55):
                e["submitted_to_insurer"] = False; e["visible_to_health_insurer"] = False
                e["paid_patient_uncovered"] = g; e["okp_gross"] = 0.0; continue
            if e["care_type"] == "inpatient_stay":
                e["paid_canton"] = CANTON_INPATIENT_SHARE * g; okp_part = (1 - CANTON_INPATIENT_SHARE) * g
                ward = "general"
                if hosp_prod in ("HOSP_SEMI", "HOSP_PRIV") and r.random() < .9:
                    if res_blocks(hosp_prod, cond): e["vvg_rejection"] = "reservation"
                    elif cond in P["undisclosed"] and P["cond"].get(cond, 9999) < P["vvg"][hosp_prod]["start"].year and r.random() < .6:
                        e["vvg_rejection"] = "breach_of_disclosure"
                    else:
                        ward = "private" if hosp_prod == "HOSP_PRIV" else "semi_private"
                        extra = g * (.95 if ward == "private" else .6) * r.uniform(.8, 1.25)
                        e["gross_cost"] += extra; e["paid_vvg"] += extra; e["vvg_product"] = hosp_prod
                if e.get("out_of_canton"):
                    diff = .12 * g; e["gross_cost"] += diff
                    if hosp_prod: e["paid_vvg"] += diff; e["vvg_product"] = e["vvg_product"] or hosp_prod
                    else: e["paid_patient_uncovered"] += diff
                e["ward"] = ward
                if not e.get("maternity") and ac != "child" and not (ac == "young_adult" and P.get("emp_y") == "student"):
                    e["hospital_contribution"] = HOSPITAL_DAY_CONTRIBUTION * e["los_days"]
            elif e.get("okp_eligible"):
                okp_part = g
                if e["care_type"] == "glasses":
                    okp_part = min(g, 180); rest = g - okp_part
                    if "AMB" in P["vvg"] and y - P["last_glasses"] >= 3:
                        pay = min(rest, 200); e["paid_vvg"] = pay; e["vvg_product"] = "AMB"; rest -= pay; P["last_glasses"] = y
                    e["paid_patient_uncovered"] = rest
                if e.get("abroad"):
                    okp_part = .5 * g; rest = g - okp_part
                    if "AMB" in P["vvg"]: e["paid_vvg"] = rest; e["vvg_product"] = "AMB"
                    else: e["paid_patient_uncovered"] = rest
                if e["care_type"] == "rescue_transport":
                    okp_part = min(.5 * g, 5000); rest = g - okp_part
                    if "AMB" in P["vvg"]: e["paid_vvg"] = rest; e["vvg_product"] = "AMB"
                    else: e["paid_patient_uncovered"] = rest
            else:   # services outside OKP
                prod = "DENT" if e["care_type"] in ("dental_checkup", "dental_treatment", "orthodontics") else "AMB"
                pay = 0.0
                if prod in P["vvg"]:
                    if e["care_type"] == "orthodontics" and res_blocks("DENT", "orthodontics"): e["vvg_rejection"] = "reservation"
                    elif e["care_type"] == "complementary_therapy" and res_blocks("AMB", cond): e["vvg_rejection"] = "reservation"
                    elif (e["care_type"] == "complementary_therapy" and cond in P["undisclosed"]
                          and P["cond"].get(cond, 9999) < P["vvg"]["AMB"]["start"].year and r.random() < .4):
                        e["vvg_rejection"] = "breach_of_disclosure"
                    else:
                        rate, lim = {"dental_checkup": (.75 if a <= 18 else .5, 1500 if a <= 18 else 1000),
                                     "dental_treatment": (.75 if a <= 18 else .5, 1500 if a <= 18 else 1000),
                                     "orthodontics": (.75, 3000), "complementary_therapy": (.8, 2500),
                                     "fitness_prevention": (1.0, 200), "glasses": (1.0, 200)}[e["care_type"]]
                        pay = min(rate * g, max(0, lim - vvg_used[prod]))
                        if e["care_type"] == "glasses":
                            pay = pay if y - P["last_glasses"] >= 3 else 0; P["last_glasses"] = y if pay else P["last_glasses"]
                        if pay == 0 and e["vvg_rejection"] is None: e["vvg_rejection"] = "limit_reached"
                elif e["care_type"] != "fitness_prevention": e["vvg_rejection"] = None
                vvg_used[prod] += pay
                e["paid_vvg"] = pay; e["vvg_product"] = prod if pay > 0 else None
                e["paid_patient_uncovered"] = g - pay
            if e["vvg_product"]: e["vvg_insurer"] = P["vvg"][e["vvg_product"]]["insurer"] if e["vvg_product"] in P["vvg"] else None
            # cost sharing on the OKP part (maternity exempt)
            if okp_part > 0:
                cs_f = cs_c = 0.0
                if not e.get("maternity"):
                    cs_f = min(okp_part, max(0, fr - used_fr)); used_fr += cs_f
                    cs_c = min(COINSURANCE * (okp_part - cs_f), max(0, cap - used_co)); used_co += cs_c
                e["cost_share_franchise"] = cs_f; e["cost_share_coinsurance"] = cs_c
                e["paid_okp"] = okp_part - cs_f - cs_c - e["hospital_contribution"]
                if e["paid_okp"] < 0: e["hospital_contribution"] += e["paid_okp"]; e["paid_okp"] = 0.0
                e["okp_gross"] = okp_part
            else: e["okp_gross"] = 0.0
            e["okp_gross"] = round(e["okp_gross"], 2)
        return evs

    # ------------------------------------------------------------------ main loop
    def run(self):
        r = self.r
        self.dyn_hist = {}; self.K_hist = {}
        for y in YEARS + [RENEWAL_YEAR]:
            for i in INS: self.dyn_hist[(i, y)] = self.dyn[i]
            for c in CANTONS: self.K_hist[(c, y)] = self.K[c]
            for i in INS:
                for p in VVG_PRODUCTS: self.vvg_dev_hist[(i, p, y)] = self.vvg_dev[i][p]
            self.publish_tariffs(y)
            if y == RENEWAL_YEAR:
                self.renewal_decisions(y); break
            if y > YEARS[0]: self.yearly_choices(y)
            else:
                for P in self.persons.values(): P["emp_y"] = self.employment(P, y)
            self.simulate_year(y)
            print(f"{y}: persons alive {sum(1 for P in self.persons.values() if P['alive'] and P['exit'] is None):,}, events {len(self.events):,}, cost scale {self.cost_scale:.3f}", flush=True)

    def publish_tariffs(self, y):
        for i in INS:
            for c in CANTONS:
                for reg in range(1, CANTONS[c][3] + 1):
                    for ac in ("child", "young_adult", "adult"):
                        self.tariff_okp.append(dict(year=y, insurer=i, canton=c, premium_region=reg, age_class=ac,
                            premium_standard_lowest_deductible=self.okp_premium(i, c, reg, ac, y, "standard", True, 0 if ac == "child" else 300)))
            for prod in VVG_PRODUCTS:
                for b in range(len(AGE_BANDS)):
                    a = AGE_BANDS[b][0] if b else 10
                    for s in ("F", "M"):
                        p = VVG_BASE_2026[prod][b] * (1 + VVG_INDEX_GROWTH[prod]) ** (y - 2026) * INSURERS[i]["vvg_level"]
                        p *= self.vvg_dev_hist.get((i, prod, y), self.vvg_dev[i][prod])
                        if prod.startswith("HOSP") and s == "F" and b in (1, 2, 3, 4, 5): p *= INSURERS[i]["sex_rated"]
                        self.tariff_vvg.append(dict(year=y, insurer=i, product=prod, age_band=band_label(b), sex=s, premium_monthly_reference=round(p, 2)))

    def simulate_year(self, y):
        r = self.r; ycost = []; realised = {c: [] for c in CANTONS}
        ins_fin = {i: dict(prem=0.0, claims=0.0, n=0.0, vvg_prem=0.0, vvg_claims=0.0) for i in INS}
        rows_ra = []
        # moves between cantons (household level, 1 January)
        for H in self.households.values():
            if r.random() < .008 and any(self.persons[p]["alive"] and self.persons[p]["exit"] is None for p in H["members"]):
                same = [c for c in CANTONS if LANG[c] == LANG[H["canton"]] and c != H["canton"]]
                pool = same if (r.random() < .75 and same) else [c for c in CANTONS if c != H["canton"]]
                w = np.array([CANTONS[c][1] for c in pool]); H["canton"] = pool[r.choice(len(pool), p=w / w.sum())]
                nreg = CANTONS[H["canton"]][3]; H["region"] = int(r.integers(1, nreg + 1)); H["moved"] = y
        # immigration (new households during the year)
        n_alive = sum(1 for P in self.persons.values() if P["alive"] and P["exit"] is None)
        for _ in range(r.poisson(.016 * n_alive / 2.2)):
            self.new_household(y, dayofyear_date(y, int(r.integers(0, 330))), "immigration")
        year_events = []
        ctx = dict(ycost=ycost, realised=realised, fin=ins_fin, ra=rows_ra, events=year_events, newborns=[])
        for P in list(self.persons.values()):
            if not P["alive"] or P["exit"] is not None or P["okp"] is None: continue
            if self.age(P, y) < 0: continue
            self.process_person(P, y, ctx)
        for K in ctx["newborns"]:
            self.process_person(K, y, ctx)
        # calibrate cost level (online): rescale this year's amounts to the national target
        tot = sum(c for c, e in ycost); expo = sum(e for c, e in ycost)
        factor = COST_TARGET[y] / (tot / expo)
        for e in year_events:
            for k in ("gross_cost", "paid_okp", "paid_canton", "paid_uvg", "paid_vvg", "cost_share_franchise", "cost_share_coinsurance",
                      "hospital_contribution", "paid_patient_uncovered", "okp_gross"):
                if e["care_type"] in ("dental_checkup", "dental_treatment", "orthodontics", "complementary_therapy", "fitness_prevention", "glasses"):
                    continue
                e[k] = round(e[k] * (factor if abs(factor - 1) > .002 else 1), 2)
        # the settlement above used the previous scale; re-settle cost sharing exactly after rescaling
        self.fix_cost_sharing(year_events, y)
        self.cost_scale *= factor
        self.events += year_events
        # recompute person-year outcome columns from the final events
        self.attach_outcomes(y, year_events)
        # risk equalisation and next year's prices
        net_by = {}
        for e in year_events:
            net_by[e["person_id"]] = net_by.get(e["person_id"], 0) + e["paid_okp"]
            if e["paid_vvg"] and e["vvg_insurer"]: ins_fin[e["vvg_insurer"]]["vvg_claims"] += e["paid_vvg"]
        ra = pd.DataFrame(rows_ra, columns=["ins", "canton", "ab", "sex", "hosp", "pcg", "pid", "exf"])
        ra["net"] = ra.pid.map(net_by).fillna(0.0)
        for i in INS: ins_fin[i]["claims"] = float(ra[ra.ins == i].net.sum())
        cell = ra.groupby(["canton", "ab", "sex"]).apply(lambda g: g.net.sum() / g.exf.sum()).rename("cell")
        ra = ra.join(cell, on=["canton", "ab", "sex"])
        base = ra.net.sum() / ra.exf.sum()
        m_h = (ra[ra.hosp == 1].net.sum() / ra[ra.hosp == 1].exf.sum()) / base if (ra.hosp == 1).any() else 1
        m_p = (ra[ra.pcg == 1].net.sum() / ra[ra.pcg == 1].exf.sum()) / base if (ra.pcg == 1).any() else 1
        ra["expected"] = ra.cell * (1 + .35 * (m_h - 1) * ra.hosp) * (1 + .35 * (m_p - 1) * ra.pcg) * ra.exf
        ra["expected"] *= ra.groupby("canton").net.transform("sum") / ra.groupby("canton").expected.transform("sum")
        ra["canton_mean"] = ra.groupby("canton").net.transform("sum") / ra.groupby("canton").exf.transform("sum") * ra.exf
        ra["transfer"] = ra.expected - ra.canton_mean
        tr = ra.groupby("ins").transfer.sum()
        for i in INS:
            f = ins_fin[i]; claims = f["claims"]
            lr = (claims - tr.get(i, 0)) / f["prem"] if f["prem"] else 1
            self.fin.append(dict(year=y, insurer=i, insured_years=round(f["n"], 1), okp_premium_income=round(f["prem"]), okp_net_benefits=round(claims),
                                 risk_equalisation_received=round(tr.get(i, 0)), okp_loss_ratio_after_ra=round(lr, 3),
                                 vvg_premium_income=round(f["vvg_prem"]), vvg_benefits=round(f["vvg_claims"] * 1.0),
                                 vvg_loss_ratio=round(f["vvg_claims"] / f["vvg_prem"], 3) if f["vvg_prem"] else None))
            self.dyn[i] = float(np.clip(.75 * self.dyn[i] + .25 * (lr - .93) + r.normal(0, .008), -.10, .12))
            vlr = f["vvg_claims"] / f["vvg_prem"] if f["vvg_prem"] else .7
            for p in VVG_PRODUCTS:   # FINMA: tariffs follow the insurer's own cost experience, bounded
                self.vvg_dev[i][p] *= 1 + float(np.clip(.25 * (vlr - .75) + r.normal(0, .01), -.03, .04))
        # premium calibration: realised mean adult premium -> official cantonal mean
        for c in CANTONS:
            if len(realised[c]) >= 20:
                self.K[c] *= float(np.clip(canton_adult_mean(c, y) / np.mean(realised[c]), .96, 1.04)) ** .6
        # emigration (household level, end of year)
        for H in self.households.values():
            alive = [self.persons[p] for p in H["members"] if self.persons[p]["alive"] and self.persons[p]["exit"] is None]
            if alive and r.random() < .006 * (2 if max(self.age(P, y) for P in alive) < 45 else .5):
                for P in alive:
                    P["exit"] = D(y, 12, 31); P["exit_reason"] = "emigration"
                    self.close_policy(P["okp"]["policy"], P["exit"], "emigration")
                    for v in P["vvg"].values(): self.close_policy(v["policy"], P["exit"], "emigration")

    def process_person(self, P, y, ctx):
        r = self.r; H = self.hh(P); a = self.age(P, y)
        start_doy = max(0, (P["entry"] - D(y, 1, 1)).days) if P["entry"].year == y else 0
        P["hh_couple"] = sum(1 for p in H["members"] if self.persons[p]["alive"] and self.age(self.persons[p], y) >= 19) >= 2
        self.onsets(P, y)
        dies = r.random() < self.qx(P, y) * (1 - start_doy / 365)
        end_doy = int(r.integers(start_doy + 1, 366)) if dies else 365
        evs, birth = self.simulate_health(P, y, H, start_doy, end_doy)
        evs += P.pop("birth_events", [])
        if dies: evs += self.terminal_events(P, y, H, end_doy - 1)
        evs = self.settle(P, y, evs, H)
        for e in evs:   # a claim reveals an undisclosed pre-existing condition: the insurer terminates the contract
            if e.get("vvg_rejection") == "breach_of_disclosure":
                prod = "AMB" if e["care_type"] == "complementary_therapy" else next((k for k in P["vvg"] if k.startswith("HOSP")), None)
                if prod and prod in P["vvg"]:
                    self.close_policy(P["vvg"][prod]["policy"], e["date"], "breach_of_disclosure"); del P["vvg"][prod]; P["bonus"].pop(prod, None)
        ctx["events"].extend(evs)
        okp_gross = sum(e["okp_gross"] for e in evs)
        P["last_okp_cost"] = okp_gross / max(self.cost_scale, 1e-9)
        ac = age_class(a); o = P["okp"]; exf = (end_doy - start_doy) / 365
        prem_m = self.okp_premium(o["insurer"], H["canton"], H["region"], ac, y, o["model"], o["accident"], o["franchise"])
        vvg_prem = {}
        for k, v in P["vvg"].items():
            if v["start"].year > y: continue
            pm = self.vvg_premium(v["insurer"], k, P, y, H["canton"], v["tariff_start"]) * P["bonus"].get(k, 1.0)
            if a <= 18 and INSURERS[v["insurer"]]["family_disc"] and self.count_children(H) >= 2: pm *= 1 - INSURERS[v["insurer"]]["family_disc"]
            vvg_prem[k] = round(pm, 2)
        subsidy = self.ipv(P, y, H, prem_m * 12)
        if ac == "adult": ctx["realised"][H["canton"]].append(prem_m)
        hosp_nights = sum(e["los_days"] for e in evs if e["care_type"] == "inpatient_stay" and e["visible_to_health_insurer"])
        pcg = int(sum(1 for e in evs if e["care_type"] == "medication") >= 3)
        fin = ctx["fin"][o["insurer"]]
        fin["prem"] += 12 * prem_m * exf; fin["n"] += exf
        ctx["ra"].append((o["insurer"], H["canton"], min(a // 5, 18), P["sex"], int(P.get("hosp_prev", 0) > 3), P.get("pcg_prev", 0), P["pid"], exf))
        for k, pm in vvg_prem.items(): ctx["fin"][P["vvg"][k]["insurer"]]["vvg_prem"] += 12 * pm * exf if k in P["vvg"] else 0
        ctx["ycost"].append((okp_gross, exf))
        for k in list(P["bonus"]):
            if k not in P["vvg"]: P["bonus"].pop(k); continue
            claimed = sum(e["paid_vvg"] for e in evs if e["vvg_product"] == k and e["care_type"] != "fitness_prevention")
            sysb = INSURERS[P["vvg"][k]["insurer"]]["bonus"]
            if sysb == "ladder": P["bonus"][k] = min(1.0, P["bonus"][k] + .1) if claimed > 0 else max(.5, P["bonus"][k] - .1)
            elif sysb == "claimfree20": P["bonus"][k] = 1.0 if claimed > 0 else .8
            elif sysb == "two_level25":
                P.setdefault("cf_years", 0); P["cf_years"] = 0 if claimed > 300 else P["cf_years"] + 1
                P["bonus"][k] = 1.0 if (claimed > 300 or (P["bonus"][k] == 1.0 and P["cf_years"] < 3)) else .75
        self.person_years.append(self.py_row(P, y, H, evs, prem_m, vvg_prem, subsidy, start_doy, end_doy, dies, hosp_nights, pcg))
        P["hosp_prev"], P["pcg_prev"] = hosp_nights, pcg
        if not dies: self.vvg_applications(P, y, H)
        if birth is not None and not dies: ctx["newborns"].append(self.newborn(P, H, birth))
        if dies:
            P["alive"] = False; P["exit"] = dayofyear_date(y, end_doy - 1); P["exit_reason"] = "death"
            self.close_policy(o["policy"], P["exit"], "death")
            for v in P["vvg"].values(): self.close_policy(v["policy"], P["exit"], "death")

    def fix_cost_sharing(self, evs, y):
        by = {}
        for e in evs: by.setdefault(e["person_id"], []).append(e)
        for pid, es in by.items():
            P = self.persons[pid]; a = self.age(P, y); ac = age_class(a)
            fr = P["okp"]["franchise"]; cap = COINS_CAP_CHILD if ac == "child" else COINS_CAP_ADULT
            uf = uc = 0.0
            for e in sorted(es, key=lambda e: e["date"]):
                part = e["okp_gross"]
                if part <= 0: continue
                cs_f = cs_c = 0.0
                if not e.get("maternity"):
                    cs_f = min(part, max(0, fr - uf)); uf += cs_f
                    cs_c = min(COINSURANCE * (part - cs_f), max(0, cap - uc)); uc += cs_c
                hc = HOSPITAL_DAY_CONTRIBUTION * e["los_days"] if e["hospital_contribution"] > 0 else 0
                e["cost_share_franchise"], e["cost_share_coinsurance"] = round(cs_f, 2), round(cs_c, 2)
                e["paid_okp"] = round(max(0, part - cs_f - cs_c - hc), 2); e["hospital_contribution"] = round(min(hc, part - cs_f - cs_c), 2)

    def ipv(self, P, y, H, annual):
        a = self.age(P, y); inc = H["income"]
        rate = 0.0
        if inc == 1: rate = .9 if a <= 25 else .7
        elif inc == 2: rate = .8 if a <= 18 else (.5 if (a <= 25 and P["pid"] % 2) else (.3 if P["pid"] % 4 == 0 else 0))
        take = (P["pid"] * 7919) % 100 < 85
        return round(annual * rate, 0) if take else 0.0

    def py_row(self, P, y, H, evs, prem_m, vvg_prem, subsidy, sd, ed, dies, hosp_nights, pcg):
        o = P["okp"]; a = self.age(P, y)
        row = dict(person_id=P["pid"], year=y, household_id=P["hid"], age=a, age_class=age_class(a), sex=P["sex"],
                   canton=H["canton"], premium_region=H["region"], municipality_type=H["mtype"], language=LANG[H["canton"]],
                   household_size=sum(1 for p in H["members"] if self.persons[p]["alive"] and self.persons[p]["exit"] is None),
                   income_band=H["income"], employment=P.get("emp_y"), insured_days=ed - sd,
                   okp_insurer=o["insurer"], okp_model=o["model"], deductible=o["franchise"], accident_cover=o["accident"],
                   okp_premium_monthly=prem_m, premium_subsidy_annual=subsidy,
                   vvg_products=";".join(sorted(k for k in vvg_prem)), vvg_premium_monthly_total=round(sum(vvg_prem.values()), 2),
                   **{f"has_{k.lower()}": (k in vvg_prem) for k in VVG_PRODUCTS},
                   **{f"premium_{k.lower()}_monthly": vvg_prem.get(k, 0.0) for k in VVG_PRODUCTS},
                   vvg_insurer=next((P["vvg"][k]["insurer"] for k in ("HOSP_PRIV", "HOSP_SEMI", "HOSP_GEN", "AMB", "DENT") if k in vvg_prem), None),
                   bonus_factor_amb=P["bonus"].get("AMB") if "AMB" in vvg_prem else None,
                   bonus_factor_hosp=next((P["bonus"].get(k) for k in ("HOSP_PRIV", "HOSP_SEMI", "HOSP_GEN") if k in vvg_prem and k in P["bonus"]), None),
                   n_vvg_reservations=sum(1 for k, v in P["vvg"].items() if v["res"] and v["res"][1] >= y),
                   ra_hospital_prev_year_gt3_nights=int(P.get("hosp_prev", 0) > 3), ra_pharma_cost_group=P.get("pcg_prev", 0),
                   died=dies)
        return row

    def attach_outcomes(self, y, evs):
        agg = {}
        for e in evs:
            g = agg.setdefault(e["person_id"], dict(okp_gross=0., paid_okp=0., cost_share=0., hosp_contrib=0., paid_canton=0., paid_vvg=0.,
                                                    paid_uvg=0., uncovered=0., gp=0, spec=0, stays=0, days=0, acc=0, n_events=0))
            g["okp_gross"] += e["okp_gross"]; g["paid_okp"] += e["paid_okp"]; g["cost_share"] += e["cost_share_franchise"] + e["cost_share_coinsurance"]
            g["hosp_contrib"] += e["hospital_contribution"]; g["paid_canton"] += e["paid_canton"]; g["paid_vvg"] += e["paid_vvg"]
            g["paid_uvg"] += e["paid_uvg"]; g["uncovered"] += e["paid_patient_uncovered"]; g["n_events"] += 1
            g["gp"] += e["care_type"] == "gp_visit"; g["spec"] += e["care_type"] == "specialist_visit"
            if e["care_type"] == "inpatient_stay": g["stays"] += 1; g["days"] += e["los_days"]
            g["acc"] += e["accident_context"] is not None and e["care_type"] in ("accident_outpatient", "inpatient_stay")
        for row in self.person_years:
            if row["year"] != y: continue
            g = agg.get(row["person_id"], {})
            row.update(okp_gross_cost=round(g.get("okp_gross", 0), 2), okp_benefits_paid=round(g.get("paid_okp", 0), 2),
                       cost_sharing=round(g.get("cost_share", 0), 2), hospital_contribution=round(g.get("hosp_contrib", 0), 2),
                       canton_inpatient_share=round(g.get("paid_canton", 0), 2), vvg_benefits_paid=round(g.get("paid_vvg", 0), 2),
                       uvg_benefits_paid=round(g.get("paid_uvg", 0), 2), patient_paid_uncovered=round(g.get("uncovered", 0), 2),
                       n_gp_visits=g.get("gp", 0), n_specialist_visits=g.get("spec", 0), n_inpatient_stays=g.get("stays", 0),
                       inpatient_days=g.get("days", 0), n_accidents=g.get("acc", 0), n_events=g.get("n_events", 0))

    def vvg_applications(self, P, y, H):
        r = self.r; a = self.age(P, y); inc = H["income"]; ins = P["okp"]["insurer"]
        def go(prod, p, channel="existing_customer"):
            if prod not in P["vvg"] and r.random() < p:
                tgt = ins if r.random() < .8 else self.choose_insurer(H["canton"])
                self.apply_vvg(P, prod, tgt, dayofyear_date(y, int(r.integers(0, 364))), channel)
        hosp = any(k.startswith("HOSP") for k in P["vvg"])
        if a <= 18:
            if 3 <= a <= 9: go("DENT", .05)
            go("AMB", .02)
        else:
            go("AMB", .02 + .015 * (inc >= 3))
            if not hosp and 22 <= a <= 60: go("HOSP_SEMI", .006 + .006 * (inc >= 3) + .006 * (inc == 4))
            if not hosp: go("HOSP_GEN", .008)
            if "HOSP_SEMI" in P["vvg"] and inc == 4 and a <= 55 and r.random() < .01:
                self.apply_vvg(P, "HOSP_PRIV", P["vvg"]["HOSP_SEMI"]["insurer"], dayofyear_date(y, int(r.integers(0, 364))), "upgrade")
                if "HOSP_PRIV" in P["vvg"]:
                    self.close_policy(P["vvg"]["HOSP_SEMI"]["policy"], P["vvg"]["HOSP_PRIV"]["start"], "upgrade"); del P["vvg"]["HOSP_SEMI"]
            go("DENT", .004)

    def newborn(self, mother, H, bdate):
        r = self.r
        K = self.new_person(mother["hid"], r.choice(["F", "M"]), bdate, bdate, "birth")
        H["members"].append(K["pid"])
        K["okp"] = dict(insurer=mother["okp"]["insurer"], model=mother["okp"]["model"] if mother["okp"]["model"] != "hmo" else "family_doctor",
                        franchise=0, accident=True, start=bdate, policy=self.open_policy(K, "OKP", mother["okp"]["insurer"], bdate))
        K["emp_y"] = "child"
        # newborn's own birth stay and possible neonatal care
        y = bdate.year; doy = (bdate - D(y, 1, 1)).days
        evs = [self.ev(K, y, doy, "inpatient_stay", "hospital_inpatient", "newborn", 2600 * r.lognormal(0, .3), los=4, extra=dict(maternity=True, elective=False))]
        if r.random() < .06: evs.append(self.ev(K, y, doy, "inpatient_stay", "hospital_inpatient", "neonatal_care", r.lognormal(math.log(45000), .6), los=int(r.integers(7, 40)), extra=dict(maternity=True, elective=False)))
        # prenatal registration: supplementary cover without health questions
        if mother["vvg"] and r.random() < .75:
            ins = mother["vvg"].get("AMB", next(iter(mother["vvg"].values())))["insurer"]
            self.apply_vvg(K, "AMB", ins, bdate, "prenatal")
            if r.random() < .3: self.apply_vvg(K, "HOSP_GEN" if r.random() < .7 else "HOSP_SEMI", ins, bdate, "prenatal")
        K["birth_events"] = evs
        return K

    # ------------------------------------------------------------------ renewal 2027 (labels)
    def renewal_decisions(self, y):
        snap = {pid: (dict(P["okp"]), {k: dict(v) for k, v in P["vvg"].items()}) for pid, P in self.persons.items()
                if P["alive"] and P["exit"] is None and P["okp"]}
        out = self.yearly_choices(y, renewal=True)
        for pid, d in out.items():
            P = self.persons[pid]; H = self.hh(P); old, new = d["old"], d["new"]; a = self.age(P, y)
            vvg_old = snap[pid][1]
            row = dict(person_id=pid, household_id=P["hid"], age_2027=a, sex=P["sex"], canton=H["canton"], premium_region=H["region"],
                       okp_insurer_2026=old["insurer"], okp_model_2026=old["model"], deductible_2026=old["franchise"],
                       okp_premium_2026_monthly=self.okp_premium(old["insurer"], H["canton"], H["region"], age_class(a - 1), y - 1, old["model"], old["accident"], old["franchise"]),
                       okp_premium_2027_same_cover_monthly=self.okp_premium(old["insurer"], H["canton"], H["region"], age_class(a), y, old["model"], old["accident"], old["franchise"]),
                       cheapest_insurer_2027=d["info"]["cheapest_insurer"],
                       cheapest_premium_2027_same_cover_monthly=min(self.okp_premium(i, H["canton"], H["region"], age_class(a), y, old["model"], old["accident"], old["franchise"]) for i in INS),
                       household_premium_change=round(d["info"]["premium_change"], 4),
                       label_switched_okp_insurer=d["switched"], label_new_okp_insurer=new["insurer"],
                       label_deductible_2027=new["franchise"], label_model_2027=new["model"])
            for k in VVG_PRODUCTS:
                if k in vvg_old:
                    v = vvg_old[k]
                    row[f"{k.lower()}_premium_2026_monthly"] = round(self.vvg_premium(v["insurer"], k, P, y - 1, H["canton"], v["tariff_start"]), 2)
                    row[f"{k.lower()}_premium_2027_monthly"] = round(self.vvg_premium(v["insurer"], k, P, y, H["canton"], v["tariff_start"]), 2)
                    ch = dict(d.get("vvg_changes", [])).get(k)
                    row[f"label_{k.lower()}_2027"] = ch or "keep"
                else:
                    row[f"label_{k.lower()}_2027"] = "not_held"
            self.renewal.append(row)

    # ------------------------------------------------------------------ export
    def export(self, out):
        os.makedirs(out, exist_ok=True); os.makedirs(os.path.join(out, "ground_truth"), exist_ok=True)
        persons = pd.DataFrame([dict(person_id=P["pid"], household_id=P["hid"], sex=P["sex"], birth_date=P["birth"], entry_date=P["entry"],
                                     entry_reason=P["entry_reason"], exit_date=P["exit"], exit_reason=P["exit_reason"]) for P in self.persons.values()])
        truth = pd.DataFrame([dict(person_id=P["pid"], frailty=round(P["frailty"], 3), risk_aversion=round(P["risk_av"], 3),
                                   complementary_medicine_affinity=round(P["altmed"], 3), smoker=P["smoker"], bmi=round(P["bmi"], 1),
                                   dental_poor=P["dental_poor"], undisclosed_conditions=";".join(sorted(P["undisclosed"])),
                                   **{f"onset_{c}": P["cond"].get(c) for c in CONDITIONS}) for P in self.persons.values()])
        hh = pd.DataFrame([dict(household_id=h, canton_2026=H["canton"], premium_region_2026=H["region"], municipality_type=H["mtype"],
                                income_band=H["income"]) for h, H in self.households.items()])
        py = pd.DataFrame(self.person_years)
        ev = pd.DataFrame(self.events)
        ev = ev[["event_id", "person_id", "date", "year", "care_type", "provider", "diagnosis_group", "condition", "accident_context", "ward", "los_days",
                 "gross_cost", "okp_gross", "paid_okp", "cost_share_franchise", "cost_share_coinsurance", "hospital_contribution", "paid_canton",
                 "paid_vvg", "vvg_product", "vvg_insurer", "vvg_rejection", "paid_uvg", "paid_patient_uncovered", "insurer_okp", "visible_to_health_insurer", "submitted_to_insurer"]]
        ev = ev.sort_values(["person_id", "date"]).reset_index(drop=True)
        money = ["gross_cost", "okp_gross", "paid_okp", "cost_share_franchise", "cost_share_coinsurance", "hospital_contribution", "paid_canton",
                 "paid_vvg", "paid_uvg", "paid_patient_uncovered"]
        ev[money] = ev[money].astype(float).round(2)
        pol = pd.DataFrame(self.policies.values())
        app = pd.DataFrame(self.applications)
        tokp = pd.DataFrame(self.tariff_okp); tvvg = pd.DataFrame(self.tariff_vvg)
        rules = pd.DataFrame([dict(insurer=i, insurer_name=INSURERS[i]["name"], deductible_rebate_share_of_max=round(self.fr_rate[i], 3),
                                   **{f"model_factor_{m}": round(MODEL_FACTOR[m] * self.model_noise[i][m], 4) for m in MODEL_FACTOR},
                                   accident_excluded_factor=ACCIDENT_EXCLUDED_FACTOR, vvg_bonus_system=INSURERS[i]["bonus"],
                                   vvg_female_factor_hospital_19_45=INSURERS[i]["sex_rated"], vvg_entry_age_tariff_from_50=INSURERS[i]["entry_age_tariff"],
                                   vvg_max_entry_age_hospital=INSURERS[i]["max_entry_hosp"], vvg_family_discount_children=INSURERS[i]["family_disc"])
                              for i in INS])
        vreg = pd.DataFrame([dict(insurer=i, canton=c, vvg_region_factor=round(self.vvg_region[i][c], 4)) for i in INS for c in CANTONS])
        cant = pd.DataFrame([dict(canton=c, name=v[0], population_share_pct=v[1], language=v[2], n_premium_regions=v[3],
                                  official_mean_adult_premium_2026=v[4], official_mean_adult_premium_2027=v[5]) for c, v in CANTONS.items()])
        fin = pd.DataFrame(self.fin); ren = pd.DataFrame(self.renewal)
        tables = dict(persons=persons, households=hh, person_years=py, events=ev, policies=pol, applications=app,
                      tariffs_okp=tokp, tariffs_vvg=tvvg, tariff_rules=rules, vvg_region_factors=vreg, cantons=cant,
                      insurer_financials=fin, renewal_2027=ren)
        for name, df in tables.items():
            df.to_csv(os.path.join(out, f"{name}.csv.gz" if name == "events" else f"{name}.csv"), index=False)
            df.to_parquet(os.path.join(out, f"{name}.parquet"), index=False)
        truth.to_csv(os.path.join(out, "ground_truth", "person_latent_truth.csv"), index=False)
        return tables


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="data"); ap.add_argument("--households", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=7); a = ap.parse_args()
    W = World(a.households, a.seed); W.run(); W.export(a.out)
