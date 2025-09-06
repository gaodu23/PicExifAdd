#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试时间戳命名功能"""
import time

def test_timestamp_naming():
    """测试时间戳命名逻辑"""
    print("测试照片时间戳命名功能...")
    print("=" * 50)
    
    # 模拟处理5张照片
    for i in range(1, 6):
        # 为每张照片生成当前时间的时间戳
        current_timestamp = time.strftime("%y%m%d%H%M%S")
        sequence = str(i).zfill(2)  # 2位序号
        new_filename = f"{current_timestamp}{sequence}.jpg"
        
        print(f"照片 {i}: {new_filename}")
        
        # 模拟处理延时
        time.sleep(1)
    
    print("=" * 50)
    print("命名格式说明:")
    print("YYMMDDHHMMSSXX.jpg")
    print("YY - 年份后两位")
    print("MM - 月份")
    print("DD - 日期")
    print("HH - 小时")
    print("MM - 分钟")
    print("SS - 秒钟")
    print("XX - 2位序号")

if __name__ == "__main__":
    test_timestamp_naming()
