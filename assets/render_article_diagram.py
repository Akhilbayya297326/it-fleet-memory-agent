"""Render the article's architecture figure from the implemented data flow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SCALE = 2
WIDTH, HEIGHT = 1440, 860
image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "#08111f")
draw = ImageDraw.Draw(image)
FONTS = Path("C:/Windows/Fonts")


def font(size, bold=False):
    return ImageFont.truetype(str(FONTS / ("segoeuib.ttf" if bold else "segoeui.ttf")), size * SCALE)


def text(x, y, value, size=22, fill="#aebdd1", bold=False, anchor=None):
    draw.text((x * SCALE, y * SCALE), value, font=font(size, bold), fill=fill, anchor=anchor)


def line(points, fill="#7087a8", width=3):
    draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=fill, width=width * SCALE)


def arrow(points, fill="#7087a8"):
    line(points, fill)
    x, y = points[-1]
    px, py = points[-2]
    if x > px:
        head = [(x, y), (x - 10, y - 6), (x - 10, y + 6)]
    elif y > py:
        head = [(x, y), (x - 6, y - 10), (x + 6, y - 10)]
    else:
        raise ValueError("Unsupported arrow direction")
    draw.polygon([(a * SCALE, b * SCALE) for a, b in head], fill=fill)


def card(x, y, title, subtitle, detail, accent="#36b7fa"):
    bounds = (x * SCALE, y * SCALE, (x + 370) * SCALE, (y + 160) * SCALE)
    draw.rounded_rectangle(bounds, radius=16 * SCALE, fill="#102036", outline=accent, width=2 * SCALE)
    text(x + 25, y + 22, title, 28, "#edf3fc", True)
    text(x + 25, y + 69, subtitle, 23, accent)
    text(x + 25, y + 112, detail, 20)


text(65, 38, "Where Hindsight sits in Fleet Command", 38, "#edf3fc", True)
text(65, 96, "Verified support cases become reusable evidence for the next conversation.", 24)

text(65, 166, "01  SAVE A VERIFIED RESOLUTION", 18, "#36b7fa", True)
card(65, 208, "Verified tickets", "JSON import or operator form", "Device / OS + issue + resolution")
card(535, 208, "Local SQLite", "Commit before cloud upload", "Stable ID + synchronization state")
card(1005, 208, "Hindsight memory", "Tagged resolution records", "fleet-verified-resolution-v1", "#af87ff")
arrow([(435, 288), (535, 288)])
text(485, 265, "save", 18, anchor="mm")
arrow([(905, 288), (1005, 288)], "#af87ff")
text(955, 265, "retain", 18, "#c6acff", anchor="mm")

arrow([(1190, 368), (1190, 444), (720, 444), (720, 526)], "#af87ff")
text(955, 421, "recall · strict verified tag", 21, "#c6acff", anchor="mm")

text(65, 484, "02  ANSWER A SUPPORT QUESTION", 18, "#38d4af", True)
card(65, 526, "Support request", "Question + device model + OS", "Current readings when opted in", "#38d4af")
card(535, 526, "Application context", "Recall results + conversation", "Recalled facts used as evidence", "#38d4af")
card(1005, 526, "Groq generation", "Streamed answer in the UI", "Memory availability is labeled", "#38d4af")
arrow([(435, 606), (535, 606)], "#38d4af")
arrow([(905, 606), (1005, 606)], "#38d4af")

line([(65, 746), (1375, 746)], "#253852", 1)
text(65, 771, "Upload failure: the ticket stays local for retry.   Empty recall: the answer is labeled as general guidance.", 22)
image.save(ROOT / "hindsight-support-architecture.png", optimize=True)
