/* HCVRP delivery simulator -- places orders, asks the backend to plan, animates. */
"use strict";

const PAD = 42, SPAN = 1000 - 2 * PAD;
const VEH_COLOURS = ["#E2561F", "#12927A", "#2E5C8A", "#D9A21B", "#7E5AA8",
                     "#C2185B", "#00838F", "#558B2F", "#5D4037", "#455A64",
                     "#AD1457", "#1565C0"];

const S = {
  scenario: { depot: { x: .5, y: .5 }, customers: [], vehicles: [] },
  info: { methods: {}, layouts: {}, train: {} },
  chosen: new Set(),
  plans: {},
  focus: null,
  t: 1,
  playing: false,
  raf: null,
};

const $ = (id) => document.getElementById(id);
const map = $("map");
const ux = (x) => PAD + x * SPAN;
const uy = (y) => PAD + y * SPAN;
const fmt = (v, n = 3) => Number(v).toFixed(n);
const el = (tag, attrs = {}) => {
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n;
};
const vehColour = (i) => VEH_COLOURS[i % VEH_COLOURS.length];

/* ------------------------------------------------------------------ boot */
async function boot() {
  try {
    const r = await fetch("/api/methods");
    S.info = await r.json();
  } catch (e) {
    $("backend").textContent = "unreachable";
    return;
  }
  $("backend").textContent = S.info.backend === "torch" ? "models loaded" : "no models";
  if (S.info.backend !== "torch") {
    const b = $("backendNote");
    b.textContent = S.info.reason || "heuristic only";
    b.classList.add("warn");
  }
  const sel = $("layout");
  for (const [k, label] of Object.entries(S.info.layouts || {})) {
    const o = document.createElement("option");
    o.value = k; o.textContent = label; sel.appendChild(o);
  }
  renderMethods();
  await generate();
  wire();
}

function renderMethods() {
  const box = $("methods");
  box.innerHTML = "";
  const order = ["parallel", "k1", "k2", "k4", "k7", "tanh", "heuristic"];
  const keys = Object.keys(S.info.methods)
    .sort((a, b) => order.indexOf(a) - order.indexOf(b));
  keys.forEach((k, i) => {
    const m = S.info.methods[k];
    const lab = document.createElement("label");
    lab.className = "m";
    lab.innerHTML =
      `<input type="checkbox" value="${k}" ${i < 3 ? "checked" : ""}>` +
      `<span class="sw" style="background:${m.colour}"></span>` +
      `<span><span class="t">${m.label}</span><br><span class="b">${m.blurb}</span></span>`;
    const cb = lab.querySelector("input");
    if (cb.checked) S.chosen.add(k);
    cb.addEventListener("change", () => {
      cb.checked ? S.chosen.add(k) : S.chosen.delete(k);
    });
    box.appendChild(lab);
  });
}

