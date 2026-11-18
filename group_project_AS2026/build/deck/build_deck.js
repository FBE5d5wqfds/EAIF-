// Group_8 presentation deck (EAIF AS 2026): title + 6 content slides, BFH style.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/Users/fabianbeyeler/.claude/skills/synced/72e0f0bc-bd6d-4d5c-85f4-100b87101c0c_c3fc9ac8-8e12-4e60-b8e4-7a12ea297474/pptx/scripts/apply_theme.js");

const OUT = process.argv[2];
const LOGO = "/Users/fabianbeyeler/Documents/Git/EAIF-/group_project_AS2026/build/assets/bfh_logo.png";
const HERE = __dirname;

const THEME = {
  name: "Group_8 BFH",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2A33", lt1: "FFFFFF", dk2: "697D91", lt2: "EEF2F4",
    accent1: "697D91", accent2: "FAC300", accent3: "1F2A33", accent4: "C9D1D6", accent5: "9AA9B8", accent6: "FFF3CC",
    hlink: "697D91", folHlink: "697D91",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Can ESG scores and machine learning earn an investor a premium?";
pres.author = "Group_8";
pres.subject = "EAIF Group Assignment AS 2026";
const C = pres.SchemeColor;

const CITE = "Data: Simulated ESG and stock-return dataset, EAIF course, Autumn Semester 2026, CC BY 4.0 (github.com/umatter/EDFB/tree/main/data/esg2026). All data are simulated.  |  Group_8";
const W = 13.333, MX = 0.6;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "G8_DARK",
  background: { color: HEX.dk1 },
  objects: [
    { image: { x: W - MX - 1.15, y: 0.4, w: 1.15, h: 1.15 * 286 / 401, path: path.join(HERE, "bfh_logo_white.png"), altText: "BFH logo" } },
    { text: { text: CITE, options: { x: MX, y: 6.95, w: W - 2 * MX, h: 0.3, fontSize: 9, color: C.accent4, margin: 0 } } },
  ],
});
pres.defineSlideMaster({
  title: "G8_CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { image: { x: W - MX - 0.8, y: 0.32, w: 0.8, h: 0.8 * 286 / 401, path: LOGO, altText: "BFH logo" } },
    { placeholder: { options: { name: "title", type: "title", x: MX + 1.0, y: 0.35, w: W - 2 * MX - 2.1, h: 0.95, fontSize: 28, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: CITE, options: { x: MX, y: 7.0, w: W - 2 * MX - 0.6, h: 0.28, fontSize: 9, color: C.text2, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.5, y: 7.0, w: 0.5, h: 0.28, fontSize: 9, color: C.text2, align: "right" },
});

// ---------------------------------------------------------------- helpers
function circleNum(slide, n, x, y, d = 0.42) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.accent2 }, line: { type: "none" }, objectName: `num-${n}` });
  slide.addText(String(n), { x, y, w: d, h: d, fontSize: 15, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function card(slide, name, x, y, w, h, fill = C.background2) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" }, objectName: name });
}
function statCard(slide, name, x, y, w, h, big, label, opts = {}) {
  card(slide, name, x, y, w, h, opts.fill || C.background2);
  slide.addText(big, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: opts.bigH || 0.62, fontSize: opts.bigSize || 30, bold: true, color: opts.bigColor || C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: name + "-big" });
  slide.addText(label, { x: x + 0.2, y: y + 0.12 + (opts.bigH || 0.62) + 0.04, w: w - 0.4, h: h - (opts.bigH || 0.62) - 0.3, fontSize: opts.labelSize || 13, color: opts.labelColor || C.text1, margin: 0, valign: "top", isTextBox: true, objectName: name + "-label" });
}
function badge(slide, n) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 0.53, w: 0.78, h: 0.6, rectRadius: 0.08, fill: { color: C.text1 }, line: { type: "none" }, objectName: "section-badge" });
  slide.addText(String(n).padStart(2, "0"), { x: MX, y: 0.53, w: 0.78, h: 0.6, fontSize: 22, bold: true, color: C.accent2, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "section-badge-text" });
}
const DK = { fill: C.text1, bigColor: C.accent2, labelColor: C.background1 };
const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 } } });
function tableRows(header, rows, { highlight = -1, boldFirst = false } = {}) {
  return [header.map(hdr), ...rows.map((r, i) => r.map((c, j) => ({
    text: c,
    options: {
      fill: { color: i === highlight ? C.accent6 : (i % 2 === 1 ? C.background2 : C.background1) },
      bold: (boldFirst && j === 0) || i === highlight && j === 0,
      color: C.text1,
    },
  })))];
}

