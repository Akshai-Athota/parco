// PARCO SRP deck, v2 — narrative: PARCO → objective → questions → 3 experiments
const pptxgen = require("pptxgenjs");
const path = require("path");

const REPO = "C:/PARCO/parco/.claude/worktrees/hcvrp-research-setup-592e98";
const AS = `${REPO}/poster/assets`;        // paper figures
const FR = `${REPO}/report/_figs`;         // report charts
const FD = `${REPO}/report/_figs_deck`;    // compute-scaling charts
const FV = `${REPO}/poster/_figs_v2`;      // decoding + spectrum

const THEME = {
  name: "PARCO SRP",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "12304A", lt1: "FFFFFF", dk2: "1F3B57", lt2: "EAF0F5",
    accent1: "E2561F", accent2: "D9A21B", accent3: "12927A",
    accent4: "2E5C8A", accent5: "7E5AA8", accent6: "6B8299",
    hlink: "2E5C8A", folHlink: "7E5AA8",
  },
};
const P = THEME.colors;
const MUTED = "5B7085";
const RULE = "D4DEE6";
const GOOD = "1C7A4A";
const BAD = "B23A1F";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "SRP Group 9";
pres.title = "Extending PARCO";

const W = 13.333, H = 7.5, MX = 0.62, CW = W - 2 * MX;
const FOOT = "Extending PARCO  ·  SRP Group 9";

/* ----------------------------------------------------------------- layouts */
pres.defineSlideMaster({
  title: "TITLE", background: { color: P.dk1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: MX, y: 1.5, w: 8, h: .35, fontSize: 13, color: "A9BED0", align: "left" }, text: " " } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 1.9, w: 8.2, h: 1.3, fontSize: 46, bold: true, color: "FFFFFF", align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 3.2, w: 7.6, h: 1.0, fontSize: 16, color: "C9D7E3", align: "left" }, text: " " } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: P.dk1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: MX, y: 2.8, w: 8, h: .4, fontSize: 14, bold: true, color: P.accent2, align: "left" }, text: " " } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 3.25, w: 11, h: 1.1, fontSize: 38, bold: true, color: "FFFFFF", align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.4, w: 9.5, h: .9, fontSize: 15, color: "A9BED0", align: "left" }, text: " " } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: .42, w: 11.9, h: .72, fontSize: 30, bold: true, color: P.dk1, align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 1.16, w: 11.9, h: .4, fontSize: 13.5, italic: true, color: MUTED, align: "left" }, text: " " } },
    { text: { text: FOOT, options: { x: 7.4, y: 6.98, w: 4.7, h: .3, fontSize: 9.5, color: "9AAEBF", align: "right", isTextBox: true } } },
  ],
  slideNumber: { x: 12.4, y: 6.98, w: .45, h: .3, fontSize: 9.5, color: "9AAEBF", align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING", background: { color: P.dk1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: MX, y: 2.1, w: 8, h: .4, fontSize: 14, bold: true, color: P.accent2, align: "left" }, text: " " } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.6, w: 11.4, h: 2.1, fontSize: 32, bold: true, color: "FFFFFF", align: "left" }, text: " " } },
  ],
});

/* ----------------------------------------------------------------- helpers */
let n = 0;
const on = (s) => `${s}_${++n}`;
const NOSH = { type: "none" };

function card(s, x, y, w, h, o = {}) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: .06,
    fill: { color: o.fill || P.lt2 }, line: { color: o.line || o.fill || P.lt2, width: .75 },
    shadow: NOSH, objectName: on("card"),
  });
}
function badge(s, x, y, t, color, d = .4) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 }, shadow: NOSH, objectName: on("b") });
  s.addText(String(t), { x, y, w: d, h: d, fontSize: 13.5, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: on("bt") });
}
function head(s, t, x, y, w, color = P.dk1, size = 15) {
  s.addText(t, { x, y, w, h: .32, fontSize: size, bold: true, color, margin: 0, isTextBox: true, objectName: on("h") });
}
function para(s, t, x, y, w, h, size = 13, color = "3C4F60") {
  s.addText(t, { x, y, w, h, fontSize: size, color, lineSpacing: size * 1.32, margin: 0, isTextBox: true, valign: "top", objectName: on("p") });
}
function rich(s, runs, x, y, w, h, size = 13) {
  s.addText(runs, { x, y, w, h, fontSize: size, lineSpacing: size * 1.34, margin: 0, isTextBox: true, valign: "top", color: "3C4F60", objectName: on("r") });
}
function bullets(s, items, x, y, w, h, size = 13.5) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i !== items.length - 1 } })),
    { x, y, w, h, fontSize: size, color: "3C4F60", lineSpacing: size * 1.3, paraSpaceAfter: 7, margin: 0, isTextBox: true, valign: "top", objectName: on("ul") });
}
function img(s, file, x, y, w) {
  const sz = require("image-size");
  let dim;
  try { dim = sz.imageSize(require("fs").readFileSync(file)); }
  catch (e) { dim = { width: 16, height: 9 }; }
  s.addImage({ path: file, x, y, w, h: w * dim.height / dim.width });
  return w * dim.height / dim.width;
}
const TH = { fill: { color: P.dk1 }, color: "FFFFFF", bold: true };
function table(s, rows, x, y, w, colW, fs = 11.5, hl = []) {
  const opts = {
    x, y, w, colW, fontSize: fs, color: "25384A",
    border: { type: "solid", color: RULE, pt: .5 }, align: "center",
    valign: "middle", rowH: .3, margin: .05, autoPage: false, objectName: on("t"),
  };
  s.addTable(rows, opts);
}

