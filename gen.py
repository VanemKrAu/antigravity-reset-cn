#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 Google Antigravity（反重力）额度重置公告的英文源，翻成中文 RSS。

数据源：agyresets.com/feed.xml（同一件事的另一个英文账本 antigravityreset.online/feed.xml 作为补充）
翻译：MyMemory 免费接口（匿名 5000 字符/天），带本地缓存，翻过的不再翻
输出：feed.xml（RSS 2.0，中文标题 + 中文正文 + 英文原文 + 原帖链接）
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(HERE, "cache.json")
OUT_PATH = os.path.join(HERE, "feed.xml")

SOURCES = [
    "https://agyresets.com/feed.xml",
    "https://antigravityreset.online/feed.xml",
]

UA = "Mozilla/5.0 (compatible; AntigravityResetCN/1.0; +https://github.com/VanemKrAu/antigravity-reset-cn)"
BJT = timezone(timedelta(hours=8))

# MyMemory 会把产品名硬翻成中文，翻完再改回来
FIX_TERMS = [
    ("反重力", "Antigravity"), ("双子座", "Gemini"), ("双子", "Gemini"),
    ("霓虹", "Neon"), ("氖", "Neon"), ("碳模型", "Carbon"), ("氢模型", "Hydrogen"),
    ("氩模型", "Argon"), ("蜂群", "Swarms"), ("群集", "Swarms"),
    ("quota", "额度"), ("Quota", "额度"),
]


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_events():
    """两个源都拉，按 guid 去重，按时间倒序"""
    seen, events = set(), []
    for src in SOURCES:
        try:
            raw = http_get(src)
            root = ET.fromstring(raw)
        except Exception as e:
            print(f"[warn] 拉取失败 {src}: {e}", file=sys.stderr)
            continue

        # RSS 2.0
        for it in root.findall(".//item"):
            link_el = it.find("link")
            guid_el = it.find("guid")
            title_el = it.find("title")
            date_el = it.find("pubDate")
            desc_el = it.find("description")
            link = (link_el.text or "").strip() if link_el is not None else ""
            guid = (guid_el.text or link).strip() if guid_el is not None else link
            if not guid or guid in seen:
                continue
            seen.add(guid)
            events.append({
                "guid": guid,
                "link": link,
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "date": parse_date((date_el.text or "") if date_el is not None else ""),
                "desc": (desc_el.text or "").strip() if desc_el is not None else "",
            })

        # Atom
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for en in root.findall("a:entry", ns):
            id_el = en.find("a:id", ns)
            link_el = en.find("a:link", ns)
            title_el = en.find("a:title", ns)
            upd_el = en.find("a:updated", ns)
            sum_el = en.find("a:summary", ns)
            cont_el = en.find("a:content", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            guid = (id_el.text or link) if id_el is not None else link
            if not guid or guid in seen:
                continue
            seen.add(guid)
            desc = ""
            if sum_el is not None and sum_el.text:
                desc = sum_el.text.strip()
            if cont_el is not None and cont_el.text:
                desc = (desc + "\n\n" + cont_el.text.strip()).strip()
            events.append({
                "guid": guid,
                "link": link,
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "date": parse_date((upd_el.text or "") if upd_el is not None else ""),
                "desc": desc,
            })

    # 两个源报道同一件事，时间一致，按分钟去重，保留先到的（agyresets 更及时）
    uniq, keys = [], set()
    for e in events:
        k = int(e["date"].timestamp() // 60) if e["date"] else f"t{len(uniq)}"
        if k in keys:
            continue
        keys.add(k)
        uniq.append(e)
    uniq.sort(key=lambda e: e["date"] or datetime(1970, 1, 1, tzinfo=timezone.utc), reverse=True)
    return uniq


def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


# ---------- 翻译 ----------

_cache = {}
if os.path.exists(CACHE_PATH):
    try:
        _cache = json.load(open(CACHE_PATH, encoding="utf-8"))
    except Exception:
        _cache = {}


def fix_terms(text):
    for a, b in FIX_TERMS:
        text = text.replace(a, b)
    return text


def mt(text):
    """逐段翻译（MyMemory 有长度限制），带缓存"""
    text = (text or "").strip()
    if not text:
        return ""
    if text in _cache:
        return _cache[text]

    out = []
    for chunk in split_chunks(text, 450):
        q = urllib.parse.urlencode({"q": chunk, "langpair": "en|zh-CN"})
        r = None
        for attempt in range(3):
            try:
                raw = http_get(f"https://api.mymemory.translated.net/get?{q}", timeout=25)
                data = json.loads(raw.decode("utf-8", "replace"))
                r = (data.get("responseData") or {}).get("translatedText")
                if r and "MYMEMORY WARNING" not in r:
                    break
                r = None
            except Exception as e:
                print(f"[warn] 翻译失败: {e}", file=sys.stderr)
                r = None
            time.sleep(2)
        if r:
            out.append(fix_terms(r))
        else:
            out.append(chunk)  # 翻不了就保留原文，不让整条挂掉
        time.sleep(0.8)

    result = " ".join(out).strip()
    if result and result != text:      # 失败时保留原文，但不要写进缓存，下次还得重试
        _cache[text] = result
    return result


def split_chunks(text, size):
    if len(text) <= size:
        return [text]
    parts, cur = [], ""
    for seg in re.split(r"(?<=[.!?。！？])\s+", text):
        if len(cur) + len(seg) + 1 > size:
            if cur:
                parts.append(cur.strip())
            cur = seg
        else:
            cur = (cur + " " + seg).strip()
    if cur:
        parts.append(cur.strip())
    return parts


MODEL_WORDS = [("gemini", "Gemini"), ("carbon", "Carbon"), ("neon", "Neon"),
               ("argon", "Argon"), ("hydrogen", "Hydrogen"),
               ("claude", "Claude"), ("gpt", "GPT")]


def model_label(en_text):
    t = en_text.lower()
    if "all models" in t or "across all models" in t:
        return "全部模型"
    hit = []
    for k, label in MODEL_WORDS:
        if k in t and label not in hit:
            hit.append(label)
    return " + ".join(hit) if hit else "全部模型"


def guess_scope(en_text):
    t = en_text.lower()
    if "everyone" in t or "all users" in t:
        return "全体用户"
    tags = []
    if "ultra" in t:
        tags.append("Ultra")
    if "pro" in t:
        tags.append("Pro 用户")
    if "free" in t:
        tags.append("免费用户")
    return "、".join(tags) if tags else "未说明范围"


def clean_title(en):
    t = (en or "").strip()
    t = re.sub(r"^(Quota reset|Reset|Quota)\s*[:\-—]\s*", "", t, flags=re.I)
    if len(t) > 110:
        t = t[:110].rsplit(" ", 1)[0] + "…"
    return t


def build_feed(events):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for e in events[:40]:
        en_blob = e["title"] + " " + e["desc"]
        en_title = clean_title(e["title"])
        zh_title = fix_terms(mt(en_title)) if en_title else "额度重置"
        zh_title = zh_title.strip()
        scope = guess_scope(e["title"] + " " + e["desc"])
        if e["date"]:
            bjt = e["date"].astimezone(BJT)
            head = f"{bjt.month}月{bjt.day}日 {bjt:%H:%M} · {scope} · {model_label(en_blob)} 额度重置"
            pub = e["date"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        else:
            head = f"{scope} · {model_label(en_blob)} 额度重置"
            pub = now

        body_en = e["desc"].strip()
        # 去掉源自带的前缀噪音
        body_en = re.sub(r"^Source:\s*https?://\S+\s*$", "", body_en, flags=re.M | re.I).strip()
        zh = mt(body_en) if body_en else zh_title
        zh_title_short = zh_title

        html = [
            f"<p><strong>{escape(model_label(en_blob))} 额度重置 · {escape(scope)}</strong></p>",
            f"<p>{escape(zh)}</p>" if zh else "",
            f"<p style=\"color:#888\">原文：{escape(body_en)}</p>" if body_en else "",
            f"<p>适用范围：{escape(scope)}　｜　北京时间：{e['date'].astimezone(BJT).strftime('%Y-%m-%d %H:%M') if e['date'] else '未知'}</p>",
            f"<p><a href=\"{escape(e['link'])}\">查看原帖</a></p>",
        ]
        desc_html = "\n".join(x for x in html if x)

        items.append(f"""    <item>
      <title>{escape(head)}</title>
      <link>{escape(e['link'])}</link>
      <guid isPermaLink="false">{escape(e['guid'])}</guid>
      <pubDate>{pub}</pubDate>
      <category>额度重置</category>
      <description><![CDATA[{desc_html}]]></description>
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>反重力额度重置（中文）</title>
    <link>https://vanemkrau.github.io/antigravity-reset-cn/</link>
    <description>Google Antigravity（反重力）全员额度重置公告，自动翻译成中文，每 15 分钟同步一次。数据来自 agyresets.com 与 antigravityreset.online，非官方。</description>
    <language>zh-CN</language>
    <ttl>15</ttl>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="https://vanemkrau.github.io/antigravity-reset-cn/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


def escape(s):
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def main():
    events = fetch_events()
    print(f"共 {len(events)} 条事件")
    if not events:
        print("没有事件，保留旧 feed", file=sys.stderr)
        return 1

    xml = build_feed(events)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(xml)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(_cache, f, ensure_ascii=False, indent=0)

    print(f"已写出 {OUT_PATH}，{len(xml)} 字节，翻译缓存 {len(_cache)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
