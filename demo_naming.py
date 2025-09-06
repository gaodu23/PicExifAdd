#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""演示每个照片使用处理时的实时时间戳命名功能"""
import time

def demo_realtime_naming():
    """演示实时时间戳命名"""
    print("演示：每个照片处理时的实时时间戳命名")
    print("=" * 60)
    print("模拟处理5张照片，每张照片间隔1秒...")
    print()
    
    # 模拟处理5张照片
    original_files = ["IMG_001.jpg", "IMG_002.jpg", "IMG_003.jpg", "IMG_004.jpg", "IMG_005.jpg"]
    
    for i, original_file in enumerate(original_files, 1):
        # 为每张照片生成当前时间的时间戳
        current_timestamp = time.strftime("%y%m%d%H%M%S")
        sequence = str(i).zfill(2)  # 2位序号
        new_filename = f"{current_timestamp}{sequence}.jpg"
        
        print(f"处理第{i}张照片:")
        print(f"  原文件名: {original_file}")
        print(f"  新文件名: {new_filename}")
        print(f"  处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 模拟处理延时（实际处理中每张照片的处理时间不同）
        time.sleep(1)
    
    print("=" * 60)
    print("命名格式说明:")
    print("YYMMDDHHMMSSXX.jpg")
    print("  YY - 年份后两位")
    print("  MM - 月份")
    print("  DD - 日期")
    print("  HH - 小时")
    print("  MM - 分钟")
    print("  SS - 秒钟")
    print("  XX - 2位序号 (01, 02, 03...)")
    print()
    print("特点：")
    print("✅ 每张照片使用其实际处理时的时间戳")
    print("✅ 时间戳精确到秒，确保文件名唯一性")
    print("✅ 2位序号便于排序和识别")
    print("✅ 可以从文件名看出照片的处理时间")

if __name__ == "__main__":
    demo_realtime_naming()