/* ====================================================== 1 · INTRODUCTION */
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  s.addText("Student Research Project · Group 9 · Universität Hildesheim", { placeholder: "eyebrow" });
  s.addText("Extending PARCO", { placeholder: "title" });
  s.addText("Does parallel decoding cost solution quality?\nThree controlled experiments on min-max HCVRP", { placeholder: "body" });
  s.addText("Akshai Athota · Charitha Yetukuri · Nitin Sharma · Shehroz Khan · Mina George Soliman Hanna",
    { x: MX, y: 4.9, w: 7.8, h: .8, fontSize: 13, color: "DCE6EE", lineSpacing: 20, margin: 0, isTextBox: true });
  img(s, `${AS}/hcvrp_instance.jpg`, 9.2, 1.5, 3.5);
  s.addNotes("We extend PARCO, a NeurIPS 2025 parallel multi-agent solver. Everything is tested on min-max HCVRP under one identical training recipe.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("What is PARCO?", { placeholder: "title" });
  s.addText("A neural solver that lets every vehicle choose its next stop in the same decoder step", { placeholder: "body" });
  const items = [
    ["Communication layers", "Transformer layers let the agents exchange context while they decode, so one agent's choice can account for what the others are about to do.", P.accent4],
    ["Multiple pointer mechanism", "Every agent gets its own pointer attention over the nodes — one row of logits each, giving a [B, M, M+N] tensor.", P.accent3],
    ["Priority-based conflict handler", "If two agents select the same customer, the higher learned priority keeps it and the other stays put. A fixed rule, not a learned module.", P.accent1],
  ];
  let y = 1.75;
  items.forEach(([t, d, c], i) => { badge(s, MX, y, i + 1, c); head(s, t, MX + .58, y + .02, 5.6, P.dk1, 15); para(s, d, MX + .58, y + .38, 5.7, .95, 12.5); y += 1.52; });
  img(s, `${AS}/parco_concept.jpg`, 7.1, 1.7, 5.6);
  s.addText("Sequential (top) vs parallel (bottom) construction", { x: 7.1, y: 6.5, w: 5.6, h: .25, fontSize: 10.5, italic: true, color: MUTED, align: "center", margin: 0, isTextBox: true });
  s.addNotes("Three mechanisms. The third is the one our work puts under test: it is a hand-written rule, and the paper never measures what it costs.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("Architecture: encoder once, decoder in a loop", { placeholder: "title" });
  s.addText("The decoder and the environment alternate until every agent is finished", { placeholder: "body" });
  img(s, `${AS}/architecture.jpg`, 1.0, 1.7, 11.3);
  card(s, MX, 5.75, CW, 1.0);
  rich(s, [
    { text: "Why this matters:  ", options: { bold: true, color: P.dk1 } },
    { text: "the encoder reads only static features — coordinates, demands, capacities, speeds. It never sees where a vehicle currently is. So re-running it mid-episode is a provable no-op, and decoder-only sequential decoding loses nothing.", options: {} },
  ], MX + .25, 5.9, CW - .5, .75, 12.5);
  s.addNotes("Encoder once, decoder in a loop with the environment. The encoder being purely static is the fact that justifies decoder-only sequential decoding later.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("The objective: min-max HCVRP", { placeholder: "title" });
  s.addText("We minimise when the last vehicle finishes — not the total distance driven", { placeholder: "body" });
  card(s, MX, 1.75, 6.5, 1.5, { fill: "F2F6F9", line: "DCE5EB" });
  s.addText("minimise    max over vehicles m of    L_m / f_m", { x: MX + .3, y: 2.0, w: 5.9, h: .4, fontSize: 17, bold: true, fontFace: "Consolas", color: P.dk1, margin: 0, isTextBox: true });
  para(s, "L_m = distance driven by vehicle m      f_m = its speed,  so L_m / f_m is its finishing time", MX + .3, 2.55, 5.9, .5, 12, MUTED);
  head(s, "Why min-max changes the problem", MX, 3.5, 6.4, P.dk1, 15);
  bullets(s, [
    "It is a balancing problem: one idle van and one overloaded van scores badly even when the total distance is small.",
    "The objective is decided by a single vehicle — the one that finishes last. Everything else is slack.",
    "Not comparable with POMO or AM on CVRP, which minimise total distance for one vehicle.",
  ], MX, 3.9, 6.5, 1.8, 13);
  card(s, MX, 5.85, 6.5, .95, { fill: "FDF3E6", line: "F2DFC2" });
  rich(s, [
    { text: "Heterogeneous:  ", options: { bold: true, color: "8A5B06" } },
    { text: "each vehicle has its own capacity (20–41) and its own speed (0.5–1.0), so a fast small van and a slow large van are genuinely different resources.", options: {} },
  ], MX + .25, 6.0, 6.0, .7, 12);
  img(s, `${AS}/hcvrp_instance.jpg`, 7.9, 1.75, 4.1);
  s.addText("Trained policy on one instance: the fleet is balanced, not merely short", { x: 7.9, y: 6.5, w: 4.1, h: .4, fontSize: 10.5, italic: true, color: MUTED, align: "center", margin: 0, isTextBox: true });
  s.addNotes("Min-max, not min-sum. The last van home IS the number we report. That also makes the simulator compelling: you watch the objective happen.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("What happens in one decoder pass", { placeholder: "title" });
  s.addText("This is the unit everything in this talk is measured in", { placeholder: "body" });
  const steps = [
    ["Decoder forward", "Produces the logits tensor [B, M, M+N] — one row of preferences per agent. This is the expensive part.", P.accent4],
    ["All M agents pick", "Each agent takes its own argmax. Nothing stops two of them choosing the same customer.", P.accent3],
    ["Conflict handler", "Collisions are repaired by the priority rule: the winner moves, the loser stays where it is.", P.accent1],
    ["env.step", "The environment applies the surviving actions and updates capacities, positions and the mask.", P.accent5],
  ];
  let y = 1.75;
  steps.forEach(([t, d, c], i) => {
    card(s, MX, y, 6.3, 1.12);
    badge(s, MX + .25, y + .22, i + 1, c, .38);
    head(s, t, MX + .78, y + .2, 5.2, P.dk1, 14);
    para(s, d, MX + .78, y + .56, 5.2, .5, 12);
    y += 1.24;
  });
  card(s, 7.3, 1.75, 5.4, 2.5, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "Why the action space is M + N", 7.55, 1.95, 4.9, P.dk1, 15);
  para(s, "The depot is replicated once per agent. Indices 0…M−1 are M copies of the depot, one per vehicle; M…M+N−1 are the customers.\n\nWithout private depot copies, the first van home would mark the depot visited for everyone — and no agent could express “stay where you are”.",
    7.55, 2.32, 4.9, 1.8, 12.5);
  card(s, 7.3, 4.45, 5.4, 2.3, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "The two costs hiding in step 3", 7.55, 4.65, 4.9, P.accent1, 15);
  bullets(s, [
    "Agents 2…M chose from logits computed before any agent acted — stale information.",
    "The overruled agent wastes its slot in this pass, and its gradient still credits a move that never ran.",
  ], 7.55, 5.02, 4.9, 1.6, 12.5);
  s.addNotes("Define the decoder pass here — it is the compute unit for the whole talk. And flag the two costs we will later measure.");
}

/* ======================================================== 2 · QUESTIONS */
pres.addSection({ title: "Questions" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Questions" });
  s.addText("The questions", { placeholder: "eyebrow" });
  s.addText("Three things the paper never measures", { placeholder: "title" });
  s.addText("PARCO optimises for speed and reports speed. What that speed costs is left open.", { placeholder: "body" });
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Questions" });
  s.addText("What we set out to answer", { placeholder: "title" });
  s.addText("Each question becomes one controlled experiment", { placeholder: "body" });
  const qs = [
    ["Q1", "What does parallelism cost in solution quality?", P.accent1,
      "The paper shows parallel decoding is far faster than sequential, but never measures the quality it gives up. Without the sequential end of the scale there is no reference point at all."],
    ["Q2", "Is the inherited logit clipping doing what we think?", P.accent2,
      "PARCO clips with C·tanh(z) at C = 10. That function has slope 10 at the origin — it amplifies small differences rather than clipping them. It was never ablated."],
    ["Q3", "Is any quality gain simply bought with extra compute?", P.accent3,
      "Sequential decoding takes more decoder passes. If it wins, we have to show the win survives when every method is given the same inference budget."],
  ];
  let y = 1.72;
  qs.forEach(([tag, t, c, d]) => {
    card(s, MX, y, CW, 1.56);
    badge(s, MX + .28, y + .3, tag, c, .46);
    head(s, t, MX + .92, y + .28, 10.5, P.dk1, 16);
    para(s, d, MX + .92, y + .68, 10.8, .8, 13);
    y += 1.72;
  });
  s.addNotes("Three questions, three experiments. Each is measured against a PARCO we trained ourselves under the identical recipe.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Questions" });
  s.addText("Four experiments", { placeholder: "title" });
  s.addText("All six finished runs share one recipe: 6 GPUs, effective batch 768, lr 1e-4, 100 epochs", { placeholder: "body" });
  table(s, [
    [{ text: "", options: TH }, { text: "Experiment", options: TH }, { text: "What we change", options: TH }, { text: "What it answers", options: TH }],
    ["1", { text: "The k parameter", options: { bold: true } }, "Pairs committed per decoder pass, k = 1 … M", "Q1 — the cost of parallelism"],
    ["2", { text: "Tanh logit clipping", options: { bold: true } }, "φ(z) = g·tanh(z/τ): separate gain from saturation", "Q2 — is the clip helping?"],
    ["3", { text: "Equal inference budget", options: { bold: true } }, "Give every model the same decoder passes", "Q3 — is the win bought?"],
    ["4", { text: "Homogeneous-fleet CVRP", options: { bold: true } }, "New environment and generator, zero model changes", "Does any of this need heterogeneity?"],
  ], MX, 1.8, 12.1, [0.6, 2.6, 4.6, 4.3], 13);
  card(s, MX, 3.9, 5.9, 1.6, { fill: "E8F3F0", line: "CFE4DE" });
  head(s, "One control for everything", MX + .28, 4.1, 5.3, P.accent3, 15);
  para(s, "Stock PARCO, trained as arm (a) of the tanh sweep on the same six GPUs. It is both the control for experiment 2 and the baseline for experiment 1. Mean cost 6.1264.",
    MX + .28, 4.48, 5.3, 1.1, 12.5);
  card(s, 6.85, 3.9, 5.85, 1.6, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "Pipeline validated first", 7.1, 4.1, 5.3, P.dk1, 15);
  para(s, "The paper prints 10.98 at N = 100, M = 3. Running the authors' released checkpoint through our own evaluation code gives 10.977 — same weights, three decimals.",
    7.1, 4.48, 5.3, 1.1, 12.5);
  card(s, MX, 5.7, CW, 1.1, { fill: "FDF3E6", line: "F2DFC2" });
  rich(s, [
    { text: "Two further ideas are not in this talk.  ", options: { bold: true, color: "8A5B06" } },
    { text: "An explicit wait action and a dynamic re-encoding variant both exceeded the 72-hour job limit before producing a single evaluation — budget findings, not results, so they appear only in the limitations.", options: {} },
  ], MX + .28, 5.84, CW - .56, .85, 12.5);
  s.addNotes("Flag early and honestly that two ideas did not finish, so nobody wonders where they went. They return once, in the limitations slide.");
}

/* ================================================= 3 · EXPERIMENT 1 — k */
pres.addSection({ title: "Experiment 1" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Experiment 1" });
  s.addText("Experiment 1", { placeholder: "eyebrow" });
  s.addText("One knob from sequential to joint", { placeholder: "title" });
  s.addText("k = how many (agent, node) pairs are committed per decoder pass", { placeholder: "body" });
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Method · the k parameter", { placeholder: "title" });
  s.addText("Our supervisor observed that in the fully sequential limit two of our ideas are the same thing — so they became one parameter", { placeholder: "body" });
  const h = img(s, `${FV}/v2_spectrum.png`, 1.1, 1.65, 11.1);
  card(s, MX, 1.65 + h + .25, 6.1, 2.25, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "What one pass does", MX + .28, 1.9 + h + .25, 5.5, P.dk1, 15);
  bullets(s, [
    "Flatten the logits into ONE joint softmax over all (agent, node) pairs",
    "Take the best pair; mask that agent's row and that node's column",
    "Repeat k times, then call env.step once",
  ], MX + .28, 2.25 + h + .25, 5.5, 1.6, 12.5);
  card(s, 6.95, 1.65 + h + .25, 5.75, 2.25, { fill: "E8F3F0", line: "CFE4DE" });
  head(s, "Two properties that follow", 7.2, 1.9 + h + .25, 5.2, P.accent3, 15);
  bullets(s, [
    "Collisions are impossible at any k — the priority handler never runs, halting ratio is 0 by construction",
    "One pass is one decoder forward: the k picks reuse the same logits tensor",
  ], 7.2, 2.25 + h + .25, 5.2, 1.6, 12.5);
  s.addNotes("k=1 is full sequential, k=M is masked joint. The second property is what makes the compute comparison in the next slides fair.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("One decoder step: PARCO vs ours", { placeholder: "title" });
  s.addText("Same logits, different way of turning them into actions", { placeholder: "body" });
  img(s, `${FV}/v2_decoding.png`, 2.0, 1.62, 9.3);
  s.addNotes("Walk through this slowly. Top: collision and overrule. Bottom: mask the row and column so a collision cannot arise.");
}

/* -------- the computation slides the brief asked for -------------------- */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Computation · what changes as k grows", { placeholder: "title" });
  s.addText("Per pass the decoder runs once regardless of k — only the number of passes changes", { placeholder: "body" });
  card(s, MX, 1.7, 6.0, 2.5, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "The work inside one pass", MX + .28, 1.9, 5.4, P.dk1, 15);
  s.addText([
    { text: "1 × decoder forward", options: { bold: true, breakLine: true } },
    { text: "    → logits [B, M, M+N]     EXPENSIVE", options: { color: MUTED, breakLine: true } },
    { text: "k × (mask + log_softmax + argmax)", options: { bold: true, breakLine: true } },
    { text: "    → reuses the same tensor   CHEAP", options: { color: MUTED, breakLine: true } },
    { text: "1 × env.step", options: { bold: true } },
  ], { x: MX + .28, y: 2.3, w: 5.4, h: 1.5, fontSize: 12.5, fontFace: "Consolas", color: "3C4F60", lineSpacing: 18, margin: 0, isTextBox: true });
  para(s, "So a pass costs essentially the same at every k. That is why decoder passes are the right unit of compute.", MX + .28, 3.72, 5.4, .45, 12, MUTED);

  table(s, [
    [{ text: "k", options: TH }, { text: "Passes", options: TH }, { text: "Ideal 85.5/k", options: TH }, { text: "Speedup", options: TH }, { text: "Min/epoch", options: TH }],
    ["1", "85.5", "85.5", "1.00×", "11:51"],
    [{ text: "2", options: { bold: true } }, { text: "43.2", options: { bold: true } }, "42.7", { text: "1.98×", options: { bold: true, color: GOOD } }, "08:28"],
    ["4", "24.6", "21.4", "3.48×", "05:51"],
    ["7", "20.0", "12.2", "4.27×", "05:40"],
  ], 7.0, 1.8, 5.7, [0.8, 1.2, 1.5, 1.2, 1.2], 12);
  card(s, 7.0, 3.6, 5.7, 1.25, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "Read the third column.  ", options: { bold: true, color: P.accent3 } },
    { text: "k = 2 lands almost exactly on the ideal 1/k curve. By k = 7 the measured count is 20.0 where the ideal says 12.2 — the speedup is running out.", options: {} },
  ], 7.25, 3.78, 5.2, 1.2, 12.5);
  img(s, `${FD}/d_passes.png`, MX, 4.32, 5.6);
  s.addNotes("Key slide. One decoder forward per pass regardless of k is what makes passes a fair unit. Then: the speedup is sublinear.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Computation · why the speedup saturates", { placeholder: "title" });
  s.addText("Doubling k does not halve the work once k gets large", { placeholder: "body" });
  img(s, `${FD}/d_efficiency.png`, MX, 1.7, 6.1);
  card(s, 7.1, 1.7, 5.6, 2.6, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "Three reasons a slot goes unused", 7.35, 1.9, 5.1, P.accent1, 15);
  bullets(s, [
    "An episode can never be shorter than the busiest vehicle's own route: passes ≥ max_m T_m",
    "Agents that have already finished sit at the depot and cannot fill a slot",
    "An agent whose remaining capacity blocks every unvisited customer must return to the depot first",
  ], 7.35, 2.28, 5.1, 1.95, 12.5);
  card(s, 7.1, 4.45, 5.6, 1.35, { fill: "F2F6F9", line: "DCE5EB" });
  rich(s, [
    { text: "Wall-clock lags further still.  ", options: { bold: true, color: P.dk1 } },
    { text: "k = 2 gives a 1.98× pass speedup but only 1.40× per epoch: the k picks are a sequential loop, and per-step overhead is fixed.", options: {} },
  ], 7.35, 4.62, 5.1, 1.05, 12.5);
  card(s, MX, 5.95, 6.1, .85, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "This is why k = 2 is the sweet spot:  ", options: { bold: true, color: P.accent3 } },
    { text: "you capture 99% of the available speedup before quality starts to pay for it.", options: {} },
  ], MX + .25, 6.1, 5.6, .65, 12.5);
  s.addNotes("99% at k=2, 87% at k=4, 61% at k=7. The returns diminish sharply, and that is half the argument for k=2.");
}

