import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import renderbfh as R            # registers Carlito
import common
common.BASE, common.BOLD, common.ITAL = "Carlito", "Carlito-Bold", "Carlito-Italic"   # fonts used inside the explainer's drawings
import outline_content as O, sheet_a_content as A, sheet_b_content as B, sheet_c_content as C, sheet_d_content as D, explainer_content as E, plan_content as P
from pypdf import PdfWriter, PdfReader

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
GROUP = "Group_8 (Beyeler Fabian, Lussi Laurin, Griessen Jan)"
STATUS = "4 November 2026"
FOOT = "Group_8 | Status " + STATUS
BASE_META = [["Institution", "Bern University of Applied Sciences (BFH)"], ["Course", "EAIF: AI for Finance, Autumn Semester 2026"], ["Group", GROUP]]
DEAD = ["Key dates", "Coaching Tue 24 Nov 2026; memo, notebook, results.json and peer evaluation Fri 27 Nov 2026, 23:59; slides Mon 7 Dec 2026, 23:59; presentation Tue 8 Dec 2026"]
SRC = ["Source of numbers", "Executed solution notebook, local run of 4 November 2026 (a fresh Colab run follows before submission)"]

docs = [
 ("docs/Outline_for_Laurin_Group_8.pdf", "Detailed outline for Laurin", "Memo, slides, questions and peer evaluation", "EAIF Group Assignment AS 2026 | Outline for Laurin",
  BASE_META + [["Document type", "Working outline for the memo (3 pages plus appendix), the slides (8 minutes) and the peer evaluation"], DEAD, SRC],
  "Tells you what each page of the memo must contain, which numbers to use and where each is computed, wording you can edit, and what not to say. The analysis is finished.", O.BLOCKS),
 ("docs/Team_Briefing_AS_2026.pdf", "Team briefing for the memo and the slides", "Rules that decide points, roles and deadlines", "EAIF Group Assignment AS 2026 | Team briefing",
  BASE_META + [["Document type", "Briefing for the writing lead and the slides"], DEAD],
  "A two-page orientation: what the assignment is, what to read first, the rules that decide points, the memo order and the deadlines.", P.BRIEF),
 ("results_sheets/Task_a_Results_and_Guide.pdf", "Task (a): results sheet and guide", "Pipeline and data audit", "EAIF Group Assignment AS 2026 | Task (a) results sheet",
  BASE_META + [["Document type", "Results sheet and plain-language guide for task (a)"], SRC],
  "The audit table with its numbers, what each problem means for an investor, suggested memo and slide text, a plain-language guide to the code, and likely questions.", A.BLOCKS),
 ("results_sheets/Task_b_Results_and_Guide.pdf", "Task (b): results sheet and guide", "Linear regression vs tree ensembles", "EAIF Group Assignment AS 2026 | Task (b) results sheet",
  BASE_META + [["Document type", "Results sheet and plain-language guide for task (b)"], SRC],
  "The model comparison next to the baseline, what the errors mean for an investor, suggested memo and slide text, a plain-language guide to the code, and likely questions.", B.BLOCKS),
 ("results_sheets/Task_c_Results_and_Guide.pdf", "Task (c): results sheet and guide", "Where does ESG pay?", "EAIF Group Assignment AS 2026 | Task (c) results sheet",
  BASE_META + [["Document type", "Results sheet and plain-language guide for task (c)"], SRC],
  "The region by period table (point-in-time and restated), what the one significant cell means and how firm it is, suggested memo and slide text, and likely questions.", C.BLOCKS),
 ("results_sheets/Task_d_Results_and_Guide.pdf", "Task (d): results sheet and guide", "Backtest with costs and an ESG floor", "EAIF Group Assignment AS 2026 | Task (d) results sheet",
  BASE_META + [["Document type", "Results sheet and plain-language guide for task (d)"], SRC],
  "The backtest table next to the benchmark, the bootstrap, what the floor costs, suggested memo and slide text, and likely questions.", D.BLOCKS),
 ("docs/Coaching_Explainer_AS_2026.pdf", "Plain-language explainer", "Ideas behind the coaching questions", "EAIF Group Assignment AS 2026 | Explainer",
  BASE_META + [["Document type", "Background reading in everyday language, corrected 3 November 2026 (28 firms)"]],
  "Explains the ideas behind the project (leakage, formation year, baselines, regression, cross-validation) with small examples. No finance or statistics background needed.", E.BLOCKS),
 ("docs/Group_Plan_AS_2026.pdf", "Group plan", "Timeline, roles and internal targets", "EAIF Group Assignment AS 2026 | Group plan",
  BASE_META + [["Document type", "Project plan written 3 November 2026"], DEAD],
  "The plan of work from the start of the project to the presentation on 8 December, with roles and internal targets.", P.PLAN),
]
paths = []
for rel, title, sub, header, meta, purpose, blocks in docs:
    out = os.path.join(OUT, os.path.basename(rel))
    R.build_pdf(out, blocks, title, sub, header, FOOT, meta=meta, purpose=purpose); paths.append((rel, title, out))
    print("built", os.path.basename(rel))

