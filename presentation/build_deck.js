// Build: cd presentation && node build_deck.js  (needs pptxgenjs: npm install pptxgenjs)
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const THEME = {
  name: "Countersign (Roper palette)",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B2442", lt1: "FFFFFF", dk2: "4A5A70", lt2: "EEF2F7",
    accent1: "1D4779", accent2: "2F80C9", accent3: "1D4779", accent4: "94A3B8",
    accent5: "334155", accent6: "71EFFC", hlink: "2F80C9", folHlink: "1D4779",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Countersign";
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.2, w: 11.9, h: 1.2, fontSize: 54, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 2.45, w: 11.9, h: 0.8, fontSize: 22, color: C.accent6 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 34, bold: true, color: C.text1, valign: "middle", align: "left" }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent4 },
});

const txt = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, ...o });
const circle = (slide, x, y, d, label, fill, name) => {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name });
  txt(slide, label, { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: d > 0.6 ? 18 : 14, bold: true, color: C.background1 });
};
const card = (slide, x, y, w, h, name) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: name });

// 1. Title
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.addText("Countersign", { placeholder: "title" });
  s.addText("SQL drafted by NVIDIA Nemotron, signed off by analysts", { placeholder: "body" });
  txt(s, "Business questions answered in minutes. Analysts answer 43% more of them.", { x: 0.7, y: 3.45, w: 11.9, h: 0.6, fontSize: 20, color: C.background2, italic: true });
  const stats = [["+43%", "questions per analyst"], ["30%", "lower cost per answer"], ["+17 pts", "accuracy from real column values"]];
  stats.forEach(([big, small], i) => {
    const x = 0.7 + i * 4.1;
    txt(s, big, { x, y: 4.6, w: 3.8, h: 1.0, fontSize: 54, bold: true, color: C.accent6, fontFace: THEME.headFontFace });
    txt(s, small, { x, y: 5.6, w: 3.8, h: 0.5, fontSize: 16, color: C.background2 });
  });
  txt(s, "Evaluated on BIRD Mini-Dev (500 business questions, 11 real databases) · Fireworks, Microsoft and NVIDIA buildathon · San Francisco · 2 November 2026", { x: 0.7, y: 6.75, w: 11.9, h: 0.35, fontSize: 12, color: C.accent4 });
  s.addNotes("[Joseph] Hi, we're Joseph and Shree, and this is Countersign. A business user asks a question in plain English and gets a working SQL query back in seconds: drafted by NVIDIA Nemotron, repaired by Kimi K3, and signed off by an analyst.");
}

