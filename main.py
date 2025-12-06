#!/usr/bin/env python3
"""
圖片風格轉換工具 - 向量插畫風格（半寫實企業頭像、賽璐璐著色、隨機高光、透明背景）

使用方式:
    python main.py --input photo.jpg --output result.png
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

from src.style_converter import StyleConverter


def process_image(
    input_path: str, 
    output_path: str = None,
    verbose: bool = True
) -> str:
    """處理單張圖片"""
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"找不到輸入檔案: {input_path}")
    
    if output_path is None:
        output_path = input_file.parent / f"{input_file.stem}_style.png"
    
    # 確保輸出目錄存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"📂 載入圖片: {input_path}")
    
    style_converter = StyleConverter()
    
    if verbose:
        print("🎨 套用風格轉換...")
        print("   → 轉換為向量插畫風格")
        print("   → 半寫實企業頭像風格")
        print("   → 賽璐璐著色（cel-shaded）、硬陰影")
        print("   → 隨機高光效果（橘色/金色邊緣光，隨機角度）")
        print("   → 透明背景")
        print("   → 身體生成機制（如果只有脖子，生成到胸部；如果全身，只生成到胸部）")
        print("   → 統一尺寸和位置（增加同質性）")
        print("   （處理中，請稍候...）")
    
    # 載入圖片
    image = Image.open(input_path)
    
    # 套用風格
    result = style_converter.apply_style(image)
    result.save(str(output_path), "PNG")
    
    if verbose:
        print(f"✅ 完成! 輸出至: {output_path}")
    
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="向量插畫風格轉換（半寫實企業頭像、賽璐璐著色、隨機高光、透明背景）")
    parser.add_argument("-i", "--input", required=True, help="輸入圖片路徑")
    parser.add_argument("-o", "--output", default=None, help="輸出圖片路徑")
    parser.add_argument("-q", "--quiet", action="store_true", help="安靜模式")
    
    args = parser.parse_args()
    
    try:
        process_image(args.input, args.output, not args.quiet)
    except Exception as e:
        print(f"❌ 處理失敗: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