/* -------- results and discussion --------------------------------------- */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Results · a clean quality–speed front", { placeholder: "title" });
  s.addText("Each model trained AND evaluated at its own k; gap is against our own PARCO control", { placeholder: "body" });
  img(s, `${FR}/pareto.png`, 6.6, 1.65, 6.2);
  table(s, [
    [{ text: "Method", options: TH }, { text: "Cost", options: TH }, { text: "Gap", options: TH }, { text: "Wins", options: TH }, { text: "Passes", options: TH }],
    ["Parallel PARCO", "6.1264", "—", "—", "65.6"],
    [{ text: "k = 1", options: { bold: true } }, { text: "5.8880", options: { bold: true } }, { text: "−4.55%", options: { bold: true, color: GOOD } }, { text: "12/12", options: { bold: true } }, "85.5"],
    [{ text: "k = 2", options: { bold: true } }, { text: "5.9762", options: { bold: true } }, { text: "−3.02%", options: { bold: true, color: GOOD } }, { text: "12/12", options: { bold: true } }, { text: "43.2", options: { bold: true } }],
    ["k = 4", "6.2193", { text: "+0.91%", options: { color: BAD } }, "4/12", "24.6"],
    ["k = 7", "6.3966", { text: "+4.77%", options: { color: BAD } }, "0/12", "20.0"],
  ], MX, 1.8, 5.8, [1.8, 1.0, 1.1, 1.0, .9], 12);
  card(s, MX, 4.0, 5.8, 1.35, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "k = 2 dominates.  ", options: { bold: true, color: P.accent3 } },
    { text: "Better on all 12 sets, 34% fewer passes than PARCO, 16% less training time. Not a trade-off — better on every axis at once.", options: {} },
  ], MX + .25, 4.16, 5.3, 1.1, 12.5);
  card(s, MX, 5.5, 5.8, 1.3, { fill: "F2F6F9", line: "DCE5EB" });
  rich(s, [
    { text: "Sanity check:  ", options: { bold: true, color: P.dk1 } },
    { text: "k = 1 reproduces our earlier sequential branch exactly (11.4836 / 6.9243 / 5.0461 at N = 100), confirming the merged implementation is faithful.", options: {} },
  ], MX + .25, 5.66, 5.3, 1.05, 12.5);
  s.addNotes("Monotone front. Crossover between k=2 and k=4. Parallel PARCO sits above and right of k=2 — dominated.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Discussion · why k = 1 and k = 2 win", { placeholder: "title" });
  s.addText("Three distinct mechanisms, all of them removed by committing fewer agents per pass", { placeholder: "body" });
  const why = [
    ["No stale logits", P.accent1,
      "In PARCO all M agents read one logits tensor computed before any of them moved. At k = 1 every decision is conditioned on all previous ones; at k = 2 only one other agent's pick is unseen."],
    ["No wasted slot", P.accent3,
      "The priority rule does not merely pick a winner — the loser stays put. That agent contributes nothing in that pass, so the plan is distorted and a step is spent for less progress."],
    ["Lower gradient variance", P.accent4,
      "With collisions impossible the proposal-to-execution map becomes the identity. The many-to-one noise disappears: 0% of gradient variance avoidable at M = 2, 11.0% at M = 3, 24.5% at M = 4."],
  ];
  let y = 1.72;
  why.forEach(([t, c, d], i) => {
    card(s, MX, y, CW, 1.52);
    badge(s, MX + .28, y + .28, i + 1, c, .44);
    head(s, t, MX + .9, y + .26, 10.4, P.dk1, 16);
    para(s, d, MX + .9, y + .64, 10.7, .8, 13);
    y += 1.68;
  });
  card(s, MX, 6.08, CW, .72, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "The prediction this makes:  ", options: { bold: true, color: P.accent3 } },
    { text: "all three effects grow with how many agents share a pass — so the advantage should grow with fleet size M. It does.", options: {} },
  ], MX + .25, 6.2, CW - .5, .55, 12.5);
  s.addNotes("Three mechanisms, and they make a testable prediction about M — which the next slide checks.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Discussion · why k = 4 and k = 7 lose", { placeholder: "title" });
  s.addText("Masking removes the collision — it does not remove the staleness", { placeholder: "body" });
  card(s, MX, 1.72, 6.1, 2.5, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "The distinction that explains the front", MX + .28, 1.92, 5.5, P.accent1, 15);
  para(s, "Inside one pass the k picks share a single logits tensor. Pick 2 sees pick 1's mask, but it does NOT see a recomputed state: no new encoder, no new decoder, no updated capacity or position.\n\nSo masking guarantees a feasible assignment, while the information each agent acts on still predates the other picks in that pass.",
    MX + .28, 2.3, 5.5, 1.85, 12.5);
  card(s, MX, 4.4, 6.1, 1.0, { fill: "F2F6F9", line: "DCE5EB" });
  rich(s, [
    { text: "As k → M we recover PARCO's own problem,  ", options: { bold: true, color: P.dk1 } },
    { text: "minus the collisions. That is exactly where the curve crosses zero.", options: {} },
  ], MX + .25, 4.55, 5.6, .8, 12.5);
  img(s, `${FD}/d_tradeoff.png`, 6.95, 1.72, 5.75);
  card(s, 6.95, 5.0, 5.75, 1.75, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "Two further costs at large k", 7.2, 5.18, 5.2, P.dk1, 14.5);
  bullets(s, [
    "k = 7 is even worse than our old joint branch (12.111 vs 11.717 at n100 m3): the self-loop guard removes a degree of freedom at k = M",
    "Pick-order variance grows with k, bounded by k! — 0% / 13.3% / 46.6% avoidable at k = 1 / 2 / 3",
  ], 7.2, 5.5, 5.2, 1.2, 11.5);
  s.addNotes("This is the sharpest point in the talk: masking fixes collisions, not staleness. That is why the front crosses zero around k=4.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 1" });
  s.addText("Discussion · the advantage scales with fleet size", { placeholder: "title" });
  s.addText("The mechanism confirming itself: the gain is largest where parallelism is supposed to pay off most", { placeholder: "body" });
  img(s, `${FR}/m_scaling.png`, MX, 1.7, 6.6);
  card(s, 7.5, 1.7, 5.2, 2.4, { fill: "E8F3F0", line: "CFE4DE" });
  head(s, "Why the slope is the right sign", 7.75, 1.9, 4.7, P.accent3, 15);
  para(s, "More agents per pass means more decisions taken on stale logits, and more collisions for the priority rule to repair. Sequencing recovers exactly that loss.\n\nSo the advantage grows from −3.0% at M = 3 to −6.2% at M = 7 for k = 1.",
    7.75, 2.28, 4.7, 1.75, 12.5);
  card(s, 7.5, 4.3, 5.2, 2.45, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "What this would predict next", 7.75, 4.5, 4.7, P.dk1, 15);
  para(s, "A fleet larger than M = 7 should widen the gap further, and a fleet of M = 2 should nearly close it. Neither is tested here — the training distribution stops at M = 7 — so this is a prediction, not a result.",
    7.75, 4.88, 4.7, 1.7, 12.5);
  s.addNotes("Good place to invite a question. Note honestly that the M>7 extrapolation is untested.");
}

