# -*- coding: utf-8 -*-
"""
尝试从网上获取暗黑4 职业图片并保存到 assets/diablo4/。
优先使用暗黑核 CDN（cloudstorage.d2core.com）的职业图标，保存为 PNG。
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装: pip install requests")
    raise SystemExit(1)

try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# 7 个职业（英文 slug -> 中文名，用于文件名）
CLASSES = [
    ("barbarian", "野蛮人"),
    ("sorcerer", "魔法使"),
    ("rogue", "侠盗"),
    ("necromancer", "死灵法师"),
    ("druid", "德鲁伊"),
    ("spiritborn", "魂灵师"),
    ("paladin", "圣教军"),
]

OUT_DIR = Path(__file__).resolve().parent / "assets" / "diablo4"
# 暗黑核 CDN 职业图标（你提供的 HTML 里出现的 node_type_paladin.webp 等）
D2CORE_BASE = "https://cloudstorage.d2core.com/data_img/d4/paragon/node_type_{}.webp"


def download_class_image(slug: str, zh_name: str) -> bool:
    url = D2CORE_BASE.format(slug)
    out_path = OUT_DIR / f"class_{zh_name}.png"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"  跳过 {zh_name} ({slug}): HTTP {r.status_code}")
            return False
        raw = r.content
        if HAS_PIL:
            img = Image.open(io.BytesIO(raw))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(out_path, "PNG")
        else:
            # 无 Pillow 时直接存 webp
            out_path = OUT_DIR / f"class_{zh_name}.webp"
            out_path.write_bytes(raw)
        print(f"  已保存: {out_path.name}")
        return True
    except Exception as e:
        print(f"  失败 {zh_name} ({slug}): {e}")
        return False


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("正在从暗黑核 CDN 下载 7 个职业图片到", OUT_DIR)
    ok = 0
    for slug, zh_name in CLASSES:
        if download_class_image(slug, zh_name):
            ok += 1
    print(f"完成：成功 {ok}/{len(CLASSES)}。未成功的可手动从暴雪 Press Center 或 Wiki 下载。")


if __name__ == "__main__":
    main()