# package: cover page with contents, then the documents in reading order
order = [("1. Detailed outline for Laurin (memo, slides, Q&A)", 0), ("2. Team briefing (rules and deadlines)", 1), ("3. Task (a) results sheet: audit and pipeline", 2),
         ("4. Task (b) results sheet: models", 3), ("5. Task (c) results sheet: where ESG pays", 4), ("6. Task (d) results sheet: backtest", 5),
         ("7. Plain-language explainer (background)", 6), ("8. Group plan and timeline", 7)]
counts = [len(PdfReader(p[2]).pages) for p in paths]
rows = []; page = 2
for label, i in order:
    rows.append([label, f"{page} to {page + counts[i] - 1}" if counts[i] > 1 else str(page)]); page += counts[i]
cover_blocks = [("h1", "Contents"), ("tbl", [["Document", "Pages"]] + rows, [0.80, 0.20], 9.5),
                ("h1", "Suggested reading order"),
                ("bul", ["**First:** the outline (part 1) and the briefing (part 2): what the memo must contain and which rules decide points.",
                         "**Then:** the four results sheets (parts 3 to 6): numbers, figures, suggested text and likely questions for each task.",
                         "**When needed:** the explainer (part 7) for everyday-language background, and the plan (part 8) for timeline and roles.",
                         "**Questions:** ask Fabian before writing down any number that looks odd. The notebook and the figures for the slides are in the repository folder group_project_AS2026."])]
cover = os.path.join(OUT, "_cover.pdf")
R.build_pdf(cover, cover_blocks, "Package for Laurin", "Memo, slides and peer evaluation: everything in one PDF", "EAIF Group Assignment AS 2026 | Package for Laurin", FOOT,
            meta=BASE_META + [["Document type", "Combined package of 8 documents in one PDF"], DEAD, ["Status", STATUS]],
            purpose="Everything Laurin needs to write the memo and the slides, in the order in which it is most useful.")
assert len(PdfReader(cover).pages) == 1, "cover must stay on one page"
w = PdfWriter(); w.append(cover); w.add_outline_item("Contents", 0); page = 1
for label, i in order:
    r = PdfReader(paths[i][2])
    for pg in r.pages: w.add_page(pg)
    w.add_outline_item(label, page); page += len(r.pages)
w.add_metadata({"/Title": "Package for Laurin: Group_8, EAIF Group Assignment AS 2026", "/Author": "Group_8"})
w.write(os.path.join(OUT, "Laurin_Package_Group_8.pdf")); print("package pages:", page); os.remove(cover)

# Markdown copy of the outline (docs/Outline_for_Laurin_Group_8.md)
def md_for(blocks, title, sub):
    out = ["# " + title, "", "*" + sub + "*", ""]
    esc = lambda c: c.replace("|", "/").replace("\n", " ").replace("\\*", "*")
    for b in blocks:
        k = b[0]
        if k == "h1": out += ["## " + b[1], ""]
        elif k == "h2": out += ["### " + b[1], ""]
        elif k == "p": out += [esc(b[1]), ""]
        elif k in ("note", "small", "callout"): out += ["> " + esc(b[1]), ""]
        elif k == "bul": out += ["- " + esc(t) for t in b[1]] + [""]
        elif k == "img": out += [f"![{b[3] if len(b) > 3 else ''}]({b[1].split('results_sheets/')[-1]})", ""]
        elif k == "tbl":
            rows = b[1]
            out.append("| " + " | ".join(esc(c) for c in rows[0]) + " |"); out.append("|" + "|".join("---" for _ in rows[0]) + "|")
            for r in rows[1:]: out.append("| " + " | ".join(esc(c) for c in r) + " |")
            out.append("")
    return "\n".join(out)
open(os.path.join(OUT, "Outline_for_Laurin_Group_8.md"), "w").write(md_for(O.BLOCKS, O.TITLE, O.SUB)); print("built Outline_for_Laurin_Group_8.md")