// ---------------------------------------------------------------- slide 1: title
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "G8_DARK", sectionTitle: "Introduction" });
s.addText("EAIF: AI for Finance  |  Group assignment, Autumn Semester 2026", { x: MX, y: 1.35, w: 9.5, h: 0.4, fontSize: 16, color: C.accent2, margin: 0, isTextBox: true });
s.addText("Can ESG scores and machine learning earn an investor a premium?", { x: MX, y: 1.85, w: 10.2, h: 1.9, fontSize: 44, bold: true, color: C.background1, margin: 0, valign: "top", isTextBox: true, objectName: "deck-title" });
s.addText([
  { text: "Group_8", options: { bold: true, breakLine: true } },
  { text: "Beyeler Fabian, Lussi Laurin, Griessen Jan", options: { breakLine: true } },
  { text: "Presentation, 8 December 2026", options: { color: C.accent4 } },
], { x: MX, y: 3.95, w: 7.0, h: 1.2, fontSize: 18, color: C.background1, margin: 0, valign: "top", isTextBox: true });
card(s, "answer-card", MX, 5.35, W - 2 * MX, 1.2, C.accent2);
s.addText([
  { text: "Our answer: ", options: { bold: true, color: C.text1 } },
  { text: "the data had seven problems, no model beat the naive forecast, the Environmental score was associated with higher returns than industry peers only in Europe from 2021 (plausible, not proven), and the backtest edge cannot be told apart from noise. We would not allocate on this evidence.", options: { color: C.text1 } },
], { x: MX + 0.3, y: 5.45, w: W - 2 * MX - 0.6, h: 1.0, fontSize: 17, margin: 0, valign: "middle", isTextBox: true });
s.addNotes(
  "About 25 seconds. We are Group 8. Our question: can ESG scores, or forecasts built on them, earn an investor a premium, and can the data be trusted for that purpose? " +
  "The short answer is on the slide: we would not allocate on this evidence. The next slides show why."
);

// ---------------------------------------------------------------- slide 2: question and data
pres.addSection({ title: "Question and data" });
s = pres.addSlide({ masterName: "G8_CONTENT", sectionTitle: "Question and data" });
s.addText("Four questions, tested on a simulated panel of 1,376 firms", { placeholder: "title" });
badge(s, 1);
const qs = [
  ["Can the data be trusted?", "Audit of all five files"],
  ["Can a model forecast 12-month returns better than the average?", "Linear regression vs tree ensembles"],
  ["Where, if anywhere, was the Environmental score associated with higher returns?", "By region and period"],
  ["Does a rule with costs and an ESG floor beat an equal-weight benchmark?", "Backtest, formation years 2018 to 2024 (July 2018 to June 2025)"],
];
qs.forEach(([q, sub], i) => {
  const y = 1.6 + i * 1.28;
  circleNum(s, i + 1, MX, y + 0.05);
  s.addText([
    { text: q, options: { bold: true, breakLine: true } },
    { text: sub, options: { color: C.text2, fontSize: 14 } },
  ], { x: MX + 0.6, y, w: 6.3, h: 1.1, fontSize: 17, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: `question-${i + 1}` });
});
const sx = 7.75, sw = 2.35, sh = 2.45, gap = 0.3;
statCard(s, "stat-firms", sx, 1.6, sw, sh, "1,376", "firms, fiscal years 2012 to 2025; 389 leave before 2025");
statCard(s, "stat-months", sx + sw + gap, 1.6, sw, sh, "171,764", "monthly stock returns (firm-months)");
statCard(s, "stat-files", sx, 1.6 + sh + gap, sw, sh, "5 files", "firm-year panel, restated ESG scores, monthly returns, factors, current universe");
statCard(s, "stat-sim", sx + sw + gap, 1.6 + sh + gap, sw, sh, "Simulated", "no real firms: the exercise tests our method, not the market", DK);
s.addNotes(
  "About 55 seconds. We asked four questions: can the data be trusted, can a model forecast twelve-month returns better than the average, " +
  "where (if anywhere) was the Environmental score associated with higher returns, and does a trading rule with costs and an ESG floor beat an equal-weight benchmark. " +
  "The data is simulated by the course: 1,376 firms over fiscal years 2012 to 2025, five files, about 172,000 monthly returns. " +
  "Because it is simulated, the exercise tests our method, not how ESG behaves in real markets. The dataset is cited at the bottom of every slide with its CC BY 4.0 licence."
);

