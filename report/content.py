"""The report text. compose(story, figs) appends every flowable in order."""

from reportlab.lib.units import cm
from reportlab.platypus import CondPageBreak, KeepTogether, Spacer

import data as D
from style import (BAD, CALLOUT, CODE, FIG, GOOD, OL, P, ST, TABLE, UL, pct)

W = 16.4 * cm


def NEWPAGE():
    """Start on a fresh page, but never emit a blank one.

    A bare PageBreak when the cursor already sits at the top of a page produces
    an empty page -- which is exactly what happened between sections 9 and 10.
    CondPageBreak only breaks when less than the requested height remains, and
    the frame is 25.5 cm tall, so at the top of a page this is a no-op.
    """
    return CondPageBreak(23 * cm)


def compose(story, figs):
    title_page(story)
    story.append(NEWPAGE())
    contents(story)
    story.append(NEWPAGE())
    s1_summary(story, figs)
    story.append(NEWPAGE())
    s2_problem(story)
    s3_parco(story)
    story.append(NEWPAGE())
    s4_theory(story, figs)
    story.append(NEWPAGE())
    s5_implementation(story)
    story.append(NEWPAGE())
    s6_setup(story)
    story.append(NEWPAGE())
    s7_results(story, figs)
    story.append(NEWPAGE())
    s8_revisions(story)
    s9_simulator(story)
    story.append(NEWPAGE())
    s10_outlook(story)
    story.append(NEWPAGE())
    appendix_a(story)
    story.append(NEWPAGE())
    appendix_b(story)


# ---------------------------------------------------------------- title --
def title_page(story):
    story.append(Spacer(1, 4.2 * cm))
    story.append(P("Extending PARCO", "title"))
    story.append(P("Controlled experiments on parallel autoregressive multi-agent "
                   "combinatorial optimization, tested on the heterogeneous "
                   "capacitated vehicle routing problem", "subtitle"))
    story.append(Spacer(1, 1.2 * cm))
    story.extend(TABLE(
        None,
        [["Project", "Student Research Project, Group 9"],
         ["Institution", "Universität Hildesheim"],
         ["Members", "Akshai Athota · Charitha Yetukuri · Nitin Sharma · "
                     "Shehroz Khan · Mina George Soliman Hanna"],
         ["Base work", "PARCO (Berto et al., NeurIPS 2025)"],
         ["Problem", "min-max HCVRP"],
         ["Code", "github.com/Akshai-Athota/parco"]],
        [3.4 * cm, 12.6 * cm], plain=True))
    story.append(Spacer(1, .6 * cm))
    story.extend(CALLOUT(
        "What this report is",
        "A complete account of the project: the problem, the PARCO architecture, "
        "the theory behind each idea we tested, what we implemented, how the "
        "experiments were controlled, what the measurements say, and which of our "
        "own earlier conclusions they overturned. Every number is traceable to a "
        "committed log file.", "note", W))


def contents(story):
    story.append(P("Contents", "h1"))
    items = [
        ("1", "Executive summary"),
        ("2", "The problem: min-max HCVRP"),
        ("3", "PARCO"),
        ("4", "Concepts and theory"),
        ("5", "What we implemented"),
        ("6", "Experimental setup"),
        ("7", "Results"),
        ("8", "Two conclusions we had to revise"),
        ("9", "The delivery simulator"),
        ("10", "Limitations and next steps"),
        ("A", "Full per-test-set results"),
        ("B", "Branch map and how to reproduce"),
    ]
    for num, name in items:
        story.append(P(f"<b>{num}</b>&nbsp;&nbsp;&nbsp;{name}", "toc"))


# ------------------------------------------------------------ 1 summary --
def s1_summary(story, figs):
    story.append(P("1  Executive summary", "h1"))
    story.append(P(
        "PARCO makes multi-agent combinatorial optimization fast by letting every "
        "vehicle choose its next stop at the same time, then repairing the "
        "resulting collisions with a fixed priority rule. The paper measures the "
        "speed this buys. It never measures what the speed costs in solution "
        "quality, and it never ablates two components it inherits: the conflict "
        "handler and the logit clipping. This project measures all three."))
    story.append(P(
        "The central result is that <b>the conflict handler is not free</b>. "
        "Replacing it with explicit masking, and committing two agents per decoder "
        "pass instead of all of them, produces better routes on every one of the 12 "
        "test sets while using less compute both at inference and in training. It is "
        "not a trade-off; it is a strict improvement on both axes."))

    rows = []
    for name, cost, g, w, passes, epoch, verdict in D.headline():
        if g == 0.0 and name.startswith("Parallel"):
            gap_cell = "—"
        elif abs(g) > 100:          # diverged: the percentage carries no meaning
            gap_cell = f'<font color="#{BAD.hexval()[2:]}"><b>diverged</b></font>'
        else:
            gap_cell = pct(g)
        rows.append([name, f"{cost:.4f}", gap_cell,
                     "—" if w is None else f"{w} / 12",
                     "—" if passes is None else f"{passes:.1f}",
                     epoch, verdict])
    story.extend(TABLE(
        ["Method", "Mean cost", "Gap", "Wins", "Passes", "Epoch", "Verdict"],
        rows, [3.9 * cm, 1.9 * cm, 2.0 * cm, 1.5 * cm, 1.8 * cm, 1.6 * cm, 3.6 * cm],
        highlight=(2, 3)))
    story.append(P(
        "Mean cost is the average over 12 HCVRP test sets of 1,280 instances each; "
        "cost is the longest route time, which is the quantity the models minimise. "
        "The gap is measured against our own PARCO control, trained with the "
        "identical recipe on the same six GPUs. Negative is better.", "small"))

    story.extend(FIG(figs["pareto"],
                     "Figure 1 — the quality/speed front produced by the single "
                     "parameter k. Parallel PARCO sits above and to the right of "
                     "k = 2, which is what dominance looks like: k = 2 is cheaper "
                     "and better at the same time."))

    story.append(P("The four findings", "h2"))
    story.extend(OL([
        "<b>k = 2 dominates parallel PARCO.</b> Better on 12/12 test sets, 34% fewer "
        "decoder passes, 16% less wall-clock per training epoch.",
        "<b>The advantage grows with fleet size</b>, from −3.0% at M = 3 to −6.2% at "
        "M = 7 for k = 1. More agents per pass means more decisions made on stale "
        "information, which is exactly what sequencing recovers.",
        "<b>The sequential win is not bought with compute.</b> Given up to 32× the "
        "inference budget, parallel PARCO never reaches a single greedy k = 1 rollout.",
        "<b>The tanh clipping result reverses.</b> We previously reported the "
        "textbook form as 3.5% worse. Under a matched control it is 0.93% better on "
        "all 12 sets. The earlier number was a confound, not a finding.",
    ]))
    story.extend(CALLOUT(
        "The one-sentence version",
        "Removing the conflict handler and committing two agents per pass beats "
        "PARCO on solution quality on every test set while using less compute, and "
        "the gain grows precisely where PARCO's parallelism is supposed to pay off "
        "most.", "good", W))


