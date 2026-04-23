// generate_slides.js — Mealy 12-slide presentation
// Usage: node generate_slides.js
// Output: Mealy_Presentation.pptx

const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

// ── theme ────────────────────────────────────────────────────────────────────
const C = {
  bg:      "0C0C10",
  orange:  "FF8C42",
  amber:   "FBBF24",
  green:   "34D399",
  white:   "EAEAEA",
  muted:   "666680",
  card:    "14141C",
  border:  "2A2A3A",
};

pptx.layout  = "LAYOUT_WIDE";
pptx.author  = "Kowsyke";
pptx.subject = "CMS22202 Computer Vision and AI — Mealy";

// ── helpers ──────────────────────────────────────────────────────────────────
function addSlide(title, fn) {
  const slide = pptx.addSlide();
  slide.background = { color: C.bg };

  // orange accent bar along the left
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.08, h: "100%", fill: { color: C.orange },
  });

  if (title) {
    slide.addText(title, {
      x: 0.3, y: 0.2, w: "90%", h: 0.55,
      fontSize: 24, bold: true, color: C.white, fontFace: "Calibri",
    });
    // underline bar
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.3, y: 0.78, w: 9.1, h: 0.03, fill: { color: C.orange }, line: { type: "none" },
    });
  }

  fn(slide);
  return slide;
}

function body(slide, items, opts = {}) {
  const {
    x = 0.3, y = 1.0, w = 9.1, h = 5.3,
    fontSize = 16, color = C.white, bullet = true,
  } = opts;
  slide.addText(items, {
    x, y, w, h,
    fontSize, color, fontFace: "Calibri",
    bullet: bullet ? { type: "bullet", indent: 10 } : false,
    valign: "top", align: "left",
    paraSpaceAfter: 6,
  });
}

function label(slide, text, x, y, w, h, color = C.muted, size = 11) {
  slide.addText(text, { x, y, w, h, fontSize: size, color, fontFace: "Calibri", align: "left" });
}

function accent(slide, text, x, y, w, h, size = 36) {
  slide.addText(text, { x, y, w, h, fontSize: size, bold: true, color: C.orange, fontFace: "Calibri", align: "left" });
}

function card(slide, x, y, w, h) {
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w, h,
    fill: { color: C.card },
    line: { color: C.border, pt: 1 },
    rectRadius: 0.08,
  });
}

// ── SLIDE 1 — Title ───────────────────────────────────────────────────────────
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bg };

  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.08, h: "100%", fill: { color: C.orange } });

  slide.addText("Mealy", {
    x: 0.4, y: 1.5, w: 9, h: 1.4,
    fontSize: 72, bold: true, color: C.orange, fontFace: "Calibri",
  });
  slide.addText("Food Image Classification with MobileNetV2", {
    x: 0.4, y: 3.0, w: 9, h: 0.6,
    fontSize: 22, color: C.white, fontFace: "Calibri",
  });
  slide.addText("CMS22202 Computer Vision and AI  ·  Ravensbourne University London  ·  Kowsyke  ·  2026", {
    x: 0.4, y: 5.8, w: 9, h: 0.4,
    fontSize: 12, color: C.muted, fontFace: "Calibri",
  });
}

// ── SLIDE 2 — Problem Statement ───────────────────────────────────────────────
addSlide("Problem Statement", slide => {
  body(slide, [
    { text: "101 food categories — each visually distinct, but similar within-class", options: { fontSize: 17, color: C.white } },
    { text: "Manual food logging is slow and error-prone", options: { fontSize: 17, color: C.white } },
    { text: "Goal: automate food recognition from a photograph in real time", options: { fontSize: 17, color: C.orange } },
    { text: "Use case: calorie tracking, restaurant tech, nutrition research", options: { fontSize: 17, color: C.white } },
    { text: "Solution: transfer learning on Food-101, served via REST API + webcam UI", options: { fontSize: 17, color: C.white } },
  ]);

  card(slide, 0.3, 3.5, 4.2, 2.1);
  label(slide, "Random baseline", 0.5, 3.65, 3.8, 0.4, C.muted, 13);
  accent(slide, "1%", 0.5, 4.0, 3.8, 0.8, 44);
  label(slide, "across 101 classes", 0.5, 4.75, 3.8, 0.35, C.muted, 12);

  card(slide, 5.1, 3.5, 4.2, 2.1);
  label(slide, "Mealy test accuracy", 5.3, 3.65, 3.8, 0.4, C.muted, 13);
  accent(slide, "37.6%", 5.3, 4.0, 3.8, 0.8, 44);
  label(slide, "37× better than random", 5.3, 4.75, 3.8, 0.35, C.green, 12);
});

