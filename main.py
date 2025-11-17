#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数图自动求解主程序
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_all_puzzles import run_all_puzzles_extract
from solver import NonogramUI

def get_png_files_from_downloads():
    """
    从下载目录获取PNG文件列表，按创建时间排序（最新优先）
    
    Returns:
        [(文件路径, 文件名), ...] 列表，按创建时间从新到旧排序
    """
    downloads_path = os.path.expanduser('~/Downloads')
    
    if not os.path.exists(downloads_path):
        return []
    
    # 获取所有PNG文件
    png_files = []
    for file in os.listdir(downloads_path):
        if file.lower().endswith('.png'):
            full_path = os.path.join(downloads_path, file)
            if os.path.isfile(full_path):
                # 获取创建时间
                ctime = os.path.getctime(full_path)
                png_files.append((full_path, file, ctime))
    
    # 按创建时间从新到旧排序
    png_files.sort(key=lambda x: x[2], reverse=True)
    
    return [(path, filename) for path, filename, _ in png_files]

def save_puzzle_clue(col_clues, row_clues, filename="puzzle_clue.txt"):
    """已弃用，爱保治\u4e0a流港"""
    pass

if __name__ == "__main__":
    # 启动NonogramUI，并传入图片选择功能
    # 初始化为空，第一次点击"解题"载入数据
    root = tk.Tk()
    app = NonogramUI(root, col_hints=[], row_hints=[], png_files_func=get_png_files_from_downloads, extract_func=run_all_puzzles_extract)
    root.mainloop()
