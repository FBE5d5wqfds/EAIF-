"""Calibration parameters for the synthetic Swiss health-insurance case study.

Every number marked [SRC] is taken from a public source (listed in README.md); every other number
is an assumption chosen to be plausible and documented here so instructors can change it.
"""
import numpy as np

YEARS = list(range(2014, 2027))      # simulated calendar years (claims observed)
RENEWAL_YEAR = 2027                  # tariffs announced in autumn 2026; renewal decisions are the labels

# ---------------------------------------------------------------------------------------------
# Cantons: population share (approx. 2024), language, number of OKP premium regions (simplified),
# mean monthly OKP premium for ADULTS 26+ in 2026 and 2027 [SRC: BAG via lohncomputer.ch, Sept 2026]
# ---------------------------------------------------------------------------------------------
CANTONS = {
    #     name                 pop%   lang  regions  adult2026 adult2027
    "ZH": ("Zürich",           18.0, "de", 3, 451.30, 477.00),
    "BE": ("Bern",             12.0, "de", 3, 470.70, 494.40),
    "VD": ("Vaud",              9.6, "fr", 2, 526.60, 543.50),
    "AG": ("Aargau",            8.1, "de", 1, 440.20, 464.70),
    "SG": ("St. Gallen",        5.9, "de", 3, 407.20, 427.40),
    "GE": ("Genève",            5.8, "fr", 1, 585.40, 610.60),
    "LU": ("Luzern",            4.8, "de", 3, 403.90, 422.20),
    "TI": ("Ticino",            4.0, "it", 2, 582.30, 603.60),
    "VS": ("Valais",            4.0, "fr", 2, 436.10, 460.90),
    "FR": ("Fribourg",          3.8, "fr", 2, 442.60, 465.50),
    "BL": ("Basel-Landschaft",  3.3, "de", 2, 522.60, 544.50),
    "TG": ("Thurgau",           3.3, "de", 1, 413.00, 433.20),
    "SO": ("Solothurn",         3.2, "de", 2, 466.70, 493.50),
    "GR": ("Graubünden",        2.3, "de", 3, 399.80, 415.60),
    "BS": ("Basel-Stadt",       2.2, "de", 1, 546.10, 570.60),
    "NE": ("Neuchâtel",         2.0, "fr", 1, 530.80, 558.80),
    "SZ": ("Schwyz",            1.9, "de", 2, 399.20, 418.50),
    "ZG": ("Zug",               1.5, "de", 1, 311.20, 324.90),
    "SH": ("Schaffhausen",      0.95,"de", 2, 444.40, 470.60),
    "JU": ("Jura",              0.85,"fr", 1, 520.50, 551.00),
    "AR": ("Appenzell A.Rh.",   0.64,"de", 1, 406.10, 422.30),
    "NW": ("Nidwalden",         0.50,"de", 1, 376.20, 397.20),
    "GL": ("Glarus",            0.47,"de", 1, 415.40, 426.50),
    "OW": ("Obwalden",          0.44,"de", 1, 371.10, 386.70),
    "UR": ("Uri",               0.42,"de", 1, 361.60, 377.70),
    "AI": ("Appenzell I.Rh.",   0.19,"de", 1, 321.40, 340.50),
}
NATIONAL_ADULT_2026 = 464.80         # [SRC] BAG: 487.60 in 2027 = +22.80 vs 2026

# National change of the mean OKP premium vs previous year [SRC: BAG annual announcements]
PREMIUM_GROWTH = {2015: .040, 2016: .040, 2017: .045, 2018: .040, 2019: .012, 2020: .002, 2021: .005,
                  2022: -.002, 2023: .066, 2024: .087, 2025: .060, 2026: .044, 2027: .050}

# OKP age classes and their premium relative to adults [SRC: BAG 2027 means 128.10 / 338.80 / 487.60]
AGE_CLASS_FACTOR = {"child": 128.10 / 487.60, "young_adult": 338.80 / 487.60, "adult": 1.0}
REGION_FACTOR = {1: 1.04, 2: 0.96, 3: 0.91}     # assumption: within-canton premium regions

# Deductibles ("franchise") and maximum rebate = 70% of the extra risk taken [SRC: BAG fact sheet]
FRANCHISES_ADULT = [300, 500, 1000, 1500, 2000, 2500]
FRANCHISES_CHILD = [0, 100, 200, 300, 400, 500, 600]
COINSURANCE, COINS_CAP_ADULT, COINS_CAP_CHILD = 0.10, 700, 350     # [SRC: KVG Art. 64, KVV Art. 103]
HOSPITAL_DAY_CONTRIBUTION = 15                                     # CHF/day for adults [SRC: KVV Art. 104]
CANTON_INPATIENT_SHARE = 0.55                                      # canton pays >=55% of inpatient DRG [SRC: KVG Art. 49a]

# Insurance models: premium factor (assumed typical rebates) and adoption
MODEL_FACTOR = {"standard": 1.00, "family_doctor": 0.90, "hmo": 0.84, "telmed": 0.87}
ACCIDENT_EXCLUDED_FACTOR = 0.93          # employed >=8h/week may suspend accident cover (UVG covers them)

