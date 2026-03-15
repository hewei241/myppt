# -*- coding: utf-8 -*-
"""
读取 assets/diablo4/d2core_builds_heat.json，
按职业聚合所有玩法的 点赞数、评论数，生成每个职业的热度数据，
并写入 assets/diablo4/d2core_class_heat.json。
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_JSON = BASE_DIR / "assets" / "diablo4" / "d2core_builds_heat.json"
OUTPUT_JSON = BASE_DIR / "assets" / "diablo4" / "d2core_class_heat.json"


def aggregate_class_heat(data: dict) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """从 d2core_builds_heat.json 中的 builds 列表聚合出职业热度，并记录每个职业下的玩法列表。"""
    agg: dict[str, dict] = defaultdict(lambda: {"likes": 0, "comments": 0, "heat": 0, "count": 0})
    per_class_builds: dict[str, list[dict]] = defaultdict(list)
    builds = data.get("builds", [])
    for item in builds:
        cls = str(item.get("职业") or "").strip()
        if not cls:
            continue
        likes = int(item.get("点赞数") or 0)
        comments = int(item.get("评论数") or 0)
        heat = likes + comments

        agg[cls]["likes"] += likes
        agg[cls]["comments"] += comments
        agg[cls]["heat"] = agg[cls]["likes"] + agg[cls]["comments"]
        agg[cls]["count"] += 1

        per_class_builds[cls].append(
            {
                "title": item.get("标题") or "",
                "likes": likes,
                "comments": comments,
                "heat": heat,
            }
        )
    return dict(agg), dict(per_class_builds)


def main() -> None:
    if not INPUT_JSON.exists():
        print(f"未找到输入文件: {INPUT_JSON}")
        raise SystemExit(1)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    agg, per_class_builds = aggregate_class_heat(data)

    # 先按热度从低到高排序，方便给出 No.N -> No.1 的倒序编号
    sorted_items = sorted(agg.items(), key=lambda kv: kv[1]["heat"])
    total = len(sorted_items)

    classes_out: list[dict] = []
    for idx, (cls, vals) in enumerate(sorted_items):
        rank_num = total - idx  # 最低热度 -> No.total，最高热度 -> No.1
        rank_label = f"No.{rank_num}"
        # 每个职业热度最高的前五个玩法标题
        builds_sorted = sorted(
            per_class_builds.get(cls, []),
            key=lambda b: b["heat"],
            reverse=True,
        )
        top5_titles = [b["title"] for b in builds_sorted[:5]]
        classes_out.append(
            {
                "class": cls,
                "likes": vals["likes"],
                "comments": vals["comments"],
                "heat": vals["heat"],
                "build_count": vals["count"],
                "rank": rank_label,
                "top_build_titles": top5_titles,
            }
        )

    out = {
        "source": INPUT_JSON.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classes": classes_out,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"已从 {INPUT_JSON} 聚合 {len(agg)} 个职业的热度数据 -> {OUTPUT_JSON}")


if __name__ == "__main__":
    main()