// ---------------------------------------------------------------- slide 3: audit and pipeline
pres.addSection({ title: "Audit and pipeline" });
s = pres.addSlide({ masterName: "G8_CONTENT", sectionTitle: "Audit and pipeline" });
s.addText("Seven data problems: one would have faked an edge", { placeholder: "title" });
badge(s, 2);
const audit = [
  ["Revenue and market cap about 1,000x too large (28 firms)", "Carbon, water, energy out of line with revenue", "Divide by 1,000", "Mean market cap 213,205 to 14,108 USD m"],
  ["300 company-months duplicated", "Repeated firm-month keys", "Keep first row", "Firm-years with 12 months 9,002 to 9,182"],
  ["Analyst_Outlook behaves as if it contains next year's return", "Rank correlation 0.68 with the next 12 months, about 0 with earlier ones", "Excluded from all models", "Random forest test RMSE 37.59 without it, 29.14 with it (naive 37.20)"],
  ["Universe file lists survivors only (987 of 1,376)", "File sizes; 389 firms end before 2025", "Full panel, exits held to last month", "Equal-weight benchmark 4.62% (full panel) vs 5.18% (survivors) a year, 2015 to 2025"],
  ["Restated scores behave as if they contain hindsight", "Both score files compared with later returns", "Point-in-time scores only", "Rank correlation with next excess return: 0.010 point-in-time vs 0.056 restated"],
  ["Environmental metrics missing (13.2%), not at random", "Mean score 47.2 if missing vs 56.5; Europe 6.3% vs 13-19%", "Keep rows, fill plus missing flag", "Linear test RMSE 38.10 to 38.05 without carbon features"],
  ["Scores at exactly 0 or 100 (213 rows); 8 returns of -95%", "Counts at the bounds", "Keep and document", "Linear test RMSE 38.10 to 38.00 without the 94 training rows at 0 or 100"],
];
s.addTable(tableRows(["Problem", "How found", "Treatment", "Effect on one headline number"], audit, { highlight: 2 }), {
  x: MX, y: 1.45, w: W - 2 * MX, colW: [3.45, 3.25, 2.1, 3.33], fontSize: 12, rowH: 0.36, margin: [0.03, 0.08, 0.03, 0.08],
  border: { type: "solid", pt: 0.5, color: HEX.accent4 }, valign: "middle", objectName: "audit-table",
});
// pipeline strip
const steps = [
  ["Fiscal-year report", "published 31 Mar to 31 May"],
  ["Portfolio formed", "1 July (formation year)"],
  ["Held July to June", "target: 12-month return"],
];
const py = 5.55, pw = 2.75, ph = 1.05;
steps.forEach(([a, b], i) => {
  const x = MX + i * (pw + 0.35);
  card(s, `pipe-${i + 1}`, x, py, pw, ph, i === 1 ? C.text1 : C.background2);
  s.addText([{ text: a, options: { bold: true, breakLine: true } }, { text: b }], {
    x: x + 0.15, y: py, w: pw - 0.3, h: ph, fontSize: 14, color: i === 1 ? C.background1 : C.text1, margin: 0, valign: "middle", isTextBox: true,
  });
  if (i < 2) s.addShape(pres.shapes.CHEVRON, { x: x + pw + 0.09, y: py + ph / 2 - 0.15, w: 0.17, h: 0.3, fill: { color: C.accent5 }, line: { type: "none" }, objectName: `arrow-${i + 1}` });
});
s.addText([
  { text: "Split by formation year: ", options: { bold: true } }, { text: "train 2015 to 2021, test 2022 to 2024, never used to choose anything.", options: { breakLine: true } },
  { text: "30 features, ", options: { bold: true } }, { text: "6 of them new, each dated; a code check rejects anything published after 1 July.", options: { breakLine: true } },
  { text: "Cross-validation ", options: { bold: true } }, { text: "in 5 folds grouped by company, inside the training years." },
], { x: MX + 3 * (pw + 0.35) - 0.1, y: py - 0.05, w: W - MX - (MX + 3 * (pw + 0.35) - 0.1), h: ph + 0.15, fontSize: 12, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "pipeline-text" });
s.addNotes(
  "About 1 minute 30. Before any model we audited all five files and found seven problems. Each effect is measured one problem at a time, so they do not add up. " +
  "The most dangerous one is highlighted: the column Analyst_Outlook has a rank correlation of 0.68 with the next twelve-month return and about zero with earlier windows, " +
  "so it behaves as if it contains next year's return. A simple random forest using it cuts the test error from 37.6 to 29.1, but no investor had it on 1 July, so we excluded it. " +
  "Other problems: 28 firms report revenue and market cap in the wrong unit (we divided by 1,000), 300 duplicated return months, a universe file with survivors only (we used the full panel), " +
  "and restated scores that behave as if they contain hindsight (we used the point-in-time scores). " +
  "Pipeline: the fiscal-year report is published by 31 May, the portfolio is formed on 1 July and held to June. We train on formation years 2015 to 2021 and test on 2022 to 2024; the test years never choose anything, and the audit uses them only to measure the size of an effect. " +
  "BACKUP, only if asked (do not read): there are exactly eight returns of -95%, none in a firm's last month, so they are not delisting returns; in the raw file nothing lies below -95%. We cannot tell them from real returns, so we kept and documented them. They are 8 of about 172,000 monthly returns."
);

