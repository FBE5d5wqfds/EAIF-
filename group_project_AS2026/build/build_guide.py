# Builds docs/Presentation_Guide_Group_8.pdf (BFH layout). Usage: python build_guide.py OUT_DIR
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import renderbfh as R
import guide_content as G
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
meta = [["Institution", "Bern University of Applied Sciences (BFH)"], ["Course", "EAIF: AI for Finance, Autumn Semester 2026"],
        ["Group", "Group_8 (Beyeler Fabian, Lussi Laurin, Griessen Jan)"],
        ["Document type", "Guide for all three members: explanation, Q&A preparation, spoken script, coaching checklist"],
        ["Key dates", "Coaching Thu 19 Nov 2026; memo, notebook, results.json and peer evaluation Fri 27 Nov 2026, 23:59; presentation Tue 8 Dec 2026"],
        ["Source of numbers", "Submission notebook (Group_8_notebook.ipynb, confirmed by a fresh Colab run) and the final slide deck of 18 Nov 2026"]]
out = os.path.join(OUT, "Presentation_Guide_Group_8.pdf")
R.build_pdf(out, G.BLOCKS, G.TITLE, G.SUB, "EAIF Group Assignment AS 2026 | Presentation and coaching guide", "Group_8 | Status 18 November 2026",
            meta=meta, purpose="Everything the three of us need for the coaching and the talk: what we did and why in plain words, likely questions with answers, the script word for word, and what to ask the lecturer.")
print("built", out)