// ── SLIDE 3 — Dataset ─────────────────────────────────────────────────────────
addSlide("Dataset — Food-101", slide => {
  body(slide, [
    { text: "Food-101 (Bossard et al., 2014) — 101 food categories, ~1,000 images each", options: { fontSize: 17, color: C.white } },
    { text: "Images scraped from food review websites — real-world noise and variety", options: { fontSize: 17, color: C.white } },
    { text: "Training used kmader/food41 on Kaggle (HDF5 format, GPU training)", options: { fontSize: 17, color: C.white } },
    { text: "11,099 train images  /  1,000 test images  /  101 classes", options: { fontSize: 17, color: C.amber } },
    { text: "Source resolution: 64×64 pixels (upsampled to 224×224 for MobileNetV2)", options: { fontSize: 17, color: C.white } },
    { text: "Second model: Fruits dataset, 36 classes, 96.7% accuracy (full-res JPEG)", options: { fontSize: 17, color: C.green } },
  ]);

  card(slide, 0.3, 4.3, 9.1, 1.2);
  label(slide, "Classes include: pizza · sushi · hotdog · ramen · steak · caesar salad · tiramisu · apple pie · bibimbap · pad thai · baklava + 90 more", 0.55, 4.55, 8.7, 0.8, C.muted, 13);
});

// ── SLIDE 4 — Full Pipeline ───────────────────────────────────────────────────
addSlide("Full Pipeline", slide => {
  const steps = [
    ["Webcam / Image", "Raw RGB frame captured via OpenCV\nor uploaded to Flask API"],
    ["preprocess.py", "Resize → 224×224\nDivide by 255 (0..1 range)"],
    ["MobileNetV2 base", "ImageNet pretrained\n~2.2M parameters frozen"],
    ["Classification head", "GAP → Dense 256 ReLU\nDropout 0.4 → Dense 101 Softmax"],
    ["Multi-region", "5 overlapping crops\nof the same frame"],
    ["Flask API", "/detect JSON\nconfidence + calories"],
  ];

  const step_w = 1.55, step_h = 1.6, gap = 0.08;
  steps.forEach(([title, desc], i) => {
    const x = 0.1 + i * (step_w + gap);
    card(slide, x, 1.1, step_w, step_h);
    slide.addText(title, { x: x + 0.08, y: 1.2, w: step_w - 0.16, h: 0.42, fontSize: 13, bold: true, color: C.orange, fontFace: "Calibri" });
    slide.addText(desc,  { x: x + 0.08, y: 1.65, w: step_w - 0.16, h: 0.9, fontSize: 10, color: C.white, fontFace: "Calibri", valign: "top" });
    if (i < steps.length - 1) {
      slide.addText("→", { x: x + step_w + 0.01, y: 1.7, w: 0.1, h: 0.4, fontSize: 14, bold: true, color: C.orange, fontFace: "Calibri", align: "center" });
    }
  });

  label(slide, "Shared preprocess.py used identically during training and inference — no train/serve mismatch.", 0.3, 3.0, 9.1, 0.35, C.muted, 12);

  body(slide, [
    { text: "Combined mode: runs Food-101 model + Fruit model simultaneously, merges by class name (highest confidence wins)", options: { fontSize: 15, color: C.white } },
    { text: "Detects two different foods in one frame — e.g. chicken + tomato in the same scan", options: { fontSize: 15, color: C.green } },
  ], { y: 3.4, h: 2.1 });
});

