#!/usr/bin/env python3
"""產生「五十音筆順字帖」PDF（方格＋筆順＋虛線描紅）。

字形來源：KanjiVG（CC BY-SA 4.0，https://kanjivg.tagaini.net）
用法：
    python3 tools/make_worksheet.py            # 產出 downloads/kana-worksheet.pdf
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "kanjivg")
OUT_DIR = os.path.join(ROOT, "downloads")
OUT_PDF = os.path.join(OUT_DIR, "kana-worksheet.pdf")
CHROME = "/home/admin/.cache/ms-playwright/chromium-*/chrome-linux64/chrome"

HIRA = [("あ","a"),("い","i"),("う","u"),("え","e"),("お","o"),
        ("か","ka"),("き","ki"),("く","ku"),("け","ke"),("こ","ko"),
        ("さ","sa"),("し","shi"),("す","su"),("せ","se"),("そ","so"),
        ("た","ta"),("ち","chi"),("つ","tsu"),("て","te"),("と","to"),
        ("な","na"),("に","ni"),("ぬ","nu"),("ね","ne"),("の","no"),
        ("は","ha"),("ひ","hi"),("ふ","fu"),("へ","he"),("ほ","ho"),
        ("ま","ma"),("み","mi"),("む","mu"),("め","me"),("も","mo"),
        ("や","ya"),("ゆ","yu"),("よ","yo"),
        ("ら","ra"),("り","ri"),("る","ru"),("れ","re"),("ろ","ro"),
        ("わ","wa"),("を","wo"),("ん","n")]
KATA = [("ア","a"),("イ","i"),("ウ","u"),("エ","e"),("オ","o"),
        ("カ","ka"),("キ","ki"),("ク","ku"),("ケ","ke"),("コ","ko"),
        ("サ","sa"),("シ","shi"),("ス","su"),("セ","se"),("ソ","so"),
        ("タ","ta"),("チ","chi"),("ツ","tsu"),("テ","te"),("ト","to"),
        ("ナ","na"),("ニ","ni"),("ヌ","nu"),("ネ","ne"),("ノ","no"),
        ("ハ","ha"),("ヒ","hi"),("フ","fu"),("ヘ","he"),("ホ","ho"),
        ("マ","ma"),("ミ","mi"),("ム","mu"),("メ","me"),("モ","mo"),
        ("ヤ","ya"),("ユ","yu"),("ヨ","yo"),
        ("ラ","ra"),("リ","ri"),("ル","ru"),("レ","re"),("ロ","ro"),
        ("ワ","wa"),("ヲ","wo"),("ン","n")]


def fetch_svg(kana):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "%05x.svg" % ord(kana))
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return open(path, encoding="utf-8").read()
    url = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/%05x.svg" % ord(kana)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read().decode("utf-8")
            open(path, "w", encoding="utf-8").write(data)
            return data
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def inner(svg):
    """抽出筆畫 paths 與筆順數字，轉成可嵌入的 <svg>。"""
    paths = re.findall(r'<path id="kvg:[0-9a-f]+-s\d+"[^>]*/>', svg)
    numbers = re.findall(r'<text transform="[^"]*">\d+</text>', svg)
    if not paths:
        raise RuntimeError("no paths")
    stroke = "".join(paths)
    nums = "".join(numbers)
    return stroke, nums


def cell(svg, mode):
    """mode: solid（筆順）｜dashed（虛線描紅）｜blank（空格）"""
    if mode == "blank":
        return '<div class="sq blank"><span class="cross"></span></div>'
    stroke, nums = inner(svg)
    if mode == "solid":
        body = ('<g style="fill:none;stroke:#1d1a16;stroke-width:3.4;stroke-linecap:round;'
                'stroke-linejoin:round">%s</g>%s' % (stroke, nums))
    else:
        body = ('<g style="fill:none;stroke:#b9b1a3;stroke-width:2.2;stroke-linecap:round;'
                'stroke-linejoin:round;stroke-dasharray:4.5 3.4">%s</g>' % stroke)
    return ('<div class="sq"><span class="cross"></span>'
            '<svg viewBox="0 0 109 109"><g style="font-size:8;fill:#9a9285">%s</g></svg></div>' % body)


def block(kana, romaji, svg):
    return ('<div class="row"><div class="lbl"><b>%s</b><span>%s</span></div>%s</div>'
            % (kana, romaji, cell(svg, "solid") + cell(svg, "dashed") + cell(svg, "dashed") + cell(svg, "blank")))


def page(title, rows):
    head = ('<div class="phead"><span class="pt">%s</span>'
            '<span class="pi">按筆順寫一次 → 沿虛線描兩次 → 自己寫一格</span></div>' % title)
    return '<section class="page">%s%s</section>' % (head, "".join(rows))


CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body { margin:0; font-family:"Noto Sans CJK TC","Noto Sans TC",system-ui,sans-serif; color:#1d1a16; }
.page { width:210mm; height:297mm; padding:12mm 12mm 10mm; page-break-after:always;
        display:flex; flex-direction:column; gap:2.6mm; background:#fff; }
.page:last-child { page-break-after:auto; }
.cover { justify-content:center; align-items:center; text-align:center; gap:6mm; }
.cover h1 { font-family:"Noto Serif CJK TC","Noto Serif JP",serif; font-size:34pt; margin:0; letter-spacing:.06em; }
.cover .sub { font-size:13pt; color:#6b6357; letter-spacing:.08em; }
.cover .box { border:1px solid #ddd5c6; border-radius:6mm; padding:7mm 9mm; font-size:10.5pt;
              color:#4a443b; line-height:1.9; text-align:left; max-width:150mm; }
.cover .small { font-size:8pt; color:#9a9285; line-height:1.7; max-width:150mm; }
.phead { display:flex; align-items:baseline; gap:4mm; border-bottom:1px solid #e3dbcc; padding-bottom:1.6mm; }
.phead .pt { font-size:13pt; font-weight:700; letter-spacing:.05em; }
.phead .pi { font-size:8pt; color:#9a9285; }
.row { display:flex; align-items:center; gap:2mm; flex:1; }
.lbl { width:20mm; text-align:center; flex:none; }
.lbl b { display:block; font-family:"Noto Serif JP",serif; font-size:20pt; line-height:1.1; }
.lbl span { font-size:8pt; color:#8c8477; letter-spacing:.04em; }
.sq { flex:1; aspect-ratio:1/1; border:0.6pt solid #cfc6b6; border-radius:1.6mm; position:relative;
      overflow:hidden; background:#fffdf9; }
.sq .cross { position:absolute; inset:0;
      background-image:linear-gradient(to right, transparent 49.6%, #e8e0d1 49.6%, #e8e0d1 50.4%, transparent 50.4%),
                       linear-gradient(to bottom, transparent 49.6%, #e8e0d1 49.6%, #e8e0d1 50.4%, transparent 50.4%);
      opacity:.9; }
.sq svg { position:absolute; inset:4%; width:92%; height:92%; }
"""