# ------------------------------------------------------------ 2 problem --
def s2_problem(story):
    story.append(P("2  The problem: min-max HCVRP", "h1"))
    story.append(P(
        "A fleet of M vehicles must serve N customers from one shared depot. "
        "Vehicles are <i>heterogeneous</i>: each has its own capacity and its own "
        "speed. Each customer has an integer demand and must be visited exactly "
        "once. A vehicle that runs out of capacity returns to the depot, reloads, "
        "and continues, so a vehicle's tour is a sequence of trips."))

    story.append(P("2.1  The objective", "h2"))
    story.extend(CODE([
        "minimise    max over vehicles m of   L_m / f_m",
        "",
        "    L_m   total route length driven by vehicle m",
        "    f_m   speed of vehicle m,  so L_m / f_m is its finishing time",
    ], W))
    story.append(P(
        "This is <b>min-max</b>, not min-sum. We are not minimising total distance; "
        "we are minimising the time at which the <i>last</i> vehicle finishes. That "
        "makes the problem about balance: a plan where one van does almost nothing "
        "and another does everything scores badly even if the total distance is "
        "small. It also means the objective is decided by a single vehicle, which is "
        "why the simulator in Section 9 is worth watching — the last van to come "
        "home is literally the number in the results table."))
    story.extend(CALLOUT(
        "Why this matters for comparisons",
        "Because the objective is a maximum, it is not comparable with methods that "
        "minimise total distance. POMO and AM numbers for CVRP are min-sum over one "
        "vehicle and cannot be placed in the same table.", "warn", W))

    story.append(P("2.2  Why the action space has M + N entries", "h2"))
    story.append(P(
        "A natural reading is that with N customers each agent chooses among N "
        "options, giving logits of shape [B, M, N]. The implementation uses "
        "[B, M, M+N] instead, and the reason is the depot."))
    story.append(P(
        "The depot is <b>replicated once per agent</b>. Node indices 0 … M−1 are M "
        "copies of the depot, all at the same coordinates, one belonging to each "
        "agent; indices M … M+N−1 are the customers. Agent m returns to the depot by "
        "selecting node m, its own copy."))
    story.append(P("Two things make this necessary:"))
    story.extend(UL([
        "<b>Masking.</b> Every node is marked visited when it is chosen. If there "
        "were one shared depot node, the first vehicle to return home would mark the "
        "depot visited and no other vehicle could ever go back. Separate copies let "
        "each agent return to the depot independently.",
        "<b>Staying put.</b> An agent that has finished sits at its depot copy by "
        "re-selecting it, which the environment treats as a no-op. Without a private "
        "depot node there would be no way to express 'do nothing this step'.",
    ]))
    story.append(P(
        "This detail matters for everything that follows, because the joint action "
        "space whose softmax we take in Section 5 is M × (M+N), not M × N.", "small"))

    story.append(P("2.3  Instance distribution", "h2"))
    story.extend(TABLE(
        ["Quantity", "Range", "Note"],
        [["Customers N", "U(60, 100) in training", "test sets use 40, 60, 80, 100"],
         ["Vehicles M", "U(3, 7)", "test sets use 3, 5, 7"],
         ["Coordinates", "U(0,1)²", "depot sampled the same way"],
         ["Demand", "integers 1 … 9", "never zero"],
         ["Capacity", "U(20, 41)", "per vehicle, from the 2D-Ptr setting"],
         ["Speed", "U(0.5, 1.0)", "per vehicle; this is what makes it heterogeneous"]],
        [3.4 * cm, 4.4 * cm, 8.6 * cm]))


# -------------------------------------------------------------- 3 parco --
def s3_parco(story):
    story.append(P("3  PARCO", "h1"))
    story.append(P(
        "PARCO is an encoder–decoder policy trained with reinforcement learning. "
        "The encoder runs <b>once</b> per instance; the decoder then loops with the "
        "environment, and at every step all M agents act simultaneously."))

    story.append(P("3.1  The three mechanisms", "h2"))
    story.extend(OL([
        "<b>Communication layers.</b> Transformer layers inside the decoder let the "
        "agents exchange context before they choose, so an agent's decision can "
        "depend on what the others are about to do.",
        "<b>Multiple pointer mechanism.</b> Every agent gets its own pointer "
        "attention over the nodes, producing one row of logits each, hence the "
        "[B, M, M+N] tensor.",
        "<b>Priority-based conflict handler.</b> When two agents select the same "
        "customer in the same step, the one with the higher learned priority keeps "
        "it and the other stays where it is. This rule has no learnable parameters "
        "of its own beyond the priority score.",
    ]))

    story.append(P("3.2  The encoder is static, and this matters", "h2"))
    story.append(P(
        "The encoder reads only features that never change during an episode: "
        "coordinates, demands, capacities and speeds. It does not read the current "
        "position of any vehicle, nor remaining capacity, nor elapsed time. "
        "Therefore re-running the encoder mid-episode is a <b>provable no-op</b> — "
        "it is a pure function of inputs that have not changed."))
    story.extend(CALLOUT(
        "Consequence",
        "Decoder-only sequential decoding loses nothing relative to re-running the "
        "whole network. This is what justifies the design in Section 5.1, and it is "
        "also why the supervisor's re-encoding variant needed a new dynamic "
        "embedding before it could do anything at all (Section 5.5).", "note", W))

    story.append(P("3.3  Training", "h2"))
    story.append(P(
        "REINFORCE with a shared baseline: several augmented copies of each instance "
        "are rolled out, and the mean reward across them serves as the baseline, so "
        "no separate critic network is needed. Augmentations come from SymNCO "
        "(rotations and reflections of the instance, which leave the optimal "
        "solution structurally unchanged)."))
    story.extend(CODE([
        "grad J(θ)  =  E[ (R(a) − b) · Σ_t ∇ log π_θ(a_t | s_t) ]",
        "",
        "    a      the actions the policy proposed",
        "    R(a)   reward, i.e. −(longest route time)",
        "    b      shared baseline: mean reward over the augmented copies",
    ], W))