// ── SLIDE 5 — MobileNetV2 Architecture ───────────────────────────────────────
addSlide("MobileNetV2 Architecture", slide => {
  body(slide, [
    { text: "Depthwise separable convolutions: 8–9× fewer multiplications than standard conv", options: { fontSize: 17, color: C.white } },
    { text: "Inverted residual blocks: expand → depthwise → project (Sandler et al., 2018)", options: { fontSize: 17, color: C.white } },
    { text: "~3.4M trainable parameters in head vs ~14M for VGG-16", options: { fontSize: 17, color: C.white } },
    { text: "Input: (224, 224, 3)  →  Base output: (7, 7, 1280)  →  GAP: (1280,)  →  Dense 101", options: { fontSize: 16, color: C.amber } },
  ]);

  const layers = [
    ["Input 224×224×3", C.border],
    ["MobileNetV2 base\n(frozen in P1)", C.orange + "33"],
    ["GAP", C.border],
    ["Dense 256 ReLU", C.border],
    ["Dropout 0.4", C.border],
    ["Dense 101 Softmax", C.green + "33"],
  ];
  const lw = 1.45, lh = 0.72, ly0 = 3.3;
  layers.forEach(([lbl, col], i) => {
    card(slide, 0.3 + i * (lw + 0.06), ly0, lw, lh);
    slide.addText(lbl, { x: 0.3 + i * (lw + 0.06) + 0.06, y: ly0 + 0.1, w: lw - 0.12, h: lh - 0.2, fontSize: 11, color: C.white, fontFace: "Calibri", valign: "middle", align: "center" });
    if (i < layers.length - 1)
      slide.addText("→", { x: 0.3 + (i + 1) * (lw + 0.06) - 0.08, y: ly0 + 0.2, w: 0.1, h: 0.35, fontSize: 12, bold: true, color: C.orange, fontFace: "Calibri", align: "center" });
  });

  label(slide, "Why MobileNetV2: small model (~10 MB), fast on CPU, well-understood preprocessing (÷255). EfficientNet tried but per-channel normalisation caused val_acc to flatline.", 0.3, 4.3, 9.1, 0.7, C.muted, 12);
});

// ── SLIDE 6 — Transfer Learning ───────────────────────────────────────────────
addSlide("Transfer Learning", slide => {
  body(slide, [
    { text: "Pretrained on ImageNet (1.2M images, 1,000 classes) — lower layers learn universal features", options: { fontSize: 17, color: C.white } },
    { text: "Lower layers: edges, textures, gradients — same for food and cars and dogs", options: { fontSize: 17, color: C.white } },
    { text: "Upper layers: object parts — adaptable to food with far less data", options: { fontSize: 17, color: C.white } },
    { text: "Phase 1: base frozen, only 256-dim head trained (fast, avoids destroying pretrained features)", options: { fontSize: 17, color: C.orange } },
    { text: "Phase 2: top 30 base layers unfrozen, full network fine-tuned at lr=1e-5", options: { fontSize: 17, color: C.orange } },
    { text: "Why not train from scratch: only ~110 images per class — not enough to learn from noise", options: { fontSize: 17, color: C.muted } },
  ]);
});

// ── SLIDE 7 — Training ────────────────────────────────────────────────────────
addSlide("Training", slide => {
  const rows = [
    ["Phase", "Layers", "Epochs", "LR", "Best val acc"],
    ["Phase 1", "Head only", "15", "1e-3", "—"],
    ["Phase 2", "Top 30 unfrozen", "7 / 20", "1e-5", "97.15%  (fruit)"],
    ["Food-101", "Both phases", "20 + 20", "1e-3 / 1e-5", "37.6%  (test)"],
  ];

  const cols = [1.8, 2.2, 1.2, 1.2, 2.2];
  const tx0 = 0.3, ty0 = 1.1, row_h = 0.55;
  rows.forEach((row, ri) => {
    let cx = tx0;
    row.forEach((cell, ci) => {
      const color = ri === 0 ? C.muted : (ci === 4 ? C.green : C.white);
      const bold  = ri === 0 || ci === 0;
      slide.addText(cell, { x: cx, y: ty0 + ri * row_h, w: cols[ci], h: row_h, fontSize: 13, bold, color, fontFace: "Calibri", valign: "middle", align: ci === 0 ? "left" : "center" });
      cx += cols[ci];
    });
  });

  // divider
  slide.addShape(pptx.ShapeType.rect, { x: 0.3, y: 1.62, w: 9.1, h: 0.02, fill: { color: C.border }, line: { type: "none" } });

  body(slide, [
    { text: "Fruit/Veg model: 36 classes, full-resolution JPEG dataset, trained 48 min on CPU", options: { fontSize: 15, color: C.white } },
    { text: "EarlyStopping patience=7, ReduceLROnPlateau × 0.5 on plateau", options: { fontSize: 15, color: C.white } },
    { text: "Per-epoch checkpoints saved — safe to interrupt and resume", options: { fontSize: 15, color: C.white } },
    { text: "Food-101 trained on Kaggle P100 GPU (~45 min); fruit trained locally on AMD Ryzen CPU", options: { fontSize: 15, color: C.muted } },
  ], { y: 3.5, h: 2.5 });
});

