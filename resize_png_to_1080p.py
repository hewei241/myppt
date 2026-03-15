"""
将 assets 目录下所有 .png 图片统一缩放到 1920x1080，
并在文件名中加上分辨率信息（如 xxx_1920x1080.png）。
铺满画布，保持宽高比，多出的左右或上下居中裁剪（无黑边）。
"""

from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    exit(1)

ASSETS_DIR = Path(__file__).parent / "assets"
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
RESOLUTION_SUFFIX = f"_{TARGET_WIDTH}x{TARGET_HEIGHT}"


def resize_to_1920x1080(assets_path: Path) -> int:
    """遍历 assets 目录，将所有 .png 缩放到 1920x1080 并重命名，返回处理数量。"""
    if not assets_path.is_dir():
        print(f"目录不存在: {assets_path}")
        return 0

    count = 0
    for png_path in assets_path.rglob("*.png"):
        # 若文件名已含分辨率后缀则跳过，避免重复处理
        if RESOLUTION_SUFFIX in png_path.stem:
            continue

        new_name = f"{png_path.stem}{RESOLUTION_SUFFIX}.png"
        out_path = png_path.parent / new_name

        try:
            with Image.open(png_path) as img:
                if img.mode == "P":
                    img = img.convert("RGBA")
                elif img.mode != "RGBA" and img.mode != "RGB":
                    img = img.convert("RGB")

                w, h = img.size
                # 铺满 1920x1080，多出的部分居中裁剪（无黑边）
                scale = max(TARGET_WIDTH / w, TARGET_HEIGHT / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                # 从中心裁出 1920x1080
                left = (new_w - TARGET_WIDTH) // 2
                top = (new_h - TARGET_HEIGHT) // 2
                canvas = img_resized.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))
                canvas.save(out_path, "PNG")

            print(f"已处理: {png_path.name} -> {new_name}")
            count += 1
        except Exception as e:
            print(f"处理失败 {png_path}: {e}")

    return count


if __name__ == "__main__":
    n = resize_to_1920x1080(ASSETS_DIR)
    print(f"\n共处理 {n} 个 PNG 文件。")
