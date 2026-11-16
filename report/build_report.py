"""Build the full SRP technical report as a PDF.

    python report/build_report.py [out.pdf]

Pulls every number from data.py and every chart from figures.py, so the prose,
the tables and the figures cannot drift apart.
"""

from __future__ import annotations

import os
import sys
import tempfile

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figures                                      # noqa: E402
from style import F, MUTED, RULE                    # noqa: E402

# ------------------------------------------------------------ page frame --
def _page(canvas, doc, first=False):
    canvas.saveState()
    if not first:
        canvas.setFont(F, 7.6)
        canvas.setFillColor(MUTED)
        canvas.drawString(2.2 * cm, 1.35 * cm,
                          "Extending PARCO · SRP Group 9 · Universität Hildesheim")
        canvas.drawRightString(A4[0] - 2.2 * cm, 1.35 * cm, str(doc.page))
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.5)
        canvas.line(2.2 * cm, 1.75 * cm, A4[0] - 2.2 * cm, 1.75 * cm)
    canvas.restoreState()


def build(out_path: str):
    figdir = os.path.join(tempfile.gettempdir(), "parco_report_figs")
    figs = figures.build(figdir)

    doc = BaseDocTemplate(out_path, pagesize=A4,
                          leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                          topMargin=2.0 * cm, bottomMargin=2.2 * cm,
                          title="Extending PARCO — SRP Group 9",
                          author="SRP Group 9, Universität Hildesheim",
                          subject="Controlled experiments on parallel multi-agent CO for HCVRP")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="n")
    doc.addPageTemplates([
        PageTemplate(id="first", frames=[frame],
                     onPage=lambda c, d: _page(c, d, first=True)),
        PageTemplate(id="main", frames=[frame], onPage=_page),
    ])

    story = []
    import content
    content.compose(story, figs)
    doc.build(story)
    return out_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "PARCO_SRP_Report.pdf")
    print("building", out)
    build(out)
    print("done:", os.path.getsize(out) // 1024, "KB")
