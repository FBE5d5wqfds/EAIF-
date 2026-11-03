# Group plan: ESG, stock returns and machine learning

*EAIF: AI for Finance, Group Assignment AS 2026. Written Tuesday 3 November 2026.*

## 1. Key dates

| Date | What |
|---|---|
| Tue 3 Nov (today) | We are in week 1 of the plan |
| **Tue 24 Nov** | Coaching with the lecturer: review of the notebook state and the draft slides |
| **Fri 27 Nov, 23:59** | Hard deadline on Moodle: memo (PDF), notebook (.ipynb), results.json, peer evaluation. Internal target: submit **Thu 26 Nov evening**. |
| Mon 7 Dec, 23:59 | Final slides (PDF), Moodle or email to the lecturers |
| Tue 8 Dec | Presentation: 8 minutes plus about 2 minutes of questions |

> The lecturer will still communicate the notebook deadline, which will be close to the hand-in date in November. If it is earlier than 27 Nov, the freeze date below moves with it.

## 2. Status on Tuesday 3 November

| Done | Still open (week 0 items that slipped) |
|---|---|
| Handouts and data dictionary saved in the repo. Coaching question sheet and plain-language explainer written. Coaching answers recorded. First data check: leads for the audit found. Starter notebook runs. | Roles confirmed by all three. Group name chosen. Notebook copy created. Both teammates have read the explainer. |

## 3. Roles (proposal until all three confirm)

| Person | Handout roles | Does |
|---|---|---|
| **You (notebook owner)** | Data lead + modelling lead | Owns the notebook, which Claude drafts. Reviews and runs it in Colab. Writes results.json. |
| **Teammate B** | Writing lead | The memo in Word, including the section "What would change with real data". Fills in the peer evaluation. |
| **Teammate C** | Analysis lead + slides | Turns notebook results into tables and figures, and builds the PowerPoint (6 slides for 8 minutes). |

The handout says every member must explain every cell, and that the peer evaluation can adjust individual scores. Neither teammate codes, so each task ends with a short walkthrough and a plain-language guide (see section 8).

## 4. Decisions from the coaching (27 Oct)

The lecturer said there is a lot of leeway: any method is fine if it is consistent and we can explain why.

- Revenue unit problem: divide revenue and market cap by 1,000. Near-duplicate returns: keep one row per company-month.
- Target: total 12-month return in (b), excess return in (c). Period split in (c) by formation year. Environmental score standardised within year across all firms.
- Formation year 2025 in the backtest: either choice is fine, we must be able to defend it. Plan: keep it in the backtest (6 months) and say so, not use it for fitting.
- Analyst_Outlook: excluded from all models, listed in the audit table and in the feature table as excluded.
- Audit table: free choice of the headline number per problem, stating which one.
- Memo: the 3 pages include tables and figures. Slides: number and software are free, but the talk is only 8 minutes.
- Libraries: scikit-learn, statsmodels, possibly lightgbm. **AI tools are encouraged.**
- The lecturer suggested one slide that explains the audit: the problems we found and how we treated them.

## 5. Timeline by week

| Week | Notebook (you, drafted by Claude) | Memo (B) | Slides (C) |
|---|---|---|---|
| **1: 3 to 8 Nov** | Finish setup (roles, group name, notebook copy). **Task (a):** audit and formation panel with 3 or more new dated features. | Memo skeleton, data section with the simulated-data statement and licence line. Preliminary audit paragraph from the lead list. | Slide skeleton (6 slides). Preliminary audit slide. |
| **2: 9 to 15 Nov** | **Task (b):** linear model, random forest, gradient boosting, compared with the baseline. | Pipeline and model sections. Outline of "What would change with real data". | Model comparison slide. |
| **3: 16 to 22 Nov** | **Task (c)** where ESG pays, **task (d)** backtest with floors and bootstrap. Then results.json and a full run in Colab. **Freeze Sun 22 Nov.** | Results sections. Complete memo draft by Sun 22 Nov. | ESG and backtest slides. Complete draft deck by Sun 22 Nov. |
| **4: 23 to 27 Nov** | Fixes after coaching. Teammate runs the notebook top to bottom in Colab. | **Tue 24 Nov coaching.** Then finalise the memo (Wed to Thu). Peer evaluation. | Adjust the deck after coaching feedback. |
| **Submit** | **Thu 26 Nov evening** (deadline Fri 27 Nov 23:59) |  |  |
| **5: 28 Nov to 8 Dec** |  |  | Final slides by Mon 7 Dec (internal: noon). Two timed rehearsals (Sat 5 Dec and Mon 7 Dec). **Present Tue 8 Dec.** |

## 6. Notebook steps in order

