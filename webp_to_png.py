"""
将 assets 目录下所有 .webp 图片转换为 .png 格式。
会递归遍历子目录，转换后的 PNG 保存在原文件同目录，原 WebP 文件保留。
"""

import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    exit(1)

ASSETS_DIR = Path(__file__).parent / "assets"


def convert_webp_to_png(assets_path: Path) -> int:
    """遍历 assets 目录，将所有 .webp 转为 .png，返回转换数量。"""
    if not assets_path.is_dir():
        print(f"目录不存在: {assets_path}")
        return 0

    count = 0
    for webp_path in assets_path.rglob("*.webp"):
        png_path = webp_path.with_suffix(".png")
        try:
            with Image.open(webp_path) as img:
                # 若含透明通道，保持 RGBA；否则 RGB
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                img.save(png_path, "PNG")
            print(f"已转换: {webp_path} -> {png_path}")
            count += 1
        except Exception as e:
            print(f"转换失败 {webp_path}: {e}")

    return count


if __name__ == "__main__":
    n = convert_webp_to_png(ASSETS_DIR)
    print(f"\n共转换 {n} 个 WebP 文件为 PNG。")
