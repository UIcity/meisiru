#!/usr/bin/env python3
"""Generate the MEISIRU industry-specific business-card-to-LINE guide.

The script creates the final PDF in both the public assets directory and the
project output directory, renders every page for QA, and creates web-ready
preview images from the rendered pages.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PDF = ROOT / "output" / "pdf" / "meisiru-industry-line-template-guide.pdf"
ASSET_PDF = ROOT / "assets" / "meisiru-industry-line-template-guide.pdf"
OFFER_DIR = ROOT / "assets" / "offer"
RENDER_DIR = ROOT / "tmp" / "pdfs"

OFFER_URL = "https://lin.ee/rxtsy4f"
CONSULT_URL = "https://lin.ee/oGIGfiq"

PAGE_W, PAGE_H = A4

# MEISIRU brand palette
NAVY = HexColor("#102A43")
DEEP_NAVY = HexColor("#071B2B")
BLUE = HexColor("#1C4F73")
TEAL = HexColor("#078A60")
GREEN = HexColor("#0A9B53")
PALE_GREEN = HexColor("#E9F6EF")
PALE_BLUE = HexColor("#EDF4F8")
YELLOW = HexColor("#F3C75B")
PALE_YELLOW = HexColor("#FFF7DC")
INK = HexColor("#173247")
MUTED = HexColor("#5B7080")
LINE = HexColor("#D7E2E8")
OFFWHITE = HexColor("#F7F9F7")
WHITE = white


FONT_REGULAR = Path(r"C:\Windows\Fonts\BIZ-UDGothicR.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\BIZ-UDGothicB.ttc")
FONT_REGULAR_NAME = "BIZUDGothic"
FONT_BOLD_NAME = "BIZUDGothic-Bold"


def register_fonts() -> None:
    if not FONT_REGULAR.exists() or not FONT_BOLD.exists():
        raise FileNotFoundError("BIZ UD Gothic fonts were not found in C:\\Windows\\Fonts")
    pdfmetrics.registerFont(TTFont(FONT_REGULAR_NAME, str(FONT_REGULAR), subfontIndex=0))
    pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, str(FONT_BOLD), subfontIndex=0))
    pdfmetrics.registerFontFamily(
        "BIZUDGothic",
        normal=FONT_REGULAR_NAME,
        bold=FONT_BOLD_NAME,
        italic=FONT_REGULAR_NAME,
        boldItalic=FONT_BOLD_NAME,
    )


def style(
    size: float,
    leading: float | None = None,
    color: Color = INK,
    bold: bool = False,
    align: int = TA_LEFT,
    space_after: float = 0,
) -> ParagraphStyle:
    return ParagraphStyle(
        name=f"s-{size}-{leading}-{bold}-{align}-{color}",
        fontName=FONT_BOLD_NAME if bold else FONT_REGULAR_NAME,
        fontSize=size,
        leading=leading or size * 1.55,
        textColor=color,
        alignment=align,
        wordWrap="CJK",
        splitLongWords=True,
        allowWidows=False,
        allowOrphans=False,
        spaceAfter=space_after,
    )


def plain(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def draw_paragraph(
    c: canvas.Canvas,
    text: str,
    x: float,
    top: float,
    width: float,
    pstyle: ParagraphStyle,
    max_height: float = 1000,
) -> float:
    p = Paragraph(text, pstyle)
    _, h = p.wrap(width, max_height)
    p.drawOn(c, x, top - h)
    return h


def rounded_rect(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: Color,
    stroke: Color | None = None,
    radius: float = 12,
    line_width: float = 1,
) -> None:
    c.saveState()
    c.setFillColor(fill)
    if stroke is None:
        c.setStrokeColor(fill)
    else:
        c.setStrokeColor(stroke)
    c.setLineWidth(line_width)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.restoreState()


def draw_brand(c: canvas.Canvas, x: float, y: float, inverse: bool = False, small: bool = False) -> None:
    size = 24 if small else 30
    c.saveState()
    c.setFillColor(GREEN)
    c.roundRect(x, y, size, size, size * 0.25, fill=1, stroke=0)
    c.setStrokeColor(WHITE)
    c.setLineWidth(2.2 if small else 2.8)
    # A compact card plus an upward path: "a business card that moves business".
    c.roundRect(x + size * 0.20, y + size * 0.27, size * 0.48, size * 0.35, 2, fill=0, stroke=1)
    c.line(x + size * 0.50, y + size * 0.44, x + size * 0.76, y + size * 0.70)
    c.line(x + size * 0.76, y + size * 0.70, x + size * 0.76, y + size * 0.53)
    c.line(x + size * 0.76, y + size * 0.70, x + size * 0.59, y + size * 0.70)
    c.setFillColor(WHITE if inverse else NAVY)
    c.setFont(FONT_BOLD_NAME, 16 if small else 20)
    c.drawString(x + size + 8, y + (3 if small else 4), "メイシル")
    c.restoreState()


def draw_qr(c: canvas.Canvas, url: str, x: float, y: float, size: float, label: str | None = None) -> None:
    pad = 7
    rounded_rect(c, x - pad, y - pad, size + pad * 2, size + pad * 2, WHITE, LINE, radius=8)
    qr = QrCodeWidget(url)
    bounds = qr.getBounds()
    qr_w = bounds[2] - bounds[0]
    qr_h = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size / qr_w, 0, 0, size / qr_h, 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, c, x, y)
    c.linkURL(url, (x - pad, y - pad, x + size + pad, y + size + pad), relative=0)
    if label:
        draw_paragraph(c, plain(label), x - 12, y - 15, size + 24, style(7.8, 10.5, MUTED, align=TA_CENTER))


def draw_footer(c: canvas.Canvas, page_num: int) -> None:
    c.saveState()
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(38, 27, PAGE_W - 38, 27)
    c.setFillColor(MUTED)
    c.setFont(FONT_REGULAR_NAME, 7.2)
    c.drawString(38, 14, "MEISIRU / UIcity Inc.  |  実務テンプレート集")
    c.setFont(FONT_BOLD_NAME, 7.2)
    c.drawRightString(PAGE_W - 38, 14, f"{page_num:02d} / 08")
    c.restoreState()


def draw_page_header(c: canvas.Canvas, page_num: int, kicker: str, title: str, subtitle: str = "") -> None:
    c.setFillColor(OFFWHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 92, PAGE_W, 92, fill=1, stroke=0)
    draw_brand(c, 38, PAGE_H - 55, inverse=True, small=True)
    draw_paragraph(c, plain(kicker), 38, PAGE_H - 103, 235, style(7.8, 10, TEAL, bold=True))
    draw_paragraph(c, plain(title), 38, PAGE_H - 119, PAGE_W - 76, style(20, 26, NAVY, bold=True))
    if subtitle:
        draw_paragraph(c, plain(subtitle), 38, PAGE_H - 148, PAGE_W - 76, style(8.6, 13.5, MUTED))
    draw_footer(c, page_num)


def draw_label(c: canvas.Canvas, text: str, x: float, y: float, color: Color = TEAL) -> None:
    width = pdfmetrics.stringWidth(text, FONT_BOLD_NAME, 8.1) + 18
    rounded_rect(c, x, y, width, 19, color, radius=9.5)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD_NAME, 8.1)
    c.drawString(x + 9, y + 5.1, text)


def content_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    body: str,
    fill: Color = WHITE,
    accent: Color = TEAL,
    font_size: float = 9.5,
    leading: float = 15.3,
) -> None:
    rounded_rect(c, x, y, w, h, fill, LINE, radius=12)
    c.setFillColor(accent)
    c.roundRect(x, y, 5, h, 2.5, fill=1, stroke=0)
    c.setFillColor(accent)
    c.setFont(FONT_BOLD_NAME, 9.1)
    c.drawString(x + 16, y + h - 22, label)
    draw_paragraph(c, plain(body), x + 16, y + h - 36, w - 30, style(font_size, leading, INK))


def cover_page(c: canvas.Canvas) -> None:
    c.bookmarkPage("cover")
    c.addOutlineEntry("表紙", "cover", level=0)
    c.setFillColor(DEEP_NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Subtle geometric field.
    c.saveState()
    c.setFillColor(Color(0.05, 0.40, 0.29, alpha=0.32))
    c.circle(PAGE_W + 10, PAGE_H - 72, 175, fill=1, stroke=0)
    c.setFillColor(Color(0.13, 0.38, 0.54, alpha=0.22))
    c.circle(-35, 130, 205, fill=1, stroke=0)
    c.setStrokeColor(Color(1, 1, 1, alpha=0.08))
    c.setLineWidth(1)
    for offset in range(-200, 700, 34):
        c.line(offset, 0, offset + 420, PAGE_H)
    c.restoreState()

    draw_brand(c, 42, PAGE_H - 76, inverse=True)
    c.setFillColor(YELLOW)
    c.setFont(FONT_BOLD_NAME, 8.5)
    c.drawRightString(PAGE_W - 42, PAGE_H - 56, "MEISIRU PRACTICAL GUIDE 01")

    draw_label(c, "日本国内の事業主向け", 42, PAGE_H - 143, TEAL)
    draw_paragraph(c, "そのまま使える", 42, PAGE_H - 181, 460, style(17, 22, YELLOW, bold=True))
    draw_paragraph(c, "業種別 名刺→LINE<br/>導線テンプレート集", 42, PAGE_H - 216, 500, style(33, 44, WHITE, bold=True))
    draw_paragraph(
        c,
        plain("名刺の一文から、登録直後のLINE、相談案内まで。\n4業種の完成文を、実装順にまとめました。"),
        45,
        PAGE_H - 324,
        455,
        style(12, 20, HexColor("#DCE8EE")),
    )

    chips = ["士業・コンサル", "不動産・保険", "サロン・店舗", "法人営業・展示会"]
    cx = 42
    for chip in chips:
        w = pdfmetrics.stringWidth(chip, FONT_BOLD_NAME, 8.5) + 22
        rounded_rect(c, cx, PAGE_H - 400, w, 28, Color(1, 1, 1, alpha=0.09), Color(1, 1, 1, alpha=0.25), radius=14)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD_NAME, 8.5)
        c.drawString(cx + 11, PAGE_H - 391, chip)
        cx += w + 8

    rounded_rect(c, 42, 102, PAGE_W - 84, 196, HexColor("#F4F8F6"), radius=18)
    draw_paragraph(c, "LINEで最新版を受け取る", 64, 266, 300, style(15, 20, NAVY, bold=True))
    draw_paragraph(
        c,
        plain("右のQRから無料で受け取れます。\nスマートフォンで読み取ってください。"),
        64,
        232,
        300,
        style(9.3, 15.5, MUTED),
    )
    rounded_rect(c, 64, 130, 268, 38, GREEN, radius=19)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD_NAME, 10)
    c.drawCentredString(198, 143, "名刺→LINE導線を今日から始める")
    c.linkURL(OFFER_URL, (64, 130, 332, 168), relative=0)
    draw_qr(c, OFFER_URL, 397, 143, 102, "無料受け取り用")

    draw_paragraph(
        c,
        plain("本書は導線設計の調整例です。成果を保証するものではありません。各業界の法令・広告規制・社内ルールに合わせてご利用ください。"),
        42,
        73,
        PAGE_W - 84,
        style(7.2, 11, HexColor("#ADC0CB"), align=TA_CENTER),
    )
    c.showPage()


def basic_page(c: canvas.Canvas) -> None:
    c.bookmarkPage("basic")
    c.addOutlineEntry("基本設計と目次", "basic", level=0)
    draw_page_header(c, 2, "BASIC DESIGN", "まず、導線はこの5点でつくります", "登録特典（無料オファー）を中心に、次の行動までを一本につなぎます。")

    labels = [("01", "名刺の\n一文"), ("02", "渡す時の\n一言"), ("03", "LINE\n登録"), ("04", "登録特典を\n即時提供"), ("05", "相談\nCTA")]
    x0, y0, gap = 38, 590, 9
    box_w = (PAGE_W - 76 - gap * 4) / 5
    for idx, (num, text_value) in enumerate(labels):
        x = x0 + idx * (box_w + gap)
        rounded_rect(c, x, y0, box_w, 88, WHITE, LINE, radius=12)
        c.setFillColor(GREEN if idx < 4 else YELLOW)
        c.circle(x + box_w / 2, y0 + 64, 13, fill=1, stroke=0)
        c.setFillColor(WHITE if idx < 4 else NAVY)
        c.setFont(FONT_BOLD_NAME, 7.8)
        c.drawCentredString(x + box_w / 2, y0 + 61.5, num)
        draw_paragraph(c, plain(text_value), x + 5, y0 + 45, box_w - 10, style(8.6, 12.5, NAVY, bold=True, align=TA_CENTER))
        if idx < 4:
            c.setFillColor(TEAL)
            c.setFont(FONT_BOLD_NAME, 12)
            c.drawCentredString(x + box_w + gap / 2, y0 + 38, "→")

    rounded_rect(c, 38, 318, 326, 266, WHITE, LINE, radius=14)
    draw_label(c, "設計の3原則", 56, 548, TEAL)
    principles = [
        ("1", "小さな悩みを1つだけ解決", "広いテーマより、受け取った直後に役立つチェックリストやシートに絞ります。"),
        ("2", "約束した価値をすぐ渡す", "登録後の最初のメッセージから、迷わず特典を開ける状態にします。"),
        ("3", "相談は選べる次の一歩に", "売り込みではなく、必要な人だけが返信できる案内にします。"),
    ]
    top = 516
    for num, heading, description in principles:
        c.setFillColor(PALE_GREEN)
        c.circle(66, top - 10, 14, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.setFont(FONT_BOLD_NAME, 9)
        c.drawCentredString(66, top - 13, num)
        draw_paragraph(c, plain(heading), 91, top, 250, style(10.2, 14, NAVY, bold=True))
        draw_paragraph(c, plain(description), 91, top - 22, 250, style(8.2, 13, MUTED))
        top -= 72

    rounded_rect(c, 378, 318, PAGE_W - 416, 266, PALE_BLUE, LINE, radius=14)
    draw_label(c, "CONTENTS", 394, 548, BLUE)
    contents = [
        "03  士業・コンサル",
        "04  不動産・保険",
        "05  サロン・店舗",
        "06  法人営業・展示会",
        "07  穴埋めワーク",
        "08  7日間の実装計画",
    ]
    top = 515
    for item in contents:
        c.setStrokeColor(LINE)
        c.line(396, top - 17, PAGE_W - 56, top - 17)
        draw_paragraph(c, plain(item), 396, top, PAGE_W - 452, style(8.4, 12, INK, bold=True))
        top -= 31

    rounded_rect(c, 38, 82, PAGE_W - 76, 214, NAVY, radius=16)
    draw_paragraph(c, "共通の型", 56, 270, 280, style(8.2, 11, YELLOW, bold=True))
    draw_paragraph(c, "LINE登録で、［成果物］を無料でお渡しします。", 56, 245, 346, style(14, 20, WHITE, bold=True))
    draw_paragraph(
        c,
        plain("登録直後：お礼 → 特典リンク → 使い方 → 返信案内\n相談CTA：必要でしたら「相談」と送ってください。"),
        56,
        195,
        340,
        style(9.2, 16, HexColor("#DDE8EE")),
    )
    draw_qr(c, OFFER_URL, 433, 125, 86, "最新版を受け取る")
    c.showPage()


INDUSTRIES = [
    {
        "bookmark": "professional",
        "page": 3,
        "kicker": "TEMPLATE 01 / PROFESSIONAL SERVICE",
        "title": "士業・コンサル",
        "subtitle": "初回相談の前に「何を整理すればよいか」を渡し、相談の質を高める設計です。",
        "benefit": "相談前に整理できる\n「初回相談チェックシート」",
        "card": "LINE登録で、初回相談前に確認したい7項目を無料でお渡しします。",
        "handoff": "ご相談の前に整理しておくと話が早い項目を、LINEで無料配布しています。よろしければお使いください。",
        "welcome": "友だち追加ありがとうございます。\n\n初回相談チェックシートをお送りします。現在の状況、期限、関係者、手元の資料など、相談前に確認したい7項目を1枚にまとめています。\n\n下のリンクから受け取り、分かる範囲でご記入ください。すべて埋める必要はありません。ご不明点は、このLINEにそのままご返信ください。",
        "cta": "チェックシートで整理しても判断が難しい項目がありましたら、「相談」と送ってください。状況を伺い、当方の対応範囲と費用の目安をご案内します。",
        "caution": "各士業の広告規程・職業倫理・業法に合わせて調整してください。結果や法的結論を断定せず、正式な見解は個別確認後に提示します。",
    },
    {
        "bookmark": "realestate",
        "page": 4,
        "kicker": "TEMPLATE 02 / REAL ESTATE & INSURANCE",
        "title": "不動産・保険",
        "subtitle": "急かさずに比較の軸を渡し、条件整理から相談へつなげる設計です。",
        "benefit": "失敗を減らす\n「比較前チェックリスト」",
        "card": "LINE登録で、物件・保険を比較する前の確認リストを無料でお渡しします。",
        "handoff": "すぐに決める必要はありません。比較するときの確認項目をLINEでお渡ししています。",
        "welcome": "友だち追加ありがとうございます。\n\n物件・保険を比べる前のチェックリストをお送りします。希望条件、優先順位、費用、将来の変化など、比較前に確認したいポイントをまとめました。\n\n下のリンクから受け取り、気になる項目に印を付けてください。商品や契約を勧める前の条件整理にお使いいただけます。",
        "cta": "条件整理を一緒に行う場合は、「相談」と送ってください。取扱範囲、進め方、費用の有無を事前にご案内します。",
        "caution": "収益、価格、保険料、将来の結果を保証しません。宅建業法・保険業法・広告表示・社内審査に合わせ、機微な個人情報はLINEで収集しない運用にしてください。",
    },
    {
        "bookmark": "salon",
        "page": 5,
        "kicker": "TEMPLATE 03 / SALON & STORE",
        "title": "サロン・店舗",
        "subtitle": "来店前にも価値を感じてもらい、メニュー選びの不安を減らす設計です。",
        "benefit": "来店前に使える\n「お悩み別セルフケアガイド」",
        "card": "LINE登録で、ご来店前にも使えるセルフケアガイドを無料でお渡しします。",
        "handoff": "ご自宅で試せる簡単なケア方法をLINEでお渡ししています。合うものだけお使いください。",
        "welcome": "友だち追加ありがとうございます。\n\nお悩み別セルフケアガイドをお送りします。ご自宅で試せる基本のケアと、避けたい行動を短くまとめました。\n\n下のリンクから受け取り、無理のない範囲でお試しください。体調や肌の状態などに不安がある場合は、使用を控えて専門家へご相談ください。",
        "cta": "施術・メニュー選びに迷う場合は、「相談」と送ってください。ご希望を伺い、当店で対応可能なメニューをご案内します。",
        "caution": "治療・改善などの医療的な効果を断定しません。薬機法、景品表示法、業界ガイドラインに合わせ、アレルギー・妊娠中・持病などへの注意も追加してください。",
    },
    {
        "bookmark": "b2b",
        "page": 6,
        "kicker": "TEMPLATE 04 / B2B & EXHIBITION",
        "title": "法人営業・展示会",
        "subtitle": "担当者が社内共有しやすい1枚を渡し、次の打ち合わせを具体化する設計です。",
        "benefit": "社内共有に使える\n「課題整理シート＋サービス概要」",
        "card": "LINE登録で、社内共有に使える課題整理シートとサービス概要をお渡しします。",
        "handoff": "社内で検討しやすいよう、要点を1枚にまとめた資料をLINEでお渡ししています。",
        "welcome": "友だち追加ありがとうございます。\n\n社内共有に使える課題整理シートとサービス概要をお送りします。現状、目標、関係部署、希望時期、判断条件を1枚で整理できます。\n\n下のリンクから受け取り、社内検討にご活用ください。機密情報は記入せず、必要な場合は安全な方法を別途ご案内します。",
        "cta": "具体的な要件整理をご希望でしたら、「相談」と送ってください。対象範囲、進め方、費用の目安を整理してご案内します。",
        "caution": "売上増加・コスト削減などの結果を保証しません。社名・ロゴ・事例は掲載許可を確認し、顧客情報や機密情報をLINEで送らない運用にしてください。",
    },
]


def industry_page(c: canvas.Canvas, data: dict[str, object]) -> None:
    page_num = int(data["page"])
    bookmark = str(data["bookmark"])
    c.bookmarkPage(bookmark)
    c.addOutlineEntry(str(data["title"]), bookmark, level=0)
    draw_page_header(c, page_num, str(data["kicker"]), str(data["title"]), str(data["subtitle"]))

    left_x, right_x, gap = 38, 304, 12
    col_w = (PAGE_W - 76 - gap) / 2
    content_top = 674

    content_card(c, left_x, content_top - 126, col_w, 126, "登録特典のアイデア", str(data["benefit"]), PALE_GREEN, TEAL, 12, 19)
    content_card(c, left_x, content_top - 304, col_w, 166, "名刺に載せる一文", str(data["card"]), WHITE, BLUE, 11, 18)
    content_card(c, left_x, content_top - 482, col_w, 166, "名刺を渡す時の一言", str(data["handoff"]), WHITE, BLUE, 10.2, 17)

    content_card(c, right_x, content_top - 294, col_w, 294, "登録直後のLINEメッセージ", str(data["welcome"]), WHITE, TEAL, 8.9, 14.6)
    content_card(c, right_x, content_top - 482, col_w, 176, "相談への案内", str(data["cta"]), PALE_YELLOW, HexColor("#C69114"), 9.7, 16.5)

    rounded_rect(c, 38, 43, PAGE_W - 76, 92, NAVY, radius=12)
    c.setFillColor(YELLOW)
    c.setFont(FONT_BOLD_NAME, 8.2)
    c.drawString(54, 113, "調整時の注意")
    draw_paragraph(c, plain(str(data["caution"])), 54, 97, PAGE_W - 108, style(7.8, 12.5, HexColor("#E2EBF0")))
    c.showPage()


def worksheet_page(c: canvas.Canvas) -> None:
    c.bookmarkPage("worksheet")
    c.addOutlineEntry("穴埋めワーク", "worksheet", level=0)
    draw_page_header(c, 7, "WORKSHEET", "自社用の完成文をつくる穴埋めワーク", "5つの材料を埋めるだけで、名刺から相談までの文章が一本につながります。")

    fields = [
        ("01", "誰に", "例：開業3年以内の小規模事業主"),
        ("02", "どんな小さな悩みを", "例：名刺交換後の連絡が続かない"),
        ("03", "何で解決するか", "例：7項目のチェックリスト"),
        ("04", "どこから受け取るか", "例：登録直後のLINEメッセージ"),
        ("05", "次の行動は何か", "例：「相談」と返信 / 予約 / 資料請求"),
    ]
    top = 674
    for idx, (num, heading, example) in enumerate(fields):
        row = idx // 2
        col = idx % 2
        w = 250 if idx < 4 else PAGE_W - 76
        x = 38 + col * 269 if idx < 4 else 38
        y = top - row * 112 - 96 if idx < 4 else 354
        h = 96
        rounded_rect(c, x, y, w, h, WHITE, LINE, radius=12)
        rounded_rect(c, x + 12, y + h - 32, 34, 20, TEAL, radius=10)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD_NAME, 7.8)
        c.drawCentredString(x + 29, y + h - 25, num)
        draw_paragraph(c, plain(heading), x + 55, y + h - 14, w - 69, style(9.5, 13, NAVY, bold=True))
        draw_paragraph(c, plain(example), x + 15, y + h - 44, w - 30, style(7.5, 11, MUTED))
        c.setStrokeColor(HexColor("#B8C8D0"))
        c.setLineWidth(0.8)
        c.line(x + 15, y + 19, x + w - 15, y + 19)

    rounded_rect(c, 38, 77, PAGE_W - 76, 264, NAVY, radius=16)
    draw_label(c, "完成文に変換", 56, 307, GREEN)
    formulas = [
        ("登録特典名", "［対象］向け ［悩み］を整理する ［形式］"),
        ("名刺の一文", "LINE登録で、［成果物］を無料でお渡しします。"),
        ("渡す時の一言", "［場面］で使える［成果物］をLINEでお渡ししています。"),
        ("登録直後", "友だち追加ありがとうございます。［成果物］はこちらです。"),
        ("相談CTA", "必要でしたら「相談」と送ってください。"),
    ]
    top = 278
    for label, formula in formulas:
        c.setFillColor(YELLOW)
        c.setFont(FONT_BOLD_NAME, 7.5)
        c.drawString(57, top - 1, label)
        draw_paragraph(c, plain(formula), 132, top + 3, PAGE_W - 190, style(9.1, 13, WHITE, bold=True))
        c.setStrokeColor(Color(1, 1, 1, alpha=0.14))
        c.line(56, top - 13, PAGE_W - 56, top - 13)
        top -= 42
    c.showPage()


def final_page(c: canvas.Canvas) -> None:
    c.bookmarkPage("action")
    c.addOutlineEntry("7日間の実装計画", "action", level=0)
    draw_page_header(c, 8, "7-DAY ACTION PLAN", "7日で、名刺→LINE導線を動かす", "完璧を待たず、小さく公開して反応を記録します。")

    days = [
        ("DAY 1", "特典を1つに絞る", "相手の小さな悩みを1つ決める"),
        ("DAY 2", "特典を作る", "1〜3ページのPDFでも十分"),
        ("DAY 3", "名刺の一文を書く", "何が無料で手に入るかを明記"),
        ("DAY 4", "登録直後を設定", "お礼・リンク・使い方を1通に"),
        ("DAY 5", "相談CTAを置く", "「相談」と返信できる形に"),
        ("DAY 6", "スマホで通しテスト", "QR、リンク、文面を自分で確認"),
        ("DAY 7", "開始して記録", "配布数・登録数・相談数を記録"),
    ]
    x, y_top, row_h = 38, 678, 47
    for idx, (day, title, note) in enumerate(days):
        y = y_top - (idx + 1) * row_h
        fill = WHITE if idx % 2 == 0 else PALE_BLUE
        rounded_rect(c, x, y, 325, row_h - 6, fill, LINE, radius=10)
        rounded_rect(c, x + 10, y + 12, 58, 22, TEAL if idx < 6 else GREEN, radius=11)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD_NAME, 7.2)
        c.drawCentredString(x + 39, y + 19, day)
        draw_paragraph(c, plain(title), x + 79, y + 36, 225, style(9, 12, NAVY, bold=True))
        draw_paragraph(c, plain(note), x + 79, y + 20, 225, style(7.2, 10.5, MUTED))

    rounded_rect(c, 380, 354, PAGE_W - 418, 324, NAVY, radius=16)
    draw_label(c, "NEXT STEP", 397, 642, GREEN)
    draw_paragraph(c, "自社向けに<br/>整えたい方へ", 398, 607, 145, style(17, 23, WHITE, bold=True))
    draw_paragraph(c, plain("LINEで「相談」と\n送ってください。"), 398, 545, 145, style(10.2, 16, YELLOW, bold=True))
    draw_qr(c, CONSULT_URL, 418, 405, 106, "相談用LINE")
    draw_paragraph(c, plain("名刺の一文・登録特典・配信文・相談先を一緒に整理します。"), 397, 382, 148, style(7.6, 11.5, HexColor("#DCE8EE"), align=TA_CENTER))

    rounded_rect(c, 38, 59, PAGE_W - 76, 276, WHITE, LINE, radius=14)
    draw_label(c, "ご利用前の注意", 56, 299, BLUE)
    notes = [
        "本書の文章は導線設計の調整例です。売上・登録・成約などの成果を保証するものではありません。",
        "業種ごとの法令、広告規制、表示義務、プラットフォーム規約、社内審査に合わせて調整してください。",
        "料金、契約条件、対応範囲は、相談者に誤解がないよう個別に確認・提示してください。",
        "顧客情報、健康情報、契約情報、社内機密などの機微情報をLINEで収集・送信しないでください。",
        "「LINE」はLINEヤフー株式会社の商標または登録商標です。本書は同社の提供・保証によるものではありません。",
    ]
    top = 269
    for idx, note in enumerate(notes, 1):
        c.setFillColor(PALE_GREEN)
        c.circle(67, top - 7, 9, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.setFont(FONT_BOLD_NAME, 6.8)
        c.drawCentredString(67, top - 9.5, str(idx))
        draw_paragraph(c, plain(note), 84, top, PAGE_W - 142, style(7.6, 12, INK))
        top -= 43
    c.showPage()


def build_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("そのまま使える 業種別 名刺→LINE導線テンプレート集")
    c.setAuthor("MEISIRU / UIcity Inc.")
    c.setSubject("日本国内の事業主向け 名刺からLINE登録・相談につなげる実務テンプレート")
    c.setCreator("MEISIRU PDF Generator")
    cover_page(c)
    basic_page(c)
    for item in INDUSTRIES:
        industry_page(c, item)
    worksheet_page(c)
    final_page(c)
    c.save()


def locate_pdftoppm() -> Path:
    bundled = Path(
        r"C:\Users\hmimu\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"
    )
    if bundled.exists():
        return bundled
    on_path = shutil.which("pdftoppm")
    if on_path:
        return Path(on_path)
    raise FileNotFoundError("pdftoppm was not found. Install Poppler or add it to PATH.")


def render_pdf(path: Path) -> list[Path]:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    for old in RENDER_DIR.glob("meisiru-page-*.png"):
        old.unlink()
    prefix = RENDER_DIR / "meisiru-page"
    subprocess.run(
        [str(locate_pdftoppm()), "-png", "-r", "170", str(path), str(prefix)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pages = sorted(
        RENDER_DIR.glob("meisiru-page-*.png"),
        key=lambda p: int(re.search(r"-(\d+)\.png$", p.name).group(1)),
    )
    if len(pages) != 8:
        raise RuntimeError(f"Expected 8 rendered pages, found {len(pages)}")
    normalized: list[Path] = []
    for idx, page in enumerate(pages, 1):
        target = RENDER_DIR / f"meisiru-page-{idx:02d}.png"
        if page != target:
            if target.exists():
                target.unlink()
            page.rename(target)
        normalized.append(target)
    return normalized


def resized(image: Image.Image, width: int) -> Image.Image:
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def create_previews(pages: list[Path]) -> None:
    OFFER_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(pages[0]) as im:
        cover = resized(im.convert("RGB"), 1200)
        cover.save(OFFER_DIR / "offer-cover.png", format="PNG", optimize=True)
        cover.save(OFFER_DIR / "offer-cover.webp", format="WEBP", quality=91, method=6)

    for index in range(1, 8):
        with Image.open(pages[index]) as im:
            filename = f"offer-page-{index + 1:02d}.webp"
            width = 900
            thumb = resized(im.convert("RGB"), width)
            thumb.save(OFFER_DIR / filename, format="WEBP", quality=88, method=6)

    thumbs: list[Image.Image] = []
    for page in pages[2:6]:
        with Image.open(page) as im:
            thumbs.append(resized(im.convert("RGB"), 455))
    gutter, outer = 18, 26
    tile_h = max(im.height for im in thumbs)
    sheet = Image.new("RGB", (outer * 2 + 455 * 2 + gutter, outer * 2 + tile_h * 2 + gutter), "#102A43")
    draw = ImageDraw.Draw(sheet)
    for idx, im in enumerate(thumbs):
        x = outer + (idx % 2) * (455 + gutter)
        y = outer + (idx // 2) * (tile_h + gutter)
        draw.rounded_rectangle((x - 4, y - 4, x + im.width + 4, y + im.height + 4), radius=8, fill="#FFFFFF")
        sheet.paste(im, (x, y))
    sheet.save(OFFER_DIR / "industry-pages-preview.webp", format="WEBP", quality=88, method=6)


def main() -> None:
    register_fonts()
    build_pdf(OUTPUT_PDF)
    ASSET_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUTPUT_PDF, ASSET_PDF)
    pages = render_pdf(OUTPUT_PDF)
    create_previews(pages)
    print(f"PDF: {OUTPUT_PDF}")
    print(f"Public PDF: {ASSET_PDF}")
    print(f"Rendered pages: {len(pages)} in {RENDER_DIR}")
    print(f"Previews: {OFFER_DIR}")


if __name__ == "__main__":
    main()