# ------------------------------------------------------------- 4 theory --
def s4_theory(story, figs):
    story.append(P("4  Concepts and theory", "h1"))

    story.append(P("4.1  The decoding spectrum", "h2"))
    story.append(P(
        "Three schemes sit on one axis, distinguished by how many (agent, node) "
        "pairs are committed from a single evaluation of the decoder:"))
    story.extend(TABLE(
        ["Scheme", "Pairs per pass", "Collisions", "Passes per episode"],
        [["Fully sequential", "1", "impossible", "many (≈ Σ_m T_m)"],
         ["Parallel PARCO", "M, then repaired", "possible, repaired by priority", "few"],
         ["Masked joint", "M, masked as we go", "impossible by construction", "few"]],
        [4.2 * cm, 3.4 * cm, 4.6 * cm, 4.2 * cm]))
    story.append(P(
        "Our supervisor's observation was that in the fully sequential limit the "
        "first and third of these are <i>the same thing</i>. That is what let us "
        "collapse two of our five ideas into a single parameter k (Section 5.1)."))

    story.append(P("4.2  The conflict handler as a many-to-one map", "h2"))
    story.append(P(
        "Write ψ for the conflict handler: it maps the vector of <i>proposed</i> "
        "actions ã to the vector of <i>executed</i> actions ψ(ã). The reward is "
        "computed on ψ(ã), but the gradient is computed on ã. This looks like it "
        "must introduce bias, and we initially reported it as such. It does not."))
    story.extend(CODE([
        "J(θ)       =  E_{ã ~ π_θ} [ R(ψ(ã)) ]",
        "∇J(θ)      =  E_{ã ~ π_θ} [ R(ψ(ã)) · Σ_t ∇ log π_θ(ã_t | s_t) ]",
    ], W))
    story.append(P(
        "Only ã is random. ψ and the environment are fixed deterministic rules with "
        "no learnable parameters, so R ∘ ψ is simply a fixed function of the "
        "proposals. The score-function identity therefore applies unchanged, and "
        "REINFORCE on the proposals is <b>unbiased</b> for the objective we actually "
        "care about. We verified this numerically: the estimator agreed with the "
        "true gradient to within 6.9 × 10⁻¹⁷."))
    story.extend(CALLOUT(
        "The biased option is the other one",
        "PARCO offers a setting that drops overruled agents from the loss "
        "(mask_handled = True). <i>That</i> is the biased estimator: it was off by "
        "19–249% in our checks, and in a 2 × 2 example it produced the wrong sign "
        "(−0.2 where the true gradient was +0.4). The default is the correct choice.",
        "bad", W))
    story.append(P(
        "The real defect is <b>variance</b>, not bias. Because ψ is many-to-one, "
        "different proposal vectors collapse to the same executed plan and therefore "
        "earn exactly the same reward, while receiving different gradient "
        "directions. By the law of total variance, the spread among proposals that "
        "map to one outcome is pure noise. We measured the avoidable share:"))
    story.extend(TABLE(
        ["Agents M", "Avoidable share of gradient variance"],
        [[str(m), f"{v:.1f}%"] for m, v in D.VARIANCE_SHARE],
        [4.0 * cm, 7.0 * cm]))
    story.append(P(
        "Masking removes this noise at the source: if collisions cannot occur, ψ is "
        "the identity and the map stops being many-to-one.", "small"))

    story.append(P("4.3  Ordering is a second latent variable when k &gt; 1", "h2"))
    story.append(P(
        "Our k-parallel scheme picks k pairs one after another inside a single pass. "
        "The order in which those k picks happen does not change the resulting set "
        "of assignments, but it does change the sequence of log-probabilities we "
        "accumulate. That reintroduces exactly the kind of avoidable variance that "
        "masking removed, bounded by k! orderings:"))
    story.extend(TABLE(
        ["k", "Avoidable share from pick ordering"],
        [[str(k), f"{v:.1f}%"] for k, v in D.ORDER_SHARE],
        [4.0 * cm, 7.0 * cm]))
    story.append(P(
        "A permutation-invariant set loss is the known fix and is listed in the next "
        "steps. We did not implement it, so the k &gt; 1 numbers in this report carry "
        "this inefficiency.", "small"))

    story.append(P("4.4  Tanh clipping: gain versus saturation", "h2"))
    story.append(P(
        "PARCO bounds the decoder logits with C·tanh(z) at C = 10. Writing the "
        "family generally separates the two things C was doing at once:"))
    story.extend(CODE([
        "φ(z)   =  g · tanh(z / τ)",
        "φ'(z)  =  (g / τ) · sech²(z / τ)",
        "",
        "    gain at the origin  =  g / τ          knee  ≈  2τ",
        "    output range        =  (−g, +g)       sech² ∈ (0, 1]",
    ], W))
    story.extend(TABLE(
        ["Form", "g", "τ", "Gain at origin", "Knee", "Effect"],
        [["PARCO (fixed)", "10", "1", "10", "≈ 2", "amplifies, then saturates hard"],
         ["Scaled", "10", "10", "1", "≈ 20", "near-identity, bounds only the tails"],
         ["Gain-matched (f)", "30", "3", "10", "≈ 6", "same gain, later knee — not yet run"]],
        [3.1 * cm, 1.2 * cm, 1.2 * cm, 2.6 * cm, 1.6 * cm, 6.5 * cm]))
    story.extend(FIG(figs["tanh_curves"],
                     "Figure 2 — the same C = 10 produces two very different "
                     "functions. Left: the scaled form tracks the identity across "
                     "the range logits actually occupy, while the fixed form is "
                     "nearly a step. Right: the slope at the origin is 10 versus 1.",
                     15.0 * cm))
    story.append(P(
        "Because a softmax over φ(z) with slope s at the origin behaves like a "
        "softmax over z at temperature 1/s, the fixed form is effectively a "
        "<b>ten-fold temperature drop</b>: it sharpens the policy and suppresses "
        "exploration early in training. The scaled form leaves the logit scale alone "
        "and only bounds the extreme tails, which is what a clip is normally for."))
    story.extend(CALLOUT(
        "Correction",
        "An earlier version of this work stated the opposite — that the scaled form "
        "makes the distribution sharper. It is the fixed form that sharpens. "
        "Swapping the two is a factor-of-ten change in effective temperature, so the "
        "direction matters.", "bad", W))

    story.append(P("4.5  Counting compute honestly", "h2"))
    story.append(P(
        "To compare methods that take different numbers of steps we need a unit of "
        "work. We use the <b>decoder pass</b>: one evaluation of the decoder head "
        "producing the [B, M, M+N] logits. This is the right unit here because a "
        "k-parallel pass commits all k of its pairs from a <i>single</i> logits "
        "tensor, so one pass costs the same regardless of k."))
    story.extend(CODE([
        "passes per instance  =  decoding steps  ×  sampling rollouts",
    ], W))
    story.append(P(
        "Two measurement traps we had to avoid. First, the decoding loop runs "
        "<tt>while not done.all()</tt>, so the reported step count is a maximum over "
        "the batch and grows with batch size; every configuration must therefore be "
        "measured at the same batch width. Second, rl4co's batchify repeats "
        "sample-major, so reducing best-of-n results with a naive reshape groups "
        "different <i>instances</i> rather than different <i>samples</i> — see "
        "Section 5.6.", "small"))


