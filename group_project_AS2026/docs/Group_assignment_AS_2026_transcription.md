# Group Assignment AS 2026: ESG, Stock Returns and Machine Learning (transcription)

> Text transcription of the handout `Group_assignment_AS_2026.pdf` (EAIF: AI for Finance). The original PDF was not
> on disk when this was saved, so this is a transcription, not the official file. Tasks (a) to (e) are also in
> Section 5 of `notebooks/Python/groupwork/Group_Work_AS_2026.ipynb`. Data dictionary: `ESG_data_description_AS_2026.pdf`
> (same folder).

## Dates

| When | What |
|---|---|
| Fri 27 Nov 2026, 23:59 | Memo (PDF), notebook (.ipynb), `results.json` and peer evaluation, via Moodle |
| Mon 7 Dec 2026, 23:59 | Slides (PDF), via Moodle or by email to the lecturers |
| Tue 8 Dec 2026 (lecture slot) | Presentations: 10 minutes per group plus questions |

## Organisation

Group size 3 to 4. Roles named in the memo: data lead (pipeline, audit), modelling lead (models, CV, tuning),
analysis lead (premium, backtest, figures, tables), writing lead (memo, slides). Everyone must be able to explain every cell.

Notebook: Sections 1 to 4 and 6 are given (run, read, do not delete). Section 5 (tasks a to e) and the values in
Section 6 are our work, in new cells below Section 5.

## The pattern every model must follow (decision-time rule)

- Portfolios are formed on 1 July of each year.
- Every feature comes from the fiscal-year row published before that date, or from returns up to June of the formation year.
- Target: total return over the following twelve months.
- Split by formation year: train on formation years up to 2021, test on 2022 to 2024.
- Tuning by (Group)KFold cross-validation inside the training years; test set used once, next to a naive baseline.

## Tasks

- **(a) Pipeline and data audit.** Own formation panel from the point-in-time file, at least three features not in the
  worked model, each justified by the decision-time rule. Audit all five files; for every problem: what it is, how found,
  how treated, effect on one headline number. Test set separated by formation year; GroupKFold by company only inside
  training. *Deliverable: one-page audit table (issue, how detected, how treated, effect on one headline number) and a
  table of features with the date from which each is known.*
- **(b) Linear baseline vs tree ensembles.** Linear regression on standardised features plus at least one of random
  forest / gradient boosting for the twelve-month return. Tune ensembles by CV inside training years. Train, CV and test
  side by side next to the naive mean baseline for every model. Select on CV, report test once. "The ensemble does not
  pay off" is a legitimate, graded result. *Deliverable: one comparison table and one sentence on whether the
  ensemble's extra complexity pays off out of sample.*
- **(c) Where does ESG pay?** Previous fiscal year's Environmental score (standardised within year) vs next twelve
  months' excess return, by region and by period (before / from 2021), with industry-by-year controls. Point estimates
  with bootstrap or clustered SEs; say where distinguishable from zero. Repeat with the restated scores and explain the
  difference. *Deliverable: one table (region x period, point-in-time and restated) and one sentence on where an
  investor could have earned an ESG premium and where not.*
- **(d) Backtest with costs and an ESG floor.** Rank on the forecast of the model selected in (b), trained for each
  formation year on earlier formation years only; top decile held July to June; 20 bp per unit of one-way turnover.
  Either re-tune inside each formation year's training window or tune once on the training years (say which and why;
  tuning once is a simplification). ESG floor: pool restricted to firms with Environmental score at or above the 50th,
  then the 80th percentile of that year. Report annualised return, volatility, Sharpe and turnover for no floor, the two
  floors and the equal-weight benchmark, all on the full panel including firms that left. Bootstrap the Sharpe
  difference between the best rule and the benchmark (resample months). *Deliverable: one table, one figure of
  cumulative return series, one sentence on what the floor costs and whether the difference to the benchmark is
  distinguishable from noise.*
- **(e) Memo and slides.** 3-page memo to an investment committee (plus appendix of any length), in this order:
  1. the question; 2. the data (state it is simulated, cite with licence); 3. the audit (a) and the pipeline: features,
  date from which each is known, the split; 4. results of (b) to (d), every metric next to its baseline;
  5. a section titled **"What would change with real data"**: what remains to be solved after an audit like ours
  (scores that are proprietary and disagree across raters, survivorship that is harder to see, costs that are not a
  constant, point-in-time availability) and, the larger part, which conclusions would survive and which not, and why;
  6. group members and roles. Group name and members on page 1.
  Slides: at most 8, 10-minute talk. Suggested: question and data (1), audit and pipeline (1), model comparison (1-2),
  where ESG pays (1), backtest with floor (1-2), what would change with real data (1).
  *Deliverable: memo PDF, slides PDF and `results.json`, with the CC BY 4.0 attribution.*

**Rules.** Every metric next to the baseline it must beat (naive mean forecast, equal-weight benchmark). Every figure
has labelled axes with units. Every feature is dated. Cite the dataset with its licence.

## Grading (100 points, one group score)

| Criterion | Pts | What the grader looks for |
|---|---|---|
| Pipeline and data audit (a) | 20 | 5 leakage-free formation panel; 15 audit table, graded against the list of planted problems |
| Model comparison (b) | 20 | linear vs tree ensemble, selection on CV, test reported once, next to naive baseline |
| Where does ESG pay (c) | 15 | 8 finding the cell where the premium exists and only that cell; 4 honest uncertainty; 3 point-in-time vs restated |
| Backtest with costs and floor (d) | 15 | formed after publication, held twelve months, costs charged, cost of the floor shown, bootstrap of difference to benchmark |
| Memo and slides (e) | 15 | clear question, clear answer, labelled figures with units, no overclaiming; 10 minutes |
| What would change with real data | 15 | 5 for the list, 10 for which conclusions survive and why |

Tasks (a) to (d) are graded from notebook and memo together: a memo result the notebook does not reproduce earns no
points. Individual adjustment: every student rates every member (incl. self) in a Moodle form by the memo deadline;
clearly unequal contributions adjust the group score for the individuals concerned.

## Submission (one per group, all four carry the group name)

| Deliverable | Format | Requirements | Where |
|---|---|---|---|
| Notebook | .ipynb | runs top to bottom in Colab without errors; given cells kept; own cells below Section 5 | Moodle |
| Memo | PDF | 3 pages plus appendix; group name and members on page 1 | Moodle |
| Slides | PDF | at most 8 slides | Moodle or email to lecturers |
| results.json | .json | written by the notebook's `write_results` helper (Section 6) | Moodle |
| Peer evaluation | Moodle form | one per student | Moodle |

`results.json` carries the same headline numbers as the memo; its audit section is a free list in our own words.

## Citation

"Simulated ESG and stock-return dataset, EAIF course, Autumn Semester 2026, CC BY 4.0"
https://github.com/umatter/EDFB/tree/main/data/esg2026

Data: 14,250 firm-years and 171,764 firm-months, 1,376 firms, fiscal years 2012 to 2025 (389 exits, 987 survivors).
Questions go to the Moodle forum.
