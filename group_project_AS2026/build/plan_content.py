# Shared content for the plan (markdown + PDF) and the team briefing (PDF).
# Block types: ("h1", text) ("h2", text) ("p", text) ("bul", [text]) ("tbl", rows, col_fractions) ("note", text)
# Inline markup: **bold** only.

PLAN_TITLE = "Group plan: ESG, stock returns and machine learning"
PLAN_SUB = "EAIF: AI for Finance, Group Assignment AS 2026. Written Tuesday 3 November 2026; formation year 2025 decision updated 4 November."

PLAN = [
    ("h1", "1. Key dates"),
    ("tbl", [
        ["Date", "What"],
        ["Tue 3 Nov (today)", "We are in week 1 of the plan"],
        ["**Tue 24 Nov**", "Coaching with the lecturer: review of the notebook state and the draft slides"],
        ["**Fri 27 Nov, 23:59**", "Hard deadline on Moodle: memo (PDF), notebook (.ipynb), results.json, peer evaluation. Internal target: submit **Thu 26 Nov evening**."],
        ["Mon 7 Dec, 23:59", "Final slides (PDF), Moodle or email to the lecturers"],
        ["Tue 8 Dec", "Presentation: 8 minutes plus about 2 minutes of questions"],
    ], [0.27, 0.73]),
    ("note", "The lecturer will still communicate the notebook deadline, which will be close to the hand-in date in November. If it is earlier than 27 Nov, the freeze date below moves with it."),

    ("h1", "2. Status on Tuesday 3 November"),
    ("tbl", [
        ["Done", "Still open (week 0 items that slipped)"],
        ["Handouts and data dictionary saved in the repo. Coaching question sheet and plain-language explainer written. Coaching answers recorded. Task (a) drafted in the solution notebook (audit, treatments, formation panel; reviewed by Claude, waiting for your review in Colab). Starter notebook runs.",
         "Roles confirmed by all three. Group name chosen. Notebook copy created. Both teammates have read the explainer."],
    ], [0.5, 0.5]),

    ("h1", "3. Roles (proposal until all three confirm)"),
    ("tbl", [
        ["Person", "Handout roles", "Does"],
        ["**You (notebook owner)**", "Data lead + modelling lead", "Owns the notebook, which Claude drafts. Reviews and runs it in Colab. Writes results.json."],
        ["**Teammate B**", "Writing lead", "The memo in Word, including the section \"What would change with real data\". Fills in the peer evaluation."],
        ["**Teammate C**", "Analysis lead + slides", "Turns notebook results into tables and figures, and builds the PowerPoint (6 slides for 8 minutes)."],
    ], [0.24, 0.26, 0.5]),
    ("p", "The handout says every member must explain every cell, and that the peer evaluation can adjust individual scores. Neither teammate codes, so each task ends with a short walkthrough and a plain-language guide (see section 8)."),

    ("h1", "4. Decisions from the coaching (27 Oct)"),
    ("p", "The lecturer said there is a lot of leeway: any method is fine if it is consistent and we can explain why."),
    ("bul", [
        "Revenue unit problem: divide revenue and market cap by 1,000. Near-duplicate returns: keep one row per company-month.",
        "Target: total 12-month return in (b), excess return in (c). Period split in (c) by formation year. Environmental score standardised within year across all firms.",
        "Formation year 2025 in the backtest: either choice is fine, we must be able to defend it. Decided (4 Nov): left out of our backtest, because it has only 6 months of returns; including it lowers every rule and the benchmark by 1.6 to 2.3 points a year and keeps the ranking (notebook (d) Step 6).",
        "Analyst_Outlook: excluded from all models, listed in the audit table and in the feature table as excluded.",
        "Audit table: free choice of the headline number per problem, stating which one.",
        "Memo: the 3 pages include tables and figures. Slides: number and software are free, but the talk is only 8 minutes.",
        "Libraries: scikit-learn, statsmodels, possibly lightgbm. **AI tools are encouraged.**",
        "The lecturer suggested one slide that explains the audit: the problems we found and how we treated them.",
    ]),

    ("h1", "5. Timeline by week"),
    ("tbl", [
        ["Week", "Notebook (you, drafted by Claude)", "Memo (B)", "Slides (C)"],
        ["**1: 3 to 8 Nov**", "Finish setup (roles, group name, notebook copy). **Task (a):** audit and formation panel with 3 or more new dated features.", "Memo skeleton, data section with the simulated-data statement and licence line. Preliminary audit paragraph from the lead list.", "Slide skeleton (6 slides). Preliminary audit slide."],
        ["**2: 9 to 15 Nov**", "**Task (b):** linear model, random forest, gradient boosting, compared with the baseline.", "Pipeline and model sections. Outline of \"What would change with real data\".", "Model comparison slide."],
        ["**3: 16 to 22 Nov**", "**Task (c)** where ESG pays, **task (d)** backtest with floors and bootstrap. Then results.json and a full run in Colab. **Freeze Sun 22 Nov.**", "Results sections. Complete memo draft by Sun 22 Nov.", "ESG and backtest slides. Complete draft deck by Sun 22 Nov."],
        ["**4: 23 to 27 Nov**", "Fixes after coaching. Teammate runs the notebook top to bottom in Colab.", "**Tue 24 Nov coaching.** Then finalise the memo (Wed to Thu). Peer evaluation.", "Adjust the deck after coaching feedback."],
        ["**Submit**", "**Thu 26 Nov evening** (deadline Fri 27 Nov 23:59)", "", ""],
        ["**5: 28 Nov to 8 Dec**", "", "", "Final slides by Mon 7 Dec (internal: noon). Two timed rehearsals (Sat 5 Dec and Mon 7 Dec). **Present Tue 8 Dec.**"],
    ], [0.14, 0.34, 0.27, 0.25]),

    ("h1", "6. Notebook steps in order"),
    ("bul", [
        "**(a) Audit.** Check the leads: wrong revenue unit, near-duplicate returns, Analyst_Outlook leakage, survivorship (universe file), restated scores, non-random missing values, clipped scores. Look for anything else. For each problem record: how found, how treated, what changed in one number.",
        "**(a) Formation panel.** One row per company and formation year. Every feature gets the date from which it is known (is it in a file that existed on 1 July, with the value it had then?). At least 3 new features beyond the starter's.",
        "**(b) Models.** Linear regression on standardised features, random forest and gradient boosting. Tune with grouped cross-validation. Show train, CV and test side by side next to the naive baseline. The test set is used once. Say plainly if the ensemble does not pay off.",
        "**(c) ESG premium.** Previous year's Environmental score against the next 12-month excess return, by region and period (before 2021, from 2021), with industry-by-year controls and honest standard errors. Run on point-in-time and restated scores and explain the difference.",
        "**(d) Backtest.** Walk-forward forecasts, top decile held July to June, 20 bp cost per unit of turnover, ESG floors at the 50th and 80th percentile, bootstrap of the Sharpe difference to the equal-weight benchmark, on the full panel including firms that left.",
        "**results.json.** Fill the template, call write_results as the last cell, run the whole notebook top to bottom.",
    ]),

    ("h1", "7. Internal targets for the team"),
    ("tbl", [
        ["Date", "Target", "Owner"],
        ["Sun 8 Nov", "Notebook task (a) done and reviewed. Results sheet (a) sent. Memo skeleton and slide skeleton ready. Walkthrough 1 (30 min).", "You, B, C"],
        ["Wed 11 Nov", "Audit paragraph and audit slide drafted from results sheet (a).", "B, C"],
        ["Sun 15 Nov", "Notebook task (b) done. Results sheet (b). Pipeline and model text, model slide. \"What would change with real data\" outline. Walkthrough 2.", "You, B, C"],
        ["Sun 22 Nov", "**Freeze.** Tasks (c) and (d) done, results.json written, Colab run clean. Complete memo draft and complete deck. Walkthrough 3.", "You, B, C"],
        ["Mon 23 Nov", "Whole-team read-through of memo and deck. List of open questions for the coaching.", "All"],
        ["**Tue 24 Nov**", "**Coaching** with the lecturer.", "All"],
        ["Wed 25 to Thu 26 Nov", "Fix findings, finalise memo, teammate runs notebook top to bottom in Colab, each person fills the peer evaluation. **Submit Thu 26 Nov evening.**", "All"],
        ["Fri 27 Nov, 23:59", "Hard deadline (fallback only).", ""],
        ["Sat 5 Dec / Mon 7 Dec", "Timed rehearsals (8 minutes). Slides submitted by Mon 7 Dec noon (deadline 23:59).", "All"],
        ["Tue 8 Dec", "Presentation. Everyone can answer questions on every slide.", "All"],
    ], [0.2, 0.62, 0.18]),

    ("h1", "8. What each task must pass before it counts as done"),
    ("bul", [
        "**Leakage check:** every feature is dated, and nothing used was unknown on 1 July of the formation year.",
        "**Baseline next to every metric:** the naive mean forecast for models, the equal-weight benchmark for backtests.",
        "**Figures:** labelled axes with units. **Tables:** the same numbers as results.json.",
        "**Claims checked:** a sentence like \"beyond X\" or \"controlling for Y\" is only written after the comparison was run (Prof. Matter's feedback). Every number gets its meaning for an investor, and magnitude words match the numbers.",
        "**Honest uncertainty:** say plainly when a result is not distinguishable from zero or from the baseline.",
        "**Handover:** a one-page results sheet and a plain-language guide for B and C, and a 30-minute walkthrough.",
    ]),

    ("h1", "9. Support from Claude"),
    ("bul", [
        "Drafts the notebook cells in group_project_AS2026/notebook/Group_Work_AS_2026_solution.ipynb (a copy of the starter, which stays untouched), runs them locally on the repo data to check they work, and commits. Nothing is pushed without asking.",
        "You review each block, run it in Colab and give feedback. You own every cell, so Claude explains each block in plain terms.",
        "Writes the results sheet and the plain-language guide for each task, with numbers checked against the data.",
        "Prepares an outline for \"What would change with real data\" (15 points) so B can start early.",
    ]),

    ("h1", "10. Hours, risks and what to cut"),
    ("p", "Your budget is under 5 hours a week. From today to 27 Nov that is about 17 hours. Review and running time per task: (a) 4 to 5 h, (b) 3 h, (c) 3 h, (d) 4 h, final run and results.json 2 h, coaching 1 h, memo review 2 h. This is tight, so:"),
    ("bul", [
        "Teammates take over anything that needs no code: running \"Run all\" in Colab, checking numbers in the memo against the notebook, formatting tables and figures.",
        "If behind, cut in this order: fewer bootstrap repeats, a smaller tuning grid, tuning once instead of re-tuning each year (the handout accepts both).",
        "Weeks 3 and 4 are the heavy part. Do not postpone the audit: tasks (b) to (d) depend on it.",
        "One person owns the notebook, so there are no merge conflicts. Teammates edit only the memo and the slides.",
    ]),

    ("h1", "11. Open items to confirm"),
    ("bul", [
        "Group name (needed in all filenames and in results.json).",
        "Full names of the three members and the final roles.",
        "Whether the talk is exactly 8 minutes (handout says 10).",
        "The notebook deadline once the lecturer communicates it.",
    ]),
]