# ----------------------------------------------------- 5 implementation --
def s5_implementation(story):
    story.append(P("5  What we implemented", "h1"))
    story.append(P(
        "Five ideas were proposed. Two of them turned out to be endpoints of one "
        "parameter and were merged; one was infeasible within the cluster's job "
        "limit; one targets a different problem. The table maps proposal to outcome."))
    story.extend(TABLE(
        ["#", "Idea", "Branch", "Outcome"],
        [["1", "Full sequential decoding", "hcvrp_sequential", "merged into k"],
         ["3", "Masked joint decoding", "hcvrp_logp_bias", "merged into k"],
         ["1+3", "The k parameter", "hcvrp_k_parallel", "trained at k = 1, 2, 4, 7"],
         ["2", "Tanh logit clipping", "hcvrp_tanh_lr", "re-run with a matched control"],
         ["4", "Homogeneous-fleet CVRP", "hcvrp_cvrp", "done, separate problem"],
         ["5", "Explicit wait action", "hcvrp_wait_token", "infeasible at 72 h"],
         ["—", "Dynamic re-encoding", "hcvrp_dynamic_encoding", "infeasible at 72 h"],
         ["—", "Equal-budget harness", "hcvrp_equal_budget", "done"],
         ["—", "Delivery simulator", "hcvrp_demo", "done"]],
        [1.2 * cm, 4.6 * cm, 4.8 * cm, 5.6 * cm]))

    story.append(P("5.1  The k parameter", "h2"))
    story.append(P(
        "k is the number of (agent, node) pairs committed per decoder pass. "
        "k = 1 is full sequential decoding; k = M is masked joint decoding; the "
        "values between trace the front."))
    story.extend(CODE([
        "for _ in range(min(k, num_agents)):",
        "    masked = logits.masked_fill(~work_mask, -inf)",
        "    flat   = masked.reshape(B, -1)",
        "    logp   = log_softmax(flat / temperature, dim=-1)",
        "    choice = select(logp)                    # one (agent, node) pair",
        "    agent  = choice // num_actions",
        "    node   = choice %  num_actions",
        "    actions = actions.scatter(1, agent, node)",
        "    work_mask.scatter_(1, agent, False)      # that agent has decided",
        "    work_mask.scatter_(2, node,  False)      # that node is taken",
    ], W))
    story.append(P("Three properties follow directly from that loop:"))
    story.extend(UL([
        "<b>Collisions are impossible at any k.</b> Masking the chosen agent's row "
        "and the chosen node's column means no two agents can be handed the same "
        "node, so the priority conflict handler never runs and the halting ratio is "
        "zero by construction.",
        "<b>One pass is one decoder forward.</b> The k picks reuse the same logits "
        "tensor, which is what makes step counts comparable as compute.",
        "<b>Agents not reached in a pass repeat their current node</b>, which the "
        "environment treats as a no-op.",
    ]))
    story.extend(CALLOUT(
        "A bug worth recording",
        "The first sequential implementation never terminated and eventually "
        "exhausted GPU memory. An agent sitting at its depot could re-select the "
        "depot; the state did not change, so a deterministic decoder returned "
        "identical logits forever, and the loop ran to max_steps = 10⁶ before dying "
        "in torch.stack. The fix is one line — forbid every agent from re-selecting "
        "the node it is standing on — plus an idle guard for rows where every option "
        "is masked. Verified against a replica of the environment: never-done at "
        "5,000 steps became 35 steps.", "bad", W))

    story.append(P("5.2  Tanh clipping", "h2"))
    story.append(P(
        "A small module implements the general family and is wired into both the "
        "decoder logits and, optionally, the encoder attention logits. The sweep in "
        "this report clips the <b>decoder only</b>, which is the change the earlier "
        "experiment failed to isolate."))
    story.extend(CODE([
        "def tanh_clip(logits, clip_value, mode, tau=None):",
        "    if mode == 'fixed':    return clip_value * torch.tanh(logits)",
        "    if mode == 'scaled':   return clip_value * torch.tanh(logits / clip_value)",
        "    if mode == 'general':  return clip_value * torch.tanh(logits / tau)",
    ], W))

    story.append(P("5.3  Homogeneous-fleet CVRP", "h2"))
    story.append(P(
        "A new environment and generator only — every vehicle shares capacity 50 and "
        "unit speed. The architecture is untouched, which makes this a clean test of "
        "whether parallel decoding helps only heterogeneous fleets."))

    story.append(P("5.4  Explicit wait action", "h2"))
    story.append(P(
        "A learnable wait token extends the action space from M+N to M+N+1, letting "
        "an agent idle instead of proposing a node it should not visit. Waiting "
        "agents are excluded from priority resolution, and a deadlock guard forces "
        "the agent with the largest act-versus-wait advantage to move if all choose "
        "to wait."))
    story.extend(CALLOUT(
        "A shape bug worth recording",
        "The deadlock guard read the environment's done flag directly and silently "
        "broadcast a [B] tensor against a [B, 1] one, producing a [B, B] "
        "cross-product — so on the steps that did not raise, the guard was deciding "
        "from the wrong tensor entirely. The environment creates done as [B] but "
        "torchrl conforms it to the done_spec shape on env.step, so it arrives as "
        "[B, 1]. Reshaping explicitly before reducing fixes it.", "bad", W))

    story.append(P("5.5  Dynamic re-encoding", "h2"))
    story.append(P(
        "Our supervisor's variant of idea 1 re-runs the encoder at every step rather "
        "than only the decoder. As established in Section 3.2 a plain re-run is a "
        "no-op, so we added an initial embedding that reads the live state — current "
        "position, remaining capacity, elapsed time, at-depot and visited flags — to "
        "give the encoder something that actually changes."))

    story.append(P("5.6  The equal-budget harness, and two bugs it exposed", "h2"))
    story.append(P(
        "Building the budget-fair comparison required fixing two defects in the test "
        "harness that would otherwise have produced confidently wrong numbers."))
    story.extend(OL([
        "<b>Best-of-n was wrong for batch sizes above one.</b> rl4co's batchify "
        "repeats sample-major, so reshape(−1, n) grouped different instances of the "
        "same sample rather than different samples of the same instance. The "
        "codebase hid this behind an assertion pinning sampling to batch_size = 1. "
        "Replacing the reduction with unbatchify fixes it and lifts the restriction.",
        "<b>Step counts are batch-width dependent.</b> The loop runs until every "
        "instance in the batch is done, so the reported step count is a maximum and "
        "grows with the batch. Measuring methods at different widths would have "
        "biased the budget axis itself; the sweep holds the width constant.",
    ]))
    story.append(P(
        "As a check, the harness recomputes the objective from the reconstructed "
        "routes and compares it against the environment's own reward. Greedy costs "
        "reproduced the main results table to four decimal places.", "small"))


