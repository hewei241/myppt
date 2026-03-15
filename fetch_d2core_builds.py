# -*- coding: utf-8 -*-
"""
从本地「Build大厅 _ 暗黑核.html」中解析每个玩法的 职业、评论数、点赞数，
按职业聚合热度，并写入 JSON 文件。
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装: pip install beautifulsoup4 lxml")
    raise SystemExit(1)

# 默认与脚本同目录下的 HTML 文件
SCRIPT_DIR = Path(__file__).resolve().parent
HTML_FILE = SCRIPT_DIR / "Build大厅 _ 暗黑核.html"
OUTPUT_JSON = SCRIPT_DIR / "assets" / "diablo4" / "d2core_builds_heat.json"

# 职业英文 -> 中文（暗黑核 class 为英文，如 Paladin, Barbarian）
CLASS_EN_TO_ZH = {
    "Barbarian": "野蛮人",
    "Sorcerer": "魔法使",
    "Rogue": "侠盗",
    "Necromancer": "死灵法师",
    "Druid": "德鲁伊",
    "Spiritborn": "魂灵师",
    "Paladin": "圣教军",
}
CLASS_NAMES = tuple(CLASS_EN_TO_ZH.values())


def _to_int(s: str) -> int:
    if not s:
        return 0
    s = re.sub(r"\s+", "", str(s).strip())
    if not s:
        return 0
    s_lower = s.lower().replace("+", "")
    if s_lower.endswith("k") or s_lower.endswith("w"):
        try:
            return int(float(s_lower[:-1].replace("w", "")) * (1000 if "k" in s_lower else 10000))
        except ValueError:
            return 0
    try:
        return int(s)
    except ValueError:
        return 0


def load_html(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_from_script_json(html: str) -> list[dict]:
    """从 script 或内联 JSON 中尝试提取 build 列表。"""
    builds = []
    # 匹配 "builds"/"list" 等键对应的 JSON 数组（限制长度避免过慢）
    for key in ("builds", "buildList", "list", "data", "items"):
        pat = re.compile(
            rf'"{key}"\s*:\s*(\[\s*\{{[\s\S]*?\}}\s*(?:,\s*\{{[\s\S]*?\}}\s*)*\])',
            re.DOTALL,
        )
        for m in pat.finditer(html):
            try:
                raw = m.group(1).strip()
                if len(raw) > 2_000_000:  # 单块过大则跳过
                    continue
                arr = json.loads(raw)
                if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], dict):
                    builds.extend(arr)
            except (json.JSONDecodeError, TypeError):
                continue
    return builds


def normalize_build_item(item: dict) -> tuple[str, int, int]:
    """从一条 build 数据中取出 (职业, 点赞数, 评论数)。"""
    cls = ""
    for key in ("class", "className", "class_name", "职业", "name"):
        if key in item and item[key]:
            cls = str(item[key]).strip()
            break
    if not cls and "title" in item:
        for c in CLASS_NAMES:
            if c in str(item.get("title", "")):
                cls = c
                break
    likes = 0
    for key in ("like", "likes", "likeCount", "thumb", "thumbUp", "点赞"):
        if key in item:
            v = item[key]
            likes = _to_int(v) if isinstance(v, (str, int, float)) else 0
            break
    comments = 0
    for key in ("comment", "comments", "commentCount", "评论"):
        if key in item:
            v = item[key]
            comments = _to_int(v) if isinstance(v, (str, int, float)) else 0
            break
    return cls, likes, comments


def _class_from_char_avatar(card) -> str:
    """从 .char-avatar 或 .char-frame 内 class 取职业（如 Paladin），并转为中文。"""
    # 结构: <div class="van-image char-avatar Paladin"> 或 img src 含 node_type_paladin
    el = card.select_one(".char-avatar, [class*='char-avatar']")
    if el:
        classes = el.get("class") or []
        for c in classes:
            if c and c != "char-avatar" and c != "van-image":
                return CLASS_EN_TO_ZH.get(c, c)
        # 从 img 的 data-src/src 取 node_type_xxx
        img = el.find("img")
        if img:
            src = (img.get("data-src") or img.get("src") or "") or ""
            m = re.search(r"node_type_(\w+)", src, re.I)
            if m:
                name = m.group(1).capitalize()
                return CLASS_EN_TO_ZH.get(name, name)
    return ""


def extract_from_dom(soup: BeautifulSoup) -> tuple[list[tuple[str, int, int]], list[dict]]:
    """从 DOM 解析暗黑核玩法卡片：.col-basic 内 职业、评论、点赞；返回 (聚合用列表, 每条明细)。"""
    results = []
    builds_detail = []
    for card in soup.select(".col-basic, [class*='col-basic']"):
        cls = _class_from_char_avatar(card)
        if not cls:
            continue
        comments = likes = 0
        social = card.select_one(".social")
        if social:
            nums = [el.get_text(strip=True) for el in social.select(".social-num")]
            if len(nums) >= 1:
                comments = _to_int(nums[0])
            if len(nums) >= 2:
                likes = _to_int(nums[1])
        results.append((cls, likes, comments))
        title_el = card.select_one(".info .title a, .title .navigator-wrap")
        title = title_el.get_text(strip=True) if title_el else ""
        builds_detail.append({
            "职业": cls,
            "评论数": comments,
            "点赞数": likes,
            "标题": title,
        })
    return results, builds_detail


def aggregate(builds: list[tuple[str, int, int]]) -> dict[str, dict]:
    """按职业聚合点赞、评论、热度。"""
    agg = defaultdict(lambda: {"likes": 0, "comments": 0, "heat": 0})
    for cls, likes, comments in builds:
        if not cls:
            continue
        agg[cls]["likes"] += likes
        agg[cls]["comments"] += comments
        agg[cls]["heat"] = agg[cls]["likes"] + agg[cls]["comments"]
    return dict(agg)


def main() -> None:
    if not HTML_FILE.exists():
        print(f"未找到文件: {HTML_FILE}")
        print("请将「Build大厅 _ 暗黑核.html」放在脚本同目录下。")
        raise SystemExit(1)

    html = load_html(HTML_FILE)
    all_builds: list[tuple[str, int, int]] = []
    builds_detail: list[dict] = []

    # 1) 从 DOM 解析（暗黑核 .col-basic 结构）
    soup = BeautifulSoup(html, "lxml")
    dom_builds, builds_detail = extract_from_dom(soup)
    all_builds.extend(dom_builds)

    # 2) 从 script/JSON 解析
    raw_list = extract_from_script_json(html)
    for item in raw_list:
        cls, likes, comments = normalize_build_item(item)
        if cls or likes or comments:
            if not cls:
                cls = "未知"
            all_builds.append((cls, likes, comments))

    if not all_builds:
        # 3) 回退：整页搜 职业+数字，简单计数
        for c in CLASS_NAMES:
            if c in html:
                all_builds.append((c, 0, 0))
        if not all_builds:
            print("未能从页面中解析出任何 Build 数据，请确认 HTML 是否包含玩法列表。")
            # 仍写出空结构
            agg = {}
    else:
        agg = aggregate(all_builds)

    # 若只有 DOM 解析到明细则用，否则从 all_builds 生成简易明细
    if not builds_detail and all_builds:
        builds_detail = [
            {"职业": cls, "评论数": comments, "点赞数": likes, "标题": ""}
            for cls, likes, comments in all_builds
        ]

    out = {
        "source": str(HTML_FILE.name),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "builds_count": len(all_builds),
        "builds": builds_detail,
        "classes": [
            {"class": k, "likes": v["likes"], "comments": v["comments"], "heat": v["heat"]}
            for k, v in sorted(agg.items(), key=lambda x: -x[1]["heat"])
        ],
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"解析到 {len(all_builds)} 条 Build 数据，{len(agg)} 个职业。")
    print(f"已写入: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