// 2. Problem and product
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Data waits on analysts; AI alone is not safe", { placeholder: "title" });
  card(s, 0.6, 1.5, 5.3, 5.2, "problem card");
  txt(s, "The problem", { x: 0.9, y: 1.75, w: 4.8, h: 0.5, fontSize: 22, bold: true, color: C.accent3, fontFace: THEME.headFontFace });
  txt(s, [
    { text: "Business users wait in an analyst queue; low-priority questions often go unanswered", options: { bullet: true, breakLine: true } },
    { text: "Analysts spend skilled hours on routine SQL instead of analysis", options: { bullet: true, breakLine: true } },
    { text: "The best single model is wrong on 1 question in 3, with no signal of which", options: { bullet: true } },
  ], { x: 0.9, y: 2.4, w: 4.8, h: 3.9, fontSize: 17, color: C.text1, paraSpaceAfter: 14, valign: "top" });

  txt(s, "What we built", { x: 6.4, y: 1.55, w: 6.3, h: 0.5, fontSize: 22, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  const steps = [
    ["NVIDIA Nemotron 3 Ultra writes 3 drafts", "in about 2 seconds"],
    ["Real column values in the prompt", "'M' vs 'Male', numbers stored as text"],
    ["Free check on the live database", "drafts that disagree or fail escalate"],
    ["Kimi K3 repairs", "sees all 3 drafts and what each returned"],
    ["Analyst signs off", "approves a working draft, not a blank page"],
  ];
  steps.forEach(([head, sub], i) => {
    const y = 2.2 + i * 0.9;
    circle(s, 6.4, y, 0.6, String(i + 1), i === 4 ? C.accent2 : C.accent1, `step ${i + 1}`);
    txt(s, head, { x: 7.2, y: y - 0.02, w: 5.5, h: 0.36, fontSize: 17, bold: true, color: C.text1 });
    txt(s, sub, { x: 7.2, y: y + 0.32, w: 5.5, h: 0.32, fontSize: 14, color: C.text2 });
  });
  s.addNotes("[Joseph] Today those questions wait days for an analyst. And AI alone isn't safe: the best model is wrong one time in three, without saying which. So Nemotron writes three drafts using real column values, we run them on the live database, and Kimi K3 repairs them.");
}

// 3. One question, start to finish (test question 346, from rows.pkl)
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Three drafts agreed. All three were wrong.", { placeholder: "title" });
  txt(s, [
    { text: "Test question 346: ", options: { color: C.text2 } },
    { text: "“How many superheroes have an alignment that is neither good nor bad?”", options: { bold: true, color: C.text1 } },
  ], { x: 0.6, y: 1.2, w: 12.1, h: 0.5, fontSize: 16 });

  const mono = { fontFace: "Consolas", fontSize: 13 };
  // Nemotron drafts
  card(s, 0.6, 1.95, 7.2, 2.65, "drafts card");
  txt(s, "NVIDIA Nemotron 3 Ultra: 3 drafts, all agree", { x: 0.9, y: 2.1, w: 6.7, h: 0.4, fontSize: 17, bold: true, color: C.text1 });
  txt(s, [
    { text: "SELECT COUNT(*) FROM superhero s", options: { breakLine: true } },
    { text: "JOIN alignment a ON s.alignment_id = a.id", options: { bold: true, color: C.accent2, breakLine: true } },
    { text: "WHERE a.alignment NOT IN ('Good', 'Bad')" },
  ], { x: 0.9, y: 2.6, w: 6.7, h: 1.05, color: C.text1, valign: "top", ...mono });
  txt(s, "Draft 1 → 28 ✗     Draft 2 → 28 ✗     Draft 3 → 28 ✗", { x: 0.9, y: 3.85, w: 6.7, h: 0.45, fontSize: 16, bold: true, color: C.text2 });
  // Kimi alone
  card(s, 0.6, 4.75, 7.2, 1.15, "kimi alone card");
  txt(s, "Kimi K3 on its own", { x: 0.9, y: 4.88, w: 6.7, h: 0.4, fontSize: 17, bold: true, color: C.text1 });
  txt(s, "Same inner join → 28 ✗  (drops 6 heroes with no alignment)", { x: 0.9, y: 5.3, w: 6.7, h: 0.45, fontSize: 15, color: C.text2 });
  // Arrow and repair
  s.addShape(pres.shapes.RIGHT_ARROW, { x: 7.88, y: 3.15, w: 0.42, h: 0.5, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: "arrow" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 1.95, w: 4.3, h: 3.95, rectRadius: 0.12, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: "repair card" });
  txt(s, "Kimi K3 repair", { x: 8.7, y: 2.1, w: 3.8, h: 0.4, fontSize: 19, bold: true, color: C.accent6 });
  txt(s, "sees all 3 drafts and what each returned", { x: 8.7, y: 2.5, w: 3.8, h: 0.35, fontSize: 14, color: C.background2 });
  txt(s, [
    { text: "SELECT COUNT(*) FROM superhero s", options: { breakLine: true } },
    { text: "LEFT JOIN alignment a", options: { bold: true, color: C.accent6, breakLine: true } },
    { text: "  ON s.alignment_id = a.id", options: { breakLine: true } },
    { text: "WHERE a.alignment IS NULL", options: { bold: true, color: C.accent6, breakLine: true } },
    { text: "  OR a.alignment NOT IN ('Good', 'Bad')" },
  ], { x: 8.7, y: 3.05, w: 3.85, h: 1.65, color: C.background1, valign: "top", fontFace: "Consolas", fontSize: 12 });
  txt(s, "→ 34 ✓ correct", { x: 8.7, y: 4.9, w: 3.8, h: 0.75, fontSize: 36, bold: true, color: C.accent6, fontFace: THEME.headFontFace });

  txt(s, "Agreement is not proof: when all three drafts agree (53% of test questions), they are right only 53% of the time. That is why the analyst signs off.", { x: 0.6, y: 6.15, w: 12.1, h: 0.7, fontSize: 17, bold: true, color: C.accent1, valign: "middle" });
  s.addNotes("[Joseph] Here's a real test question: how many superheroes are neither good nor bad? All three drafts agree: 28. Kimi on its own: also 28. All wrong, because the join silently drops six heroes. Shown the three drafts, Kimi switches to a left join and gets 34, the right answer. Agreement isn't proof, so an analyst always signs off. Shree?");
}

