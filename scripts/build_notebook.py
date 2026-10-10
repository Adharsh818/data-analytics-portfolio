"""Turn notebooks/olist_analysis.py (percent format) into an executed .ipynb.

Runs each cell, captures printed output, the last expression's value and matplotlib
figures, and writes notebooks/olist_analysis.ipynb with outputs embedded, so the notebook
renders fully on GitHub. Uses only the standard library, pandas and matplotlib.

Usage: python scripts/build_notebook.py
"""
import ast
import base64
import contextlib
import io
import json
import os
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "notebooks" / "olist_analysis.py"
DST = ROOT / "notebooks" / "olist_analysis.ipynb"


def split_cells(text: str):
    for chunk in re.split(r"^# %%", text, flags=re.M)[1:]:
        header, _, body = chunk.partition("\n")
        if "[markdown]" in header:
            md = "\n".join(re.sub(r"^# ?", "", line) for line in body.strip().splitlines())
            yield "markdown", md
        else:
            yield "code", body.strip()


def run_cell(code: str, ns: dict, count: int):
    outputs = []
    figures = []
    plt.show = lambda *a, **k: figures.extend(plt.get_fignums())
    tree = ast.parse(code)
    last_expr = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(tree, "<cell>", "exec"), ns)
        value = eval(compile(ast.Expression(last_expr.value), "<cell>", "eval"), ns) if last_expr else None
    if buf.getvalue():
        outputs.append({"output_type": "stream", "name": "stdout", "text": buf.getvalue()})
    for num in dict.fromkeys(figures):
        png = io.BytesIO()
        plt.figure(num).savefig(png, format="png", bbox_inches="tight")
        outputs.append({"output_type": "display_data", "metadata": {},
                        "data": {"image/png": base64.b64encode(png.getvalue()).decode(), "text/plain": "<Figure>"}})
    plt.close("all")
    if value is not None:
        data = {"text/plain": repr(value)}
        if hasattr(value, "to_html"):
            data["text/html"] = value.to_html()
        outputs.append({"output_type": "execute_result", "execution_count": count, "metadata": {}, "data": data})
    return outputs


def main() -> None:
    os.chdir(ROOT / "notebooks")
    ns = {"__name__": "__main__"}
    cells, count = [], 0
    for kind, src in split_cells(SRC.read_text(encoding="utf-8")):
        lines = src.splitlines(keepends=True)
        if kind == "markdown":
            cells.append({"cell_type": "markdown", "metadata": {}, "source": lines})
            continue
        count += 1
        print(f"Running cell {count}...")
        cells.append({"cell_type": "code", "execution_count": count, "metadata": {},
                      "outputs": run_cell(src, ns, count), "source": lines})
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    DST.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"Wrote {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