// ── SLIDE 8 — Results ─────────────────────────────────────────────────────────
addSlide("Results", slide => {
  const metrics = [
    ["Food-101\n101 classes", "37.6%", C.amber],
    ["Fruit / Veg\n36 classes",  "96.7%", C.green],
    ["Combined\n137 classes",    "Both",  C.orange],
    ["Random\nbaseline",         "1%",    C.muted],
  ];

  metrics.forEach(([lbl, val, col], i) => {
    const x = 0.3 + i * 2.35;
    card(slide, x, 1.1, 2.2, 2.3);
    label(slide, lbl, x + 0.1, 1.25, 2.0, 0.6, C.muted, 12);
    slide.addText(val, { x: x + 0.1, y: 1.9, w: 2.0, h: 0.85, fontSize: 38, bold: true, color: col, fontFace: "Calibri", align: "center" });
    label(slide, "test accuracy", x + 0.1, 2.82, 2.0, 0.3, C.muted, 10);
  });

  body(slide, [
    { text: "Food-101 gap from SOTA (~90%): source images stored at 64×64, upsampled to 224×224 — upsampling adds no information", options: { fontSize: 15, color: C.white } },
    { text: "Fruit model uses full-resolution JPEG images at native size — accuracy jumps to 96.7%", options: { fontSize: 15, color: C.green } },
    { text: "The gap between 37.6% and 96.7% proves the resolution constraint, not the model or method", options: { fontSize: 15, color: C.white } },
  ], { y: 3.65, h: 2.5 });
});

// ── SLIDE 9 — Combined Detection ──────────────────────────────────────────────
addSlide("Combined Detection — Dual Database", slide => {
  body(slide, [
    { text: "Real meals combine foods from both databases — chicken fry + tomatoes, burger + salad", options: { fontSize: 17, color: C.white } },
    { text: "POST /detect_combined runs Food-101 model AND Fruit model on the same frame simultaneously", options: { fontSize: 17, color: C.orange } },
    { text: "Merge strategy: deduplicate by class name, keep highest-confidence entry", options: { fontSize: 17, color: C.white } },
    { text: "Up to 6 combined detections returned; calorie totals span both databases", options: { fontSize: 17, color: C.white } },
    { text: "137 total recognisable classes: 101 (food) + 36 (fruit/veg)", options: { fontSize: 17, color: C.green } },
    { text: "Three UI modes: Food only · Fruit+Veg only · Combined (both models)", options: { fontSize: 17, color: C.white } },
  ]);
});

