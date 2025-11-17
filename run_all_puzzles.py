#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
运行所有数图题目识别功能
"""

import cv2
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from horizontal_clues_splitter import HorizontalCluesSplitter
from vertical_clues_splitter import VerticalCluesSplitter
from ui_screenshot import UIScreenshotExtractor

def run_all_columns(col_puzzle_ui_image):
    """运行所有列的数字识别功能
    
    Args:
        col_puzzle_ui_image: 列题目区域图像（numpy数组）
        
    Returns:
        成功返回数组（每列的数字列表），失败返回None
    """
    # 检查传入的numpy数组是否有效
    if col_puzzle_ui_image is None:
        print("错误: col_puzzle_ui_image为None")
        return None
    if col_puzzle_ui_image.size == 0:
        print("错误: col_puzzle_ui_image为空数组")
        return None
    
    splitter = HorizontalCluesSplitter()
    all_clues = splitter.split_and_extract_clues(col_puzzle_ui_image)
    
    if all_clues:
        print("\n所有列的数字:")
        for i, clues in enumerate(all_clues):
            print(f"列 {i+1:2d}: {clues}")
        return all_clues
    return None

def run_all_rows(row_puzzle_ui_image):
    """运行所有行的数字识别功能
    
    Args:
        row_puzzle_ui_image: 行题目区域图像（numpy数组）
        
    Returns:
        成功返回数组（每行的数字列表），失败返回None
    """
    # 检查传入的numpy数组是否有效
    if row_puzzle_ui_image is None:
        print("错误: row_puzzle_ui_image为None")
        return None
    if row_puzzle_ui_image.size == 0:
        print("错误: row_puzzle_ui_image为空数组")
        return None
    
    splitter = VerticalCluesSplitter()
    all_clues = splitter.split_and_extract_clues(row_puzzle_ui_image)
    
    if all_clues:
        print("\n所有行的数字:")
        for i, clues in enumerate(all_clues):
            print(f"行 {i+1:2d}: {clues}")
        return all_clues
    return None

def run_all_puzzles_extract(image_path):
    """运行数图题目提取功能并提取列题目和行题目区域
    
    第一步：提取整个puzzle界面，直接通过数据结构传递（numpy数组）
    第二步：从截取的puzzle界面中提取列题目和行题目区域，中间debug文件保存到pic_debug目录
    
    Args:
        image_path: UI截图路径
        
    Returns:
        (col_clues, row_clues) - 列题目数字数组和行题目数字数组，失败返回(None, None)
    """
    if not os.path.exists(image_path):
        print(f"错误: 图片 {image_path} 不存在")
        return None, None
    
    extractor = UIScreenshotExtractor()
    
    # 第一步：提取整个puzzle界面（直接传递numpy数组，不经过文件）
    output_filename = f"puzzle_ui_{os.path.basename(image_path).split('.')[0]}.jpg"
    puzzle_ui_image = extractor.extract_and_save(image_path, output_filename)
    
    if puzzle_ui_image is None:
        print("错误: puzzle界面截取失败，终止运行")
        return None, None
    
    print(f"\npuzzle界面截取成功: 尺寸={puzzle_ui_image.shape[1]}x{puzzle_ui_image.shape[0]}")
    
    # 第二步：从截取的puzzle界面中提取列题目和行题目区域（使用数据结构直接传递）
    col_puzzle_ui, row_puzzle_ui = extractor.extract_col_and_row_ui(puzzle_ui_image)
    
    # 列题目不为None时进行识别
    col_clues = None
    if col_puzzle_ui is not None:
        print(f"\n列题目提取成功: 尺寸={col_puzzle_ui.shape[1]}x{col_puzzle_ui.shape[0]}")
        print("\n开始运行列题目数字识别:")
        col_clues = run_all_columns(col_puzzle_ui)
        if col_clues is None:
            print("错误: 列题目数字识别失败，终止运行")
            return None, None
    else:
        print("错误: 列题目提取失败，终止运行")
        return None, None
    
    # 行题目不为None时进行识别
    row_clues = None
    if row_puzzle_ui is not None:
        print(f"\n行题目提取成功: 尺寸={row_puzzle_ui.shape[1]}x{row_puzzle_ui.shape[0]}")
        print("\n开始运行行题目数字识别:")
        row_clues = run_all_rows(row_puzzle_ui)
        if row_clues is None:
            print("错误: 行题目数字识别失败，终止运行")
            return None, None
    else:
        print("错误: 行题目提取失败，终止运行")
        return None, None
    
    print("\n✓ 所有步骤完成")
    return col_clues, row_clues

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "pic/puzzle_ui_test.jpg"  # 默认测试图片
    
    col_clues, row_clues = run_all_puzzles_extract(image_path)
    if col_clues is not None and row_clues is not None:
        print(f"\n最终结果:")
        print(f"列题目: {col_clues}")
        print(f"行题目: {row_clues}")
    else:
        print("\n运行失败")
        sys.exit(1)
