import json, sys, os, uuid, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nb_a_cells import CELLS as A
from nb_b_cells import CELLS as B
from nb_c_cells import CELLS as C
from nb_d_cells import CELLS as D, FINAL
CELLS = A + B + C + D
src, dst = sys.argv[1], sys.argv[2]
nb = json.load(open(src))
idx = next(i for i, c in enumerate(nb["cells"]) if c["cell_type"] == "markdown" and "".join(c["source"]).startswith("# 5. Your tasks"))
new = []
for kind, text in CELLS:
    cell = {"cell_type": kind, "id": uuid.uuid4().hex[:8], "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code": cell.update(execution_count=None, outputs=[])
    new.append(cell)
nb["cells"] = nb["cells"][:idx + 1] + new + nb["cells"][idx + 1:]
URL = "https://colab.research.google.com/github/FBE5d5wqfds/EAIF-/blob/main/group_project_AS2026/notebook/Group_Work_AS_2026_solution.ipynb"
nb["cells"].insert(0, {"cell_type": "markdown", "id": uuid.uuid4().hex[:8], "metadata": {}, "source": ["[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](" + URL + ")"]})
for kind, text in FINAL:
    nb["cells"].append({"cell_type": kind, "id": uuid.uuid4().hex[:8], "metadata": {}, "source": text.strip("\n").splitlines(keepends=True), "execution_count": None, "outputs": []})
json.dump(nb, open(dst, "w"), indent=1, ensure_ascii=False)
print("inserted", len(new), "cells after index", idx, "-> total", len(nb["cells"]))
