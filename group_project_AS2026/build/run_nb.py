import sys, os, nbformat, time
from nbclient import NotebookClient
src, dst = sys.argv[1], sys.argv[2]
os.environ.setdefault("ESG2026_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "esg2026", ""))
nb = nbformat.read(src, as_version=4)
t = time.time()
NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": os.path.dirname(os.path.abspath(dst))}}).execute()
nbformat.write(nb, dst); print("executed in %.0fs" % (time.time() - t))
