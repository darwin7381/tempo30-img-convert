#!/usr/bin/env python3
"""測試 AI 自動修圖效果"""

import os
import io
import sys
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def enhance_image(image_path: str, output_path: str):
    """使用 AI 自動修圖"""
    print(f"📂 載入圖片: {image_path}")
    
    image = Image.open(image_path)
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[3])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    prompt = """Enhance this photo professionally:
- Improve lighting and exposure
- Enhance skin tone naturally
- Sharpen details
- Improve color balance
- Make it look like a professional headshot photo
- Keep the person looking natural, not over-processed

Output an enhanced version of this photo."""
    
    print("🎨 AI 自動修圖中...")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            prompt,
            types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        ],
        config=types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            result = Image.open(io.BytesIO(part.inline_data.data))
            result.save(output_path, "PNG")
            print(f"✅ 完成! 輸出至: {output_path}")
            return
    
    print("❌ AI 未返回圖片")

if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else "Juin Chiu.png"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "ai_enhanced.png"
    enhance_image(input_path, output_path)