# -------------------------------------------------------------- 6 setup --
def s6_setup(story):
    story.append(P("6  Experimental setup", "h1"))
    story.extend(CALLOUT(
        "What changed from the previous round",
        "Earlier comparisons were confounded: the tanh run used 8 GPUs while "
        "everything else used 6, the baseline came from a different branch, and the "
        "clipping change touched the decoder and the encoder attention at once. All "
        "six finished runs in this report share one recipe on the same six GPUs, "
        "with one control. That single change is what reversed the tanh conclusion.",
        "warn", W))

    story.append(P("6.1  Training recipe", "h2"))
    story.extend(TABLE(
        ["Setting", "Our runs", "PARCO paper"],
        [["Epochs", "100", "100"],
         ["Instances per epoch", "100,000", "400,000"],
         ["GPUs", "6 (every run)", "8"],
         ["Batch per GPU × accumulation", "16 × 8", "—"],
         ["Effective batch", "768", "512"],
         ["Optimizer", "Adam 1e-4, ×0.1 at epochs 80 and 95", "same"],
         ["SymNCO augmentations", "4", "10"],
         ["Train distribution", "N ~ U(60,100), M ~ U(3,7)", "same"]],
        [5.6 * cm, 6.0 * cm, 4.4 * cm]))
    story.append(P(
        "Our smaller per-epoch budget is why our PARCO sits 6–12% above the "
        "published numbers. That is a budget difference, not a method difference, "
        "which is precisely why every gap in this report is measured against our own "
        "control rather than against the paper.", "small"))

    story.append(P("6.2  Test protocol", "h2"))
    story.extend(UL([
        "12 test sets: N ∈ {40, 60, 80, 100} × M ∈ {3, 5, 7}, 1,280 instances each.",
        "Identical instance files for every arm; greedy decoding; batch 128; last.ckpt.",
        "Cost is the longest route time. Lower is better; a negative gap is better.",
    ]))

    story.append(P("6.3  The control", "h2"))
    story.append(P(
        "The control is stock PARCO — fixed clipping, encoder attention untouched — "
        "trained as arm (a) of the tanh sweep. It therefore serves as both the "
        "control for the clipping experiment and the baseline for the k sweep, on "
        "identical hardware with an identical recipe. Its mean cost over the 12 sets "
        f"is <b>{D.mean_cost(D.CONTROL):.4f}</b>."))

    story.append(P("6.4  Pipeline validation", "h2"))
    story.append(P(
        "Before trusting any of this we reproduced the authors' released checkpoint "
        "through our own evaluation code. The paper prints 10.98 at N = 100, M = 3; "
        "our run of their checkpoint gives 10.977. Same weights, same number to three "
        "decimals — the match is what validates the evaluation pipeline, separately "
        "from any question about our own training."))