/* ============================================= 4 · EXPERIMENT 2 — tanh */
pres.addSection({ title: "Experiment 2" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Experiment 2" });
  s.addText("Experiment 2", { placeholder: "eyebrow" });
  s.addText("Separating gain from saturation", { placeholder: "title" });
  s.addText("Is PARCO's inherited logit clip doing what a clip is supposed to do?", { placeholder: "body" });
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 2" });
  s.addText("Method · what C was doing twice", { placeholder: "title" });
  s.addText("Write the clip as φ(z) = g·tanh(z/τ): the gain at the origin is g/τ, the knee sits near 2τ", { placeholder: "body" });
  img(s, `${FR}/tanh_curves.png`, MX, 1.7, 6.5);
  table(s, [
    [{ text: "Form", options: TH }, { text: "g", options: TH }, { text: "τ", options: TH }, { text: "Gain", options: TH }, { text: "Effect", options: TH }],
    ["PARCO (fixed)", "10", "1", { text: "10", options: { bold: true } }, "amplifies, then saturates"],
    ["Scaled", "10", "10", { text: "1", options: { bold: true } }, "near-identity, bounds tails"],
  ], 7.4, 1.8, 5.3, [1.6, .55, .55, .7, 1.9], 11.5);
  card(s, 7.4, 3.1, 5.3, 1.9, { fill: "FDF3E6", line: "F2DFC2" });
  head(s, "What this implies", 7.65, 3.28, 4.8, "8A5B06", 15);
  para(s, "A softmax over φ(z) with slope s at the origin behaves like a softmax over z at temperature 1/s. PARCO's fixed form is therefore an effective 10× temperature drop: it sharpens the policy and suppresses exploration early in training.",
    7.65, 3.65, 4.8, 1.3, 12.5);
  card(s, 7.4, 5.2, 5.3, 1.55, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "Correction to our earlier talk", 7.65, 5.38, 4.8, P.accent1, 14.5);
  para(s, "We previously said the scaled form makes the policy sharper. It is the other way round — and the direction matters, because swapping them is a factor of ten in temperature.",
    7.65, 5.72, 4.8, .95, 12);
  s.addNotes("The point is that one constant C was controlling two separate things. Separating them is the contribution here.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 2" });
  s.addText("Results and discussion · the conclusion reverses", { placeholder: "title" });
  s.addText("With a matched control and the encoder-attention half switched off, the textbook form wins", { placeholder: "body" });
  table(s, [
    [{ text: "Arm", options: TH }, { text: "Clip", options: TH }, { text: "lr", options: TH }, { text: "Cost", options: TH }, { text: "vs control", options: TH }, { text: "Wins", options: TH }],
    [{ text: "(a) control", options: { bold: true } }, "10·tanh(z)", "1e-4", "6.1264", "—", "—"],
    [{ text: "(b) scaled", options: { bold: true } }, "10·tanh(z/10)", "1e-4", { text: "6.0801", options: { bold: true } }, { text: "−0.93%", options: { bold: true, color: GOOD } }, { text: "12/12", options: { bold: true } }],
    [{ text: "(d) scaled", options: { bold: true } }, "10·tanh(z/10)", "1e-3", { text: "69.34", options: { color: BAD } }, { text: "diverged", options: { bold: true, color: BAD } }, "0/12"],
  ], MX, 1.8, 7.2, [1.4, 1.7, .8, 1.1, 1.3, .9], 12);
  card(s, MX, 3.3, 7.2, 1.5, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "Why our earlier +3.5% was wrong", MX + .28, 3.48, 6.6, P.accent1, 15);
  para(s, "That run clipped the encoder attention logits as well as the decoder's, and trained on 8 GPUs against a baseline trained on 6. Isolating the decoder clip and matching the hardware removes both confounds — and the sign flips.",
    MX + .28, 3.86, 6.6, .9, 12.5);
  card(s, MX, 4.95, 7.2, 1.85, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "Why the effect is small, and why 10× lr diverges", MX + .28, 5.13, 6.6, P.dk1, 15);
  bullets(s, [
    "The clip only touches decoder logits, and a trained policy is already confident, so most logits sit in the saturating tail either way.",
    "A flatter softmax explores more, which raises return variance; combining that with a 10× step size destabilises REINFORCE — best checkpoint at epoch 22, then collapse.",
  ], MX + .28, 5.48, 6.6, 1.25, 11.5);
  card(s, 8.05, 1.8, 4.65, 2.3, { fill: "E8F3F0", line: "CFE4DE" });
  s.addText("−0.93%", { x: 8.3, y: 2.0, w: 4.0, h: .7, fontSize: 36, bold: true, color: P.accent3, margin: 0, isTextBox: true });
  para(s, "and better on all 12 test sets, at identical cost per epoch (09:59 vs 10:03). Small, perfectly consistent, and free.", 8.3, 2.75, 4.1, 1.1, 12.5);
  card(s, 8.05, 4.25, 4.65, 2.55, { fill: "FDF3E6", line: "F2DFC2" });
  head(s, "What this experiment still owes", 8.3, 4.43, 4.1, "8A5B06", 14.5);
  para(s, "Arm (f): φ(z) = 30·tanh(z/3). It holds the gain at 10 while moving the knee, so it is the only arm that separates the gain effect from the saturation effect. Not yet run.\n\nAnd with one seed, −0.93% needs error bars before it is settled.",
    8.3, 4.78, 4.1, 1.9, 12);
  s.addNotes("Be explicit that this reverses our own earlier claim and say why. Then explain why the effect is small and why the big lr fails.");
}