def build_pages():
    parts = []
    parts.append("""<section class="page cover">
      <h1>五十音 筆順字帖</h1>
      <div class="sub">あいうえお · 平假名與片假名 · 方格描紅</div>
      <div class="box">
        1. 先看左邊的筆順字，記住每一筆的次序（數字 1、2、3…）。<br>
        2. 沿兩格虛線描紅，筆順要跟足。<br>
        3. 最後一格自己寫，寫完對一對位置。<br>
        4. 每日一行，兩星期可寫完平假名。
      </div>
      <div class="small">
        字形來源：KanjiVG（https://kanjivg.tagaini.net），
        依 Creative Commons Attribution-ShareAlike 4.0 授權使用；本字帖為衍生作品，同樣以 CC BY-SA 4.0 提供。
      </div>
      <div class="small">練習 app：https://alice-creator-lab.github.io/kana-dojo/</div>
    </section>""")

    per_page = 6   # 297mm 高度扣起頁首/邊距，6 行剛好；7 行會爆出頁尾被切
    for label, table in (("平假名 ひらがな", HIRA), ("片假名 カタカナ", KATA)):
        rows = []
        for i, (kana, romaji) in enumerate(table):
            svg = fetch_svg(kana)
            rows.append(block(kana, romaji, svg))
            if len(rows) == per_page or i == len(table) - 1:
                parts.append(page("%s　%d–%d" % (label, i - len(rows) + 2, i + 1), rows))
                rows = []
    return parts