/* ------------------------------------------------------------- scenario */
async function generate() {
  const body = {
    n: +$("nOrders").value, m: +$("nVeh").value,
    layout: $("layout").value, seed: +$("seed").value,
  };
  const r = await fetch("/api/generate", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  S.scenario = await r.json();
  resetPlans();
  renderVehicles();
  draw();
}

function resetPlans() {
  S.plans = {}; S.focus = null; S.t = 1; stop();
  $("results").innerHTML = `<p class="maphint">Plan the routes to compare the checkpoints.</p>`;
  $("perVehicle").innerHTML = "";
  $("mapTitle").textContent = "";
  $("play").disabled = true; $("scrub").disabled = true; $("clock").textContent = "—";
}

function renderVehicles() {
  const box = $("vehicles");
  box.innerHTML = "";
  S.scenario.vehicles.forEach((v, i) => {
    const d = document.createElement("div");
    d.className = "veh";
    d.innerHTML =
      `<span class="sw" style="background:${vehColour(i)}"></span>` +
      `<input type="number" step="1" min="1" value="${v.capacity}" title="capacity">` +
      `<input type="number" step="0.05" min="0.05" value="${v.speed}" title="speed">` +
      `<button title="remove">×</button>`;
    const [cap, spd] = d.querySelectorAll("input");
    cap.addEventListener("change", () => { v.capacity = +cap.value; resetPlans(); });
    spd.addEventListener("change", () => { v.speed = +spd.value || 0.1; resetPlans(); });
    d.querySelector("button").addEventListener("click", () => {
      S.scenario.vehicles.splice(i, 1); resetPlans(); renderVehicles(); draw();
    });
    box.appendChild(d);
  });
  $("nVeh").value = S.scenario.vehicles.length;
}

/* ------------------------------------------------------------------ map */
function svgPoint(evt) {
  const r = map.getBoundingClientRect();
  const x = ((evt.clientX - r.left) / r.width) * 1000;
  const y = ((evt.clientY - r.top) / r.height) * 1000;
  return { x: (x - PAD) / SPAN, y: (y - PAD) / SPAN };
}

function draw() {
  const sc = S.scenario;
  map.innerHTML = "";

  const g = el("g");
  for (let i = 0; i <= 10; i++) {
    const p = PAD + (i / 10) * SPAN;
    g.appendChild(el("line", { x1: p, y1: PAD, x2: p, y2: PAD + SPAN, stroke: "#EEF2F5", "stroke-width": 1 }));
    g.appendChild(el("line", { x1: PAD, y1: p, x2: PAD + SPAN, y2: p, stroke: "#EEF2F5", "stroke-width": 1 }));
  }
  g.appendChild(el("rect", { x: PAD, y: PAD, width: SPAN, height: SPAN, fill: "none", stroke: "#DBE3EA", "stroke-width": 1.5 }));
  map.appendChild(g);

  const plan = S.focus ? S.plans[S.focus] : null;
  const T = plan ? S.t * Math.max(plan.objective, 1e-9) : Infinity;
  const done = new Set();

  if (plan) {
    plan.routes.forEach((r, vi) => {
      const col = vehColour(vi);
      const pts = [];
      for (let i = 0; i < r.stops.length; i++) {
        const s = r.stops[i];
        if (s.arrive_time <= T) {
          pts.push([ux(s.x), uy(s.y)]);
          if (s.customer !== null) done.add(s.customer);
        } else {
          const prev = r.stops[i - 1];
          if (prev) {
            const span = s.arrive_time - prev.arrive_time;
            const f = span <= 0 ? 1 : (T - prev.arrive_time) / span;
            pts.push([ux(prev.x + (s.x - prev.x) * f), uy(prev.y + (s.y - prev.y) * f)]);
          }
          break;
        }
      }
      // full route, faint
      map.appendChild(el("polyline", {
        points: r.stops.map((s) => `${ux(s.x)},${uy(s.y)}`).join(" "),
        fill: "none", stroke: col, "stroke-width": 1.6, opacity: .18,
        "stroke-linejoin": "round",
      }));
      if (pts.length > 1) {
        map.appendChild(el("polyline", {
          points: pts.map((p) => p.join(",")).join(" "), fill: "none",
          stroke: col, "stroke-width": 2.6, "stroke-linejoin": "round",
          "stroke-linecap": "round", opacity: .95,
        }));
      }
      if (pts.length) {
        const [hx, hy] = pts[pts.length - 1];
        map.appendChild(el("circle", { cx: hx, cy: hy, r: 9, fill: col, stroke: "#fff", "stroke-width": 2.5 }));
        map.appendChild(el("text", {
          x: hx, y: hy + 3.6, "text-anchor": "middle", "font-size": 10,
          "font-weight": "700", fill: "#fff",
        })).textContent = String(vi + 1);
      }
    });
  }

  sc.customers.forEach((c, i) => {
    const r = 5 + Math.sqrt(Math.max(c.demand, 1)) * 2.4;
    const delivered = done.has(i);
    const node = el("circle", {
      cx: ux(c.x), cy: uy(c.y), r,
      fill: delivered ? "#1C7A4A" : "#9AA8B5",
      opacity: delivered ? .92 : .72,
      stroke: "#fff", "stroke-width": 1.5, cursor: "pointer",
    });
    node.addEventListener("click", (e) => {
      e.stopPropagation();
      S.scenario.customers.splice(i, 1); resetPlans(); draw();
    });
    const ttl = el("title");
    ttl.textContent = `order ${i + 1} · demand ${c.demand}`;
    node.appendChild(ttl);
    map.appendChild(node);
  });

  const d = sc.depot;
  const dep = el("rect", {
    x: ux(d.x) - 11, y: uy(d.y) - 11, width: 22, height: 22, rx: 4,
    fill: "#12304A", stroke: "#fff", "stroke-width": 2.5, cursor: "grab",
  });
  dep.appendChild(el("title")).textContent = "depot — drag to move";
  map.appendChild(dep);
  dep.addEventListener("pointerdown", (e) => {
    e.stopPropagation(); dep.setPointerCapture(e.pointerId);
    const move = (ev) => {
      const p = svgPoint(ev);
      d.x = Math.min(1, Math.max(0, p.x)); d.y = Math.min(1, Math.max(0, p.y));
      draw();
    };
    const up = () => {
      dep.removeEventListener("pointermove", move);
      dep.removeEventListener("pointerup", up);
      resetPlans(); draw();
    };
    dep.addEventListener("pointermove", move);
    dep.addEventListener("pointerup", up);
  });

  const legend = $("legendVeh");
  legend.innerHTML = sc.vehicles.map((v, i) =>
    `<span style="margin-right:9px"><i style="background:${vehColour(i)}"></i> van ${i + 1}</span>`).join("");
}

/* ----------------------------------------------------------------- solve */
async function plan() {
  if (!S.chosen.size) { msg("err", "Pick at least one planner."); return; }
  const btn = $("plan");
  btn.disabled = true; btn.textContent = "Planning…";
  document.body.classList.add("spin");
  try {
    const r = await fetch("/api/solve", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: S.scenario, methods: [...S.chosen] }),
    });
    const data = await r.json();
    if (!r.ok) { msg("err", data.error || "solve failed"); return; }
    S.plans = data.plans;
    const keys = Object.keys(S.plans);
    if (!keys.length) { msg("err", "No planner returned a result."); return; }
    S.focus = keys[0]; S.t = 1;
    renderResults(data);
    $("play").disabled = false; $("scrub").disabled = false;
    $("scrub").value = 1000;
    draw(); renderBars();
  } catch (e) {
    msg("err", String(e));
  } finally {
    btn.disabled = false; btn.textContent = "Plan routes";
    document.body.classList.remove("spin");
  }
}

