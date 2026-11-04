import os
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results_sheets", "figures", "")
TITLE = "Task (d): results sheet and plain-language guide"
SUB = "Backtest with costs and an ESG floor. For the memo and the slides (Laurin). Updated 4 November 2026 from the executed notebook. Group_8."
BLOCKS = [
    ("h1", "1. The result in four sentences"),
    ("p", "Each 1 July we ranked firms on the forecast of the model selected in task (b) (linear regression, refitted every year on earlier years only), held the top decile for twelve months and charged 20 basis points per unit of one-way turnover, on the full panel including firms that left (formation years 2018 to 2024, 84 months). The rule earned **9.4% a year against 8.8%** for the equal-weight benchmark (Sharpe ratio 0.46 against 0.42). Restricting the pool to firms with an Environmental score at or above the 50th and the 80th percentile gave 9.6% and 11.4%: **in this sample the floor did not cost return**, it cost concentration (about 19 names at the 80th percentile) and trading. The best rule's Sharpe advantage over the benchmark (+0.11) is **not distinguishable from noise** (95% interval -0.16 to +0.38), and the floor result is **not an ESG effect**: holding every firm above the 80th percentile earns about the benchmark (8.9%), and the gap comes from a few names picked in formation year 2022."),
    ("h1", "2. The table (July 2018 to June 2025, after costs, full panel including firms that left)"),
    ("tbl", [
        ["Rule", "Return (% a year)", "Volatility (% a year)", "Sharpe ratio", "One-way turnover", "Names held"],
        ["Linear regression, no floor", "9.39", "16.80", "0.457", "0.70", "94"],
        ["Linear regression, floor 50th percentile", "9.59", "17.08", "0.464", "0.76", "47"],
        ["Linear regression, floor 80th percentile", "**11.39**", "18.38", "**0.533**", "0.82", "19"],
        ["**Equal-weight benchmark (all firms)**", "**8.77**", "17.12", "**0.419**", "0.17 (no cost)", "945"],
    ], [0.34, 0.13, 0.14, 0.12, 0.15, 0.12], 8.4),
    ("small", "Cost convention (from the starter): the replaced share of the portfolio is sold and bought, 20 bp each way, so 40 bp on the replaced share, charged in the first month of each holding year. Cost drag per year: 0.28 points (no floor), 0.31 (50th), 0.33 (80th). The benchmark is charged no cost, as in the starter. Floors: Environmental score at or above the 50th or 80th percentile of that formation year; the top decile is 10% of the restricted pool."),
    ("tbl", [
        ["Sharpe difference to the benchmark (95% interval, 5,000 resamples of the 84 months)", "Difference", "Lower", "Upper"],
        ["No floor minus benchmark", "+0.038", "-0.159", "+0.226"],
        ["Floor 50th minus benchmark", "+0.045", "-0.176", "+0.255"],
        ["**Floor 80th minus benchmark (best rule)**", "**+0.114**", "**-0.162**", "**+0.381**"],
    ], [0.58, 0.14, 0.14, 0.14], 8.4),
    ("tbl", [
        ["What drives the result ((d) Step 6)", "No floor", "Floor 50th", "Floor 80th", "Benchmark"],
        ["The rule, return % a year (from the table above)", "9.39", "9.59", "11.39", "8.77"],
        ["Every firm above the floor at equal weight, no forecast", "n/a", "8.75", "8.88", "8.77"],
        ["The rule without formation year 2022 (72 months)", "6.05", "6.20", "6.58", "6.70"],
        ["Holding year of formation 2022 alone (%)", "31.7", "32.4", "45.2", "22.0"],
        ["Share of 1,000 random selections of the same size that do at least as well", "16%", "19%", "11%", "n/a"],
    ], [0.44, 0.14, 0.14, 0.14, 0.14], 8.4),
    ("small", "Reading: the floor itself adds nothing (row 2 is about the benchmark), the whole edge of every rule comes from formation year 2022 (row 3), and a random selection of the same size would match the rule in 11% to 19% of cases (row 5)."),
    ("img", FIG + "d1_cumulative_returns.png", 1.0, "Figure d1 (notebook, (d) Step 4): cumulative value of 1 invested in July 2018 after costs. Left: the selected model with and without the floor against the benchmark. Right: the labelled robustness checks."),
    ("tbl", [
        ["Only the clean out-of-sample years (formation 2022 to 2024, 36 months)", "Return", "Volatility", "Sharpe"],
        ["Linear regression, no floor", "21.92", "14.70", "1.111"],
        ["Linear regression, floor 50th", "21.83", "14.92", "1.092"],
        ["Linear regression, floor 80th", "25.28", "15.74", "1.222"],
        ["Equal-weight benchmark", "21.37", "15.17", "1.052"],
    ], [0.55, 0.15, 0.15, 0.15], 8.4),
    ("tbl", [
        ["Labelled robustness checks (not chosen on cross-validation)", "Return", "Volatility", "Sharpe", "Turnover"],
        ["Gradient boosting, no floor", "8.14", "16.71", "0.390", "0.78"],
        ["Gradient boosting, floor 50th / floor 80th", "9.25 / 9.56", "16.90 / 17.71", "0.448 / 0.452", "0.82 / 0.86"],
        ["Linear, past return standardised within year, no floor", "11.46", "16.89", "0.568", "0.55"],
        ["Same variant, floor 50th / floor 80th", "10.83 / 10.24", "16.92 / 18.08", "0.534 / 0.481", "0.60 / 0.69"],
    ], [0.44, 0.15, 0.15, 0.16, 0.10], 8.4),

    ("h1", "3. What the numbers mean for an investor"),
    ("bul", [
        "**No convincing edge.** The forecast has almost no ranking skill: the rank correlation between forecast and realised return averages +0.01 over 2018 to 2024 (+0.03 in 2018 to 2021, -0.02 in 2022 to 2024, and it changes sign across years). The strategy holds about 94 names against about 945 for the benchmark, and 16% of random selections of the same size from the same pool do at least as well: a gap of 0.6 points a year is within what an unskilled selection of names produces.",
        "**What the floor costs.** Not return in this sample. The 50th-percentile floor earned +0.2 points against no floor and the 80th +2.0 points. What it cost: fewer names (47 and 19 instead of 94), more volatility (17.1% and 18.4% against 16.8%) and more trading (turnover 0.76 and 0.82 against 0.70, a cost drag of 0.31 and 0.33 points a year against 0.28). The 80th-percentile result is **not an ESG effect**: holding every firm above the 80th percentile at equal weight earns 8.9%, about the benchmark's 8.8%, so the floor itself adds nothing. The gap comes from the about 19 names the model picked, mostly in one year (formation 2022: +45% against +22%). Without formation year 2022 every rule trails the benchmark (6.0%, 6.2% and 6.6% against 6.7%).",
        "**Is the difference to the benchmark noise?** Yes, for all three rules the interval contains zero. The best rule's Sharpe difference is +0.11 (interval -0.16 to +0.38). Two cautions: picking the best of three rules after seeing the results flatters it, and 84 months are few. Resampling blocks of 3, 6 or 12 months instead of single months gives intervals that are no wider (12-month blocks: -0.07 to +0.31).",
        "**The clean out-of-sample years** (July 2022 to June 2025, a strong market) tell the same story: 21.9% against 21.4% without a floor; the Sharpe ratios 1.11 and 1.05 are close.",
        "**Robustness.** Gradient boosting earned 8.1% without a floor (below the benchmark). A linear variant with the past return standardised within year earned 11.5% (Sharpe 0.57), the highest no-floor result, but it was not the model selected in task (b), and choosing it now because it looks best would be selecting on the test period.",
    ]),

    ("h1", "4. Suggested text (edit freely)"),
    ("p", "**Memo (about 140 words).** Each 1 July we ranked firms on the forecast of the model selected in (b) (linear regression, refitted each year on earlier years only), held the top decile for twelve months and charged 20 bp per unit of one-way turnover, on the full panel including firms that left (formation years 2018 to 2024). The rule earned 9.4% a year against 8.8% for the equal-weight benchmark (Sharpe 0.46 against 0.42). Floors at the 50th and 80th percentile of the Environmental score gave 9.6% and 11.4%: the floor did not cost return here, only concentration (about 19 names at the 80th percentile) and trading. This is not an ESG effect: all firms above the 80th percentile at equal weight earn 8.9%, and without formation year 2022 every rule trails the benchmark. The best rule's Sharpe advantage (+0.11, 95% interval -0.16 to +0.38) is not distinguishable from noise."),
    ("p", "**Slide (backtest with the floor, about 1.5 minutes).** Title: \"A backtest with an ESG floor: no edge that beats noise\". Figure d1 (left) or the four-row table. One line: \"Sharpe difference to the benchmark +0.11, interval -0.16 to +0.38; the floor adds nothing by itself; the gap is one year (2022)\"."),

    ("h1", "5. Plain-language guide: what the notebook did"),
    ("bul", [
        "**Step 1, forecasts.** For every formation year from 2018 to 2024 the model is trained only on earlier years (for 2018: 2015 to 2017) and forecasts the return of every firm for the next year. A real investor never has later data, so neither do we.",
        "**Step 2, portfolios and costs.** Each July: take the firms of the pool, pick the 10% with the highest forecast, hold them equally weighted until the next June (firms that leave contribute until their last month), and charge trading costs on the share of the portfolio that changed. The floor versions first remove firms with a low Environmental score. The benchmark holds all firms equally.",
        "**Step 3, bootstrap.** Resample the 84 months with replacement 5,000 times and recompute the Sharpe difference each time, to see how much it moves by chance. The interval is the middle 95% of these differences.",
        "**Step 4, figure** of the cumulative return series.",
        "**Step 5, numbers for results.json** (four rules and the bootstrap).",
        "**Step 6, checks on what drives the result.** Random selections of the same size; every firm above the floor without a forecast; each holding year separately and the backtest without 2022; a survivors-only benchmark; formation year 2025 included; the bootstrap with blocks of months.",
        "**Final cell.** Collects everything from tasks (a) to (d), checks that no number is missing or infinite, and writes results.json with the group name Group_8 and the three members.",
    ]),

    ("h1", "6. Questions you may be asked"),
    ("tbl", [["Question", "Answer"],
        ["Why does the strategy beat the benchmark if the forecast has no skill?", "It does not beat it in any way that can be told from chance: the interval of the Sharpe difference contains zero. The 0.6-point gap comes with a very different portfolio (94 names against 945)."],
        ["Why did the floor not cost return?", "With 19 to 47 names the result is dominated by which names happen to be picked. We make no claim that ESG screening adds return. The honest cost of the floor is concentration and trading."],
        ["Why start in 2018, and why leave out 2025?", "The first forecast needs several earlier years to train on (2015 to 2017). Formation 2025 has only 6 months of returns and is left out; including it lowers every rule and the benchmark by 1.6 to 2.3 points a year and keeps the ranking ((d) Step 6)."],
        ["Is the benchmark fair?", "It is equal weight on all firms of the formation panel including firms that left, with no cost, as in the starter. Using survivors only would raise it from 8.77% to 9.22% a year (+0.46 points over 2018 to 2024; (d) Step 6)."],
        ["How realistic are the costs?", "A flat 20 bp each way is a simplification. Real costs vary by stock size and market conditions; the memo should say so."],
        ["Why bootstrap months?", "To see how much the Sharpe difference moves by chance with only 84 months. Resampling blocks of consecutive months, which keeps dependence between months, gives intervals that are no wider, so the conclusion does not depend on it."],
    ], [0.32, 0.68], 8.6),

    ("h1", "7. What to be careful about"),
    ("bul", [
        "Do not present the 80th-percentile floor (11.4%) as an ESG result: all firms above the floor earn about the benchmark, the gap is one year (2022) and 19 names, and the interval contains zero.",
        "Do not pick the linear variant because it looks best: it is a labelled robustness check.",
        "The tuning of gradient boosting was done once on the training years of task (b), a simplification stated in the notebook.",
        "Report the benchmark next to every metric. Say that the sample is 84 months in one mostly rising market.",
        "Numbers come from the run of 4 November.",
    ]),
]