def page_html(body):
    return ("<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
            "<title>五十音 筆順字帖</title><style>%s</style></head><body>%s</body></html>" % (CSS, body))


def html_to_pdf(page_files, pdf_path):
    """逐頁開一個乾淨的 headless Chrome 截圖（A4、2x），再用 PIL 合成 PDF。
    這台機的 --print-to-pdf 會 exit 2、printToPDF 回空、同一瀏覽器連續截圖第二頁會死，
    所以每頁獨立開一次瀏覽器，最穩。"""
    import base64, glob as _glob, json, time, urllib.request
    from PIL import Image
    import websockets

    chrome = sorted(_glob.glob(CHROME))[-1]
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    shots = []

    async def shot(f, idx):
        import asyncio, io
        port = 9760 + idx
        proc = subprocess.Popen(
            [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
             "--single-process", "--no-zygote", "--force-device-scale-factor=2",
             "--remote-debugging-port=%d" % port,
             "--user-data-dir=/tmp/cdp-ws-%d" % idx, "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ver = None
            for _ in range(80):
                try:
                    ver = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2))
                    break
                except Exception:
                    await asyncio.sleep(.3)
            ws = await websockets.connect(ver["webSocketDebuggerUrl"], max_size=None)
            seq = [0]

            async def call(method, params=None, sid=None, t=90):
                seq[0] += 1
                mid = seq[0]
                msg = {"id": mid, "method": method, "params": params or {}}
                if sid:
                    msg["sessionId"] = sid
                await ws.send(json.dumps(msg))
                end = time.time() + t
                while time.time() < end:
                    try:
                        r = json.loads(await asyncio.wait_for(ws.recv(), timeout=max(.1, end - time.time())))
                    except Exception:
                        return {}
                    if r.get("id") == mid:
                        return r
                return {}

            tid = (await call("Target.createTarget", {"url": "about:blank"}))["result"]["targetId"]
            sid = (await call("Target.attachToTarget", {"targetId": tid, "flatten": True}))["result"]["sessionId"]
            await call("Page.enable", {}, sid)
            await call("Emulation.setDeviceMetricsOverride",
                       {"width": 794, "height": 1123, "deviceScaleFactor": 2, "mobile": False}, sid)
            await call("Page.navigate", {"url": "file://" + f}, sid)
            await asyncio.sleep(1.6)
            d = await call("Page.captureScreenshot", {"format": "png"}, sid)
            b64 = d.get("result", {}).get("data")
            if not b64:
                raise RuntimeError("screenshot 失敗 page %d: %s" % (idx, json.dumps(d)[:200]))
            img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
            await ws.close()
            return img
        finally:
            proc.terminate()
            proc.wait(timeout=10)

    for i, f in enumerate(page_files):
        shots.append(__import__("asyncio").run(shot(f, i)))
        print("  page %d/%d ok" % (i + 1, len(page_files)))

    if not shots:
        raise RuntimeError("no pages")
    shots[0].save(pdf_path, "PDF", save_all=True, append_images=shots[1:], resolution=192.0)


def main():
    pages = build_pages()
    os.makedirs(OUT_DIR, exist_ok=True)
    tmpdir = os.path.join(ROOT, "cache", "worksheet-pages")
    os.makedirs(tmpdir, exist_ok=True)
    files = []
    for i, body in enumerate(pages):
        f = os.path.join(tmpdir, "p%02d.html" % i)
        open(f, "w", encoding="utf-8").write(page_html(body))
        files.append(f)
    print("pages:", len(files))
    html_to_pdf(files, OUT_PDF)
    size = os.path.getsize(OUT_PDF)
    print("PDF:", OUT_PDF, "%.1f MB" % (size / 1e6))


if __name__ == "__main__":
    main()
