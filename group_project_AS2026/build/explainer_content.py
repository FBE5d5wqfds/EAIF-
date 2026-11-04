from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib import colors
from common import *

BLUE = colors.HexColor("#3b7bbf"); ORANGE = colors.HexColor("#e08a1e"); GREY = colors.HexColor("#b8c0c8"); GREEN = colors.HexColor("#2f855a")

def fig_formation_years():
    w, h = CONTENT_W, 62
    d = Drawing(w, h); years = list(range(2015, 2026)); bw = (w - 10) / len(years)
    for i, y in enumerate(years):
        col = BLUE if y <= 2021 else (ORANGE if y <= 2024 else GREY)
        d.add(Rect(5 + i * bw, 26, bw - 3, 20, fillColor=col, strokeColor=colors.white))
        d.add(String(5 + i * bw + (bw - 3) / 2, 33, str(y), fontName=BOLD, fontSize=8, fillColor=colors.white, textAnchor="middle"))
    def lab(i0, i1, text, col):
        x0, x1 = 5 + i0 * bw, 5 + (i1 + 1) * bw - 3
        d.add(Line(x0, 21, x1, 21, strokeColor=col, strokeWidth=1.4)); d.add(String((x0 + x1) / 2, 11, text, fontName=BOLD, fontSize=8, fillColor=col, textAnchor="middle"))
    lab(0, 6, "training years (formation 2015 to 2021)", BLUE); lab(7, 9, "test years (2022 to 2024)", ORANGE)
    d.add(String(5 + 10 * bw + (bw - 3) / 2, 11, "2025: only", fontName=BOLD, fontSize=7, fillColor=MUTED, textAnchor="middle"))
    d.add(String(5 + 10 * bw + (bw - 3) / 2, 3, "6 months", fontName=BOLD, fontSize=7, fillColor=MUTED, textAnchor="middle"))
    d.add(String(w / 2, h - 8, "Each box is one \"formation year\": the portfolio is formed on 1 July of that year.", fontName=ITAL, fontSize=8, fillColor=MUTED, textAnchor="middle"))
    return d

def fig_timeline():
    w, h = CONTENT_W, 100
    d = Drawing(w, h); x0, x1 = 8, w - 8; n = 30.0
    X = lambda m: x0 + (x1 - x0) * m / n
    base = 44
    d.add(Line(x0, base, x1, base, strokeColor=MUTED, strokeWidth=1))
    for m, t in [(0, "Jan 2020"), (12, "Jan 2021"), (18, "1 Jul 2021"), (24, "Jan 2022"), (30, "Jun 2022")]:
        d.add(Line(X(m), base - 3, X(m), base + 3, strokeColor=MUTED, strokeWidth=1)); d.add(String(X(m), base - 13, t, fontName=BASE, fontSize=7.5, fillColor=MUTED, textAnchor="middle"))
    d.add(Rect(X(0), base + 8, X(12) - X(0), 14, fillColor=BLUE, strokeColor=colors.white))
    d.add(String((X(0) + X(12)) / 2, base + 12, "fiscal year 2020", fontName=BOLD, fontSize=8, fillColor=colors.white, textAnchor="middle"))
    d.add(Rect(X(14), base + 8, X(17) - X(14), 14, fillColor=ORANGE, strokeColor=colors.white))
    d.add(String(X(14.8), base + 26, "row published", fontName=BOLD, fontSize=7.5, fillColor=ORANGE, textAnchor="middle"))
    d.add(String(X(14.8), base + 36, "(31 Mar to 31 May 2021)", fontName=BASE, fontSize=7, fillColor=ORANGE, textAnchor="middle"))
    d.add(Line(X(18), base - 3, X(18), base + 46, strokeColor=INK, strokeWidth=1.6))
    d.add(String(X(18), base + 52, "1 July 2021 = formation date", fontName=BOLD, fontSize=8, fillColor=INK, textAnchor="middle"))
    d.add(Rect(X(18), base + 8, X(30) - X(18), 14, fillColor=GREEN, strokeColor=colors.white))
    d.add(String((X(18) + X(30)) / 2, base + 12, "holding period (Jul 2021 to Jun 2022)", fontName=BOLD, fontSize=8, fillColor=colors.white, textAnchor="middle"))
    d.add(String(w / 2, 4, "The fiscal-year-2020 numbers may be used on 1 July 2021. Nothing published later may be used.", fontName=ITAL, fontSize=8, fillColor=MUTED, textAnchor="middle"))
    return d