# ------------------------------------------------------------ 7 results --
def s7_results(story, figs):
    story.append(P("7  Results", "h1"))

    story.append(P("7.1  The k front", "h2"))
    rows = []
    for k in (1, 2, 4, 7):
        d = D.K_TRAINED[k]
        rows.append([f"k = {k}", f"{D.mean_cost(d):.4f}", pct(D.gap(d)),
                     f"{D.wins(d)} / 12", f"{D.mean_steps(d):.1f}", D.EPOCH_MIN[k]])
    rows.insert(0, ["Parallel PARCO", f"{D.mean_cost(D.CONTROL):.4f}", "—", "—",
                    f"{D.mean_steps(D.CONTROL):.1f}", D.EPOCH_MIN["parallel"]])
    story.extend(TABLE(
        ["Method", "Mean cost", "Gap", "Wins", "Passes", "Min/epoch"],
        rows, [4.4 * cm, 2.4 * cm, 2.2 * cm, 2.0 * cm, 2.0 * cm, 2.4 * cm],
        highlight=(1, 2)))
    story.append(P(
        "Cost rises and passes fall monotonically in k, with the crossover between "
        "k = 2 and k = 4. One parameter spans the whole range from maximum quality "
        "to maximum speed."))
    story.extend(CALLOUT(
        "Two cross-checks",
        "k = 1 reproduces the earlier sequential branch exactly (11.4836 / 6.9243 / "
        "5.0461 at N = 100), confirming the merged implementation is faithful. "
        "k = 7 came out <i>worse</i> than the old joint branch (12.111 / 7.479 / "
        "5.587 versus 11.717 / 7.140 / 5.326), contrary to our prediction that the "
        "self-loop guard would help slightly: at k = M the guard removes a degree of "
        "freedom the old decoder had, and that costs something.", "note", W))

    story.append(P("7.2  The advantage scales with fleet size", "h2"))
    story.extend(FIG(figs["m_scaling"],
                     "Figure 3 — cost gap against parallel PARCO, split by fleet "
                     "size. The more agents commit per pass, the more there is for "
                     "sequencing to recover."))
    story.append(P(
        "This is the mechanism confirming itself. More agents per pass means more "
        "decisions taken on stale logits and more collisions for the priority rule "
        "to repair; sequencing recovers exactly that loss. The effect is largest "
        "precisely where PARCO's parallelism is supposed to pay off most."))

    story.append(P("7.3  Tanh clipping", "h2"))
    trows = []
    for key in ("a", "b", "d"):
        arm = D.TANH[key]
        d = arm["data"]
        g = ("—" if key == "a" else
             f'<font color="#{BAD.hexval()[2:]}"><b>diverged</b></font>'
             if abs(D.gap(d)) > 100 else pct(D.gap(d)))
        trows.append([arm["label"], arm["lr"], f"{D.mean_cost(d):.4f}", g,
                      f"{D.wins(d)} / 12" if key != "a" else "—", arm["epoch"]])
    story.extend(TABLE(
        ["Arm", "lr", "Mean cost", "vs control", "Wins", "Min/epoch"],
        trows, [5.0 * cm, 1.6 * cm, 2.4 * cm, 2.6 * cm, 2.0 * cm, 2.2 * cm],
        highlight=(2,)))
    story.append(P(
        "With the encoder-attention half switched off and a matched control, the "
        "scaled form is <b>0.93% better and better on all 12 test sets</b>, at "
        "identical cost per epoch. Small, but perfectly consistent, and free."))
    story.append(P(
        "Arm (d) tested whether a flatter softmax wants a larger step size to "
        "compensate. It does not: at ten times the learning rate the run collapsed, "
        "with the best checkpoint at epoch 22 and step counts pinned at the episode "
        "cap."))

    story.append(P("7.4  Equal inference budget", "h2"))
    story.append(P(
        "A greedy k = 1 rollout spends 1.34× the decoder passes of parallel PARCO, "
        "so part of its margin could simply be bought with compute. To test that, "
        "each model was swept over best-of-n sampling and its cost read off against "
        "the budget actually consumed."))
    brows = []
    for i, mult in enumerate(D.EQUAL_BUDGET["mults"]):
        r = [f"{mult:g}×"]
        best = min(D.EQUAL_BUDGET["rows"][k][i] for k in D.EQUAL_BUDGET["rows"])
        for key in ("parallel", "k1", "k2", "k4", "k7"):
            v = D.EQUAL_BUDGET["rows"][key][i]
            r.append(f'<font color="#{GOOD.hexval()[2:]}"><b>{v:.4f}</b></font>'
                     if v == best else f"{v:.4f}")
        r.append(f"{D.EQUAL_BUDGET['sets_in_common'][i]}")
        brows.append(r)
    story.extend(TABLE(
        ["Budget", "Parallel", "k = 1", "k = 2", "k = 4", "k = 7", "Sets"],
        brows, [1.9 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 1.5 * cm]))
    story.append(P(
        "Budget 1.0× is the passes parallel PARCO spends on one greedy rollout of "
        "that dataset. k = 1 wins 12 of 12 sets at every level from 2× upward. "
        "Giving parallel PARCO 32× the budget does not close a 4.5% gap.", "small"))
    story.extend(FIG(figs["best_of_n"],
                     "Figure 4 — why the budget rows are flat. Sampling at "
                     "temperature 1 is a weak way to spend compute for every model "
                     "here: best-of-32 only just climbs back to the greedy cost."))
    story.extend(CALLOUT(
        "An honest caveat",
        "The only mechanism we gave each model for spending surplus budget was "
        "i.i.d. best-of-n sampling at temperature 1, and it is weak for all of them "
        "(the best sampling result is +1.08% against greedy for parallel PARCO and "
        "+0.09% for k = 1). So the defensible claim is narrower than it first looks: "
        "<i>extra compute spent this way</i> does not close the gap. A "
        "temperature-tuned or augmentation-based search might, and that is listed in "
        "the next steps. One encouraging sign: the ordering k1 &lt; k2 &lt; parallel "
        "&lt; k4 &lt; k7 holds at every sample count tested, not only at greedy.",
        "warn", W))

    story.append(P("7.5  Runs that did not finish", "h2"))
    story.extend(TABLE(
        ["Run", "Reached", "Rate", "Extrapolated"],
        [["Dynamic re-encoding", "43 of 100 epochs in 71.9 h", "~100 min/epoch",
          "~7 days"],
         ["Explicit wait action", "3 epochs", "0.15 it/s, ~3.9 h/epoch", "~2 weeks"]],
        [4.4 * cm, 5.4 * cm, 3.4 * cm, 3.2 * cm]))
    story.append(P(
        "Both were killed by the cluster's 72-hour job limit. These are budget "
        "findings, not negative results about the ideas: neither was evaluated. The "
        "wait-action run also lengthens as it trains, because a policy that learns "
        "to wait produces longer episodes.", "small"))

    story.append(P("7.6  Homogeneous-fleet CVRP", "h2"))
    story.extend(TABLE(
        ["Test set", "Cost", "Steps", "Time/batch"],
        [[n, f"{c:.3f}", f"{s:.1f}", f"{t:.3f} s"] for n, c, s, t in D.CVRP],
        [3.6 * cm, 3.0 * cm, 3.0 * cm, 3.4 * cm]))
    story.append(P(
        "† zero-shot at twice the largest training size. M = 5 and M = 7 hold up; "
        "M = 3 degenerates to 28.487 where roughly 11 is expected — too few agents "
        "at double scale fall into long, unbalanced tours. Note these are min-max "
        "route <i>lengths</i> for a homogeneous fleet and are not comparable with "
        "the HCVRP numbers elsewhere in this report.", "small"))


