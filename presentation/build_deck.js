const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME_JS || "./apply_theme.js");

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
  s.addNotes("Countersign turns a plain-English business question into a working SQL query. NVIDIA Nemotron drafts it, Kimi K3 repairs it, and an analyst signs off. The headline: analysts answer 43% more questions at 30% lower cost per answer, and real column values in the prompt added up to 17 points of accuracy.");
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
  s.addNotes("The problem: business questions queue behind a small analyst team, and fully automatic AI is wrong about one time in three without saying which. Countersign: Nemotron drafts three queries with real column values in the prompt, a free check runs them on the database, Kimi K3 repairs disagreements, and the analyst signs off.");
}

// 3. Results
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
  s.addNotes("We scored everything on BIRD Mini-Dev: 500 real business questions over 11 real databases, each with a human-written answer query. An answer counts only if our query returns the same rows. The cascade, where Nemotron writes three drafts and Kimi K3 repairs them, reaches 75.7%, beating Kimi K3 alone at 68.0% and Nemotron alone at 43.4%; the gap over Kimi is statistically significant. Showing real column values in the prompt added 16 to 17 points to both models.");
}

// 4. Business value and differentiation
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

  txt(s, "Why this is different", { x: 7.7, y: 1.5, w: 5.0, h: 0.5, fontSize: 22, bold: true, color: C.accent2, fontFace: THEME.headFontFace });
  const diffs = [
    ["Measured, not demoed", "350 held-out questions, scored by running the SQL"],
    ["Built for review", "agreement does not signal correctness, so the analyst signs"],
    ["No lock-in", "open models on Fireworks; first-pass model swapped in one line"],
    ["Clear next gain", "a correct draft exists for 88% of questions; our best setup is right on 76%"],
  ];
  diffs.forEach(([head, sub], i) => {
    const y = 2.15 + i * 1.12;
    circle(s, 7.7, y + 0.05, 0.5, "✓", C.accent1, `diff ${i + 1}`);
    txt(s, head, { x: 8.4, y, w: 4.3, h: 0.38, fontSize: 17, bold: true, color: C.text1 });
    txt(s, sub, { x: 8.4, y: y + 0.4, w: 4.3, h: 0.6, fontSize: 14, color: C.text2, valign: "top" });
  });
  s.addNotes("The analyst still approves every answer, so accuracy stays at 100%. Reviewing a working draft is faster than writing from scratch: 21 minutes instead of 30, so the same analysts answer 43% more questions at 30% lower cost. Text-to-SQL is crowded; our edge is that we measured where it fails and built the workflow around review.");
}

// 5. Stack and next
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.addText("Built on NVIDIA and Fireworks", { placeholder: "title" });
  s.addText("github.com/shree6791/eval-harness", { placeholder: "body" });
  const cols = [
    ["NVIDIA Nemotron 3 Ultra", "Writes every first draft in ~2 s at under a cent; answers 53% of questions without escalation"],
    ["Fireworks serverless", "Both models behind one API, billed per token, no GPUs to manage; three drafts per question stay affordable"],
    ["What's next", "Pick the right draft (76% → 88%), cheaper repair, self-serve for routine questions, beyond SQL"],
  ];
  cols.forEach(([head, body], i) => {
    const x = 0.7 + i * 4.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.6, w: 3.8, h: 2.15, rectRadius: 0.12, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `stack card ${i + 1}` });
    txt(s, head, { x: x + 0.3, y: 3.85, w: 3.2, h: 0.5, fontSize: 19, bold: true, color: C.accent6 });
    txt(s, body, { x: x + 0.3, y: 4.45, w: 3.2, h: 1.2, fontSize: 15, color: C.background1, valign: "top" });
  });
  txt(s, "Team: Shreenidhi Sudhakar · Joseph Mikhail", { x: 0.7, y: 6.75, w: 11.9, h: 0.35, fontSize: 12, color: C.accent4 });
  s.addNotes("NVIDIA Nemotron 3 Ultra is the workhorse: every first draft, in about two seconds, at under a cent. Fireworks serverless makes three drafts per question affordable and let us swap models mid-event. Next: a selector to pick the right draft, since a correct one already exists for 88% of questions.");
}

(async () => {
  await pres.writeFile({ fileName: "Countersign.pptx" });
  await applyTheme("Countersign.pptx", THEME);
  console.log("written");
})();