// ---------------------------------------------------------------- slide 4: models
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "G8_CONTENT", sectionTitle: "Results" });
s.addText("No model beats the naive forecast out of sample", { placeholder: "title" });
badge(s, 3);
const models = ["Naive mean (baseline)", "Linear regression (selected on CV)", "Random forest (tuned)", "Gradient boosting (tuned)"];
s.addChart(pres.charts.BAR, [
  { name: "Train RMSE", labels: models, values: [29.16, 28.73, 28.11, 28.28] },
  { name: "Cross-validation RMSE", labels: models, values: [29.16, 28.88, 28.92, 28.90] },
  { name: "Test RMSE (2022-2024)", labels: models, values: [37.20, 38.10, 37.93, 37.84] },
], {
  x: MX, y: 1.45, w: 7.6, h: 5.35, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
  chartColors: [HEX.accent4, HEX.dk2, HEX.dk1],
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.dk1, dataLabelFormatCode: "0.0",
  catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.dk1,
  valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.dk2, valAxisMinVal: 0, valAxisMaxVal: 45, valAxisMajorUnit: 10,
  showValAxisTitle: true, valAxisTitle: "RMSE, percentage points of 12-month return", valAxisTitleFontSize: 11, valAxisTitleFontFace: "+mn-lt", valAxisTitleColor: HEX.dk2,
  showCatAxisTitle: true, catAxisTitle: "Model", catAxisTitleFontSize: 11, catAxisTitleFontFace: "+mn-lt", catAxisTitleColor: HEX.dk2,
  valGridLine: { color: HEX.accent4, size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "t", legendFontSize: 11, legendFontFace: "+mn-lt", legendColor: HEX.dk1,
  showTitle: false, objectName: "model-chart", altText: "Train, cross-validation and test RMSE of four models",
});
const rx = 8.6, rw = W - MX - rx;
statCard(s, "stat-tie", rx, 1.45, rw, 1.45, "Tie: 0.05", "RMSE points separate the three models in CV (fold-to-fold SD 0.32); the best model changes from fold to fold", { ...DK, bigSize: 28, bigH: 0.5 });
statCard(s, "stat-boom", rx, 3.05, rw, 1.45, "+21.6% vs +0.9%", "mean 12-month return, test vs training years; a naive forecast that knew each test year's mean scores 30.9, not 37.2", { bigSize: 26, bigH: 0.5 });
statCard(s, "stat-ic", rx, 4.65, rw, 1.45, "-0.02", "rank correlation of forecast and outcome in the test years (+0.07, -0.05, -0.09 by year): no stable ranking skill", { bigSize: 26, bigH: 0.5 });
s.addText("The extra complexity of the ensembles does not pay off out of sample.", { x: rx, y: 6.2, w: rw, h: 0.6, fontSize: 14, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "model-verdict" });
s.addNotes(
  "About 1 minute 10. We compared linear regression with a tuned random forest and tuned gradient boosting, every model next to the naive forecast, which predicts the training average for every firm. " +
  "The ensembles were tuned by company-grouped cross-validation inside 2015 to 2021; linear regression has nothing to tune. Cross-validation selects linear regression, but the three models are within 0.05 points: a tie. " +
  "On the test years, 2022 to 2024, no model beats the naive forecast: 37.2 for the baseline against 37.8 to 38.1. " +
  "Why is the test error so much higher than in cross-validation? Mainly because the test years were strong: a mean twelve-month return of 21.6% against 0.9% in training. " +
  "And the forecasts do not rank firms either: the rank correlation is about minus 0.02 and changes sign across years. So the extra complexity of the ensembles does not pay off."
);

// ---------------------------------------------------------------- slide 5: ESG
s = pres.addSlide({ masterName: "G8_CONTENT", sectionTitle: "Results" });
s.addText("Environmental score: only Europe from 2021 stands out", { placeholder: "title" });
badge(s, 4);
const regions = ["Africa", "Asia", "Europe", "Latin America", "Middle East", "North America", "Oceania"];
s.addChart(pres.charts.BAR, [
  { name: "Formation years before 2021", labels: regions, values: [-0.07, 0.15, 0.47, -1.19, -0.92, -0.40, -0.24] },
  { name: "Formation years from 2021", labels: regions, values: [0.75, 0.39, 3.08, -2.94, 0.28, -0.61, -0.80] },
], {
  x: MX, y: 1.45, w: 7.6, h: 4.85, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 50,
  chartColors: [HEX.accent4, HEX.dk2],
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.dk1, dataLabelFormatCode: "+0.00;-0.00",
  catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.dk1, catAxisOrientation: "maxMin", catAxisLabelPos: "low",
  valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.dk2, valAxisMinVal: -4, valAxisMaxVal: 4, valAxisMajorUnit: 1,
  showValAxisTitle: true, valAxisTitle: "Percentage points of 12-month excess return per 1 SD (about 17 score points) of the Environmental score", valAxisTitleFontSize: 10, valAxisTitleFontFace: "+mn-lt", valAxisTitleColor: HEX.dk2,
  valGridLine: { color: HEX.accent4, size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "t", legendFontSize: 11, legendFontFace: "+mn-lt", legendColor: HEX.dk1,
  objectName: "esg-chart", altText: "Point-in-time estimates by region and period",
});
s.addText("Point-in-time scores; peers = same industry and year; errors clustered by firm. 95% intervals are not adjusted for the 14 cells; only Europe from 2021 stays significant after the Holm correction.", {
  x: MX, y: 6.32, w: 7.6, h: 0.55, fontSize: 11, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "esg-caption",
});
s.addText("95% CI +1.2 to +5.0 (excludes 0)", { x: 1.95, y: 3.72, w: 2.85, h: 0.3, fontSize: 11, bold: true, color: C.text1, align: "right", valign: "middle", margin: 0, isTextBox: true, objectName: "ci-europe" });
s.addText("95% CI -6.2 to +0.3 (includes 0)", { x: 5.05, y: 4.25, w: 3.0, h: 0.3, fontSize: 11, color: C.text2, align: "left", valign: "middle", margin: 0, isTextBox: true, objectName: "ci-latam" });
statCard(s, "stat-eu", rx, 1.45, rw, 1.45, "+3.1 pp", "12-month excess return vs industry peers per +1 SD of the score, Europe from 2021; 95% interval 1.2 to 5.0", { ...DK, bigSize: 28, bigH: 0.5 });
statCard(s, "stat-p", rx, 3.05, rw, 1.45, "p = 0.018, but 0.09", "0.018 after Holm for 14 cells, firm-clustered errors; 0.09 with the 4 years as the unit, not Holm-corrected: plausible, not proven", { bigSize: 26, bigH: 0.5 });
statCard(s, "stat-restated", rx, 4.65, rw, 1.45, "+4.88 restated", "restated scores look stronger: they behave as if they contain hindsight; investors only had the point-in-time score", { bigSize: 26, bigH: 0.5 });
s.addText("An association found after looking at 14 cells, not a return shown to be tradable after costs.", { x: rx, y: 6.2, w: rw, h: 0.6, fontSize: 14, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "esg-verdict" });
s.addNotes(
  "About 1 minute 20. We related the previous fiscal year's Environmental score, standardised within year, to the next twelve months' excess return, region by region, before and from 2021, " +
  "always comparing a firm with industry peers of the same year. Pooled over all regions, nothing is distinguishable from zero. Region by region, exactly one cell stands out: Europe from 2021, " +
  "about plus 3.1 percentage points per standard deviation of the score, which is about 17 score points. The second-longest bar, Latin America from 2021, is not distinguishable from zero: its interval runs from minus 6.2 to plus 0.3. After the Holm correction for the 14 cells it is still significant, p = 0.018. " +
  "But that p-value treats firms as independent; with the four formation years as the unit the p-value is about 0.09, before any correction for the fourteen cells, and the cell was singled out after looking at all fourteen. So: plausible, not proven, and an association rather than a tradable return. " +
  "The restated scores give higher estimates everywhere, 4.88 for Europe, because what the restatement added correlates with later returns: they behave as if they contain hindsight."
);

// ---------------------------------------------------------------- slide 6: backtest
s = pres.addSlide({ masterName: "G8_CONTENT", sectionTitle: "Results" });
s.addText("A backtest with an ESG floor shows no edge that beats noise", { placeholder: "title" });
badge(s, 5);
const csv = fs.readFileSync(path.join(HERE, "series.csv"), "utf8").trim().split("\n").map((l) => l.split(","));
const months = csv.slice(1).map((r) => r[0]);
const cum = (j) => { let v = 1; return csv.slice(1).map((r) => (v *= 1 + parseFloat(r[j]) / 100)); };
const mlab = months.map((m) => { const [y, mm] = m.split("-"); return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][parseInt(mm, 10) - 1] + " " + y; });
s.addChart(pres.charts.LINE, [
  { name: "Linear regression, no floor", labels: mlab, values: cum(1) },
  { name: "Floor 50th percentile", labels: mlab, values: cum(2) },
  { name: "Floor 80th percentile", labels: mlab, values: cum(3) },
  { name: "Equal-weight benchmark (no cost)", labels: mlab, values: cum(4) },
], {
  x: MX, y: 1.45, w: 7.0, h: 5.35, lineSize: 2, lineDataSymbol: "none",
  chartColors: [HEX.dk2, HEX.accent5, "D9A400", HEX.dk1],
  catAxisLabelFrequency: 12, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.dk1, catAxisLabelRotate: 0,
  valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: HEX.dk2, valAxisMinVal: 0.8, valAxisMaxVal: 2.2, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "0.0",
  showValAxisTitle: true, valAxisTitle: "Value of 1 invested in July 2018 (rules after costs)", valAxisTitleFontSize: 11, valAxisTitleFontFace: "+mn-lt", valAxisTitleColor: HEX.dk2,
  showCatAxisTitle: true, catAxisTitle: "Month (formation years 2018 to 2024, held July to June)", catAxisTitleFontSize: 11, catAxisTitleFontFace: "+mn-lt", catAxisTitleColor: HEX.dk2,
  valGridLine: { color: HEX.accent4, size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "t", legendFontSize: 11, legendFontFace: "+mn-lt", legendColor: HEX.dk1,
  objectName: "backtest-chart", altText: "Cumulative value of the three rules and the benchmark",
});
const bx = 7.95, bw = W - MX - bx;
s.addTable(tableRows(["Rule (84 months)", "Return % a year", "Sharpe", "Turnover", "Names"], [
  ["No floor", "9.39", "0.457", "0.70", "94"],
  ["Floor 50th pct", "9.59", "0.464", "0.76", "47"],
  ["Floor 80th pct", "11.39", "0.533", "0.82", "19"],
  ["Benchmark (no cost)", "8.77", "0.419", "0.17", "945"],
], { boldFirst: true }), {
  x: bx, y: 1.45, w: bw, colW: [1.55, 0.98, 0.75, 0.82, 0.68], fontSize: 12, rowH: 0.36, margin: [0.03, 0.06, 0.03, 0.06],
  border: { type: "solid", pt: 0.5, color: HEX.accent4 }, valign: "middle", objectName: "backtest-table",
});
statCard(s, "stat-sharpe", bx, 3.45, bw, 1.45, "+0.11 Sharpe", "best rule vs benchmark; 95% bootstrap interval -0.16 to +0.38 (84 months resampled 5,000 times)", { ...DK, bigSize: 28, bigH: 0.5 });
statCard(s, "stat-floor", bx, 5.05, bw, 1.75, "Floor: no return cost", "It cost concentration (19 vs 94 names), volatility (18.4% vs 16.8%) and turnover (0.82 vs 0.70). All firms above the 80th percentile earn 8.9% (benchmark 8.8%); without formation year 2022 every rule trails the benchmark.", { bigSize: 26, bigH: 0.5, labelSize: 12 });
s.addNotes(
  "About 1 minute 20. Each 1 July we ranked firms on the linear-regression forecast, refitted every year on earlier years only, held the top decile for twelve months, " +
  "charged 20 basis points per unit of one-way turnover, and used the full panel including firms that left. Formation years 2018 to 2024, 84 months; 2025 has only six months of returns and is left out. " +
  "The ESG floor restricts the pool to firms at or above the 50th or 80th percentile of the Environmental score. " +
  "In this sample the floor did not cost return; it cost concentration, 19 names at the 80th percentile, and trading. But the gain is not from the floor itself: holding every firm above the 80th percentile earns 8.9%, about the benchmark, " +
  "and without formation year 2022 every rule trails the benchmark. The best rule's Sharpe advantage, plus 0.11, has a 95% bootstrap interval from minus 0.16 to plus 0.38: not distinguishable from noise. " +
  "And 11 to 19% of random selections of the same size do at least as well as our rules."
);

// ---------------------------------------------------------------- slide 7: real data
pres.addSection({ title: "Real data and recommendation" });
s = pres.addSlide({ masterName: "G8_CONTENT", sectionTitle: "Real data and recommendation" });
s.addText("What would change with real data", { placeholder: "title" });
badge(s, 6);
s.addText("Still to solve after an audit like ours", { x: MX, y: 1.4, w: 5.6, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
const issues = [
  ["Raters disagree", "Six major raters correlate only 0.38 to 0.71, average 0.54 (Berg, Kölbel and Rigobon, 2022); we had one score"],
  ["Point-in-time history", "Vendors rewrite past scores; here the restatement lifted Europe from +3.08 to +4.88"],
  ["Survivorship is harder to see", "No file gives itself away and delisting returns go missing; survivors only flattered our 2018 to 2024 benchmark by 0.46 points a year"],
  ["Costs are not a constant", "Spread, liquidity and order size; even a flat 20 bp cost 0.28 to 0.33 points a year"],
];
issues.forEach(([a, b], i) => {
  const y = 1.9 + i * 1.02;
  circleNum(s, i + 1, MX, y + 0.03, 0.38);
  s.addText([{ text: a, options: { bold: true, breakLine: true } }, { text: b, options: { fontSize: 13 } }], {
    x: MX + 0.55, y, w: 5.05, h: 0.95, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: `issue-${i + 1}`,
  });
});
const tx = 6.55, tw = W - MX - tx;
s.addText("Would our conclusions survive?", { x: tx, y: 1.4, w: tw, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
s.addTable(tableRows(["Our conclusion", "On real data"], [
  ["No model beats the naive forecast", "Likely survives: we found no skill with 7 training years; any real gain would be small"],
  ["Our data checks (cross-column, return windows, publication dates)", "The checks survive; the specific errors do not"],
  ["Survivors-only and restated data flatter results", "Direction survives, size does not"],
  ["Europe from 2021: an association", "Not as a signal: here the course said one real link exists; real data gives no such hint (1 of 14 cells, p 0.09 by year)"],
  ["No backtest edge; the floor cost no return", "No edge survives. The floor may not stay free: its gain came mostly from formation year 2022, and real high-score firms cluster in sectors"],
], { boldFirst: false }), {
  x: tx, y: 1.9, w: tw, colW: [2.6, 3.58], fontSize: 12, rowH: 0.5, margin: [0.03, 0.08, 0.03, 0.08],
  border: { type: "solid", pt: 0.5, color: HEX.accent4 }, valign: "middle", objectName: "survive-table",
});
card(s, "recommendation", MX, 6.05, W - 2 * MX, 0.8, C.text1);
s.addText([
  { text: "Recommendation: ", options: { bold: true, color: C.accent2 } },
  { text: "we would not allocate on this evidence. First: several raters, dated vintages, delisting returns, realistic costs and a replication of the Europe result.", options: { color: C.background1 } },
], { x: MX + 0.3, y: 6.05, w: W - 2 * MX - 0.6, h: 0.8, fontSize: 15, margin: 0, valign: "middle", isTextBox: true });
s.addNotes(
  "About 1 minute 10. What would change with real data? Four things remain hard after an audit like ours. Raters disagree: six major raters correlate only 0.38 to 0.71, so a result for one rater may not hold for another. " +
  "Vendors rewrite past scores, and we saw how much a restatement can flatter a result. Survivorship is harder to see in real files, and costs depend on spread, liquidity and order size. " +
  "Which conclusions survive? That no model beats the naive forecast likely survives. Our checks survive, not the specific errors. Survivorship and restatement bias survive in direction, not in size. " +
  "The Europe result does not survive as a signal: here the course told us that one genuine relationship exists; with real data nobody tells you that, and one cell of fourteen with p 0.09 by year cannot be told apart from chance. " +
  "Nor would the floor necessarily stay free: most of its gain came from one formation year, 2022, and real high-score firms cluster in certain sectors, so a floor becomes a sector bet. So our recommendation: we would not allocate on this evidence."
);

// ---------------------------------------------------------------- slide 8: closing (dark)
s = pres.addSlide({ masterName: "G8_DARK", sectionTitle: "Real data and recommendation" });
s.addText("Conclusion", { x: MX, y: 1.35, w: 9.5, h: 0.4, fontSize: 16, color: C.accent2, margin: 0, isTextBox: true });
s.addText("We would not allocate on this evidence", { x: MX, y: 1.85, w: 10.2, h: 1.0, fontSize: 40, bold: true, color: C.background1, margin: 0, valign: "top", isTextBox: true, objectName: "closing-title" });
[["01", "Seven data problems found and treated; one column would have faked a forecasting edge"],
 ["02", "No model beats the naive forecast out of sample"],
 ["03", "Environmental score: only Europe from 2021 stands out; plausible, not proven"],
 ["04", "The backtest edge cannot be told apart from noise"]].forEach(([n, t], i) => {
  const y = 3.15 + i * 0.62;
  s.addText(n, { x: MX, y, w: 0.6, h: 0.48, fontSize: 18, bold: true, color: C.accent2, margin: 0, valign: "middle", isTextBox: true });
  s.addText(t, { x: MX + 0.7, y, w: 10.5, h: 0.48, fontSize: 18, color: C.background1, margin: 0, valign: "middle", isTextBox: true, objectName: `closing-point-${i + 1}` });
});
s.addText("Thank you. Questions?", { x: MX, y: 5.85, w: 8, h: 0.7, fontSize: 28, bold: true, color: C.accent2, margin: 0, valign: "middle", isTextBox: true, objectName: "closing-questions" });
s.addNotes("About 10 seconds. To sum up: we would not allocate on this evidence. Thank you; we are happy to take questions.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