function msg(kind, text) {
  $("msg").innerHTML = text ? `<div class="note ${kind}">${text}</div>` : "";
}

function renderResults(data) {
  const warn = (data.check && data.check.warnings) || [];
  const fails = Object.entries(data.failures || {});
  msg("warn", warn.length ? warn.join("<br>") : "");

  const keys = Object.keys(S.plans);
  const best = Math.min(...keys.map((k) => S.plans[k].objective));
  const ref = S.plans["parallel"] ? S.plans["parallel"].objective : null;

  let html = `<table><thead><tr>
      <th>Planner</th><th>Longest route</th><th>vs PARCO</th>
      <th>Total dist.</th><th>Passes</th><th>ms</th></tr></thead><tbody>`;
  for (const k of keys) {
    const p = S.plans[k];
    const meta = S.info.methods[k] || { label: k, colour: "#888" };
    const d = ref && k !== "parallel" ? ((p.objective - ref) / ref) * 100 : null;
    const dtxt = d === null ? "—"
      : `<span class="delta ${d < 0 ? "good" : "bad"}">${d > 0 ? "+" : ""}${d.toFixed(1)}%</span>`;
    const bad = !p.validity.ok
      ? ` <span title="${p.validity.missing.length} order(s) unserved">⚠</span>` : "";
    html += `<tr class="pick ${k === S.focus ? "sel" : ""} ${p.objective === best ? "best" : ""}" data-k="${k}">
      <td><span class="sw" style="background:${meta.colour}"></span>${meta.label}${bad}</td>
      <td>${fmt(p.objective)}</td><td>${dtxt}</td>
      <td>${fmt(p.total_distance, 2)}</td><td>${p.steps}</td><td>${Math.round(p.elapsed_ms)}</td></tr>`;
  }
  html += `</tbody></table>`;

  const notes = keys.filter((k) => S.plans[k].note).map((k) =>
    `${S.info.methods[k]?.label || k}: ${S.plans[k].note}`);
  if (notes.length) html += `<div class="note warn">${notes.join("<br>")}</div>`;
  if (fails.length) {
    html += `<div class="note err">` +
      fails.map(([k, e]) => `${k}: ${e}`).join("<br>") + `</div>`;
  }
  html += `<div class="note ok">Longest route = the objective the models minimise:
    max over vehicles of distance ÷ speed. Lower is better.</div>`;

  const box = $("results");
  box.innerHTML = html;
  box.querySelectorAll("tr.pick").forEach((tr) => {
    tr.addEventListener("click", () => {
      S.focus = tr.dataset.k; S.t = 1; $("scrub").value = 1000;
      box.querySelectorAll("tr.pick").forEach((o) => o.classList.toggle("sel", o === tr));
      draw(); renderBars(); updateClock();
    });
  });
  updateClock();
}

