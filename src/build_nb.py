"""Turn a percent-format script (notebooks/_py/NN_name.py) into an executed notebook.

    python src/build_nb.py 01_cleaning        # builds + runs notebooks/01_cleaning.ipynb

Cells are split on lines starting with '# %%'; '# %% [markdown]' cells hold markdown
written as '# ' comment lines.
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def convert(src: Path) -> nbformat.NotebookNode:
    nb = nbformat.v4.new_notebook()
    kind, buf = None, []

    def flush():
        if kind is None:
            return
        text = "\n".join(buf).strip("\n")
        if not text:
            return
        if kind == "md":
            text = "\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in text.split("\n"))
            nb.cells.append(nbformat.v4.new_markdown_cell(text))
        else:
            nb.cells.append(nbformat.v4.new_code_cell(text))

    for line in src.read_text(encoding="utf-8").split("\n"):
        if line.startswith("# %%"):
            flush()
            kind, buf = ("md" if "[markdown]" in line else "code"), []
        else:
            buf.append(line)
    flush()
    return nb


if __name__ == "__main__":
    for name in sys.argv[1:]:
        src = ROOT / "notebooks" / "_py" / f"{name}.py"
        nb = convert(src)
        NotebookClient(nb, timeout=3600, kernel_name="python3",
                       resources={"metadata": {"path": str(ROOT / "notebooks")}}).execute()
        out = ROOT / "notebooks" / f"{name}.ipynb"
        nbformat.write(nb, out)
        print("built", out)
