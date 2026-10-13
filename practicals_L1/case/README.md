# Adaptive pricing in Swiss health insurance: a synthetic case study and dataset

**What this is.** A synthetic but realistic dataset of **7,946 people in 3,628 households** living in all 26 cantons. It follows them from **2014 to 2026** and adds the **1 January 2027 renewal**. Each person has a full history of:
- their **basic health insurance** (OKP/KVG/LAMal): insurer, deductible, insurance model, accident cover, premium and premium subsidy;
- their **supplementary policies** (VVG/LCA): applications, underwriting decisions, exclusions ("reservations"), premiums, bonus levels, cancellations and downgrades;
- every **illness, accident, birth, hospital stay and death**, recorded as about 950,000 invoices. Each invoice is split between basic insurance, canton, supplementary insurer, accident insurer and patient.

Between 6,000 and 6,700 people are insured in any given year. Premiums are calibrated to the official 2026 and 2027 cantonal averages, and costs to the Federal Office of Public Health's 2024 figure of CHF 391 per insured person per month.

**Everything is fictional.** No real person is represented. The eight insurers (Arvena, Bergquell, Lemanis, Nordwind, Sorell, Talwyn, Ustra, Vireo) are invented; their behaviour is inspired by product features that Swiss insurers describe publicly. The dataset contains no real health records.

---

## 1. Why health insurance is a good case for adaptive pricing

Switzerland runs **two pricing regimes side by side**, so one dataset can teach both regulated and risk-based pricing.

| | Basic insurance (OKP, KVG) | Supplementary insurance (VVG/LCA) |
|---|---|---|
| Access | Mandatory; insurers **must accept everyone** | Private law; insurers **may decline without giving reasons** |
| What the premium may depend on | Insurer × canton × premium region × **3 age classes** (0–18, 19–25, 26+) × deductible × insurance model × accident cover. **No individual risk.** | **Attained age** (5-year bands), region, **sex** at some insurers, **health questionnaire** at entry (decline or exclusion of a condition), bonus/no-claims ladders, family discounts |
| Who approves the tariff | Federal Office of Public Health (BAG) | FINMA, which checks that tariffs are "neither abusive nor solvency-endangering". Each tariff change needs new approval and must be justified by general cost development. |
| Can the insurer re-price one person after claims? | No | No individual re-pricing. Bonus/malus ladders are part of the approved tariff. **Since the 2022 VVG revision, insurers can no longer cancel contracts**, except for fraud, breach of the duty to disclose, or non-payment. |
| Where the adaptive part sits | Insurer-level price positioning by canton and region, deductible and model design, risk equalisation between insurers. Customers can switch every year. | Underwriting at entry, attained-age tariff design, entry-age options, bonus ladders, product design (general / semi-private / private ward). Customers rarely switch once they are older or ill. |

**The answer to "is there adaptive pricing in Swiss complementary insurance?" is yes, but only in a constrained form.**
- **At entry**, insurers price and select by risk: questionnaire, exclusions, refusals, age limits.
- **After entry**, the price adapts only through tariff features approved in advance: age bands, bonus ladders, the insurer's overall cost experience.
- **In basic insurance**, adaptation happens at market level. Insurers set prices per canton and region, and customers respond by switching. Risk equalisation removes most of the incentive to select good risks.

That contrast is the teaching core: the same machine-learning model that is legal for an underwriting decision in supplementary insurance would be illegal as a pricing input in basic insurance.

---

## 2. One case across three lectures

**Scenario.** Students join the pricing and analytics team of the fictional insurer **Arvena** in autumn 2026. The 2027 tariffs have just been published, and the team has three jobs.

