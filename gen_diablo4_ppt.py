"""
生成 Diablo 4 风格 PPT 模板。
第一页：封面页，以 cover.png 为背景，居中大标题（54 号字）。
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

ASSETS_DIR = Path(__file__).parent / "assets" / "diablo4"
COVER_IMAGE = ASSETS_DIR / "cover.png"
OUTPUT_PATH = Path(__file__).parent / "diablo4_template.pptx"
TITLE_FONT_SIZE = Pt(54)
COVER_TITLE = "暗黑破坏神 IV"  # 封面标题占位
COVER_TITLE_MAX_CHARS_PER_LINE = 4  # 每行最多显示字数


def wrap_title(text: str, max_chars: int = COVER_TITLE_MAX_CHARS_PER_LINE) -> str:
    """将标题按每行最多 max_chars 个字换行。"""
    return "\n".join(text[i : i + max_chars] for i in range(0, len(text), max_chars))


def gen_cover_slide(prs: Presentation, cover_path: Path) -> None:
    """添加封面页：背景图 + 居中 54 号字标题。"""
    blank_layout = prs.slide_layouts[6]  # 6 = blank
    slide = prs.slides.add_slide(blank_layout)

    slide_width = prs.slide_width
    slide_height = prs.slide_height

    # 1. 背景图（先添加，自然在底层）
    slide.shapes.add_picture(
        str(cover_path),
        Emu(0),
        Emu(0),
        width=slide_width,
        height=slide_height,
    )

    # 2. 居中标题（54 号字）
    # 文本框宽度约 80% 幻灯片宽，居中放置
    box_width = int(slide_width * 0.8)
    box_left = int((slide_width - box_width) / 2)
    box_top = int(slide_height * 0.4)  # 垂直略偏上
    box_height = Emu(1000000)  # 约 1.1 英寸高

    tx = slide.shapes.add_textbox(box_left, box_top, box_width, box_height)
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = wrap_title(COVER_TITLE)
    p.alignment = PP_ALIGN.CENTER
    p.font.size = TITLE_FONT_SIZE
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)  # 白色字，在深色背景上清晰


def main():
    if not COVER_IMAGE.exists():
        print(f"请将封面图放在: {COVER_IMAGE}")
        print("  或修改脚本顶部 COVER_IMAGE 路径。")
        exit(1)

    prs = Presentation()
    prs.slide_width = Emu(12192000)   # 16:9 约 13.333 英寸
    prs.slide_height = Emu(6858000)   # 约 7.5 英寸

    gen_cover_slide(prs, COVER_IMAGE)
    prs.save(OUTPUT_PATH)
    print(f"已生成: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
