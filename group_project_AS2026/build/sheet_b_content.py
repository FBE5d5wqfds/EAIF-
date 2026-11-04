import os
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results_sheets", "figures", "")
TITLE = "Task (b): results sheet and plain-language guide"
SUB = "Linear regression vs tree ensembles. For the memo and the slides (Laurin). Updated 4 November 2026 from the executed notebook. Group_8."
BLOCKS = [
    ("h1", "1. The result in four sentences"),
    ("p", "We forecast each firm's total return over the next 12 months from 30 features that are known on 1 July, training on formation years 2015 to 2021 and testing on 2022 to 2024. **No model beats the naive forecast** (the training average) on the test years: the baseline's test error is 37.20 percentage points, against 38.10 for linear regression, 37.93 for a tuned random forest and 37.84 for tuned gradient boosting. Cross-validation selects linear regression, but the three models are within 0.05 points of each other, so the choice is effectively a tie. The extra complexity of the ensembles does not pay off out of sample, which the assignment accepts as a legitimate result."),
    ("h1", "2. The comparison table (every model next to the baseline)"),
    ("tbl", [
        ["Model", "Train RMSE", "CV RMSE (sd)", "Test RMSE", "Train R2", "CV R2", "Test R2", "Test rank corr."],
        ["**Naive mean (baseline)**", "29.16", "29.16 (0.29)", "**37.20**", "0.00", "0.00", "-0.45", "n/a"],
        ["Linear regression", "28.73", "**28.88** (0.36)", "38.10", "0.03", "0.02", "-0.52", "-0.02"],
        ["Random forest (tuned)", "28.11", "28.92 (0.29)", "37.93", "0.07", "0.02", "-0.51", "-0.03"],
        ["Gradient boosting (tuned)", "28.28", "28.90 (0.32)", "37.84", "0.06", "0.02", "-0.50", "-0.02"],
    ], [0.24, 0.10, 0.15, 0.10, 0.09, 0.08, 0.09, 0.15], 8.4),
    ("small", "RMSE = typical size of the forecast error in percentage points of 12-month return (lower is better). CV = cross-validation inside the training years, folds grouped by company. Test rank corr. = average over the three test years of the rank correlation between forecast and outcome. Settings chosen by CV: random forest 150 trees, depth 6, minimum leaf 60; gradient boosting 100 trees, learning rate 0.03, depth 3. Selected on CV: linear regression."),
    ("img", FIG + "b1_errors_and_test_year_means.png", 1.0, "Figure b1 (notebook, (b) Step 3): left, train, CV and test error next to the baseline; right, the mean 12-month return by formation year."),
    ("img", FIG + "b2_coefficients_and_importances.png", 1.0, "Figure b2: the 10 largest standardised coefficients of the linear model and the 10 most important features of gradient boosting."),

    ("h1", "3. What the numbers mean for an investor"),
    ("bul", [
        "**The forecasts cannot be used.** An error of 37 to 38 points on 12-month returns that average between +1% and +22% is far too large to size or rank positions. Cross-validated R2 is about 2%: in the training years the models explain almost nothing.",
        "**R2 is negative for everyone, including the baseline (-0.45).** That is because R2 here is measured against the test years' own average, and the test years were a boom. Measured against the training-average forecast, the models are slightly worse than guessing the average (R2 -0.05 linear, -0.04 forest, -0.03 boosting).",
        "**Why test error (37 to 38) is so much higher than CV error (28.9).** The three test years all averaged about +21% (+22.0%, +21.7%, +21.2%), against +0.9% in the training years; only 2018 (+24%) was as high before. A forecast built on the training average is far too low. A naive forecast that already knew each test year's average would score 30.9. Cross-validation mixes years inside the training period and cannot see this shift. The starter notebook calls the test years a downturn; the data show the opposite.",
        "**It is not only the level shift.** After removing each year's average from outcome and forecast, the models still do not beat the zero forecast (30.91): linear 31.40, forest 31.31, boosting 31.23. And the rank correlation between forecast and outcome flips sign across years (linear +0.07 in 2022, -0.05 in 2023, -0.09 in 2024; average -0.02): no reliable ability to rank firms.",
        "**The cross-validation gain over the baseline is small but consistent, and it does not carry forward in time.** Linear regression's CV error is 28.88 against 29.16 for the baseline, a gain of 0.28, and it is lower in all 5 folds (by 0.07 to 0.47). But validated in time order inside the training years (train on earlier years, check on the next one, 2017 to 2021), no model beats the naive forecast (average error 30.46 for the baseline, 30.63 to 30.77 for the models), which matches the test result ((b) Step 6).",
        "**One feature drives the linear model's result.** Its largest coefficient (-3.3 points per standard deviation) is on the past 12-month return, which carries market-wide year-to-year variation learned from only 7 training years. Without that feature its test error is 37.69: better, but still above the baseline.",
    ]),

    ("h1", "4. Suggested text (edit freely)"),
    ("p", "**Memo (about 120 words).** We forecast each firm's 12-month total return from 30 features known on 1 July, training on formation years 2015 to 2021 and testing on 2022 to 2024. Linear regression (selected on cross-validation), a tuned random forest and tuned gradient boosting were compared with the naive training-average forecast. None beat the baseline out of sample: test RMSE is 37.20 for the baseline and 38.10, 37.93 and 37.84 for the models. The three models are within 0.05 points in cross-validation, so the selection is effectively a tie. The test years were a uniform boom (average 12-month return +21.6%, against +0.9% in training), and even after removing year averages the models show no cross-sectional skill (rank correlation about -0.02). The extra complexity of the ensembles does not pay off out of sample."),
    ("p", "**Slide (model comparison, about 1.5 minutes).** Title: \"No model beats the naive forecast\". The four-row table (baseline, linear, random forest, boosting; train, CV, test RMSE) or figure b1 (left). One line below: \"Test years were a +21% boom; no cross-sectional skill (rank correlation -0.02)\". Say: the models learn something in training, but nothing that carries to the test years."),

    ("h1", "5. Plain-language guide: what the notebook did"),
    ("bul", [
        "**Step 1, setup and tuning.** Took the table of firm-years from task (a), split it by year (training up to 2021, test 2022 to 2024). Each ensemble has settings (tree depth, learning rate). We tried 4 settings for each and kept the best by cross-validation: cut the training data into 5 groups of companies, train on 4, check on the 5th, rotate. All rows of a company stay in one group, so a model cannot recognise a company it already saw.",
        "**Step 2, side-by-side table.** Fitted every model on the training years, measured train, CV and test error next to the naive forecast, and chose the model with the lowest CV error. The test years are used once, here.",
        "**Step 3, figures.** Errors next to the baseline, the yearly average returns, and which features matter.",
        "**Step 4, numbers for results.json.** Stored the baseline, linear, best-ensemble errors and the selected model.",
        "**Step 5, reading.** Computed the sentences above from the table (including the year-by-year rank correlation and the within-year check), so they update if the data change. Test errors reported here are diagnostics, not used to choose anything.",
        "**Step 6, two checks on the selection (training years only).** The error fold by fold (linear beats the baseline in every fold, but the best of the three models changes from fold to fold) and a validation in time order (no model beats the naive forecast).",
    ]),

    ("h1", "6. Questions you may be asked"),
    ("tbl", [["Question", "Answer"],
        ["Why linear regression, when boosting has the best test error?", "The model is chosen on cross-validation only; the test years are used once, to report, not to choose. Choosing on the test result would flatter it. The three models are in any case within 0.05 CV points."],
        ["Why is test R2 negative?", "R2 compares with the test years' own average. All three test years were about +21% and the models predict near the training average (about +1%), so every forecast, including the baseline (-0.45), looks bad on that scale."],
        ["Are the models useless?", "They show no skill out of sample here. That is common: 12-month stock returns are very hard to forecast. The assignment accepts this result."],
        ["What did you tune in linear regression?", "Nothing: ordinary linear regression has no setting to tune, so it enters as it is. Only the two ensembles were tuned, on 4 settings each."],
        ["Why group the folds by company?", "Otherwise the same company would sit in training and in the check set, and the model could recognise it instead of forecasting. The folds still mix years, which makes CV a little optimistic."],
        ["Could a different year split change the answer?", "Possibly. The test years are one regime (a boom). We report that plainly and do not claim more than 'no evidence of skill'."],
    ], [0.30, 0.70], 8.6),

    ("h1", "7. What to be careful about"),
    ("bul", [
        "The selection of linear regression is a near-tie: the three models are within 0.05 CV points, and the best of them changes from fold to fold (linear regression wins 3 of 5 folds; (b) Step 6). Never say it won clearly.",
        "The test set covers three years of one regime; \"no model beats the baseline\" rests on that.",
        "The tuning grids are small (4 settings per ensemble, 100 to 150 trees), and the folds mix years.",
        "Rows with fewer than 12 holding months (302 firm-years of exiting firms) are not in the model samples.",
        "All numbers come from the run of 4 November; the notebook's printed sentences are recomputed on every run, this sheet is not.",
    ]),
]