| Lecture | Question | Task type | Data |
|---|---|---|---|
| **SL for finance 2 · regression** | What will each insured person cost next year, and what is a supplementary hospital policy worth at each age? | Regression on a skewed, zero-inflated target. Use Tweedie/Poisson losses, MLPs with entity embeddings for canton and insurer, and compare with GLMs. | `person_years` (features in year *t*, target `okp_gross_cost` or `vvg_benefits_paid` in *t+1*) |
| **SL for finance 2 · classification** | Who will leave Arvena on 1 January 2027, and who will cancel or downgrade a hospital supplement? Which applicants would underwriting accept? | Binary and multiclass classification with price features; calibration; profit-weighted thresholds. | `renewal_2027` (labels), `applications` (underwriting decisions) |
| **GenAI 1 · transformers** | Can a model that reads each person's **sequence of invoices** predict next-year cost or hospitalisation better than annual aggregates? Can an **LLM agent** draft a compliant quote and explain an underwriting decision? | Transformer encoder over event tokens (care type, provider, amount bucket, days since last event, ward). Agent with tools: tariff lookup, deductible optimiser, legal checks. | `events` (about 950,000 rows), `tariffs_*`, `tariff_rules` |
| **Lecture 3 · evaluation and explainability** | Are the models fair (sex-rated VVG tariffs, age), calibrated, and stable over time? What do explanations show, and are they true? | Proper scoring rules, temporal backtests, SHAP and its pitfalls with correlated rating factors, probing of the transformer, checks against the **ground truth**. | `ground_truth/` (instructor only) |

**Built-in phenomena students can discover:**
- **Adverse selection through the deductible.** Healthy people choose CHF 2,500, people with chronic conditions keep CHF 300. People with high deductibles also submit fewer small invoices (see `submitted_to_insurer`).
- **Price-driven switching.** OKP switching rises with the insurer's increase relative to the market and with the savings available. It peaks with the large premium increases of 2023–2024. People with a hospital supplement at the same insurer rarely switch.
- **Confounding in price response.** Insurers with a costly book raise prices more (through the loss-ratio feedback), and their customers then leave. Price changes are therefore not random. No randomised price test exists, because FINMA- and BAG-approved tariffs forbid individual price experiments.
- **Underwriting and undisclosed conditions.** Some applicants omit a condition. When a later claim reveals it, the insurer refuses the claim and terminates the contract (`end_reason = breach_of_disclosure`).
- **Ageing in supplementary premiums.** Premiums step up every 5 years. One insurer (Talwyn) switches long-standing customers to an entry-age tariff at 50. Lapses rise near retirement for lower-income holders.
- **Data visibility.**
  - Accidents of people employed at least 8 hours a week are paid by accident insurance (UVG). The health insurer never sees them (`visible_to_health_insurer = False`).
  - Cantons pay 55% of inpatient costs.
  - Dental care and glasses are mostly outside basic insurance.

---

## 3. Tables

All tables are provided as CSV (`events.csv.gz` is compressed) and Parquet. Money amounts are in CHF.

### `persons` — one row per person (7,946)
`person_id`, `household_id`, `sex` (F/M), `birth_date`, `entry_date`, `entry_reason` (`portfolio_2014`, `birth`, `immigration`), `exit_date`, `exit_reason` (`death`, `emigration`, empty if still insured).

### `households` — one row per household (3,628)
`household_id`, `canton_2026`, `premium_region_2026`, `municipality_type` (urban/suburban/rural), `income_band` (1 = lowest … 4 = highest).