# ---------------------------------------------------------- 8 revisions --
def s8_revisions(story):
    story.append(P("8  Two conclusions we had to revise", "h1"))
    story.append(P(
        "Both came from the same cause: comparisons that were not properly "
        "controlled. Recording them is part of the result, because the controlled "
        "design is what caught them."))

    story.append(P("8.1  Tanh clipping: +3.5% worse became −0.93% better", "h2"))
    story.append(P(
        "The earlier run clipped the encoder attention logits as well as the "
        "decoder's and trained on 8 GPUs against a baseline trained on 6. Isolating "
        "the decoder clip and matching the hardware removes both confounds, and the "
        "sign flips. The functional form was never the problem; the experiment was."))

    story.append(P("8.2  The conflict handler introduces variance, not bias", "h2"))
    story.append(P(
        "We initially described PARCO's training signal as biased because the reward "
        "is computed on executed actions while the gradient is taken on proposed "
        "ones. Section 4.2 shows that estimator is unbiased, and that the biased "
        "option is the <i>other</i> setting. The defect is real but it is variance, "
        "which changes the fix: not a re-weighting, but removing collisions so the "
        "proposal-to-execution map stops being many-to-one."))

    story.append(P("8.3  Ideas 1 and 3 were not two ideas", "h2"))
    story.append(P(
        "Full sequential decoding and masked joint decoding were implemented and "
        "reported as separate branches. They are the two endpoints of a single "
        "parameter, and in the fully sequential limit they are identical. One sweep "
        "now replaces two experiments that were never directly comparable."))


# ---------------------------------------------------------- 9 simulator --
def s9_simulator(story):
    story.append(P("9  The delivery simulator", "h1"))
    story.append(P(
        "A table saying k = 2 is 3% better does not convey what that looks like. The "
        "repository includes an interactive demo on branch <tt>hcvrp_demo</tt>: "
        "place delivery orders on a map, plan them with each trained checkpoint, and "
        "watch the fleet deliver."))
    story.append(P(
        "Because the objective is a maximum over vehicles, the <b>last van to finish "
        "is the number in the results table</b>. The animation therefore shows the "
        "quantity being minimised rather than describing it. In one test run all 30 "
        "orders were delivered by t = 1.235 while the objective was 1.646; the gap "
        "is the slowest van's empty return leg, which min-max penalises and min-sum "
        "would not."))
    story.extend(UL([
        "Click to add or delete orders, drag the depot, generate seeded scenarios.",
        "Edit per-vehicle capacity and speed; add or remove vans.",
        "Compare longest route, gap versus parallel PARCO, total distance, decoder "
        "passes and solve time across checkpoints.",
        "Scrub or play the clock; a per-vehicle panel shows which van is the "
        "bottleneck and how many trips each made.",
    ]))
    story.extend(CALLOUT(
        "Read it as intuition, not evidence",
        "A single hand-placed instance is one sample. The gaps in this report are "
        "means over 12 test sets of 1,280 instances; on any one scenario the "
        "ordering of methods can easily differ from the average. The simulator also "
        "warns when a scenario leaves the trained range (N ~ U(60,100), M ~ U(3,7)) "
        "rather than presenting the number as comparable.", "warn", W))


