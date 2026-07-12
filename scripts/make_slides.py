#!/usr/bin/env python3
"""Generate StyleCap pitch deck PDF for lablab submission."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

W, H = landscape((13.333 * inch, 7.5 * inch))  # 16:9


def bg(c: canvas.Canvas) -> None:
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1e3a5f"))
    c.circle(W * 0.85, H * 0.78, 120, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#431407"))
    c.circle(W * 0.12, H * 0.15, 80, fill=1, stroke=0)


def badge(c: canvas.Canvas, text: str, y: float) -> None:
    c.setFillColor(colors.HexColor("#0c4a6e"))
    c.roundRect(0.55 * inch, y - 0.12 * inch, 2.4 * inch, 0.32 * inch, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#7dd3fc"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.7 * inch, y, text.upper())


def title(c: canvas.Canvas, text: str, y: float) -> None:
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(0.55 * inch, y, text)


def subtitle(c: canvas.Canvas, text: str, y: float) -> None:
    c.setFillColor(colors.HexColor("#38bdf8"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.55 * inch, y, text)


def body(c: canvas.Canvas, lines: list[str], y: float, size: int = 13) -> float:
    c.setFillColor(colors.HexColor("#cbd5e1"))
    c.setFont("Helvetica", size)
    for line in lines:
        c.drawString(0.55 * inch, y, line)
        y -= 0.28 * inch
    return y


def bullet(c: canvas.Canvas, lines: list[str], y: float) -> float:
    c.setFont("Helvetica", 13)
    for line in lines:
        c.setFillColor(colors.HexColor("#f97316"))
        c.drawString(0.55 * inch, y, "→")
        c.setFillColor(colors.HexColor("#e2e8f0"))
        c.drawString(0.75 * inch, y, line)
        y -= 0.32 * inch
    return y


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, lines: list[str]) -> None:
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setStrokeColor(colors.HexColor("#334155"))
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 0.15 * inch, y + h - 0.22 * inch, label.upper())
    cy = y + h - 0.45 * inch
    c.setFillColor(colors.HexColor("#e2e8f0"))
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(x + 0.15 * inch, cy, line)
        cy -= 0.22 * inch


def mono(c: canvas.Canvas, text: str, y: float, size: int = 11) -> None:
    c.setFillColor(colors.HexColor("#7dd3fc"))
    c.setFont("Courier-Bold", size)
    c.drawString(0.55 * inch, y, text)


def footer(c: canvas.Canvas, left: str, right: str = "") -> None:
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 8)
    c.drawString(0.55 * inch, 0.35 * inch, left)
    if right:
        c.drawRightString(W - 0.55 * inch, 0.35 * inch, right)


def slide1(c: canvas.Canvas) -> None:
    bg(c)
    badge(c, "AMD ACT II · Track 2", H - 0.9 * inch)
    title(c, "StyleCap", H - 1.55 * inch)
    subtitle(c, "Grounded multi-style video captioning", H - 2.05 * inch)
    body(c, [
        "One clip → four voices. Every caption locked to a verified visual fact sheet.",
        "Formal · Sarcastic · Humorous-tech · Humorous-non-tech",
    ], H - 2.55 * inch)
    tags = ["Gemma 3 12B", "AMD MI300X", "ROCm", "Fireworks AI", "Docker"]
    x = 0.55 * inch
    for t in tags:
        c.setFillColor(colors.HexColor("#334155"))
        c.roundRect(x, H - 4.1 * inch, 1.35 * inch, 0.3 * inch, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + 0.675 * inch, H - 3.98 * inch, t)
        x += 1.45 * inch
    footer(c, "QuantumByte-01", "github.com/QuantumByte-01/amd-track2-captioner")


def slide2(c: canvas.Canvas) -> None:
    bg(c)
    badge(c, "Problem", H - 0.9 * inch)
    title(c, "Accuracy + style", H - 1.55 * inch)
    subtitle(c, "10-minute container, LLM judge", H - 2.05 * inch)
    bullet(c, [
        "Judge scores factual accuracy and tone match per style",
        "Generic or hallucinated captions score near zero",
        "~12 clips, 4 styles each, valid JSON required",
        "No API key injected at runtime — baked in Docker image",
    ], H - 2.6 * inch)
    card(c, 7.8 * inch, H - 4.8 * inch, 4.8 * inch, 2.2 * inch, "Four styles", [
        "Formal — objective, detail-rich",
        "Sarcastic — dry, Ah yes... cadence",
        "Humorous-tech — one dev metaphor",
        "Humorous-non-tech — relatable one-liner",
    ])
    footer(c, "StyleCap")


def slide3(c: canvas.Canvas) -> None:
    bg(c)
    badge(c, "Architecture", H - 0.9 * inch)
    title(c, "Fact sheet first", H - 1.55 * inch)
    steps = ["ffmpeg", "Vision JSON", "Write x2", "Judge", "results.json"]
    x = 0.55 * inch
    for i, s in enumerate(steps):
        c.setFillColor(colors.HexColor("#1e293b"))
        c.roundRect(x, H - 2.55 * inch, 1.5 * inch, 0.45 * inch, 8, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + 0.75 * inch, H - 2.38 * inch, s)
        if i < len(steps) - 1:
            c.setFillColor(colors.HexColor("#f97316"))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(x + 1.55 * inch, H - 2.38 * inch, "→")
        x += 1.85 * inch
    bullet(c, [
        "6 uniform-seek frames @ 768px per clip",
        "Parallel workers + 90s per-clip budget",
        "Degradation ladder — never empty output",
        "Schema repair guarantees valid JSON",
    ], H - 3.2 * inch)
    card(c, 0.55 * inch, 0.7 * inch, 5.5 * inch, 1.5 * inch, "Graded models", [
        "kimi-k2p6  —  vision / grounding",
        "glm-5p2    —  write + batched judge",
    ])
    footer(c, "Two-phase anti-hallucination pipeline")


def slide4(c: canvas.Canvas) -> None:
    bg(c)
    badge(c, "Gemma on AMD", H - 0.9 * inch)
    title(c, "MI300X end-to-end", H - 1.55 * inch)
    subtitle(c, "Same pipeline, local vLLM", H - 2.05 * inch)
    mono(c, "google/gemma-3-12b-it", H - 2.55 * inch, 13)
    body(c, [
        "Ground + write + judge — all Gemma via ROCm/vLLM",
        "No Fireworks Gemma deploy — avoids $7/hr credit drain",
        "Demo video: live rocm-smi + pipeline run",
    ], H - 3.0 * inch)
    card(c, 7.5 * inch, H - 4.5 * inch, 4.5 * inch, 2.0 * inch, "Benchmark", [
        "86 seconds — 8 public clips",
        "~40 GB VRAM (82% utilization)",
        "Evidence: GEMMA_RESULTS.md",
    ])
    footer(c, "Partner prize: AMD-hosted Gemma")


def slide5(c: canvas.Canvas) -> None:
    bg(c)
    badge(c, "Submit", H - 0.9 * inch)
    title(c, "Ready for grader", H - 1.55 * inch)
    card(c, 0.55 * inch, H - 3.2 * inch, 11.5 * inch, 0.85 * inch, "Docker image", [
        "ghcr.io/quantumbyte-01/amd-track2-captioner:v34",
    ])
    card(c, 0.55 * inch, H - 4.35 * inch, 11.5 * inch, 0.85 * inch, "Repository", [
        "github.com/QuantumByte-01/amd-track2-captioner",
    ])
    body(c, [
        "linux/amd64 · Public GHCR · CANDIDATES=2 · 9-min soft deadline",
    ], H - 5.0 * inch, 12)
    footer(c, "StyleCap — evidence-locked captions, four voices, one fact sheet.")


def main() -> None:
    out = "/workspace/track2/StyleCap_Slides.pdf"
    c = canvas.Canvas(out, pagesize=(W, H))
    for fn in (slide1, slide2, slide3, slide4, slide5):
        fn(c)
        c.showPage()
    c.save()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