/* =========================================== 5 · EXPERIMENT 3 — budget */
pres.addSection({ title: "Experiment 3" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Experiment 3" });
  s.addText("Experiment 3", { placeholder: "eyebrow" });
  s.addText("Is the win simply bought with compute?", { placeholder: "title" });
  s.addText("A greedy k = 1 rollout spends 1.34× the decoder passes of parallel PARCO", { placeholder: "body" });
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 3" });
  s.addText("Method · a budget-fair comparison", { placeholder: "title" });
  s.addText("Give every model the same decoder passes and let it spend them however it likes", { placeholder: "body" });
  const steps = [
    ["Count compute in decoder passes", "A k-parallel pass commits all k pairs from one logits tensor, so a pass costs the same at any k.", P.accent4],
    ["passes = steps × samples", "For best-of-n sampling all rollouts of an instance advance in lockstep. Both factors are measured, never assumed.", P.accent3],
    ["Sweep, don't force one point", "Each model runs at n = 1 (greedy), 2, 3, 4, 6, 8, 12, 16, 24, 32; cost is read off against the budget actually consumed.", P.accent1],
    ["Hold the batch width constant", "The loop runs while not done.all(), so the step count is a per-batch maximum and grows with batch size.", P.accent2],
  ];
  let y = 1.72;
  steps.forEach(([t, d, c], i) => {
    const x = MX + (i % 2) * 6.15, yy = y + Math.floor(i / 2) * 1.62;
    card(s, x, yy, 5.85, 1.45);
    badge(s, x + .26, yy + .24, i + 1, c, .38);
    head(s, t, x + .78, yy + .22, 4.8, P.dk1, 14);
    para(s, d, x + .28, yy + .6, 5.3, .75, 12);
  });
  card(s, MX, 5.1, CW, 1.65, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "Two harness bugs this exposed first", MX + .28, 5.28, 11.5, P.accent1, 15);
  bullets(s, [
    "Best-of-n was wrong for batch > 1: rl4co's batchify repeats sample-major, so a naive reshape grouped different instances rather than different samples. The codebase hid this behind an assert pinning sampling to batch_size = 1.",
    "Step counts are batch-width dependent, so measuring methods at different widths would have biased the budget axis itself.",
  ], MX + .28, 5.62, 11.5, 1.1, 11.5);
  s.addNotes("Both bugs would have produced confidently wrong numbers. Worth saying — it shows the result was checked, not assumed.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 3" });
  s.addText("Results and discussion · the win is not bought", { placeholder: "title" });
  s.addText("Budget 1.0× = the passes parallel PARCO spends on one greedy rollout of that dataset", { placeholder: "body" });
  table(s, [
    [{ text: "Budget", options: TH }, { text: "Parallel", options: TH }, { text: "k = 1", options: TH }, { text: "k = 2", options: TH }, { text: "k = 4", options: TH }, { text: "k = 7", options: TH }],
    ["1.3×", "6.0513", { text: "5.8007", options: { bold: true, color: GOOD } }, "5.9187", "6.1847", "6.2562"],
    ["2×", "6.1258", { text: "5.8880", options: { bold: true, color: GOOD } }, "5.9769", "6.2187", "6.3963"],
    ["8×", "6.1258", { text: "5.8880", options: { bold: true, color: GOOD } }, "5.9769", "6.2187", "6.3963"],
    ["32×", "6.1258", { text: "5.8880", options: { bold: true, color: GOOD } }, "5.9769", "6.2187", "6.3963"],
  ], MX, 1.8, 7.0, [1.0, 1.3, 1.2, 1.2, 1.15, 1.15], 12);
  para(s, "k = 1 wins 12 / 12 sets at every level from 2× upward. Giving parallel PARCO 32× the budget does not close a 4.5% gap.", MX, 3.4, 7.0, .5, 12.5, MUTED);
  img(s, `${FR}/best_of_n.png`, MX, 3.95, 7.0);
  card(s, 7.9, 1.8, 4.8, 2.4, { fill: "FDF3E6", line: "F2DFC2" });
  head(s, "Why the rows are flat", 8.15, 1.98, 4.3, "8A5B06", 15);
  para(s, "Sampling at temperature 1 is a weak way to spend budget for EVERY model here: best-of-32 only just climbs back to the greedy cost (+1.08% for PARCO, +0.09% for k = 1).\n\nOver ~90 steps with ~100 options each, one bad pick cascades.",
    8.15, 2.35, 4.3, 1.8, 12.5);
  card(s, 7.9, 4.35, 4.8, 1.3, { fill: "FDECE4", line: "F6D6C6" });
  rich(s, [
    { text: "So the honest claim is narrower:  ", options: { bold: true, color: P.accent1 } },
    { text: "extra compute spent THIS WAY does not close the gap. A temperature-tuned or augmentation-based search might.", options: {} },
  ], 8.15, 4.52, 4.3, 1.05, 12.5);
  card(s, 7.9, 5.8, 4.8, .95, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "Encouraging sign:  ", options: { bold: true, color: P.accent3 } },
    { text: "the ordering k1 < k2 < parallel < k4 < k7 holds at every sample count, not only at greedy.", options: {} },
  ], 8.15, 5.95, 4.3, .75, 12);
  s.addNotes("Volunteer the caveat before anyone asks. The flat rows need explaining, and the explanation is that sampling is weak for all models.");
}

