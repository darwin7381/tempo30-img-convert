#!/usr/bin/env python3
"""
清理 outputs/ 資料夾中的重複版本檔案
保留最新版本，刪除舊版本
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def find_duplicates(directory):
    """找出重複的版本檔案"""
    duplicates = defaultdict(list)
    
    for file_path in Path(directory).rglob("*.png"):
        filename = file_path.name
        
        # 匹配版本號模式：_v1.png, _v2.png, _fixed.png 等
        # 提取基礎檔名（不含版本號）
        base_match = re.match(r'(.+?)(_v\d+|_fixed)?\.png$', filename)
        if base_match:
            base_name = base_match.group(1)
            version_suffix = base_match.group(2) or ""
            
            # 提取版本號
            if version_suffix.startswith("_v"):
                version_num = int(version_suffix[2:])
            elif version_suffix == "_fixed":
                version_num = 999  # fixed 版本視為最新
            else:
                version_num = 0  # 無版本號視為最舊
            
            duplicates[base_name].append((version_num, file_path))
    
    return duplicates

def cleanup_duplicates(directory):
    """清理重複檔案，保留最新版本"""
    duplicates = find_duplicates(directory)
    
    deleted_count = 0
    kept_count = 0
    
    for base_name, versions in duplicates.items():
        if len(versions) > 1:
            # 按版本號排序，保留最新的
            versions.sort(key=lambda x: x[0], reverse=True)
            latest = versions[0][1]
            
            # 刪除舊版本
            for version_num, file_path in versions[1:]:
                try:
                    file_path.unlink()
                    print(f"🗑️  刪除: {file_path.name} (保留: {latest.name})")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 無法刪除 {file_path.name}: {e}")
            
            kept_count += 1
            print(f"✅ 保留: {latest.name}")
    
    print(f"\n📊 統計：")
    print(f"   - 保留檔案: {kept_count}")
    print(f"   - 刪除檔案: {deleted_count}")

if __name__ == "__main__":
    outputs_dir = Path(__file__).parent / "outputs"
    
    if not outputs_dir.exists():
        print(f"❌ 找不到 outputs/ 資料夾: {outputs_dir}")
        exit(1)
    
    print(f"🔍 掃描 {outputs_dir} 中的重複檔案...\n")
    cleanup_duplicates(outputs_dir)
    print("\n✅ 清理完成！")