# ---------------- team briefing (for B and C) ----------------
BRIEF_TITLE = "Team briefing for the memo and the slides"
BRIEF_SUB = "For the writing lead (B) and the analysis and slides lead (C). EAIF Group Assignment AS 2026. Written 3 November 2026."

BRIEF = [
    ("h1", "What this is"),
    ("p", "A graded group assignment worth 100 points, one score for the group. We get simulated data about 1,376 companies (ESG scores and stock returns) and have to check it for errors, forecast returns, test whether good environmental scores paid, and test a trading strategy. **You do not need to code.** The notebook is built by the notebook owner, with AI help. You turn its results into the memo and the slides. Everyone must be able to explain what the notebook does, because the peer evaluation and the presentation can change individual scores."),
    ("h1", "Read first (about 45 minutes)"),
    ("bul", [
        "**Coaching_Explainer_AS_2026.pdf**: the big picture, the four tasks, sections 1 to 5 and the glossary. The key idea is *leakage*: using information that the investor did not have at the time.",
        "**Group_assignment_AS_2026_transcription.md** (the assignment text): tasks (a) to (e), grading table and rules.",
        "Both are in the repo folder group_project_AS2026/docs/. Results sheets will appear in group_project_AS2026/results_sheets/.",
    ]),
    ("h1", "Rules that decide points"),
    ("bul", [
        "**Every number appears next to the baseline it must beat** (the naive average forecast for models, the equal-weight benchmark for the backtest).",
        "**Every figure has labelled axes with units.** Every feature is dated (the date from which it is known).",
        "**Say that the data is simulated** and cite it with its licence: \"Simulated ESG and stock-return dataset, EAIF course, Autumn Semester 2026, CC BY 4.0\", https://github.com/umatter/EDFB/tree/main/data/esg2026. Put it in the memo and on the slides.",
        "**Memo: 3 pages including tables and figures** (the lecturer confirmed), plus an appendix of any length. Group name and members on page 1.",
        "**No overclaiming.** A result like \"the model does not beat the baseline\" is accepted and graded as such. Write a claim only after the number behind it was checked.",
        "**Explain what each number means for an investor**, not only the number. Use size words that match the numbers.",
    ]),
    ("h1", "Memo order (Word, 3 pages)"),
    ("bul", [
        "1. The question. 2. The data (simulated, licence). 3. The audit and the pipeline: features, the date from which each is known, the split.",
        "4. Results of tasks (b), (c), (d), each metric next to its baseline.",
        "5. A section titled **\"What would change with real data\"**: what remains unsolved after our audit (ESG scores are proprietary and raters disagree, survivorship is harder to see, trading costs are not constant, point-in-time availability) and, the larger part, which of our conclusions would survive and which would not, and why. Worth 15 points.",
        "6. Group members and their roles.",
    ]),
    ("h1", "Teammate B: writing lead"),
    ("tbl", [
        ["By", "Deliverable"],
        ["Sun 8 Nov", "Memo skeleton in Word with the six headings. Data section with the simulated-data statement and licence line."],
        ["Wed 11 Nov", "Audit paragraph (uses results sheet (a))."],
        ["Sun 15 Nov", "Pipeline and model sections. Outline of \"What would change with real data\"."],
        ["Sun 22 Nov", "Complete memo draft (results sections from sheets (c) and (d))."],
        ["Tue 24 Nov", "Coaching with the draft."],
        ["Thu 26 Nov", "Final memo as PDF. Peer evaluation filled in. Submit evening."],
    ], [0.18, 0.82]),
    ("h1", "Teammate C: analysis lead and slides"),
    ("p", "The talk is **8 minutes plus about 2 minutes of questions**, so plan 6 slides, about 1 to 1.5 minutes each. The lecturer asked for one slide that explains the audit: the problems found and how we treated them."),
    ("tbl", [
        ["Slide", "Content", "Minutes"],
        ["1", "Question and data (state: simulated, licence)", "1:00"],
        ["2", "Audit and pipeline: problems found, how treated", "1:30"],
        ["3", "Model comparison: linear vs ensemble vs baseline", "1:30"],
        ["4", "Where does ESG pay: region and period table", "1:15"],
        ["5", "Backtest with ESG floor: table and cumulative return figure", "1:30"],
        ["6", "What would change with real data", "1:15"],
    ], [0.1, 0.72, 0.18]),
    ("tbl", [
        ["By", "Deliverable"],
        ["Sun 8 Nov", "Slide skeleton in PowerPoint (6 slides, headings only)."],
        ["Wed 11 Nov", "Audit slide draft."],
        ["Sun 15 Nov", "Model comparison slide."],
        ["Sun 22 Nov", "Complete draft deck (also tables and figures with labelled axes and units)."],
        ["Tue 24 Nov", "Draft deck shown at the coaching."],
        ["Sat 5 and Mon 7 Dec", "Two timed rehearsals. Final PDF by Mon 7 Dec noon (deadline 23:59)."],
        ["Tue 8 Dec", "Presentation."],
    ], [0.22, 0.78]),
    ("h1", "What you get from the notebook owner"),
    ("bul", [
        "After each task: a **one-page results sheet** (the numbers, each next to its baseline, with suggested wording) and a **plain-language guide** to what the code did.",
        "A **30-minute walkthrough** on Sun 8, Sun 15 and Sun 22 Nov. After each one, write three sentences in your own words about what was done and why. If you can do that, you can answer questions on it.",
        "If a number looks odd, ask before you write it down.",
    ]),
    ("h1", "Everyone"),
    ("bul", [
        "All three of us must be able to answer questions on every slide and every part of the notebook, in plain terms.",
        "Each student fills in the **peer evaluation** on Moodle by the memo deadline.",
        "Coaching with the lecturer: **Tue 24 Nov**. Bring the draft memo and draft deck.",
    ]),
]