# ------------------------------------------------------------ 10 outlook --
def s10_outlook(story):
    story.append(P("10  Limitations and next steps", "h1"))

    story.append(P("10.1  Limitations", "h2"))
    story.extend(UL([
        "<b>One seed per configuration.</b> Two or three are needed for error bars, "
        "and the tanh effect (−0.93%) is small enough to require them before it "
        "should be called established. The k results (−4.55%, 12/12 sets) are far "
        "enough outside plausible seed noise to be safe.",
        "<b>Budget was spent only through i.i.d. sampling at temperature 1</b>, which "
        "Section 7.4 shows is weak for every model tested.",
        "<b>The k front has gaps</b>: k = 3, 5, 6 are not yet trained.",
        "<b>Training and decoding effects are not separated.</b> Every model was "
        "evaluated at the k it was trained with, so we cannot yet say how much of "
        "the gain is from training at k rather than decoding at k.",
        "<b>Arm (f), 30·tanh(z/3), has not run.</b> It is the only arm that holds the "
        "gain fixed while moving the knee, so it is the one that would separate the "
        "gain effect from the saturation effect.",
        "<b>k &gt; 1 carries the ordering variance</b> described in Section 4.3.",
    ]))

    story.append(P("10.2  Next steps", "h2"))
    story.extend(OL([
        "<b>Decoding-only k sweep</b> — one checkpoint evaluated at every k. The "
        "cheapest and most informative remaining run, since it separates "
        "training-at-k from decoding-at-k.",
        "<b>Spend the inference budget better</b> — low-temperature sampling, beam "
        "search, or SymNCO augmentation instead of plain best-of-n.",
        "<b>A learned, parametric conflict handler</b> to replace the priority rule.",
        "<b>A permutation-invariant likelihood for k &gt; 1</b>, removing the "
        "ordering variance.",
        "<b>Seeds and error bars</b> on the tanh arms, plus arm (f).",
        "<b>Extend k to the other two problems</b>, OMDCPDP and FFSP.",
    ]))
    story.extend(CALLOUT(
        "Related work to position against",
        "MACSIM (ICLR 2026) independently implements collision-free masked "
        "assignment and an explicit wait action on the same benchmarks, and uses a "
        "permutation-invariant set loss. Our contribution should be positioned as "
        "the controlled measurement of the k spectrum and the budget-fairness "
        "analysis rather than as priority on the masking idea itself.", "note", W))


# --------------------------------------------------------------- appendix --
def appendix_a(story):
    story.append(P("Appendix A  Full per-test-set results", "h1"))
    story.append(P(
        "Cost is the longest route time; steps are decoder passes. The control is "
        "stock PARCO under the identical recipe.", "small"))

    for k in (1, 2, 4, 7):
        story.append(P(f"A.{k}  k = {k}", "h3") if k == 1 else P(f"k = {k}", "h3"))
        rows = []
        for n, m in D.SETS:
            c, s = D.K_TRAINED[k][(n, m)]
            cc, _ = D.CONTROL[(n, m)]
            rows.append([f"n{n} m{m}", f"{cc:.4f}", f"{c:.4f}",
                         pct(100 * (c - cc) / cc, 1), f"{s:.1f}"])
        story.extend(TABLE(["Test set", "Control", f"k = {k}", "Gap", "Steps"], rows,
                           [3.0 * cm, 3.0 * cm, 3.0 * cm, 2.6 * cm, 2.6 * cm]))

    story.append(P("A.5  Tanh arms", "h3"))
    rows = []
    for n, m in D.SETS:
        a = D.TANH["a"]["data"][(n, m)][0]
        b = D.TANH["b"]["data"][(n, m)][0]
        rows.append([f"n{n} m{m}", f"{a:.4f}", f"{b:.4f}", pct(100 * (b - a) / a, 2)])
    story.extend(TABLE(["Test set", "(a) fixed", "(b) scaled", "Gap"], rows,
                       [3.4 * cm, 3.4 * cm, 3.4 * cm, 3.0 * cm]))


def appendix_b(story):
    story.append(P("Appendix B  Branch map and how to reproduce", "h1"))
    story.extend(TABLE(
        ["Branch", "Contents"],
        [["main", "upstream PARCO, unmodified"],
         ["parallel_hcvrp", "first baseline runs"],
         ["hcvrp_sequential", "idea 1, superseded by hcvrp_k_parallel"],
         ["hcvrp_logp_bias", "idea 3, superseded by hcvrp_k_parallel"],
         ["hcvrp_k_parallel", "the k parameter, all k checkpoints and training logs"],
         ["hcvrp_tanh_scaled", "first tanh attempt (8 GPU, encoder+decoder clip)"],
         ["hcvrp_tanh_lr", "controlled tanh sweep, arms a / b / d"],
         ["hcvrp_cvrp", "homogeneous-fleet CVRP environment"],
         ["hcvrp_wait_token", "explicit wait action"],
         ["hcvrp_dynamic_encoding", "encoder re-run with a dynamic init embedding"],
         ["hcvrp_equal_budget", "budget-fair evaluation harness"],
         ["hcvrp_demo", "interactive delivery simulator"]],
        [4.8 * cm, 11.2 * cm]))
    story.extend(CALLOUT(
        "Checkpoints live inside branches",
        "logs/train/runs is tracked, so the trained checkpoints exist on "
        "hcvrp_k_parallel and switching to a branch cut before they were pushed "
        "removes them from the working tree. This is worth knowing before concluding "
        "that a checkpoint is missing.", "warn", W))

    story.append(P("B.1  Reproducing the main results", "h2"))
    story.extend(CODE([
        "# train one k model (repeat for k = 1, 2, 4, 7)",
        "sbatch train_hcvrp_k2.sh",
        "",
        "# evaluate every k-trained model at its own k",
        "sbatch test_hcvrp_k_trained.sh",
        "",
        "# the controlled tanh sweep",
        "sbatch train_hcvrp_tanh_a_ctrl.sh      # and _b_, _d_",
        "sbatch test_hcvrp_tanh_sweep.sh",
        "",
        "# budget-fair comparison (no training; reuses the checkpoints)",
        "sbatch test_hcvrp_equal_budget.sh",
        "",
        "# interactive simulator (login node; forward the port)",
        "./run_demo.sh",
    ], W))

    story.append(P("B.2  Log files", "h2"))
    story.extend(TABLE(
        ["Log", "What it contains"],
        [["hcvrp_k{1,2,4,7}_parco.log", "k training runs, epoch wall-clock"],
         ["hcvrp_k_trained_test.log", "k sweep evaluation, Section 7.1"],
         ["tanh_{a,b,d}_*.log", "tanh training runs"],
         ["tanh_sweep_test.log", "tanh evaluation, Section 7.3"],
         ["hcvrp_equal_budget.log", "budget sweep, Section 7.4"],
         ["hcvrp_dynamic_encoding_parco.log", "the run that hit the 72 h wall"]],
        [6.0 * cm, 10.0 * cm]))