// 4. Results
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Cascade wins: 75.7% vs 68.0% for Kimi K3 alone", { placeholder: "title" });
  txt(s, "Benchmark: BIRD Mini-Dev, 500 real business questions over 11 real databases, each with a human-written answer query. Scored by running both queries; no AI grader.", { x: 0.6, y: 1.2, w: 12.1, h: 0.5, fontSize: 14, color: C.text2 });
  s.addChart(pres.charts.BAR, [
    { name: "Accuracy", labels: ["Nemotron 3 Ultra alone\n$2.54 per 1k", "Kimi K3 alone\n$32.41 per 1k", "Cascade: Nemotron x3\n+ Kimi repair\n$98.58 per 1k"], values: [43.4, 68.0, 75.7] },
  ], {
    x: 0.6, y: 1.8, w: 6.9, h: 4.75, barDir: "col", barGapWidthPct: 50,
    chartColors: [HEX.accent4, HEX.accent4, HEX.accent1],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0\"%\"", dataLabelFontSize: 16, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    showTitle: true, title: "Accuracy on 350 held-out test questions", titleFontSize: 16, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 90, valAxisHidden: true, valGridLine: { style: "none" },
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", catGridLine: { style: "none" },
    showLegend: false,
  });
  card(s, 7.9, 1.85, 4.8, 2.25, "column values card");
  txt(s, "+16–17 pts", { x: 8.2, y: 2.0, w: 4.3, h: 0.9, fontSize: 44, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  txt(s, "from real column values in the prompt: Nemotron 28.1% → 43.8%, Kimi K3 50.3% → 67.5% (same 320 questions)", { x: 8.2, y: 2.9, w: 4.3, h: 1.1, fontSize: 15, color: C.text1, valign: "top" });
  card(s, 7.9, 4.3, 4.8, 2.25, "repair card");
  txt(s, "+7.7 pts", { x: 8.2, y: 4.45, w: 4.3, h: 0.9, fontSize: 44, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
  txt(s, "cascade over Kimi K3 alone, statistically significant (p = 0.006), at three times the cost", { x: 8.2, y: 5.35, w: 4.3, h: 1.1, fontSize: 15, color: C.text1, valign: "top" });
  txt(s, "τ chosen on 150 separate questions, reported on the other 350. This question file is mostly the hardest tier, so scores are not comparable to the public BIRD leaderboard.", { x: 0.6, y: 6.7, w: 12.1, h: 0.4, fontSize: 11, color: C.text2 });
  s.addNotes("[Shree] Thanks. We didn't just demo this, we measured it. BIRD Mini-Dev: 500 real business questions over 11 databases, each with a human-written answer. An answer counts only if our query returns the same rows, so no AI grades AI. We tuned on 150 questions and report on the other 350. The cascade reaches 75.7%, versus 68% for Kimi alone, a statistically significant gap. Just showing the models real column values added 16 to 17 points.");
}

// 5. Business value, stack and next
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("43% more capacity, no one replaced", { placeholder: "title" });
  s.addTable([
    [
      { text: "Per question", options: { bold: true, color: C.background1, fill: { color: C.text1 } } },
      { text: "Analyst today", options: { bold: true, color: C.background1, fill: { color: C.text1 } } },
      { text: "Countersign + review", options: { bold: true, color: C.background1, fill: { color: C.accent2 } } },
    ],
    ["Time to answer", "Days in a queue", { text: "Seconds to draft, minutes to approve", options: { bold: true } }],
    ["Analyst time", "30 min", { text: "21 min (+43% capacity)", options: { bold: true } }],
    ["Accuracy", "100%", "100% (every answer reviewed)"],
    ["Cost", "$31.04", { text: "$21.75 (30% lower)", options: { bold: true } }],
  ], { x: 0.6, y: 1.55, w: 6.6, colW: [1.7, 2.0, 2.9], fontSize: 15, color: C.text1, border: { type: "solid", pt: 0.75, color: HEX.lt2 }, rowH: 0.62, valign: "middle", margin: 0.08 });
  txt(s, "Analyst at $62.07/h (BLS, San Jose metro, May 2025). Assumed: 30 min to write, 10 min to review.", { x: 0.6, y: 4.85, w: 6.6, h: 0.5, fontSize: 11, color: C.text2 });

  txt(s, "Built on NVIDIA and Fireworks", { x: 7.7, y: 1.5, w: 5.0, h: 0.5, fontSize: 22, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  const items = [
    ["NVIDIA Nemotron 3 Ultra", "every first draft in ~2 s, under a cent"],
    ["Fireworks serverless", "both models, one API; we swapped models with one line"],
    ["Next: get to 88% accurate", "the right answer is already among our drafts 88% of the time; we need to choose it better"],
  ];
  items.forEach(([head, sub], i) => {
    const y = 2.15 + i * 1.12;
    circle(s, 7.7, y + 0.05, 0.5, String(i + 1), C.accent1, `item ${i + 1}`);
    txt(s, head, { x: 8.4, y, w: 4.3, h: 0.38, fontSize: 17, bold: true, color: C.text1 });
    txt(s, sub, { x: 8.4, y: y + 0.4, w: 4.3, h: 0.6, fontSize: 14, color: C.text2, valign: "top" });
  });
  txt(s, "github.com/shree6791/eval-harness · Team: Shreenidhi Sudhakar · Joseph Mikhail", { x: 0.6, y: 6.6, w: 11.5, h: 0.35, fontSize: 13, color: C.text2 });
  s.addNotes("[Shree] For the business: analysts still approve every answer, but reviewing a draft takes 21 minutes instead of 30. Same team, 43% more questions, 30% lower cost, and no one replaced. It runs on NVIDIA Nemotron and Fireworks serverless, and next, we get to 88% accuracy: the right answer is already among our drafts 88% of the time, so we just need to get better at choosing it. Thank you.");
}

(async () => {
  await pres.writeFile({ fileName: "Countersign.pptx" });
  await applyTheme("Countersign.pptx", THEME);
  console.log("written");
})();