/* ============================================= 5b · EXPERIMENT 4 — CVRP */
pres.addSection({ title: "Experiment 4" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Experiment 4" });
  s.addText("Experiment 4", { placeholder: "eyebrow" });
  s.addText("Does any of this need heterogeneity?", { placeholder: "title" });
  s.addText("Transfer the architecture to a homogeneous fleet — same capacity, same speed for every vehicle", { placeholder: "body" });
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Experiment 4" });
  s.addText("Experiment 4 · homogeneous-fleet CVRP", { placeholder: "title" });
  s.addText("A new environment and generator only — the model is untouched", { placeholder: "body" });

  card(s, MX, 1.72, 5.9, 1.95, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "What changed, and what did not", MX + .28, 1.9, 5.3, P.dk1, 15);
  bullets(s, [
    "Every vehicle shares capacity 50 and unit speed — the fleet is uniform",
    "Zero model changes: same encoder, decoder and conflict handler",
    "Still min-max, so the objective is the longest route LENGTH",
  ], MX + .28, 2.28, 5.3, 1.3, 12.5);

  table(s, [
    [{ text: "Test set", options: TH }, { text: "M = 3", options: TH }, { text: "M = 5", options: TH }, { text: "M = 7", options: TH }],
    ["N = 50", "3.779", "2.463", "2.190"],
    ["N = 100", "6.163", "3.829", "2.999"],
    [{ text: "N = 200 †", options: { bold: true } }, { text: "28.487", options: { bold: true, color: BAD } }, "6.977", "4.898"],
  ], MX, 3.85, 5.9, [1.8, 1.4, 1.35, 1.35], 12.5);
  para(s, "† zero-shot at twice the largest training size. Trained on N ∈ [50, 100].", MX, 5.3, 5.9, .4, 11.5, MUTED);

  card(s, MX, 5.75, 5.9, 1.05, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "The architecture transfers.  ", options: { bold: true, color: P.accent3 } },
    { text: "Parallel decoding is not something that only works when vehicles differ from one another.", options: {} },
  ], MX + .25, 5.9, 5.4, .8, 12.5);

  card(s, 6.95, 1.72, 5.75, 3.62, { fill: "FDECE4", line: "F6D6C6" });
  head(s, "Why M = 3 collapses at N = 200", 7.2, 1.9, 5.2, P.accent1, 15);
  para(s, "28.487 where roughly 11–12 is expected. The tempting reading is “N = 200 is too big”, but M = 5 and M = 7 are fine at the same N.", 7.2, 2.28, 5.2, .8, 12.5);
  rich(s, [
    { text: "The axis that matters is customers per vehicle, not N.  ", options: { bold: true, color: P.dk1 } },
    { text: "Training spans 7 (N=50, M=7) to 33 (N=100, M=3). At N = 200:", options: {} },
  ], 7.2, 3.08, 5.2, .75, 12.5);
  table(s, [
    [{ text: "Fleet", options: TH }, { text: "Cust./vehicle", options: TH }, { text: "vs training", options: TH }, { text: "Result", options: TH }],
    ["M = 7", "28.6", "in range", "4.898  fine"],
    ["M = 5", "40.0", "1.2× over", "6.977  elevated"],
    [{ text: "M = 3", options: { bold: true } }, { text: "66.7", options: { bold: true } }, { text: "2.0× over", options: { bold: true, color: BAD } }, { text: "28.487  collapse", options: { bold: true, color: BAD } }],
  ], 7.2, 3.9, 5.2, [1.0, 1.5, 1.3, 1.4], 11.5);

  card(s, 6.95, 5.5, 5.75, 1.3, { fill: "F2F6F9", line: "DCE5EB" });
  head(s, "Not comparable with POMO or AM", 7.2, 5.66, 5.2, P.dk1, 14.5);
  para(s, "Those minimise the total distance of a single vehicle. We minimise the longest of M routes, so the numbers answer a different question and cannot be placed in the same table.", 7.2, 6.0, 5.2, .9, 12);
  s.addNotes("CVRP finished and has results, unlike the wait action. The customers-per-vehicle framing is the real explanation for the zero-shot failure — M=7 at N=200 is still in distribution, which is why it holds up.");
}

