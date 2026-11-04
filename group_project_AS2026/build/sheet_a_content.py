TITLE = "Task (a): results sheet and plain-language guide"
SUB = "Pipeline and data audit. For the memo (B) and the slides (C). Updated 4 November 2026 from the executed notebook."

BLOCKS = [
    ("h1", "1. The result in four sentences"),
    ("p", "We checked all five data files before building any model and found **seven problems**, which are treated in the notebook. Three of them change numbers a reader would notice: a unit error made 28 firms look about 1,000 times bigger than they are, duplicated return months silently removed 181 firm-years from the model data, and the column Analyst_Outlook carries information from the future. We excluded that column, because no investor could have had it on 1 July. Then we built the **formation panel**: one row per company and formation year, with 30 features, six of them new, each with the date from which it is known."),

    ("h1", "2. The audit table (numbers from the notebook)"),
    ("tbl", [
        ["Problem", "How found", "What we did", "Effect on one number"],
        ["**Unit error:** 28 firms (302 firm-years) have revenue and market cap about 1,000 times too large", "Carbon, water and energy scale with revenue; for these firms they sit about 1,000 times below that relation", "Divided revenue and market cap by 1,000", "Mean market cap 213,205 to 14,108 USD million. These firms were 100% of the 100 largest firm-years by market cap before, 0% after."],
        ["**Duplicate returns:** 300 company-months appear twice (values differ by at most 0.01 points)", "Repeated (Company_ID, Month) keys", "Kept the first row", "Firm-years with a full 12 holding months: 9,002 to 9,182. 181 firm-years had 13 months and had been dropped."],
        ["**Analyst_Outlook** carries future information", "Rank correlation with the return in three 12-month windows", "Excluded from all models", "Rank correlation with the next 12-month return 0.68 (other windows -0.01 and 0.01). Random forest test error 37.59 without it, 29.14 with it, baseline 37.20."],
        ["**Survivorship:** the universe file lists 987 survivors out of 1,376 firms", "389 firms have a last fiscal year before 2025", "Everything built on the full panel, exiting firms held until their last month", "Equal-weight benchmark 4.62% a year on the full panel vs 5.18% on survivors only (Sharpe 0.213 vs 0.248), formation years 2015 to 2025. The model samples also drop 302 firm-years of exiting firms (fewer than 12 holding months)."],
        ["**Restated scores** behave as if they contain hindsight", "Compared with the point-in-time scores; changes correlate with later returns", "Point-in-time scores everywhere; restated only for the comparison in task (c)", "459 firms have every score changed (by 5.7 points on average). Within-year rank correlation of the Environmental score with the next excess return 0.010 (point-in-time) vs 0.056 (restated)."],
        ["**Missing environmental data:** carbon, water, energy missing together, not at random", "Missing share by region and by score", "Kept all rows; carbon intensity filled with the industry-year median plus a missing flag", "13.2% of formation rows. Europe 6.3% missing vs 13.0% to 18.9% elsewhere. Mean Environmental score 47.2 (missing) vs 56.5. Dropping the carbon features changes the linear test error from 38.10 to 38.05."],
        ["**Values at the bounds:** scores at exactly 0 or 100 (65 Environmental, 72 Social, 77 Governance; 213 rows, 1.5%) and 8 returns at -95%", "Counts at the minimum and maximum", "Kept and documented", "Removing the clipped training rows changes the linear test error from 38.10 to 38.00."],
    ], [0.27, 0.2, 0.2, 0.33]),

    ("h1", "3. What the numbers mean for an investor"),
    ("bul", [
        "**Unit error.** Left in, these 28 firms would be treated as the largest firms in the data and would distort every feature that depends on size. The mean market cap would be overstated by a factor of about 15.",
        "**Duplicates.** One extra month changes a firm's 12-month return, and a firm with 13 months does not pass the \"exactly 12 months\" rule, so it was silently left out of the model data.",
        "**Analyst_Outlook.** A model using it looks far better than the baseline (29.1 against 37.2), but only because the column contains the outcome. An investor on 1 July could not have had it. The inference that it carries future information rests on the pattern of correlations: it is related to the next 12 months and to nothing else.",
        "**Survivorship.** A test on survivors alone would make an equal-weight portfolio look about 0.6 percentage points a year better than it was (formation years 2015 to 2025; about 0.46 points over the 2018 to 2024 backtest window of task d), because the firms that failed are missing.",
        "**Restated scores.** The restated Environmental score is more strongly related to later returns than the score investors actually saw (0.056 against 0.010). Using it to \"test\" a strategy would suggest more of an ESG premium than could have been earned.",
        "**Missing data.** Dropping the rows with gaps would remove 13.2% of the sample and tilt it towards firms with higher Environmental scores.",
    ]),

    ("h1", "4. The formation panel and the features"),
    ("tbl", [
        ["Item", "Number"],
        ["Formation rows (one per company and formation year, 2015 to 2025)", "10,410"],
        ["Rows with a full 12 holding months (used to fit and test models)", "9,182"],
        ["Training rows (formation years up to 2021) / test rows (2022 to 2024)", "6,473 / 2,709"],
        ["Naive baseline: training mean 12-month return / test RMSE", "0.94% / 37.20 percentage points"],
        ["Mean 12-month return, training years / test years", "0.9% / 21.6%"],
    ], [0.72, 0.28]),
    ("p", "The test years were strong years for the data (mean 12-month return +21.6% against +0.9% in training). This is why a model that is trained on the earlier years looks poor on the test years. The starter notebook mentions a market downturn, but the data shows the opposite."),
    ("tbl", [
        ["New feature", "What it is", "Known from"],
        ["Env_Change", "Environmental score minus the previous year's", "Published 31 Mar to 31 May of Y+1, so before 1 July"],
        ["Margin_Change", "Profit margin minus the previous year's", "Same"],
        ["log_MC_to_Rev", "Log of market cap divided by revenue (valuation relative to sales)", "Same"],
        ["log_Carbon_Int", "Log of carbon emissions per USD million revenue; gaps filled with the industry-year median", "Same"],
        ["Carbon_Missing", "1 if carbon, water and energy are missing", "Same"],
        ["Past_Vol_Pct", "Standard deviation of the 12 monthly returns before formation", "Returns through 30 June of the formation year"],
    ], [0.2, 0.52, 0.28]),

    ("h1", "5. Suggested text (edit freely)"),
    ("p", "**Memo, audit paragraph (about 110 words).** Before modelling, we audited all five files and found seven problems. Revenue and market cap of 28 firms were about 1,000 times too large, probably recorded in USD thousand, so we divided them by 1,000. 300 company-months appeared twice in the returns file and we kept the first row. The column Analyst_Outlook is closely tied to the next 12-month return (rank correlation 0.68, about zero for other windows), so it cannot have been known on 1 July and we excluded it. The universe file holds survivors only, so we used the full panel. Restated ESG scores behave as if they contain hindsight, so we used the point-in-time scores. Missing environmental data is not random and was flagged, not dropped."),
    ("p", "**Slide (the audit slide the lecturer suggested).** Title: \"What we found in the data and what we did\". A table with five rows (Problem, Fix, Effect): unit error, duplicates, Analyst_Outlook, survivorship, restated scores. One line below: \"Seven problems found and treated; every feature is dated and known on 1 July.\" Speaking time about 1.5 minutes."),

    ("h1", "6. Plain-language guide: what the notebook did"),
    ("bul", [
        "**Step 1, structure checks.** Looked for duplicate keys, gaps and publication dates outside the expected window. Only the returns file had duplicates.",
        "**Step 2, unit error.** Within an industry, a firm's carbon, water and energy use grow with its revenue. For 28 firms the revenue was about 1,000 times too large for that relationship, so we divided it (and market cap) by 1,000.",
        "**Step 3, duplicates.** Kept one row for each company-month that appeared twice.",
        "**Step 4, Analyst_Outlook.** Compared it with the return in three different 12-month windows. It matched only the window that is the thing we try to predict. Excluded.",
        "**Step 5, survivorship.** Compared a benchmark of all firms with a benchmark of survivors only.",
        "**Step 6, restated scores.** Compared both score files and checked how each relates to later returns.",
        "**Step 7, missing data and bounds.** Described the gaps and the values at 0, 100 and -95%.",
        "**Steps 8 to 10, audit table, panel, feature table.** Collected the numbers into one table, built the panel with the new features, and checked in code that no row is used before it was published.",
    ]),

    ("h1", "7. Questions you may be asked"),
    ("tbl", [
        ["Question", "Answer"],
        ["Why divide by 1,000 instead of dropping the 28 firms?", "Dropping them loses 28 firms for nothing. Their carbon, water and energy figures look normal for their size, so only revenue and market cap are wrong. The lecturer's feedback also allowed any consistent, explained method."],
        ["How do you know it is a unit error?", "The 28 firms show the same factor of 1,000 on revenue and market cap, and the environmental columns are normal. We cannot confirm it with the data owner, so we say \"probably\"."],
        ["Why keep the first duplicate?", "The two values differ by at most 0.01 percentage points, so keeping the first or averaging gives practically the same result."],
        ["How do you know Analyst_Outlook leaks?", "It has a rank correlation of 0.68 with the next 12-month return and about zero with the two earlier windows. A genuine forecast would not be that good. Using it would cut the test error from 37.6 to 29.1."],
        ["Why not use the universe file?", "It lists only the 987 firms that still exist. The 389 that left are missing, which makes returns look better than they were."],
        ["Why not drop rows with missing environmental data?", "It would remove 13.2% of the sample and bias it towards higher scores, because missing rows have lower Environmental scores."],
    ], [0.34, 0.66]),

    ("h1", "8. What to be careful about"),
    ("bul", [
        "The unit fix is an inference, not confirmed. Say \"probably\".",
        "The correlations in this sheet are averaged over all regions and years. Task (c) tests the Environmental score region by region and period by period, and may show something different.",
        "Each effect was measured one problem at a time, on the data as it stood before the other fixes, so the effects do not add up.",
        "All numbers come from the notebook run of 4 November. If the notebook changes, the numbers must be checked again.",
    ]),
]