### `person_years` — panel, one row per person and calendar year (84,060)
| Group | Columns |
|---|---|
| Identity and place | `person_id`, `year`, `household_id`, `age` (age reached in the year), `age_class` (child/young_adult/adult), `sex`, `canton`, `premium_region`, `municipality_type`, `language`, `household_size`, `income_band`, `employment` (employed/student/not_employed/retired/child), `insured_days` |
| Basic insurance | `okp_insurer`, `okp_model` (standard/family_doctor/hmo/telmed), `deductible` (adults 300–2,500; children 0–600), `accident_cover`, `okp_premium_monthly` (after model, accident and deductible rebates), `premium_subsidy_annual` (cantonal individual premium reduction) |
| Supplementary insurance | `vvg_products` (semicolon list), `vvg_premium_monthly_total`, `has_<product>` and `premium_<product>_monthly` for AMB (outpatient supplement: complementary therapies, glasses, fitness, travel), HOSP_GEN (general ward anywhere in Switzerland), HOSP_SEMI (semi-private), HOSP_PRIV (private) and DENT (dental); `vvg_insurer`, `bonus_factor_amb`, `bonus_factor_hosp` (1.0 = no discount), `n_vvg_reservations` |
| Risk-equalisation indicators | `ra_hospital_prev_year_gt3_nights`, `ra_pharma_cost_group` (chronic medication in the previous year) |
| Outcomes (year *t*) | `died`, `okp_gross_cost` (basic-insurance-relevant costs incl. cost sharing; excludes the canton's inpatient share), `okp_benefits_paid`, `cost_sharing` (deductible + 10% co-payment), `hospital_contribution` (CHF 15/day), `canton_inpatient_share`, `vvg_benefits_paid`, `uvg_benefits_paid`, `patient_paid_uncovered`, `n_gp_visits`, `n_specialist_visits`, `n_inpatient_stays`, `inpatient_days`, `n_accidents`, `n_events` |

### `events` — one row per invoice (953,061)
`event_id`, `person_id`, `date`, `year`, `care_type` (gp_visit, specialist_visit, outpatient_hospital, inpatient_stay, medication, physiotherapy, psychotherapy, home_care, nursing_home_care, maternity_care, accident_outpatient, rescue_transport, emergency_abroad, dental_checkup, dental_treatment, orthodontics, glasses, complementary_therapy, fitness_prevention), `provider`, `diagnosis_group`, `condition` (link to a chronic condition when relevant), `accident_context` (sport/home_leisure/traffic/work), `ward` (general/semi_private/private), `los_days`, and the payer split: `gross_cost`, `okp_gross`, `paid_okp`, `cost_share_franchise`, `cost_share_coinsurance`, `hospital_contribution`, `paid_canton`, `paid_vvg`, `vvg_product`, `vvg_insurer`, `vvg_rejection` (reservation / limit_reached / breach_of_disclosure), `paid_uvg`, `paid_patient_uncovered`, `insurer_okp`, `visible_to_health_insurer`, `submitted_to_insurer`.

### `policies` — contract spells (23,476)
`policy_id`, `person_id`, `line` (OKP, AMB, HOSP_GEN, HOSP_SEMI, HOSP_PRIV, DENT), `insurer`, `start_date`, `end_date`, `end_reason` (active, switch_insurer, cancelled_by_customer, downgrade, upgrade, death, emigration, breach_of_disclosure), `reservation_condition`, `reservation_until` (9999 = permanent).

### `applications` — supplementary applications incl. declined ones (2,885)
`application_id`, `person_id`, `date`, `insurer`, `product`, `channel` (existing_customer, new_resident, prenatal = registration before birth without health questions, upgrade), `age`, `sex`, `canton`, `height_cm`, `weight_kg`, `smoker`, `declared_conditions`, `n_declared`, `decision` (accepted, accepted_with_reservation, declined, declined_age_limit), `reservation_condition`, `reservation_until`.

### `renewal_2027` — the labels for the autumn-2026 decisions (6,565 people insured on 31.12.2026)
- **Current cover:** `okp_insurer_2026`, model, deductible and 2026 premium.
- **New tariffs:** the 2027 premium for the same cover, and the cheapest insurer and premium in the person's region, plus `household_premium_change`.
- **Labels:** `label_switched_okp_insurer`, `label_new_okp_insurer`, `label_deductible_2027`, `label_model_2027`, and for each supplementary product `label_<product>_2027` (keep / cancel / downgrade / not_held), together with its 2026 and 2027 list premiums.

### Tariffs and market
- **`tariffs_okp`** (year 2014–2027 × insurer × canton × region × age class): monthly premium for the standard model with the lowest deductible and accident cover. Combine it with `tariff_rules` to price any cover.
- **`tariffs_vvg`** (year × insurer × product × 5-year age band × sex): reference monthly premium before the canton factor (`vvg_region_factors`), bonus and family discount.
- **`tariff_rules`**: per insurer, the deductible-rebate share, model factors, accident factor, bonus system (ladder, claim-free 20%, two-level 25%, none), female factor in hospital products for ages 19–45, entry-age tariff from 50, maximum entry age for hospital cover, and family discount.
- **`cantons`**: official 2026 and 2027 mean adult premiums, language, number of premium regions.
- **`insurer_financials`**: premium income, net benefits, risk-equalisation transfers, loss ratios for basic and supplementary business.

### `ground_truth/person_latent_truth.csv` — **instructor only**
Latent frailty, risk aversion, affinity for complementary medicine, smoker, BMI, dental status, undisclosed conditions, and onset year of each chronic condition (cardiovascular, diabetes, respiratory, mental, musculoskeletal, cancer, dementia). Use it to check whether models and explanations recover the truth.

---

## 4. How the data was generated

`generate.py` simulates each calendar year in five steps.
1. **Tariffs.**
   - Basic premiums start from the official cantonal mean, back-cast with the national yearly premium changes. They are then shaped by premium region, the three age classes, each insurer's price position, model and accident factors, and deductible rebates (at most 70% of the extra risk taken).
   - Insurers adjust their price each year from their loss ratio after risk equalisation.
   - Supplementary tariffs follow published 2026 price levels by age, and grow with each insurer's cost experience within approved bounds.
2. **Choices on 1 January.**
   - Households decide whether to switch basic insurer, using a logit on available savings, premium increase, age, chronic illness and ties to a supplementary policy.
   - People choose a deductible by expected cost, risk aversion and premium, and a model (alternative models rise from about 55% to 76%).
   - Accident cover follows employment.
   - Supplementary holders may cancel or downgrade from the third contract year. This becomes more likely after large increases, at retirement and with lower income, and less likely when ill.
3. **Underwriting.** During the year, people apply for supplementary products. Insurers score declared conditions, BMI, smoking and age, then accept, accept with a 5-year or permanent reservation, or decline. Some applicants omit a condition.
4. **Health.**
   - Chronic conditions start with age-, sex-, smoking- and BMI-dependent hazards.
   - Each person also has pregnancies and births (newborns enter the dataset), accidents (with ski-season peaks), hospital stays (with length of stay and a per-stay price), care at home or in a nursing home, end-of-life costs and deaths.
   - Each invoice is then split between payers according to the Swiss rules: deductible, 10% co-payment capped at CHF 700 (CHF 350 for children), CHF 15/day hospital contribution, no cost sharing for maternity, 55% canton share of inpatient costs, UVG for employed people's accidents, and the supplementary benefit limits and reservations.
5. **Market.** Risk equalisation runs by canton × 5-year age band × sex, with indicators for a hospital stay of more than 3 nights and for chronic medication. Insurer loss ratios then feed next year's prices.

Total costs are rescaled every year so that the mean basic-insurance gross cost per insured matches the official figure.

Run: `python generate.py --out data --households 3000 --seed 2026` (about 90 seconds). `python validate.py data` prints the checks below.

### 4.1 Daily step counts (`activity_daily.parquet`, used in Lecture 1 Practical 3)

`generate_activity.py` adds a daily step-count table for members of Arvena-style step-bonus programmes: people aged 20–79 in 2023 who hold an ambulatory supplementary policy (2,638 people, 3.9 million person-days, 1 January 2023 to 31 December 2026). Columns: `person_id`, `date`, `steps` (0 = device not worn).

Each person's series multiplies a personal level (falling with age, chronic conditions and frailty) by weekday and seasonal factors and a slow random drift, plus daily noise. Life events from `events.parquet` and the generator's own episodes leave marks of different shapes:
- **colds** (about three per year): a drop of 50–80% for 2–6 days, then full recovery within a week;
- **holidays**: 1–3 per year, 5–21 days at a different level;
- **accidents**: a fracture lowers activity by about two thirds with recovery over 30–60 days; minor injuries for a few days;
- **flare-ups before hospital stays**: before many admissions (probability depending on the diagnosis), one to three dips followed by a slow and **incomplete** recovery to 85–95% of the previous level, persisting until admission; activity during the stay is near zero and recovers over 2–8 weeks;
- **device not worn**: runs of zero days (0.5–4% of days per person).

Run after `generate.py`: `python generate_activity.py --data data` (about one minute). The table is distributed in its own archive to keep each archive below 30 MB.

## 5. Validation against official Swiss figures

| Check | Synthetic | Reference |
|---|---|---|
| Age 0–18 / 19–64 / 65+ (2024) | 19% / 59% / 22% | about 19% / 62% / 19% (FSO) |
| Mean basic-insurance gross cost per insured, 2024 | CHF 4,692 | CHF 4,692 = 391 per month (BAG) |
| Cost sharing per insured | CHF 58 per month | CHF 52 per month (BAG 2024) |
| Mean adult premium, 2026 | CHF 467 | CHF 464.80 (BAG) |
| Cantonal adult premiums 2026: mean absolute error / correlation | 1.5% / 0.99 | official cantonal means |
| Deductibles, adults 2024 (300/500/1000/1500/2000/2500) | 34/17/6/5/8/30% | 2015: 44/14/5/12/4/21%; the share choosing 2,500 has grown since |
| Alternative insurance models, 2014 → 2024 | 55% → 75% | about 60% → over 75% (BAG) |
| Basic-insurance switching rate per year | 4.5–8.6% per year, peak 8.6% in 2024; 5.0% in the 2027 renewal labels | about 5–9%, higher after the 2023–24 increases (comparis surveys) |
| People with at least one hospital stay / stays per 100 insured | 12.0% / 15.9 | about 11–13% / about 16 (FSO) |
| Crude death rate | 9.1 per 1,000 (the synthetic population is slightly older) | about 8 per 1,000 (FSO) |
| Cost concentration: top 1% / top 10% | 14% / 59% | about 20% / 60–70% |
| Semi-private or private hospital supplement | 20.3% | about 20%, 1.5 million people |
| Any supplementary product | 75% | about 70–75% |
| Receives a premium subsidy | 29% | about 25–28% |
| Cost at 80+ vs ages 26–35 | 7.9× | about 5–8× (BAG age profiles; 80+ includes nursing-home care) |
| Women vs men cost, ages 26–40 | 1.36× | above 1× (maternity, gynaecology) |
| Insurer loss ratios after risk equalisation (2024) | 0.86–0.99 | about 0.9–1.0 |

`validation.txt` holds the full output.

## 6. Simplifications to tell students about
- **Premium regions and insurers.** Premium regions are simplified (1–3 per canton, fixed factors). Insurers are fictional and only eight; the real market has about 40.
- **Supplementary premiums.** Premiums for a given age are list prices from the published 2026 levels. Real products differ in benefit details, and these products are stylised.
- **Clinical detail.** Diagnoses are coarse groups, not ICD codes. Hospital prices follow a simple length-of-stay formula rather than SwissDRG.
- **Policy changes.** Uniform financing (EFAS, from 2028), recent law changes on children's premiums, and cantonal subsidy formulas are approximated or omitted. The subsidy is a simple function of income band and age.
- **Calibration.** The calibration targets national averages. Some cantonal cost patterns, such as the higher use of outpatient care in French-speaking cantons, are only approximated through a cost index.

## 7. Sources
- BAG, *Krankenversicherungsprämien 2027* (press release, September 2026): national and group means.
- Cantonal 2026/2027 adult mean premiums: BAG data as published by lohncomputer.ch.
- BAG, *Faktenblatt Franchisen* (2017): deductible levels, rebate rule, 2015 distribution.
- BAG, *Leistungen der Krankenversicherung 2024*: gross benefits CHF 391 per insured per month, cost sharing CHF 52, cost groups.
- FINMA, *Faktenblatt Krankenzusatzversicherung* and *Tarifprüfung Krankenversicherung*: supervision and tariff approval.
- CSS, *VVG-Revision*: no ordinary termination by the insurer since 1 January 2022; customer cancellation from the third year.
- Comparis, *Gesundheitsfragen*: health questionnaire, reservations, refusals.
- Moneyland, *Bonus-Malus in der Krankenversicherung*: bonus ladders and claim-free discounts in supplementary insurance.
- Expat-Savvy, *Hospital insurance cost index 2026*: semi-private and private premiums by age, sex differences, entry-age tariffs.
- Helvetic Care: about 1.5 million people with semi-private or private cover; premium increases with age.