/* ========================================================= 6 · CLOSING */
pres.addSection({ title: "Conclusions" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Conclusions" });
  s.addText("Conclusions", { placeholder: "eyebrow" });
  s.addText("What we measured, and what we still owe", { placeholder: "title" });
  s.addText("Mean over 12 HCVRP test sets; gap against our own PARCO control, negative = better", { placeholder: "body" });
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusions" });
  s.addText("Final comparison", { placeholder: "title" });
  s.addText("One recipe, one control, six GPUs — every number directly comparable", { placeholder: "body" });
  table(s, [
    [{ text: "Method", options: TH }, { text: "Mean cost", options: TH }, { text: "Gap", options: TH }, { text: "Wins / 12", options: TH }, { text: "Passes", options: TH }, { text: "Min/epoch", options: TH }, { text: "Verdict", options: TH }],
    ["Parallel PARCO (control)", "6.1264", "0.0%", "—", "65.6", "10:03", "reference"],
    [{ text: "k = 1  ·  full sequential", options: { bold: true, color: P.accent1 } }, { text: "5.8880", options: { bold: true } }, { text: "−4.55%", options: { bold: true, color: GOOD } }, { text: "12 / 12", options: { bold: true } }, "85.5", "11:51", { text: "best quality", options: { bold: true } }],
    [{ text: "k = 2", options: { bold: true, color: P.accent1 } }, { text: "5.9762", options: { bold: true } }, { text: "−3.02%", options: { bold: true, color: GOOD } }, { text: "12 / 12", options: { bold: true } }, { text: "43.2", options: { bold: true } }, { text: "08:28", options: { bold: true } }, { text: "dominates", options: { bold: true, color: GOOD } }],
    [{ text: "Tanh scaled  10·tanh(z/10)", options: { color: P.accent2 } }, "6.0801", { text: "−0.93%", options: { color: GOOD } }, "12 / 12", "62.8", "09:59", "small, free win"],
    ["k = 4", "6.2193", { text: "+0.91%", options: { color: BAD } }, "4 / 12", "24.6", "05:51", "speed point"],
    [{ text: "k = 7  ·  masked joint", options: { color: P.accent3 } }, "6.3966", { text: "+4.77%", options: { color: BAD } }, "0 / 12", "20.0", "05:40", "fastest"],
    [{ text: "Tanh scaled, lr 1e-3", options: { color: MUTED } }, "69.34", { text: "diverged", options: { color: BAD } }, "0 / 12", "—", "04:43", "collapsed at ep. 22"],
  ], MX, 1.8, 12.1, [2.9, 1.3, 1.1, 1.15, .95, 1.2, 1.9], 11);
  card(s, MX, 5.3, CW, 1.1, { fill: "E8F3F0", line: "CFE4DE" });
  rich(s, [
    { text: "The conflict handler is not free.  ", options: { bold: true, color: P.accent3 } },
    { text: "Replacing it with explicit masking and committing two agents per pass beats PARCO on every test set while using 34% fewer decoder passes and 16% less training time. Experiment 4 is absent from this table on purpose: homogeneous CVRP is a different problem, so its costs are not comparable with these.", options: {} },
  ], MX + .3, 5.46, CW - .6, .85, 13);
  s.addNotes("One table, everything in it. Tanh passes come from the budget run's narrower batch, so they read slightly lower.");
}
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusions" });
  s.addText("Limitations and next steps", { placeholder: "title" });
  s.addText("What the present evidence does not yet support, and what would settle it", { placeholder: "body" });
  card(s, MX, 1.72, 6.0, 4.1);
  badge(s, MX + .3, 1.94, "!", P.accent1, .4);
  head(s, "Limitations", MX + .86, 1.96, 4.6, P.dk1, 17);
  bullets(s, [
    "One seed per configuration. The k results (−4.55%, 12/12) are safely outside seed noise; the −0.93% tanh effect is not, and needs 2–3 seeds.",
    "Budget was spent only through i.i.d. sampling at temperature 1, which is weak for every model tested.",
    "Training and decoding effects are not separated — every model was evaluated at the k it was trained with.",
    "k = 3, 5, 6 are untrained, so the front has holes; arm (f) of the tanh sweep has not run.",
    "Two ideas never produced a result: an explicit wait action and a dynamic re-encoding variant, both stopped by the 72-hour job limit.",
  ], MX + .3, 2.42, 5.4, 3.2, 12);
  card(s, 7.1, 1.72, 5.6, 4.1, { fill: "E8F3F0", line: "CFE4DE" });
  badge(s, 7.4, 1.94, "→", P.accent3, .4);
  head(s, "Next steps", 7.96, 1.96, 4.4, P.dk1, 17);
  bullets(s, [
    "Decoding-only k sweep: one checkpoint evaluated at every k, separating training-at-k from decoding-at-k. Cheapest and most informative run left.",
    "Spend the inference budget better: low-temperature sampling, beam search, or SymNCO augmentation instead of plain best-of-n.",
    "Replace the priority rule with a learned, parametric conflict handler.",
    "Permutation-invariant likelihood for k > 1, removing the pick-order variance.",
    "Extend k to the other two problems, OMDCPDP and FFSP.",
  ], 7.4, 2.42, 5.0, 3.2, 12);
  card(s, MX, 5.95, CW, .85, { fill: "F2F6F9", line: "DCE5EB" });
  rich(s, [
    { text: "Related work:  ", options: { bold: true, color: P.dk1 } },
    { text: "MACSIM (ICLR 2026) independently implements collision-free masked assignment on the same benchmarks. Our contribution is the controlled measurement of the k spectrum and the budget-fairness analysis.", options: {} },
  ], MX + .28, 6.1, CW - .56, .65, 12);
  s.addNotes("Be candid about the single seed and about the two unfinished ideas. Position against MACSIM before anyone raises it.");
}
{
  const s = pres.addSlide({ masterName: "CLOSING", sectionTitle: "Conclusions" });
  s.addText("Take-away", { placeholder: "eyebrow" });
  s.addText("Parallel decoding is not free. Committing two agents per pass instead of all M beats PARCO on every test set while using less compute — and the advantage grows with the size of the fleet.", { placeholder: "title" });
  s.addText("Thank you — questions?", { x: MX, y: 5.2, w: 6, h: .5, fontSize: 18, color: "A9BED0", margin: 0, isTextBox: true });
  s.addNotes("Close on the dominance result: it is the one that is both positive and budget-safe.");
}

(async () => {
  const out = path.join(__dirname, "PARCO_SRP_Deck_v2.pptx");
  await pres.writeFile({ fileName: out });
  const { applyTheme } = require(process.env.SKILL_DIR + "/scripts/apply_theme.js");
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
