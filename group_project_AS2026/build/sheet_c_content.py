import os
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results_sheets", "figures", "")
TITLE = "Task (c): results sheet and plain-language guide"
SUB = "Where does ESG pay? For the memo and the slides (Laurin). Updated 4 November 2026 from the executed notebook. Group_8."
BLOCKS = [
    ("h1", "1. The result in four sentences"),
    ("p", "We related the previous fiscal year's **Environmental score** (standardised within each year) to the **next 12 months' excess return**, region by region and for formation years before 2021 and from 2021, comparing each firm with same-industry firms of the same year. Pooled over all regions there is nothing. Region by region, exactly **one cell** stands out: **Europe, from 2021**, where a firm one standard deviation (about 17 points) higher on the score was associated with about **+3.1 percentage points** more 12-month excess return (95% interval 1.2 to 5.0; Holm-adjusted p = 0.018). No other region-period cell is distinguishable from zero. The evidence rests on only four formation years: with years as the unit instead of firms, p is about 0.09, so we call it a plausible premium, not a proven one. The restated scores, which behave as if they contain hindsight, give higher estimates everywhere and more significant cells before the correction; after it they, too, keep only Europe from 2021 (+4.88)."),
    ("h1", "2. The table (percentage points of 12-month excess return per 1 standard deviation of the score; standard error in brackets)"),
    ("tbl", [
        ["Region", "Point-in-time, before 2021", "Point-in-time, from 2021", "Restated, before 2021", "Restated, from 2021"],
        ["Africa", "-0.07 (1.45)", "+0.75 (1.43)", "+0.93 (1.38)", "+2.40 (1.25)"],
        ["Asia", "+0.15 (0.68)", "+0.39 (0.96)", "+1.06 (0.67)", "+1.95 (0.94) \\*"],
        ["**Europe**", "+0.47 (0.65)", "**+3.08 (0.96) \\*\\***", "+1.59 (0.68) \\*", "+4.88 (0.90) \\*\\*"],
        ["Latin America", "-1.19 (1.08)", "-2.94 (1.66)", "-0.05 (1.14)", "-1.33 (1.77)"],
        ["Middle East", "-0.92 (1.08)", "+0.28 (1.57)", "+0.43 (1.11)", "+2.75 (1.55)"],
        ["North America", "-0.40 (0.72)", "-0.61 (1.19)", "+0.93 (0.71)", "+0.99 (1.21)"],
        ["Oceania", "-0.24 (0.88)", "-0.80 (1.33)", "+0.73 (0.87)", "+0.79 (1.31)"],
        ["All regions (reference)", "-0.12 (0.28)", "+0.63 (0.43)", "+0.87 (0.28) \\*", "+2.13 (0.42) \\*"],
    ], [0.20, 0.20, 0.20, 0.20, 0.20], 8.4),
    ("small", "\\* = p < 0.05 for that cell alone; \\*\\* = still p < 0.05 after the Holm correction across the 14 region-period cells (the 'All regions' rows are reference only). Standard errors are clustered by company; controls are industry-by-formation-year effects. Cell sizes (firm-years): Europe 1,659 before and 814 from 2021; other regions 667 to 1,686 before and 340 to 817 from 2021. Europe, from 2021, point-in-time: 95% interval 1.20 to 4.96, p = 0.0013, Holm 0.018, 814 firm-years, 223 firms."),
    ("img", FIG + "c1_region_period_estimates.png", 1.0, "Figure c1 (notebook, (c) Step 3): estimates and 95% intervals by region and period, point-in-time (blue) and restated (orange). The intervals are not adjusted for the 14 cells."),
    ("img", FIG + "c2_europe_by_year.png", 0.65, "Figure c2: the Europe estimate year by year (95% interval). The premium appears from 2022: 2021 is +0.35."),

    ("h1", "3. What the numbers mean for an investor"),
    ("bul", [
        "**Where could an investor have earned a premium?** Only among European firms from 2021: a European firm about 17 points above its year's average Environmental score was associated with about 3 points more 12-month excess return than industry peers of the same year. Everywhere else, and before 2021, the data show no relation that can be told apart from zero.",
        "**This is an association, not a return.** The table does not show that a portfolio built on the score would have earned this after costs; task (d) tests a ranking rule, not this region-specific effect.",
        "**How firm is it?** The firm-clustered p-value (0.0013) treats firms as independent. With years as the unit (Fama-MacBeth over the four yearly slopes +0.35, +5.93, +1.81, +4.18) the p-value is about 0.09. We examined 14 cells and 12 yearly estimates, so we call it a plausible premium, not a proven one.",
        "**Is it different from before 2021?** Europe before 2021 is +0.47 (se 0.65); the extra effect from 2021 is +2.61 (se 1.26, p = 0.038), an exploratory test run after the cell was singled out.",
        "**Why pooling hides it.** Pooled over all regions the estimate is -0.12 before 2021 and +0.63 from 2021: one region cannot be seen in a global ranking.",
    ]),
    ("h2", "The restated scores: why the estimates differ"),
    ("bul", [
        "The restated file gives higher coefficients in every region and period (by 0.9 to 2.5 points) and, before the Holm correction, makes more cells look significant, for example Europe before 2021 (+1.59) and Asia from 2021 (+1.95), where the point-in-time scores show nothing. After the correction only Europe from 2021 remains (+4.88).",
        "The reason: the restatement behaves as if it contains hindsight. What it added to the score is related to the return that followed (within-year rank correlation 0.16; in a joint regression +5.3 points per standard deviation of the restatement). An investor on 1 July would have seen only the point-in-time score, so the restated version overstates what could have been earned and points to premiums that did not exist at the time.",
    ]),

    ("h1", "4. Suggested text (edit freely)"),
    ("p", "**Memo (about 130 words).** We estimated, for each region and for formation years before and from 2021, the relation between the previous fiscal year's Environmental score (standardised within year) and the next 12 months' excess return, comparing each firm with same-industry firms of the same year (standard errors clustered by company, Holm correction across the 14 cells). Pooled over regions the relation is indistinguishable from zero. An investor could have earned an ESG premium only in Europe from 2021: about +3.1 percentage points per standard deviation of the score (Holm-adjusted p = 0.018), found in 1 of 14 cells and resting on four formation years (p about 0.09 with years as the unit). Restated scores, which behave as if they contain hindsight, give higher estimates everywhere and more significant cells before the correction."),
    ("p", "**Slide (where ESG pays, about 1.25 minutes).** Title: \"ESG paid in one place: Europe from 2021\". Figure c1 (or a table of the 14 cells with Europe from 2021 highlighted). One line: \"1 of 14 cells; +3.1 points per standard deviation; restated scores look stronger (hindsight)\"."),

    ("h1", "5. Plain-language guide: what the notebook did"),
    ("bul", [
        "**Step 1, sample.** One row per firm and year, 2013 to 2024, with a full 12 months of returns. The score is standardised within each year (average 0, spread 1). The outcome is the excess return: total return minus what a safe account paid.",
        "**Step 2, one regression per cell.** For each region and period: how much does the next-year excess return change when the score is one spread higher, comparing only firms in the same industry in the same year? We compute the uncertainty with the firm-clustered method (a firm's years are not independent evidence) and apply the Holm correction, which raises the bar because looking at 14 cells can produce a lucky hit by chance. The same is done with the restated scores.",
        "**Step 3, figure** of all estimates with intervals.",
        "**Step 4, why restated differs.** Compared the two score versions and showed that what the restatement added correlates with later returns.",
        "**Step 5, the Europe cell in detail:** a test against Europe before 2021, year-by-year estimates, and the years-as-unit test (p about 0.09). Marked exploratory.",
        "**Step 6, numbers and the one-sentence conclusion** for results.json.",
    ]),

    ("h1", "6. Questions you may be asked"),
    ("tbl", [["Question", "Answer"],
        ["Is this causal? Does a higher score cause higher returns?", "No. It is a cross-sectional association within industry and year. We make no causal claim."],
        ["Why the Holm correction?", "We look at 14 cells. At the 5% level one false hit is expected about every 20 looks, so we raise the bar. Only Europe from 2021 clears it (adjusted p = 0.018)."],
        ["Why cluster by company?", "The same company appears in many years and its years resemble each other; counting them as independent would make us overconfident."],
        ["Why does Europe from 2021 start in 2022?", "The 2021 formation year is +0.35. The cell averages 2021 to 2024; the premium shows in 2022 (+5.9), 2023 (+1.8, wide) and 2024 (+4.2)."],
        ["Why is the restated version bigger?", "It behaves as if it contains hindsight: what it added correlates with the return that followed. It overstates what an investor could have known."],
        ["Does the result depend on how you measure uncertainty?", "Yes. Holm-adjusted p = 0.018 holds with errors clustered by company. With the four formation years as the unit (Fama-MacBeth) p is about 0.09. We report both, which is why we say plausible, not proven."],
        ["Is 'Europe from 2021' the planted relationship?", "We cannot know. It is the only cell that survives a multiple-testing correction. In real data a single cell out of 14 would need replication before anyone relied on it."],
    ], [0.32, 0.68], 8.6),

    ("h1", "7. What to be careful about"),
    ("bul", [
        "Say \"associated with\", never \"earned\" without the caveat that it is not a tradable return.",
        "Four formation years: do not call it proven. The intervals in the figure are unadjusted for the 14 cells.",
        "The cutoff \"from 2021\" is by formation year (agreed in the coaching).",
        "The 3.1 points are per standard deviation of the score (about 17 points), not per score point.",
        "Numbers come from the run of 4 November.",
    ]),
]