function renderBars() {
  const p = S.plans[S.focus];
  const host = $("perVehicle");
  if (!p) { host.innerHTML = ""; return; }
  const meta = S.info.methods[S.focus] || { label: S.focus };
  $("mapTitle").textContent = `— ${meta.label}`;
  const max = Math.max(p.objective, 1e-9);
  const slowest = p.routes.reduce((a, b) => (b.time > a.time ? b : a), p.routes[0]);
  host.innerHTML =
    `<h2 style="margin-top:14px">Per-vehicle — ${meta.label}</h2>` +
    p.routes.map((r, i) => `
      <div class="bar ${r === slowest ? "last" : ""}">
        <span class="lab">van ${i + 1} · ${r.served}</span>
        <span class="track"><span class="fill" style="width:${(r.time / max) * 100}%;background:${vehColour(i)}"></span></span>
        <span class="val">${fmt(r.time)}</span>
      </div>`).join("") +
    `<p class="maphint">Bar = time to finish (distance ÷ speed); the red value is the
     slowest van, which <em>is</em> the objective. “· n” is orders delivered.
     Trips: ${p.routes.map((r) => r.trips).join(" / ")}.</p>`;
}

/* ------------------------------------------------------------ animation */
function updateClock() {
  const p = S.plans[S.focus];
  if (!p) { $("clock").textContent = "—"; return; }
  $("clock").textContent = `${fmt(S.t * p.objective)} / ${fmt(p.objective)}`;
}

function stop() {
  S.playing = false;
  if (S.raf) cancelAnimationFrame(S.raf);
  S.raf = null;
  $("play").textContent = "▶ Play";
}

function play() {
  const p = S.plans[S.focus];
  if (!p) return;
  if (S.playing) { stop(); return; }
  if (S.t >= 1) S.t = 0;
  S.playing = true;
  $("play").textContent = "❚❚ Pause";
  let last = performance.now();
  const tick = (now) => {
    if (!S.playing) return;
    S.t = Math.min(1, S.t + (now - last) / 6000);   // ~6s for a full run
    last = now;
    $("scrub").value = Math.round(S.t * 1000);
    draw(); updateClock();
    if (S.t >= 1) { stop(); return; }
    S.raf = requestAnimationFrame(tick);
  };
  S.raf = requestAnimationFrame(tick);
}

/* ----------------------------------------------------------------- wire */
function wire() {
  $("gen").addEventListener("click", generate);
  $("reroll").addEventListener("click", () => {
    $("seed").value = Math.floor(Math.random() * 10000); generate();
  });
  $("clear").addEventListener("click", () => {
    S.scenario.customers = []; resetPlans(); draw();
  });
  $("addVeh").addEventListener("click", () => {
    S.scenario.vehicles.push({ capacity: 30, speed: 0.75 });
    resetPlans(); renderVehicles(); draw();
  });
  $("delVeh").addEventListener("click", () => {
    S.scenario.vehicles.pop(); resetPlans(); renderVehicles(); draw();
  });
  $("plan").addEventListener("click", plan);
  $("play").addEventListener("click", play);
  $("scrub").addEventListener("input", (e) => {
    stop(); S.t = +e.target.value / 1000; draw(); updateClock();
  });
  map.addEventListener("click", (e) => {
    const p = svgPoint(e);
    if (p.x < 0 || p.x > 1 || p.y < 0 || p.y > 1) return;
    S.scenario.customers.push({
      x: +p.x.toFixed(4), y: +p.y.toFixed(4),
      demand: 1 + Math.floor(Math.random() * 9),
    });
    $("nOrders").value = S.scenario.customers.length;
    resetPlans(); draw();
  });
}

boot();