// ── SLIDE 10 — Flask API ──────────────────────────────────────────────────────
addSlide("Flask API — Port 5001", slide => {
  const endpoints = [
    ["GET",  "/health",          "System status, both model states"],
    ["POST", "/predict",         "Single-region Food-101 classification"],
    ["POST", "/detect",          "Multi-region food detection (up to 4)"],
    ["POST", "/predict_fruit",   "Single-region Fruit/Veg classification"],
    ["POST", "/detect_fruit",    "Multi-region Fruit/Veg detection"],
    ["POST", "/detect_combined", "Both models, merged results (up to 6)"],
  ];

  const ex0 = 0.3, ey0 = 1.1, ew = [0.65, 2.0, 6.0];
  label(slide, "METHOD", ex0, ey0, 0.65, 0.4, C.muted, 11);
  label(slide, "ENDPOINT", ex0 + 0.65, ey0, 2.0, 0.4, C.muted, 11);
  label(slide, "DESCRIPTION", ex0 + 2.65, ey0, 6.0, 0.4, C.muted, 11);
  slide.addShape(pptx.ShapeType.rect, { x: 0.3, y: 1.5, w: 9.1, h: 0.02, fill: { color: C.border }, line: { type: "none" } });

  endpoints.forEach(([method, path, desc], i) => {
    const y = 1.55 + i * 0.55;
    const mc = method === "GET" ? C.green : C.orange;
    slide.addText(method, { x: ex0, y, w: 0.65, h: 0.45, fontSize: 11, bold: true, color: mc, fontFace: "Calibri", align: "left", valign: "middle" });
    slide.addText(path,   { x: ex0 + 0.65, y, w: 2.0, h: 0.45, fontSize: 11, color: C.amber, fontFace: "Calibri", align: "left", valign: "middle" });
    slide.addText(desc,   { x: ex0 + 2.65, y, w: 6.0, h: 0.45, fontSize: 12, color: C.white, fontFace: "Calibri", align: "left", valign: "middle" });
  });

  label(slide, "TF models load lazily on first request — Flask binds in 0.35s; /health always responds immediately.", 0.3, 5.0, 9.1, 0.4, C.muted, 11);
});

// ── SLIDE 11 — Ethics + Limitations ──────────────────────────────────────────
addSlide("Ethics + Limitations", slide => {
  body(slide, [
    { text: "Dataset bias: Food-101 weighted toward Western and East Asian cuisines", options: { fontSize: 16, color: C.white } },
    { text: "Privacy: food images could reveal dietary restrictions or health conditions — no data stored, stateless API", options: { fontSize: 16, color: C.white } },
    { text: "Transparency: model always returns confidence score, not just a label; top-5 visible in UI", options: { fontSize: 16, color: C.white } },
    { text: " ", options: { fontSize: 10 } },
    { text: "64×64 source images limit feature detail — the main accuracy constraint", options: { fontSize: 16, color: C.amber } },
    { text: "~110 images per class is insufficient for 101-way classification at this resolution", options: { fontSize: 16, color: C.amber } },
    { text: "Single-frame classification: no object localisation or bounding boxes", options: { fontSize: 16, color: C.amber } },
  ]);
});

// ── SLIDE 12 — Future Work + References ──────────────────────────────────────
addSlide("Future Work + References", slide => {
  body(slide, [
    { text: "Full Food-101 at 224×224 resolution (101,000 images, 750/class) — train_optimized.py ready", options: { fontSize: 15, color: C.white } },
    { text: "EfficientNetV2 backbone with correct per-channel normalisation", options: { fontSize: 15, color: C.white } },
    { text: "CutMix / Mixup augmentation for harder decision boundaries", options: { fontSize: 15, color: C.white } },
    { text: "TFLite export for mobile deployment (<10 MB, 50ms inference on device)", options: { fontSize: 15, color: C.white } },
    { text: " ", options: { fontSize: 8 } },
    { text: "Bossard, L. et al. (2014). Food-101 — Mining Discriminative Components with Random Forests. ECCV, pp.446–461.", options: { fontSize: 12, color: C.muted } },
    { text: "Sandler, M. et al. (2018). MobileNetV2: Inverted Residuals and Linear Bottlenecks. CVPR, pp.4510–4520.", options: { fontSize: 12, color: C.muted } },
    { text: "Geron, A. (2019). Hands-on Machine Learning with Scikit-Learn, Keras, and TensorFlow. 2nd ed. O'Reilly.", options: { fontSize: 12, color: C.muted } },
    { text: "GitHub: github.com/Kowsyke/Mealy", options: { fontSize: 13, color: C.orange } },
  ], { y: 1.0, h: 5.3 });
});

// ── generate ──────────────────────────────────────────────────────────────────
const OUT = "Mealy_Presentation.pptx";
pptx.writeFile({ fileName: OUT })
  .then(() => console.log(`[pptx] Saved: ${OUT}`))
  .catch(err => { console.error("[pptx] Error:", err); process.exit(1); });
