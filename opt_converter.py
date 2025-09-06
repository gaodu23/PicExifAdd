#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPT畸变参数转换工具
用于将OPT文件中的相机畸变参数转换为DJI XMP格式的畸变参数
"""

import os
import xml.etree.ElementTree as ET
import datetime

def parse_opt_file(opt_file_path):
    """
    解析OPT文件，提取相机参数
    
    Args:
        opt_file_path: OPT文件路径
    
    Returns:
        dict: 包含相机参数的字典
    """
    try:
        tree = ET.parse(opt_file_path)
        root = tree.getroot()
        
        # 创建结果字典
        camera_params = {}
        
        # 提取基本参数
        camera_params['Name'] = root.find('Name').text if root.find('Name') is not None else "Unknown"
        
        # 提取图像尺寸
        image_dimensions = root.find('ImageDimensions')
        if image_dimensions is not None:
            camera_params['Width'] = int(image_dimensions.find('Width').text)
            camera_params['Height'] = int(image_dimensions.find('Height').text)
        
        # 提取传感器尺寸和焦距
        camera_params['SensorSize'] = float(root.find('SensorSize').text) if root.find('SensorSize') is not None else 0
        camera_params['FocalLength'] = float(root.find('FocalLength').text) if root.find('FocalLength') is not None else 0
        
        # 提取畸变参数
        distortion = root.find('Distortion')
        if distortion is not None:
            camera_params['Distortion'] = {
                'K1': float(distortion.find('K1').text) if distortion.find('K1') is not None else 0,
                'K2': float(distortion.find('K2').text) if distortion.find('K2') is not None else 0,
                'K3': float(distortion.find('K3').text) if distortion.find('K3') is not None else 0,
                'P1': float(distortion.find('P1').text) if distortion.find('P1') is not None else 0,
                'P2': float(distortion.find('P2').text) if distortion.find('P2') is not None else 0,
                'Direct': distortion.find('Direct').text.lower() == 'true' if distortion.find('Direct') is not None else True
            }
        
        # 提取主点
        principal_point = root.find('PrincipalPoint')
        if principal_point is not None:
            camera_params['PrincipalPoint'] = {
                'X': float(principal_point.find('X').text) if principal_point.find('X') is not None else 0,
                'Y': float(principal_point.find('Y').text) if principal_point.find('Y') is not None else 0
            }
        
        # 提取相机信息
        exif = root.find('Exif')
        if exif is not None:
            camera_params['Exif'] = {
                'Make': exif.find('Make').text if exif.find('Make') is not None else "",
                'Model': exif.find('Model').text if exif.find('Model') is not None else "",
                'LensModel': exif.find('LensModel').text if exif.find('LensModel') is not None else ""
            }
        
        return camera_params
    
    except Exception as e:
        print(f"解析OPT文件失败: {e}")
        return None

def convert_opt_to_dji_dewarp(opt_data):
    """
    将OPT畸变参数转换为DJI DewarpData格式
    
    Args:
        opt_data: 从OPT文件解析出的相机参数字典
    
    Returns:
        str: DJI DewarpData字符串
    """
    try:
        # 提取需要的参数
        focal_length = opt_data['FocalLength']
        width = opt_data['Width']
        height = opt_data['Height']
        
        # 提取畸变系数
        k1 = opt_data['Distortion']['K1']
        k2 = opt_data['Distortion']['K2']
        k3 = opt_data['Distortion']['K3']
        p1 = opt_data['Distortion']['P1']
        p2 = opt_data['Distortion']['P2']
        is_direct = opt_data['Distortion']['Direct']
        
        # 提取主点坐标
        principal_x = opt_data['PrincipalPoint']['X']
        principal_y = opt_data['PrincipalPoint']['Y']
        
        # 计算归一化系数 (DJI使用归一化坐标)
        # 计算的是从像素坐标系到归一化坐标系的转换
        norm_factor = max(width, height) / focal_length
        
        # 计算主点相对图像中心的偏移，并归一化
        center_offset_x = (principal_x - width/2) / focal_length
        center_offset_y = (principal_y - height/2) / focal_length
        
        # 归一化畸变系数
        k1_dji = k1 * norm_factor**2
        k2_dji = k2 * norm_factor**4
        k3_dji = k3 * norm_factor**6
        p1_dji = p1 * norm_factor**2
        p2_dji = p2 * norm_factor**2
        
        # 如果是直接畸变模型，需要反转符号（DJI使用反向畸变）
        if is_direct:
            k1_dji = -k1_dji
            k2_dji = -k2_dji
            k3_dji = -k3_dji
            p1_dji = -p1_dji
            p2_dji = -p2_dji
        
        # 获取当前日期
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 创建DJI DewarpData字符串
        # 格式：日期;fx;fy;cx;cy;k1;k2;p1;p2;k3
        dewarp_data = f"{today};{focal_length};{focal_length};{center_offset_x};{center_offset_y};{k1_dji};{k2_dji};{p1_dji};{p2_dji};{k3_dji}"
        
        return dewarp_data
    
    except Exception as e:
        print(f"转换畸变参数失败: {e}")
        return None

def create_dji_dewarp_xmp(opt_file_path):
    """
    从OPT文件创建DJI DewarpData和相关XMP数据
    
    Args:
        opt_file_path: OPT文件路径
    
    Returns:
        dict: 包含DJI XMP数据的字典
    """
    try:
        # 解析OPT文件
        opt_data = parse_opt_file(opt_file_path)
        if not opt_data:
            return None
        
        # 转换为DJI格式
        dewarp_data = convert_opt_to_dji_dewarp(opt_data)
        if not dewarp_data:
            return None
        
        # 创建XMP数据字典
        xmp_data = {
            "drone-dji:DewarpData": dewarp_data,
            "drone-dji:DewarpFlag": "0",  # 0表示需要校正
            "drone-dji:CalibratedFocalLength": str(opt_data['FocalLength']),
            "drone-dji:CalibratedOpticalCenterX": str(opt_data['PrincipalPoint']['X']),
            "drone-dji:CalibratedOpticalCenterY": str(opt_data['PrincipalPoint']['Y'])
        }
        
        return xmp_data
    
    except Exception as e:
        print(f"创建DJI XMP数据失败: {e}")
        return None

def get_available_opt_files(directory="cameraInfo"):
    """
    获取可用的OPT文件列表
    
    Args:
        directory: 存放OPT文件的目录
    
    Returns:
        list: OPT文件路径列表
    """
    opt_files = []
    
    # 确保目录存在
    if not os.path.exists(directory):
        return opt_files
    
    # 遍历目录
    for file in os.listdir(directory):
        if file.lower().endswith('.opt'):
            opt_path = os.path.join(directory, file)
            opt_files.append(opt_path)
    
    return opt_files

# 测试函数
def test_opt_conversion(opt_file_path):
    """测试OPT文件转换"""
    print(f"测试OPT文件: {opt_file_path}")
    
    # 解析OPT文件
    opt_data = parse_opt_file(opt_file_path)
    if not opt_data:
        print("解析失败")
        return
    
    # 打印基本信息
    print(f"相机名称: {opt_data.get('Name', 'Unknown')}")
    print(f"分辨率: {opt_data.get('Width', 0)} x {opt_data.get('Height', 0)}")
    print(f"焦距: {opt_data.get('FocalLength', 0)}")
    
    # 打印畸变参数
    if 'Distortion' in opt_data:
        print("\nOPT畸变参数:")
        print(f"K1: {opt_data['Distortion'].get('K1', 0)}")
        print(f"K2: {opt_data['Distortion'].get('K2', 0)}")
        print(f"K3: {opt_data['Distortion'].get('K3', 0)}")
        print(f"P1: {opt_data['Distortion'].get('P1', 0)}")
        print(f"P2: {opt_data['Distortion'].get('P2', 0)}")
        print(f"Direct: {opt_data['Distortion'].get('Direct', True)}")
    
    # 转换为DJI格式
    dewarp_data = convert_opt_to_dji_dewarp(opt_data)
    if dewarp_data:
        print("\nDJI DewarpData:")
        print(dewarp_data)
        
        # 解析DewarpData，便于查看
        parts = dewarp_data.split(';')
        if len(parts) >= 10:
            print("\nDJI畸变参数:")
            print(f"日期: {parts[0]}")
            print(f"fx: {parts[1]}")
            print(f"fy: {parts[2]}")
            print(f"cx: {parts[3]}")
            print(f"cy: {parts[4]}")
            print(f"k1: {parts[5]}")
            print(f"k2: {parts[6]}")
            print(f"p1: {parts[7]}")
            print(f"p2: {parts[8]}")
            print(f"k3: {parts[9]}")
    else:
        print("转换失败")

if __name__ == "__main__":
    # 测试默认OPT文件
    default_opt = os.path.join("cameraInfo", "default.opt")
    if os.path.exists(default_opt):
        test_opt_conversion(default_opt)
    else:
        print(f"默认OPT文件不存在: {default_opt}")
        
        # 尝试查找可用的OPT文件
        opt_files = get_available_opt_files()
        if opt_files:
            print(f"找到 {len(opt_files)} 个OPT文件:")
            for i, opt_file in enumerate(opt_files):
                print(f"{i+1}. {opt_file}")
            
            # 测试第一个找到的OPT文件
            test_opt_conversion(opt_files[0])
        else:
            print("未找到任何OPT文件")