TITLE = "Plain-language explainer"
SUB = "Ideas behind the coaching questions. EAIF: AI for Finance, Group Assignment AS 2026. Corrected 3 November 2026 with the results of the audit (28 firms)."

BLOCKS = [
    ("callout", "**What this document is.** Each section explains the idea behind one question on the question sheet, in everyday words, with a small example. You do not need any finance or statistics background. The numbers come from the course data, the starter notebook and our own audit in the solution notebook."),
    ("h1", "The big picture in five sentences"),
    ("bul", [
        "The course gives us **simulated** data about 1,376 companies over 14 years (fiscal years 2012 to 2025). No real firm is behind it.",
        "Every company publishes a report once a year. The year it covers is its **fiscal year**. The data has one row per company per year, plus one row per company per month for its stock return.",
        "An **ESG score** (0 to 100) says how responsibly a company behaves. We look at the **Environmental** part.",
        "We pretend to be an investor who picks stocks on **1 July** each year, holds them for 12 months, and asks: could we have predicted which stocks do well?",
        "The assignment tests whether we handle the data honestly. The main danger is using information the investor could not have had at the time. This is called **leakage**."]),
    ("h1", "The four tasks of the assignment"),
    ("bul", [
        "**(a) Audit:** check the data for errors (the course deliberately inserted some) and write a table: the problem, how we found it, how we fixed it, and what it changed in one number.",
        "**(b) Models:** predict each firm's return over the next 12 months with a simple model (linear regression) and with tree models, and compare them with a naive guess.",
        "**(c) ESG premium:** ask whether firms with a better Environmental score earned higher returns afterwards, by region and period. A **premium** is extra return earned by one group of firms.",
        "**(d) Backtest:** replay a strategy on past data as if we had traded it: each July buy the top-ranked 10% of firms (a **portfolio** is the set of stocks held), hold for 12 months and pay trading costs. Compare with buying all firms equally."]),
    ("p", "A **feature** is an input column the model uses to predict (for example profit margin). The **target** is the number it predicts."),

    ("h1", "1 Units and rescaling"), ("small", "Belongs to: Q1"),
    ("p", "A column has a **unit**. Here, Revenue and Market_Cap are in **USD million**. If one value was typed in USD *thousand* instead, it looks 1,000 times bigger than it should be. It is like one runner's time being recorded in seconds while everyone else's is in minutes."),
    ("p", "What the audit found: **28 firms** (302 firm-years) report revenue and market cap about 1,000 times too large. We found them by checking that carbon, water and energy use grow with revenue inside an industry: for these 28 firms they sit about 1,000 times below that relation, so only revenue and market cap are off. A simple revenue cut-off finds only 22 to 27 of them (firm 406 sits just below the usual line). Example: Company_ID 30 has revenue of 1,441,650 in 2012. As USD million that would be USD 1.4 trillion, bigger than any real company. Divided by 1,000 it is 1,441.65, which fits the typical firm (median revenue about 2,300 to 2,400). **Market cap** (the total value of a firm's shares) is scaled the same way."),
    ("tbl", [["Option on the sheet", "What it means", "Risk"],
             ["Divide by 1,000, keep the firms", "We treat the values as a unit mix-up and repair them.", "If they really are huge firms, we shrink them wrongly."],
             ["Keep as is", "We treat them as real mega firms.", "Size features (such as the logarithm of revenue, a transformation that shrinks big numbers) get extreme outliers: values far from all the others that pull averages."],
             ["Exclude the firms", "We remove them completely.", "We lose 28 firms (and the audit table should say so)."]], [0.26, 0.34, 0.40], 8.8),
    ("small", "Why it matters: the audit table (task a) is graded against a list of planted problems. The course deliberately inserted errors into the data. A unit problem is a classic one, and the grader wants to see what we did and what it changed. The lecturer agreed that dividing by 1,000 is acceptable."),

    ("h1", "2 Near-duplicate rows and why they matter"), ("small", "Belongs to: Q2"),
    ("p", "A **duplicate** is a row that appears twice. Here the two rows are not exactly equal: Company 1, March 2020 has -27.7587 and -27.7549 (percent). That looks like one measurement stored twice with a tiny rounding difference."),
    ("p", "Why it matters: a 12-month return is built by **compounding** the monthly returns, which means multiplying them. Each month is a factor: a return of -27.76% is the factor 0.7224. Take a firm that earned 0% in every other month. Its true yearly return is -27.76%. If the March row is counted twice, the factor is 0.7224 x 0.7224 = 0.5219, which gives **-47.8%**. One extra row makes the loss about 1.7 times larger (-48% instead of -28%)."),
    ("p", "The two values differ by at most 0.01 percentage points, so keeping the first row or averaging them gives practically the same result. Dropping both deletes the month entirely, which leaves a hole in that firm's year. In the starter, that firm-year would then have only 11 holding months and drop out of the model data (it needs 12), so it is the least attractive."),

    ("h1", "3 Total return, excess return and what a \"target\" is"), ("small", "Belongs to: Q3"),
    ("p", "The **target** is the number the model tries to predict. Here it is a firm's return over the 12 months after the portfolio is formed."),
    ("tbl", [["", "Definition", "Example"],
             ["Total return", "What an investor in the share earned over the period.", "Firm earned +8% over the year."],
             ["Risk-free rate", "What a safe account pays. In the data it is 0.1% to 0.4% per month, which is roughly 1.2% to 5% over a year.", "Safe account paid about 1.2% (in a year at 0.1% a month)."],
             ["Excess return", "Total return minus the risk-free rate. It measures the reward for taking risk.", "8% - 1.2% = about 6.8%."]], [0.18, 0.52, 0.30], 8.8),
    ("p", "The starter notebook predicts the **total** return in task (b), and so does our notebook. Task (c) asks about the **excess** return. They are close in the training years (about 1 point apart on average) but about 5 points apart in the test years, because the risk-free rate rose after 2021. Every table in the memo should say which one it uses. The handout's decision-time rule names the total return as the target."),
    ("p", "**The baseline.** The simplest possible forecast is \"everyone earns the average of the training years\". Its test error (RMSE, the typical size of a forecast error in percentage points) is 36.93 in the starter and 37.20 in our cleaned data. A model is only useful if it beats this number. In the starter, the random forest gets 37.31, so it does *not* beat the baseline, and the same is true for all our models. The assignment says that is a legitimate result, as long as we say so. Individual stocks swing a lot, so even the best forecasts are far off. What matters is the difference to the baseline."),

    ("h1", "4 Formation year, holding period and training years"), ("small", "Belongs to: Q4"),
    ("p", "The **formation year** is the year in which the portfolio is formed (on 1 July). The **holding period** runs from that July to the next 30 June. The starter fits the model on formation years 2015 to 2021 (training) and tests it on 2022 to 2024 (test). A random split would be wrong: a model could then learn from 2023 returns to \"predict\" 2021, which no real investor can do."),
    ("draw", fig_formation_years()),
    ("p", "**Why 2025 is special.** Returns stop in December 2025. A portfolio formed in July 2025 can only be followed for 6 months, so its 12-month return does not exist yet. The starter's model leaves 2025 out (it needs 12 months). Its **backtest** keeps it (6 months), which is why the starter's backtest has 126 months. Our own backtest (task d) uses formation years 2018 to 2024 (84 months) and leaves 2025 out."),
    ("p", "**Walk-forward training (task d).** In the backtest, the forecast for each formation year may only use *earlier* formation years. For 2018 the model trains on 2015 to 2017. For 2019 it trains on 2015 to 2018, and so on. That mimics a real investor, who never has future data. The first years have very little training data, so we start the backtest in 2018."),

    ("h1", "5 Fiscal year, formation year and calendar year"), ("small", "Belongs to: Q5"),
    ("p", "Three different \"years\" appear in the data, and mixing them up causes leakage."),
    ("bul", ["**Fiscal year t:** the year the company reports on. Example: fiscal year 2020.",
             "**Formation year:** the year in which we may use that report. A fiscal-year-2020 row is published between 31 March and 31 May 2021, so it is used for the portfolio formed on 1 July 2021. Formation year = fiscal year + 1.",
             "**Calendar year of the return:** the months in which the stock moved. The holding period July 2021 to June 2022 straddles two calendar years, so this option is ambiguous."]),
    ("draw", fig_timeline()),
    ("p", "**Why the question matters.** Task (c) compares \"before 2021\" and \"from 2021\". The score for fiscal year 2020 belongs to the formation year 2021. If the split is defined on the *fiscal* year, that score falls in the \"before\" group. If it is defined on the *formation* year (our choice, confirmed in the coaching), it falls in the \"from 2021\" group. The assignment says the data contains one genuine relationship, which should show up in one cell of the region-by-period table, so moving a year of data between the two periods can hide or dilute it."),

    ("h1", "6 Standardising the score (and the task (c) method)"), ("small", "Belongs to: Q6"),
    ("p", "**Standardising (z-score).** Subtract the average and divide by the spread: z = (score - average) / standard deviation. After this, the average is 0 and one unit means \"one standard deviation higher\". In the data the within-year spread of the Environmental score is about 17 points, so z = +1 means about 17 points above the year's average. We standardise within each year so that a year with generally higher or lower scores does not distort the comparison."),
    ("p", "**The option choice.** \"Within year, across all firms\" compares a firm with everybody. \"Within year and region\" compares it only with its regional peers. Because task (c) reports results by region, standardising within region would change what \"one unit\" means in each region. Example: if the spread in Europe is 10 points and in Asia 25, one unit would mean 10 points in Europe but 25 points in Asia, so the units would differ between regions."),
    ("h2", "Only needed later, not for the question: the method behind task (c)"),
    ("p", "**Regression with industry-by-year controls.** A regression fits a line through a cloud of points. Its slope (the **coefficient**) says how much the return changes when the score goes up by one unit, holding other things fixed. \"Industry-by-year controls\" means we compare each firm only to firms in the same industry in the same year (for example Energy firms in 2019). This stops us from mistaking an industry boom for an ESG effect."),
    ("p", "**Standard errors.** A coefficient is only an estimate. The standard error says how uncertain it is. If the estimate is less than about two standard errors from zero, we cannot tell it apart from noise. Two ways to get honest standard errors: **clustering by company** (we tell the software that the rows of one company belong together, because one company's years resemble each other and do not count as separate evidence; this is unrelated to clustering in machine learning), or the **bootstrap** (draw rows at random from our own data, with replacement, thousands of times, and see how much the answer jumps)."),

    ("h1", "7 Leakage and the Analyst_Outlook column"), ("small", "Belongs to: Q7"),
    ("p", "**Leakage** means the model sees information it would not have in real life. It is like a student who studies with the answer sheet: great marks, no real skill. The decision-time rule is the test: *was this value in a file that existed on 1 July, with the value it had then?*"),
    ("p", "**Our finding.** Analyst_Outlook is a score from 1 to 5. We measured its rank correlation with the return in several 12-month windows. A **rank correlation** (Spearman) asks whether firms with a higher rank on one variable also tend to have a higher rank on the other. It runs from -1 to +1, and 0 means no link."),
    ("small", "Here t is the fiscal year of the row. Example for the portfolio formed on 1 July 2021 (the fiscal year 2020 row):"),
    ("tbl", [["12-month window compared with Analyst_Outlook", "Rank correlation"],
             ["The 12 months after formation, Jul 2021 to Jun 2022 (the thing we try to predict)", "**0.68**"],
             ["The 12 months before formation, Jul 2020 to Jun 2021", "-0.01"],
             ["The 12 months before that, Jul 2019 to Jun 2020", "0.01"]], [0.78, 0.22], 8.8),
    ("p", "Real analyst ratings predict returns only weakly. A column that agrees so strongly with the future and with no other window behaves as if it was stamped with future information. A model that used it would look great on paper and be useless in practice: in our data a random forest reaches a test error of 29.1 with it against 37.6 without it (baseline 37.2)."),
    ("tbl", [["Option on the sheet", "What it means"],
             ["Yes, that is enough", "We report it in the audit table (how found, that we excluded it) and list it as \"excluded\" in the feature table. The feature table shows every candidate feature and the date from which it is known."],
             ["Also show a model with it included", "A warning demonstration: it shows how misleadingly good a leaking model looks. The options add to each other: tick all that apply."]], [0.30, 0.70], 8.8),

    ("h1", "8 The \"effect on one headline number\""), ("small", "Belongs to: Q8"),
    ("p", "A **headline number** is one figure that summarises a result, for example the average 12-month return, the model's test error (RMSE), or the Sharpe ratio. For each problem in the audit table, we show what the number was *before* and *after* the fix. Example row: \"Near-duplicate returns; found by counting repeated firm-months; fixed by keeping one row; firm-years with a full 12 holding months went from 9,002 to 9,182.\""),
    ("p", "The **Sharpe ratio** is the average excess return divided by its ups and downs (volatility), scaled to a year. It measures return per unit of risk. Higher is better."),

    ("h1", "9 Page and slide limits"), ("small", "Belongs to: Q9"),
    ("p", "This is a rule question, no concept needed. The handout says \"3-page memo (plus appendix of any length)\" and \"at most 8 slides, 10-minute talk\". The lecturer confirmed that tables and figures count towards the 3 pages and that the number of slides and the software are free; the talk is 8 minutes plus about 2 minutes of questions."),

    ("h1", "10 Libraries, Colab and run time"), ("small", "Belongs to: Q10"),
    ("p", "**Colab** is Google's free online notebook: our code runs on Google's computers. A **library** is a toolbox of ready-made code; **pip** is the command that installs one. **scikit-learn** has the models of task (b). **statsmodels** fits regressions and prints standard errors, which task (c) needs. Our notebook runs top to bottom in a few minutes on Colab (the model tuning is the slowest step)."),
    ("h2", "Optional background for tasks (b) to (d)"),
    ("tbl", [["Name", "In plain words"],
             ["Linear regression", "Finds one weight per input and adds them up (like a recipe). Easy to read, can only draw straight-line relationships. The handout asks for standardised inputs, which makes the weights comparable."],
             ["Random forest", "Builds hundreds of decision trees (flowcharts of yes/no questions such as \"is profit margin above 10%?\") and averages their answers."],
             ["Gradient boosting", "Also trees, but built one after another. Each new tree tries to fix the mistakes of the previous ones."],
             ["Overfitting", "The model memorises the training data (including its noise) and does badly on new data."]], [0.22, 0.78], 8.8),
    ("p", "**Tuning and cross-validation.** A model has **settings** chosen by us, such as how deep the trees may grow (hyperparameters). We choose them with **cross-validation**: cut the training data into 5 parts, train on 4, check on the fifth, and rotate. Our folds keep all rows of one company in the same part, so the model cannot recognise a company it saw in training. Inside the training years the parts mix different years, so the cross-validation score is a little optimistic. That is why the test years come last and are used once."),
    ("tbl", [["Our result (cleaned data)", "RMSE (percentage points)"],
             ["Naive baseline on the test years", "37.20"],
             ["Linear regression, test", "38.10"],
             ["Random forest (tuned), test", "37.93"],
             ["Gradient boosting (tuned), test", "37.84"],
             ["Cross-validation (training years), linear regression", "28.88"]], [0.70, 0.30], 8.8),
    ("p", "Cross-validation looks much better (28.9) than the test (37 to 38). The starter's own text blames a market downturn in the test years, but the data shows the opposite: the average 12-month return was **+21.6%** in the test formation years 2022 to 2024 against **+0.9%** in the training years, and only 2018 (+24%) was as high in training. The training average is therefore far too low for the test years."),
    ("p", "**Tune once vs re-tune each year (task d).** The handout accepts both. We tune gradient boosting once on the training years of task (b), which is a simplification because the setting uses years the early forecasts should not have seen. Linear regression has nothing to tune."),

    ("h1", "11 Use of AI tools"), ("small", "Belongs to: Q11"),
    ("p", "The lecturer's answer in the coaching: AI tools are encouraged. The handout also states that every group member must be able to explain every cell of the notebook, so it is best to keep a short log of where AI helped."),

    ("h1", "12 Notebook version"), ("small", "Belongs to: Q12"),
    ("p", "The notebook deadline will be communicated by the lecturer and will be close to the hand-in date in November. The handout gives the dates: 27 November for the memo, notebook and peer evaluation; 7 December for slides; 8 December for presentations."),

    ("h1", "A Quick glossary"), ("small", "Terms used in several sections"),
    ("tbl", [["Term", "Meaning"],
             ["Fiscal year", "The year a company's yearly report covers."],
             ["Leakage", "A model uses information that would not have been available at decision time."],
             ["Backtest", "Replaying a strategy on past data as if it had been traded."],
             ["Baseline", "A deliberately simple forecast (here: the training average) that every model must beat."],
             ["Compounding", "Multiplying monthly return factors to get a yearly return."],
             ["Volatility", "How much returns go up and down; technically the standard deviation of returns, usually per year."],
             ["Point-in-time", "Using only what was known on the decision date, with the value it had then."],
             ["Formation date", "1 July each year: portfolios are picked and held until the next 30 June."],
             ["Survivorship bias", "Testing only on firms that still exist, which hides the ones that failed. The file universe_current.csv has only survivors (987 of 1,376 firms)."],
             ["Restated scores", "ESG scores as a download today shows them, revised with hindsight, so they are not what an investor knew back then."],
             ["RMSE", "Typical size of a forecast error, in the units of the target (percentage points of return). Lower is better."],
             ["R squared", "Share of the variation the model explains. 0 is as good as the average; negative is worse than the average."],
             ["Bootstrap", "Draw rows at random from our own data, with replacement, thousands of times, to see how much a result moves by chance."],
             ["Sharpe ratio", "Average excess return divided by volatility, scaled to a year: return per unit of risk."],
             ["Turnover", "Share of the portfolio replaced at each rebalancing. Each unit costs 20 basis points (0.20%) in the starter's convention, charged on the sell and the buy."]], [0.22, 0.78], 8.8),
]