# Target gross OKP benefits per insured person and year, CHF [SRC: BAG 2024 = 391/month = 4692/yr;
# +5.3% in 2025, +4.7% expected 2026; earlier years interpolated at ~2.8%/yr]
COST_TARGET = {2024: 4692.0}
for y in range(2023, 2013, -1):
    COST_TARGET[y] = COST_TARGET[y + 1] / 1.028
COST_TARGET[2025] = 4692.0 * 1.053
COST_TARGET[2026] = COST_TARGET[2025] * 1.047

# ---------------------------------------------------------------------------------------------
# Fictional insurers (names invented; behaviour inspired by publicly described product features)
# level: relative OKP price position; affinity: language regions where the insurer is strong
# vvg: supplementary tariff features
# ---------------------------------------------------------------------------------------------
INSURERS = {
    "ARV": dict(name="Arvena",    share=.17, level=.00,  affinity={"de": 1.0, "fr": 1.0, "it": .8},
                bonus="ladder", sex_rated=1.00, entry_age_tariff=False, max_entry_hosp=65, strict=0.0,  family_disc=.10, vvg_level=1.00),
    "BRQ": dict(name="Bergquell", share=.15, level=.03,  affinity={"de": 1.3, "fr": .6, "it": .6},
                bonus="claimfree20", sex_rated=1.30, entry_age_tariff=False, max_entry_hosp=60, strict=0.2, family_disc=.10, vvg_level=1.08),
    "LEM": dict(name="Lemanis",   share=.14, level=-.02, affinity={"de": .5, "fr": 2.4, "it": .9},
                bonus="none", sex_rated=1.00, entry_age_tariff=False, max_entry_hosp=65, strict=0.0,  family_disc=.15, vvg_level=0.95),
    "NRW": dict(name="Nordwind",  share=.13, level=.05,  affinity={"de": 1.2, "fr": .8, "it": .7},
                bonus="none", sex_rated=1.90, entry_age_tariff=False, max_entry_hosp=55, strict=0.6, family_disc=.00, vvg_level=1.15),
    "SOR": dict(name="Sorell",    share=.12, level=-.06, affinity={"de": 1.0, "fr": 1.1, "it": 1.0},
                bonus="none", sex_rated=1.00, entry_age_tariff=False, max_entry_hosp=50, strict=0.4, family_disc=.00, vvg_level=0.90),
    "TLW": dict(name="Talwyn",    share=.11, level=.01,  affinity={"de": 1.2, "fr": .7, "it": .8},
                bonus="none", sex_rated=1.00, entry_age_tariff=True,  max_entry_hosp=69, strict=0.2, family_disc=.10, vvg_level=1.10),
    "UST": dict(name="Ustra",     share=.10, level=-.03, affinity={"de": 1.3, "fr": .5, "it": .5},
                bonus="two_level25", sex_rated=1.30, entry_age_tariff=False, max_entry_hosp=70, strict=0.1, family_disc=.10, vvg_level=1.00),
    "VIR": dict(name="Vireo",     share=.08, level=.02,  affinity={"de": .7, "fr": .8, "it": 3.0},
                bonus="none", sex_rated=1.00, entry_age_tariff=False, max_entry_hosp=65, strict=0.1, family_disc=.10, vvg_level=1.02),
}

# ---------------------------------------------------------------------------------------------
# Supplementary (VVG) products, 2026 base monthly premiums (Bern level, men, before discounts).
# Hospital levels follow published comparisons [SRC: expat-savvy hospital insurance cost index 2026]
# ---------------------------------------------------------------------------------------------
VVG_PRODUCTS = ["AMB", "HOSP_GEN", "HOSP_SEMI", "HOSP_PRIV", "DENT"]
AGE_BANDS = [(0, 18), (19, 25), (26, 30), (31, 35), (36, 40), (41, 45), (46, 50), (51, 55),
             (56, 60), (61, 65), (66, 70), (71, 75), (76, 80), (81, 120)]
VVG_BASE_2026 = {
    #            0-18 19-25 26-30 31-35 36-40 41-45 46-50 51-55 56-60 61-65 66-70 71-75 76-80 81+
    "HOSP_SEMI": [18,  42,   68,   72,   80,   92,  112,  138,  170,  210,  262,  320,  390,  460],
    "HOSP_PRIV": [30,  70,  112,  120,  135,  155,  185,  225,  280,  345,  430,  520,  610,  700],
    "HOSP_GEN":  [3,    7,    9,   10,   11,   13,   15,   18,   22,   26,   31,   36,   42,   48],
    "AMB":       [11,  18,   22,   23,   24,   26,   29,   33,   37,   42,   47,   52,   56,   60],
    "DENT":      [24,  30,   34,   35,   36,   38,   40,   42,   44,   46,   48,   50,   52,   54],
}
VVG_INDEX_GROWTH = {"HOSP_SEMI": .022, "HOSP_PRIV": .025, "HOSP_GEN": .015, "AMB": .018, "DENT": .015}

CONDITIONS = ["cardiovascular", "diabetes", "respiratory", "mental", "musculoskeletal", "cancer", "dementia"]
