#!/usr/bin/env python3
"""Generate polished StyleCap pitch deck PDF for lablab submission."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import cairosvg
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
W, H = landscape((13.333 * inch, 7.5 * inch))
TOTAL_SLIDES = 10

MARGIN = 0.5 * inch
FOOTER_Y = 0.55 * inch
CONTENT_BOTTOM = 0.72 * inch

# Palette
BG = colors.HexColor("#0b1220")
ACCENT = colors.HexColor("#38bdf8")
ORANGE = colors.HexColor("#f97316")
PURPLE = colors.HexColor("#a855f7")
GREEN = colors.HexColor("#22c55e")
TEXT = colors.HexColor("#f1f5f9")
MUTED = colors.HexColor("#94a3b8")
CARD = colors.HexColor("#1e293b")
BORDER = colors.HexColor("#334155")

STYLE_COLORS = {
    "formal": colors.HexColor("#3b82f6"),
    "sarcastic": colors.HexColor("#f97316"),
    "humorous_tech": colors.HexColor("#a855f7"),
    "humorous_non_tech": colors.HexColor("#22c55e"),
}


def load_references() -> dict:
    path = ROOT / "eval" / "references.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def render_architecture_png(svg_path: Path, png_path: Path) -> None:
    try:
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1600)
    except Exception as exc:
        print(f"[warn] cairosvg failed ({exc}); using PIL fallback")
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1600, 700), "#0f172a")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except OSError:
            font = ImageFont.load_default()
            small = font
        draw.text((800, 40), "StyleCap Pipeline Architecture", fill="#f8fafc", anchor="mm", font=font)
        boxes = [
            (40, 120, 200, 70, "tasks.json", "#1e3a8a"),
            (280, 120, 200, 70, "Download x6", "#1e3a8a"),
            (520, 120, 200, 70, "ffmpeg 6f", "#14532d"),
            (760, 120, 220, 70, "GROUND vision", "#7c2d12"),
            (1020, 120, 200, 70, "WRITE batch", "#581c87"),
            (1260, 120, 180, 70, "JUDGE", "#581c87"),
        ]
        for x, y, w, h, label, fill in boxes:
            draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=fill, outline="#38bdf8", width=2)
            draw.text((x + w // 2, y + h // 2), label, fill="#f1f5f9", anchor="mm", font=small)
        draw.rounded_rectangle([40, 280, 1560, 90], radius=12, fill="#1e293b", outline="#475569", width=2)
        draw.text(
            (800, 325),
            "Degradation: full pipeline -> write-only -> direct vision -> schema repair",
            fill="#94a3b8",
            anchor="mm",
            font=small,
        )
        draw.rounded_rectangle([40, 420, 760, 70], radius=12, fill="#0c4a6e", outline="#0ea5e9", width=2)
        draw.text((400, 455), "Graded: Kimi K2.6 + GLM 5.2 (Fireworks)", fill="#bae6fd", anchor="mm", font=small)
        draw.rounded_rectangle([820, 420, 760, 70], radius=12, fill="#431407", outline="#f97316", width=2)
        draw.text((1200, 455), "Gemma: google/gemma-3-12b-it on MI300X", fill="#fed7aa", anchor="mm", font=small)
        img.save(png_path)


def draw_bg(c: canvas.Canvas) -> None:
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1e3a5f"))
    c.setFillAlpha(0.22)
    c.circle(W * 0.9, H * 0.85, 110, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#431407"))
    c.circle(W * 0.08, H * 0.1, 75, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setFillColor(ACCENT)
    c.rect(0, H - 0.1 * inch, W, 0.1 * inch, fill=1, stroke=0)
    c.setFillColor(ORANGE)
    c.rect(0, H - 0.1 * inch, W * 0.4, 0.1 * inch, fill=1, stroke=0)


def draw_badge(c: canvas.Canvas, text: str, y: float, color=ACCENT) -> None:
    tw = len(text) * 5.8 + 28
    c.setFillColor(colors.HexColor("#0c4a6e"))
    c.roundRect(MARGIN, y - 0.12 * inch, tw, 0.34 * inch, 8, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN + 0.12 * inch, y, text.upper())


def draw_title(c: canvas.Canvas, text: str, y: float, size: int = 34) -> None:
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", size)
    c.drawString(MARGIN, y, text)


def draw_subtitle(c: canvas.Canvas, text: str, y: float, color=ACCENT) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica", 14)
    c.drawString(MARGIN, y, text)


def draw_footer(c: canvas.Canvas, page: int) -> None:
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN, FOOTER_Y - 0.22 * inch, "StyleCap | AMD ACT II Track 2 | QuantumByte-01")
    c.drawRightString(W - MARGIN, FOOTER_Y - 0.22 * inch, f"{page} / {TOTAL_SLIDES}")
    c.drawCentredString(W / 2, FOOTER_Y - 0.22 * inch, "github.com/QuantumByte-01/amd-track2-captioner")


def wrap_draw(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_w: float,
    size: int = 11,
    color=MUTED,
    leading: float = 1.3,
    max_lines: int | None = None,
) -> float:
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    chars = int(max_w / (size * 0.48))
    lines = textwrap.wrap(text, width=max(20, chars))
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= size * leading
    return y


def draw_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    accent=ACCENT,
    body_size: int = 10,
    body_lines: int | None = None,
) -> None:
    c.setFillColor(CARD)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(accent)
    c.rect(x, y + h - 0.05 * inch, w, 0.05 * inch, fill=1, stroke=0)
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 0.12 * inch, y + h - 0.2 * inch, title.upper())
    wrap_draw(
        c,
        body,
        x + 0.12 * inch,
        y + h - 0.38 * inch,
        w - 0.24 * inch,
        body_size,
        TEXT,
        leading=1.25,
        max_lines=body_lines,
    )


def draw_bullet(c: canvas.Canvas, text: str, y: float, marker: str = ">", marker_color=ORANGE, size: int = 12) -> float:
    c.setFillColor(marker_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, marker)
    return wrap_draw(c, text, MARGIN + 0.28 * inch, y, W - 1.2 * inch, size, TEXT) - 0.08 * inch


def draw_style_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, style: str, caption: str) -> None:
    col = STYLE_COLORS[style]
    c.setFillColor(CARD)
    c.setStrokeColor(col)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(col)
    c.rect(x, y + h - 0.04 * inch, w, 0.04 * inch, fill=1, stroke=0)
    label = style.replace("_", " ").title()
    c.setFillColor(col)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 0.1 * inch, y + h - 0.18 * inch, label)
    lines = 3 if style == "formal" else 2
    wrap_draw(c, caption, x + 0.1 * inch, y + h - 0.36 * inch, w - 0.2 * inch, 9, TEXT, leading=1.22, max_lines=lines)


def slide_title(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "AMD Developer Hackathon ACT II", H - 0.78 * inch)
    draw_title(c, "StyleCap", H - 1.4 * inch, 46)
    draw_subtitle(c, "Grounded Multi-Style Video Captioning", H - 1.9 * inch)
    wrap_draw(
        c,
        "Containerized Track 2 agent: watches short clips, extracts visual facts, writes four distinct caption styles - each grounded in what is actually on screen.",
        MARGIN,
        H - 2.48 * inch,
        9.2 * inch,
        13,
        TEXT,
    )
    tags = [
        ("Gemma 3 12B", ORANGE),
        ("AMD MI300X", ORANGE),
        ("ROCm + vLLM", ORANGE),
        ("Fireworks AI", ACCENT),
        ("Docker GHCR", GREEN),
    ]
    x = MARGIN
    for label, col in tags:
        c.setFillColor(CARD)
        c.setStrokeColor(col)
        c.roundRect(x, H - 3.35 * inch, 1.65 * inch, 0.34 * inch, 6, fill=1, stroke=1)
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + 0.825 * inch, H - 3.22 * inch, label)
        x += 1.75 * inch
    draw_card(
        c,
        MARGIN,
        CONTENT_BOTTOM,
        3.95 * inch,
        1.15 * inch,
        "Graded image",
        "ghcr.io/quantumbyte-01/amd-track2-captioner:v34",
        GREEN,
        body_size=9,
    )
    draw_card(
        c,
        MARGIN + 4.15 * inch,
        CONTENT_BOTTOM,
        3.95 * inch,
        1.15 * inch,
        "GitHub",
        "github.com/QuantumByte-01/amd-track2-captioner",
        ACCENT,
        body_size=10,
    )
    draw_card(
        c,
        MARGIN + 8.3 * inch,
        CONTENT_BOTTOM,
        4.1 * inch,
        1.15 * inch,
        "Contact",
        "GitHub: quantibyte | swastik.r.900@gmail.com",
        PURPLE,
        body_size=10,
        body_lines=2,
    )
    draw_footer(c, 1)


def slide_problem(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "Track 2 Challenge", H - 0.78 * inch)
    draw_title(c, "The Problem", H - 1.35 * inch, 32)
    bullets = [
        "Caption each 30s-2min clip in 4 styles: formal, sarcastic, humorous-tech, humorous-non-tech",
        "Docker container, ~12 clips, 10-minute wall clock, valid JSON schema, no runtime API key",
        "Generic captions that could fit any video score near 0.6 accuracy - specificity wins",
        "Any model allowed for Track 2; leaderboard scored by automated LLM judge",
    ]
    y = H - 2.0 * inch
    for b in bullets:
        y = draw_bullet(c, b, y, size=11)
    styles = [
        ("Formal", "Objective, detail-rich sentences grounded in visible facts", ACCENT),
        ("Sarcastic", "Dry irony - Ah yes... cadence from reference winners", ORANGE),
        ("Humorous-tech", "One dev metaphor anchored to a real visual detail", PURPLE),
        ("Humorous-non-tech", "Relatable When you finally... line, still clip-specific", GREEN),
    ]
    x = MARGIN
    for name, desc, col in styles:
        draw_card(c, x, CONTENT_BOTTOM, 2.85 * inch, 1.35 * inch, name, desc, col, body_size=9)
        x += 3.05 * inch
    draw_footer(c, 2)


def slide_judging(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "Judging Alignment", H - 0.78 * inch, PURPLE)
    draw_title(c, "Built for the Grader", H - 1.32 * inch, 30)
    draw_subtitle(c, "Accuracy + style match on every caption", H - 1.72 * inch)
    criteria = [
        ("Factual accuracy", "Vision fact sheet before styling. Captions trace back to frames.", GREEN),
        ("Style register", "Prompts calibrated to reference cadence and per-style length caps.", PURPLE),
        ("Reliability", "Degradation ladder + schema repair. Never empty or invalid JSON.", ACCENT),
        ("Speed", "6 parallel workers, batched judge, 90s/clip budget, 9-min soft deadline.", ORANGE),
    ]
    cw = (W - 2 * MARGIN - 0.25 * inch) / 2
    ch = 1.15 * inch
    top = H - 2.15 * inch
    for i, (title, body, col) in enumerate(criteria):
        col_x = MARGIN + (i % 2) * (cw + 0.25 * inch)
        row_y = top - (i // 2) * (ch + 0.18 * inch) - ch
        draw_card(c, col_x, row_y, cw, ch, title, body, col, body_size=10, body_lines=3)
    draw_card(
        c,
        MARGIN,
        CONTENT_BOTTOM,
        W - 2 * MARGIN,
        1.05 * inch,
        "Partner prize ($3k Gemma)",
        "Same pipeline end-to-end on google/gemma-3-12b-it via vLLM on AMD MI300X. Demo video + GEMMA_RESULTS.md in repo.",
        ORANGE,
        body_size=10,
        body_lines=2,
    )
    draw_footer(c, 3)


def slide_architecture(c: canvas.Canvas, diagram_path: str) -> None:
    draw_bg(c)
    draw_badge(c, "Architecture", H - 0.78 * inch)
    draw_title(c, "Fact Sheet First", H - 1.2 * inch, 30)
    draw_subtitle(c, "Two-phase anti-hallucination pipeline", H - 1.58 * inch)
    if os.path.exists(diagram_path):
        img = ImageReader(diagram_path)
        c.drawImage(
            img,
            MARGIN,
            CONTENT_BOTTOM + 0.05 * inch,
            width=W - 2 * MARGIN,
            height=H - 2.15 * inch - CONTENT_BOTTOM,
            preserveAspectRatio=True,
            anchor="sw",
        )
    draw_footer(c, 4)


def slide_how_it_works(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "How It Works", H - 0.78 * inch)
    draw_title(c, "Per-Clip Pipeline", H - 1.25 * inch, 30)
    steps = [
        ("1", "Download", "Parallel fetch across 6 workers"),
        ("2", "Sample", "ffmpeg uniform-seek, 6 frames at 768px"),
        ("3", "Ground", "Vision model produces strict JSON fact sheet"),
        ("4", "Write", "GLM batch: 2 candidates per style"),
        ("5", "Judge", "One batched call picks best per style"),
        ("6", "Repair", "Length policy + schema validation + ladder"),
    ]
    x0, y0 = MARGIN, H - 1.95 * inch
    for i, (num, title, desc) in enumerate(steps):
        col = x0 + (i % 3) * 4.1 * inch
        row = y0 - (i // 3) * 1.45 * inch
        c.setFillColor(ACCENT)
        c.circle(col + 0.15 * inch, row + 0.05 * inch, 0.14 * inch, fill=1, stroke=0)
        c.setFillColor(BG)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(col + 0.15 * inch, row, num)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(col + 0.38 * inch, row + 0.02 * inch, title)
        wrap_draw(c, desc, col + 0.38 * inch, row - 0.2 * inch, 3.5 * inch, 10, MUTED, max_lines=2)
    metrics = [
        ("6", "frames / clip"),
        ("2", "candidates"),
        ("~90s", "clip budget"),
        ("540s", "soft deadline"),
        ("86s", "Gemma 8-clip"),
        ("8/8", "eval strong"),
    ]
    x = MARGIN
    for val, lbl in metrics:
        c.setFillColor(CARD)
        c.roundRect(x, CONTENT_BOTTOM, 1.95 * inch, 0.9 * inch, 8, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(x + 0.975 * inch, CONTENT_BOTTOM + 0.58 * inch, val)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + 0.975 * inch, CONTENT_BOTTOM + 0.22 * inch, lbl)
        x += 2.08 * inch
    draw_footer(c, 5)


def draw_sample_clip(c: canvas.Canvas, clip_id: str, refs: dict, page: int) -> None:
    clip = refs.get(clip_id, {})
    desc = clip.get("desc", clip_id)
    draw_bg(c)
    draw_badge(c, "Sample Output", H - 0.78 * inch)
    draw_title(c, f"Clip {clip_id}", H - 1.25 * inch, 28)
    draw_subtitle(c, desc, H - 1.58 * inch, MUTED)

    samples = [
        ("formal", clip.get("formal", "")),
        ("sarcastic", clip.get("sarcastic", "")),
        ("humorous_tech", clip.get("humorous_tech", "")),
        ("humorous_non_tech", clip.get("humorous_non_tech", "")),
    ]

    card_w = W - 2 * MARGIN
    card_h = 1.12 * inch
    gap = 0.1 * inch
    y = H - 1.95 * inch - card_h
    for style, cap in samples:
        if not cap:
            continue
        draw_style_card(c, MARGIN, y, card_w, card_h, style, cap)
        y -= card_h + gap

    draw_footer(c, page)


def slide_gemma(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "Partner Prize", H - 0.78 * inch, ORANGE)
    draw_title(c, "Gemma on AMD MI300X", H - 1.32 * inch, 32)
    draw_subtitle(c, "Identical pipeline - end-to-end on the pod", H - 1.72 * inch)

    left_w = 6.1 * inch
    bullets = [
        "google/gemma-3-12b-it via vLLM + ROCm on Instinct MI300X (~82% VRAM)",
        "Ground, write, judge all on Gemma - no Fireworks deploy ($7/hr avoided)",
        "8 public clips in 86 seconds - GEMMA_RESULTS.md in repo",
        "Demo: rocm-smi + vLLM logs + live caption generation",
    ]
    y = H - 2.15 * inch
    for b in bullets:
        c.setFillColor(ORANGE)
        c.drawString(MARGIN, y, ">")
        y = wrap_draw(c, b, MARGIN + 0.22 * inch, y, left_w - 0.3 * inch, 11, TEXT, max_lines=2) - 0.04 * inch

    gemma_samples = [
        ("formal", "Urban street with traffic, buses, and yellow-leaf trees beside gray apartment towers."),
        ("sarcastic", "Ah yes, a perfectly organized urban commute where everything moves in the same direction."),
        ("humorous_tech", "When you refactor your codebase and everything still runs on the same lanes of traffic."),
        ("humorous_non_tech", "When you think you mastered parallel parking, then you see the traffic."),
    ]
    rx = 6.85 * inch
    rw = W - MARGIN - rx
    card_h = 1.0 * inch
    gap = 0.1 * inch
    y = H - 2.0 * inch - card_h
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(rx, y + card_h + 0.12 * inch, "GEMMA OUTPUT (v1 autumn boulevard)")
    for style, cap in gemma_samples:
        draw_style_card(c, rx, y, rw, card_h, style, cap)
        y -= card_h + gap

    draw_footer(c, 8)


def slide_graded(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "Leaderboard Path", H - 0.78 * inch, GREEN)
    draw_title(c, "Graded Docker Image", H - 1.32 * inch, 30)
    draw_subtitle(c, "Serverless models for post-deadline grader availability", H - 1.72 * inch)
    rows = [
        ("Vision / Ground", "accounts/fireworks/models/kimi-k2p6", "Multimodal fact extraction from 6 frames"),
        ("Caption / Judge", "accounts/fireworks/models/glm-5p2", "Style batch + batched candidate pick"),
        ("Fallback", "glm-5p2-fast router", "JSON recovery under time pressure"),
        ("Container", "linux/amd64, public GHCR", "FIREWORKS_API_KEY baked at build time"),
    ]
    y = H - 2.2 * inch
    for role, model, note in rows:
        c.setFillColor(CARD)
        c.roundRect(MARGIN, y - 0.55 * inch, W - 2 * MARGIN, 0.6 * inch, 6, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN + 0.15 * inch, y - 0.1 * inch, role)
        c.setFillColor(ACCENT)
        c.setFont("Courier-Bold", 9)
        c.drawString(2.7 * inch, y - 0.1 * inch, model)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(2.7 * inch, y - 0.28 * inch, note)
        y -= 0.72 * inch
    mono = "ghcr.io/quantumbyte-01/amd-track2-captioner:v34"
    c.setFillColor(colors.HexColor("#0c4a6e"))
    c.roundRect(MARGIN, CONTENT_BOTTOM, W - 2 * MARGIN, 0.72 * inch, 8, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN + 0.15 * inch, CONTENT_BOTTOM + 0.48 * inch, "SUBMIT THIS IMAGE ON LABLAB")
    c.setFillColor(TEXT)
    c.setFont("Courier-Bold", 13)
    c.drawString(MARGIN + 0.15 * inch, CONTENT_BOTTOM + 0.18 * inch, mono)
    draw_footer(c, 9)


def slide_closing(c: canvas.Canvas) -> None:
    draw_bg(c)
    draw_badge(c, "Summary", H - 0.78 * inch)
    draw_title(c, "Why StyleCap Wins", H - 1.32 * inch, 32)
    wins = [
        "Accuracy-first: every caption traces to a vision JSON fact sheet",
        "Style-calibrated: reference-winning cadence baked into write + judge prompts",
        "Reliable: degradation ladder always returns schema-valid results.json",
        "Fast: parallel workers + batched judge fits the 10-minute container limit",
        "AMD story: Gemma-3-12B proven on MI300X with recorded demo evidence",
    ]
    y = H - 1.95 * inch
    for wtxt in wins:
        c.setFillColor(GREEN)
        c.drawString(MARGIN, y, "+")
        y = wrap_draw(c, wtxt, MARGIN + 0.22 * inch, y, 9.5 * inch, 13, TEXT) - 0.04 * inch
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, 1.42 * inch, "Repository + submission")
    c.setFillColor(TEXT)
    c.setFont("Courier", 10)
    c.drawString(MARGIN, 1.18 * inch, "github.com/QuantumByte-01/amd-track2-captioner")
    c.drawString(MARGIN, 0.98 * inch, "ghcr.io/quantumbyte-01/amd-track2-captioner:v34")
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGIN, 0.72 * inch, "Thank you")
    draw_footer(c, 10)


def main() -> None:
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    svg_path = assets / "architecture.svg"
    png_path = assets / "architecture.png"
    render_architecture_png(svg_path, png_path)

    refs = load_references()
    out = ROOT / "StyleCap_Slides.pdf"
    c = canvas.Canvas(str(out), pagesize=(W, H))
    slides = [
        slide_title,
        slide_problem,
        slide_judging,
        lambda cv: slide_architecture(cv, str(png_path)),
        slide_how_it_works,
        lambda cv: draw_sample_clip(cv, "v2", refs, 6),
        lambda cv: draw_sample_clip(cv, "v7", refs, 7),
        slide_gemma,
        slide_graded,
        slide_closing,
    ]
    for fn in slides:
        fn(c)
        c.showPage()
    c.save()
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")
    print(f"Diagram: {png_path}")


if __name__ == "__main__":
    main()
