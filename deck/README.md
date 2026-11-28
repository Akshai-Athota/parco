# Deck v2

Narrative: PARCO → the objective → the open questions → three experiments,
each with its method, its computation cost, its results and a discussion of
*why* the result came out the way it did.

```bash
npm install pptxgenjs image-size
SKILL_DIR=<pptx skill dir> node deck/build_deck_v2.js
```

Figures are read from `report/_figs`, `report/_figs_deck` and `poster/_figs_v2`;
regenerate them first:

```bash
python report/figures.py report/_figs
python report/figures_deck.py report/_figs_deck
python poster/figures_v2.py poster/_figs_v2
```

Every number comes from `report/data.py`, so the deck, the report and the
posters cannot disagree.

The two unfinished ideas (explicit wait action, dynamic re-encoding) are not
presented as experiments; they appear once, in the limitations slide.
