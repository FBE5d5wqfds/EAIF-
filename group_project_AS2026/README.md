# Group project AS 2026: ESG, stock returns and machine learning

EAIF: AI for Finance (BFH). Graded group assignment on a simulated ESG and stock-return panel
(dataset: "Simulated ESG and stock-return dataset, EAIF course, Autumn Semester 2026, CC BY 4.0",
https://github.com/umatter/EDFB/tree/main/data/esg2026; a copy is in `../data/esg2026/`).

| Folder | Content |
|---|---|
| `notebook/` | `Group_Work_AS_2026_solution.ipynb`: the starter notebook with our own cells for tasks (a) to (d) below Section 5 |
| `results_sheets/` | One PDF per task (a to d): results, meaning for an investor, suggested memo and slide text, plain-language guide, likely questions; `figures/` holds the notebook's figures for the memo and slides |
| `docs/` | Assignment handouts, group plan, team briefing, coaching question sheet and explainer, and `Outline_for_Laurin_Group_8` (detailed memo, slide and Q&A outline) |
| `submission/` | Files to hand in: `Group_8_notebook.ipynb` (executed; same numbers as a fresh Colab run on 4 Nov 2026) and `Group_8_results.json` |
| `build/` | Sources that build the notebook cells and every PDF (see below); `assets/` holds the fonts and logo for the BFH layout |

Open the notebook in Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FBE5d5wqfds/EAIF-/blob/main/group_project_AS2026/notebook/Group_Work_AS_2026_solution.ipynb)

Group name: **Group_8** (Beyeler Fabian, Lussi Laurin, Griessen Jan).

Key dates: coaching Tue 24 Nov 2026; memo, notebook, results.json and peer evaluation due Fri 27 Nov 2026 23:59;
slides Mon 7 Dec 2026 23:59; presentation Tue 8 Dec 2026. See `docs/PLAN.md`.


## Rebuilding (from the repository root)

```
python group_project_AS2026/build/make_nb.py notebooks/Python/groupwork/Group_Work_AS_2026.ipynb /tmp/sol.ipynb   # starter + our cells
python group_project_AS2026/build/run_nb.py /tmp/sol.ipynb /tmp/sol_exec.ipynb                                     # execute locally (uses ../data/esg2026)
python group_project_AS2026/build/build_bfh_all.py /tmp/out                                                        # all PDFs, the package and the outline .md
```

Needs pandas, scikit-learn, statsmodels, matplotlib, nbclient, ipykernel, reportlab and pypdf. Copy the PDFs from `/tmp/out` into
`docs/` and `results_sheets/` as listed in `build_bfh_all.py`. The text of each PDF lives in the `*_content.py` files; notebook cells live in `nb_*_cells.py`.
