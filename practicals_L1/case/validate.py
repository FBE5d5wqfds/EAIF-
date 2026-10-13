"""Compare synthetic aggregates with official Swiss figures."""
import sys, pandas as pd, numpy as np
d = sys.argv[1]
py = pd.read_parquet(f"{d}/person_years.parquet"); ev = pd.read_parquet(f"{d}/events.parquet")
pol = pd.read_parquet(f"{d}/policies.parquet"); app = pd.read_parquet(f"{d}/applications.parquet")
ren = pd.read_parquet(f"{d}/renewal_2027.parquet"); cant = pd.read_parquet(f"{d}/cantons.parquet"); fin = pd.read_parquet(f"{d}/insurer_financials.parquet")
pd.set_option("display.width", 200)
out = []
def chk(name, synth, official, src=""): out.append((name, synth, official, src))
y = py[py.year == 2024]
chk("persons (unique) / alive 2026", f"{py.person_id.nunique():,} / {(py.year==2026).sum():,}", ">= 5,000", "")
chk("age 0-18 / 19-64 / 65+ share 2024", " / ".join(f"{v:.0%}" for v in [(y.age<=18).mean(), ((y.age>18)&(y.age<65)).mean(), (y.age>=65).mean()]), "~19% / 62% / 19%", "FSO")
w = y.insured_days / 365
chk("mean OKP gross cost per insured 2024 (CHF)", f"{(y.okp_gross_cost.sum()/w.sum()):,.0f}", "4,692", "BAG 2024: 391/month")
chk("cost sharing per insured 2024 (CHF/month)", f"{((y.cost_sharing+y.hospital_contribution).sum()/w.sum()/12):,.0f}", "52", "BAG 2024")
a = y[y.age_class == "adult"]
chk("mean adult premium 2026 (CHF/month)", f"{py[(py.year==2026)&(py.age_class=='adult')].okp_premium_monthly.mean():.0f}", "464.80", "BAG")
x = py[(py.year == 2026) & (py.age_class == "adult")].groupby("canton").okp_premium_monthly.mean().rename("synthetic").to_frame().join(cant.set_index("canton").official_mean_adult_premium_2026)
chk("canton adult premium 2026: mean abs. % error", f"{(abs(x.synthetic/x.official_mean_adult_premium_2026-1)).mean():.1%}", "small", "")
chk("canton premium correlation", f"{x.corr().iloc[0,1]:.2f}", "1.0", "")
ad = py[(py.year == 2024) & (py.age >= 19)]
fd = ad.deductible.value_counts(normalize=True).sort_index()
chk("deductible distribution adults 2024", " ".join(f"{k}:{v:.0%}" for k, v in fd.items()), "2015: 300:44 500:14 1000:5 1500:12 2000:4 2500:21", "BAG fact sheet (2015)")
chk("alternative model share 2014 / 2024", f"{(py[py.year==2014].okp_model!='standard').mean():.0%} / {(y.okp_model!='standard').mean():.0%}", "~ 60% / ~ 75%+", "BAG statistics")
sw = py.sort_values(["person_id","year"]).copy(); sw["prev"] = sw.groupby("person_id").okp_insurer.shift()
sw = sw.dropna(subset=["prev"]); rate = sw.groupby("year").apply(lambda g: (g.okp_insurer != g.prev).mean())
chk("OKP insurer switching rate by year", " ".join(f"{k%100:02d}:{v:.1%}" for k, v in rate.items()), "~ 5-9%; peak with 2024 increases", "comparis surveys")
chk("share with >=1 inpatient stay 2024", f"{(y.n_inpatient_stays>0).mean():.1%}", "~ 11-13%", "FSO hospital statistics")
chk("inpatient stays per 100 insured 2024", f"{100*y.n_inpatient_stays.sum()/w.sum():.1f}", "~ 16", "FSO: ~1.4-1.5 m stays")
chk("deaths per 1,000 (crude) 2015-2025", f"{1000*py[(py.year>=2015)&(py.year<=2025)].died.mean():.1f}", "~ 8", "FSO")
c = y.okp_gross_cost.sort_values(ascending=False); top = c.cumsum() / c.sum()
chk("cost concentration: top 1% / 10% share 2024", f"{top.iloc[int(len(c)*.01)]:.0%} / {top.iloc[int(len(c)*.1)]:.0%}", "~ 20-25% / ~ 60-70%", "literature")
chk("hospital supplementary (semi/private) holders 2024", f"{(y.has_hosp_semi|y.has_hosp_priv).mean():.1%}", "~ 20% (1.5 m)", "Helvetic Care / industry")
chk("any supplementary 2024", f"{(y.vvg_products!='').mean():.0%}", "~ 70-75%", "industry estimates")
chk("receives premium subsidy 2024", f"{(y.premium_subsidy_annual>0).mean():.0%}", "~ 25-28%", "BAG/IPV statistics")
chk("cost ratio age 80+ vs 26-35 (2024)", f"{y[y.age>=80].okp_gross_cost.mean()/y[(y.age>=26)&(y.age<=35)].okp_gross_cost.mean():.1f}x", "~ 5-8x", "BAG age profiles")
chk("cost women/men age 26-40", f"{y[(y.age.between(26,40))&(y.sex=='F')].okp_gross_cost.mean()/y[(y.age.between(26,40))&(y.sex=='M')].okp_gross_cost.mean():.2f}", "> 1.3 (maternity, gynaecology)", "")
dec = app[app.channel != "prenatal"].decision.value_counts(normalize=True)
chk("VVG application outcomes", " ".join(f"{k}:{v:.0%}" for k, v in dec.items()), "plausible", "")
chk("renewal 2027: OKP switching label rate", f"{ren.label_switched_okp_insurer.mean():.1%}", "~ 6-10%", "")
for k in ["hosp_semi", "hosp_priv", "amb"]:
    col = f"label_{k}_2027"; held = ren[ren[col] != "not_held"]
    chk(f"renewal 2027: {k} cancel/downgrade among holders", f"{(held[col]!='keep').mean():.1%}", "a few %", "")
chk("OKP loss ratio after RA (2024, by insurer)", " ".join(f"{r.insurer}:{r.okp_loss_ratio_after_ra:.2f}" for r in fin[fin.year==2024].itertuples()), "~ 0.9-1.05", "")
for r in out: print(f"{r[0]:52s} | {r[1]:58s} | {r[2]} {('['+r[3]+']') if r[3] else ''}")