- **(a) Audit.** Check the leads: wrong revenue unit, near-duplicate returns, Analyst_Outlook leakage, survivorship (universe file), restated scores, non-random missing values, clipped scores. Look for anything else. For each problem record: how found, how treated, what changed in one number.
- **(a) Formation panel.** One row per company and formation year. Every feature gets the date from which it is known (is it in a file that existed on 1 July, with the value it had then?). At least 3 new features beyond the starter's.
- **(b) Models.** Linear regression on standardised features, random forest and gradient boosting. Tune with grouped cross-validation. Show train, CV and test side by side next to the naive baseline. The test set is used once. Say plainly if the ensemble does not pay off.
- **(c) ESG premium.** Previous year's Environmental score against the next 12-month excess return, by region and period (before 2021, from 2021), with industry-by-year controls and honest standard errors. Run on point-in-time and restated scores and explain the difference.
- **(d) Backtest.** Walk-forward forecasts, top decile held July to June, 20 bp cost per unit of turnover, ESG floors at the 50th and 80th percentile, bootstrap of the Sharpe difference to the equal-weight benchmark, on the full panel including firms that left.
- **results.json.** Fill the template, call write_results as the last cell, run the whole notebook top to bottom.

## 7. Internal targets for the team

| Date | Target | Owner |
|---|---|---|
| Sun 8 Nov | Notebook task (a) done and reviewed. Results sheet (a) sent. Memo skeleton and slide skeleton ready. Walkthrough 1 (30 min). | You, B, C |
| Wed 11 Nov | Audit paragraph and audit slide drafted from results sheet (a). | B, C |
| Sun 15 Nov | Notebook task (b) done. Results sheet (b). Pipeline and model text, model slide. "What would change with real data" outline. Walkthrough 2. | You, B, C |
| Sun 22 Nov | **Freeze.** Tasks (c) and (d) done, results.json written, Colab run clean. Complete memo draft and complete deck. Walkthrough 3. | You, B, C |
| Mon 23 Nov | Whole-team read-through of memo and deck. List of open questions for the coaching. | All |
| **Tue 24 Nov** | **Coaching** with the lecturer. | All |
| Wed 25 to Thu 26 Nov | Fix findings, finalise memo, teammate runs notebook top to bottom in Colab, each person fills the peer evaluation. **Submit Thu 26 Nov evening.** | All |
| Fri 27 Nov, 23:59 | Hard deadline (fallback only). |  |
| Sat 5 Dec / Mon 7 Dec | Timed rehearsals (8 minutes). Slides submitted by Mon 7 Dec noon (deadline 23:59). | All |
| Tue 8 Dec | Presentation. Everyone can answer questions on every slide. | All |

## 8. What each task must pass before it counts as done

- **Leakage check:** every feature is dated, and nothing used was unknown on 1 July of the formation year.
- **Baseline next to every metric:** the naive mean forecast for models, the equal-weight benchmark for backtests.
- **Figures:** labelled axes with units. **Tables:** the same numbers as results.json.
- **Claims checked:** a sentence like "beyond X" or "controlling for Y" is only written after the comparison was run (Prof. Matter's feedback). Every number gets its meaning for an investor, and magnitude words match the numbers.
- **Honest uncertainty:** say plainly when a result is not distinguishable from zero or from the baseline.
- **Handover:** a one-page results sheet and a plain-language guide for B and C, and a 30-minute walkthrough.

## 9. Support from Claude

- Drafts the notebook cells in a new copy next to the starter (Group_Work_AS_2026_solution.ipynb), runs them locally on the repo data to check they work, and commits. Nothing is pushed without asking.
- You review each block, run it in Colab and give feedback. You own every cell, so Claude explains each block in plain terms.
- Writes the results sheet and the plain-language guide for each task, with numbers checked against the data.
- Prepares an outline for "What would change with real data" (15 points) so B can start early.

## 10. Hours, risks and what to cut

Your budget is under 5 hours a week. From today to 27 Nov that is about 17 hours. Review and running time per task: (a) 4 to 5 h, (b) 3 h, (c) 3 h, (d) 4 h, final run and results.json 2 h, coaching 1 h, memo review 2 h. This is tight, so:

- Teammates take over anything that needs no code: running "Run all" in Colab, checking numbers in the memo against the notebook, formatting tables and figures.
- If behind, cut in this order: fewer bootstrap repeats, a smaller tuning grid, tuning once instead of re-tuning each year (the handout accepts both).
- Weeks 3 and 4 are the heavy part. Do not postpone the audit: tasks (b) to (d) depend on it.
- One person owns the notebook, so there are no merge conflicts. Teammates edit only the memo and the slides.

## 11. Open items to confirm

- Group name (needed in all filenames and in results.json).
- Full names of the three members and the final roles.
- Whether the talk is exactly 8 minutes (handout says 10).
- The notebook deadline once the lecturer communicates it.
