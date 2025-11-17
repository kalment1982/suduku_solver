#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从UI截取puzzle界面的模块
"""

import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class UIScreenshotExtractor:
    def __init__(self, debug_dir="pic_debug"):
        """初始化UI截取器"""
        self.debug_dir = debug_dir
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
        
        # 加载模板图像
        self.zhuxian_template = None
        self.challenge_template = None
        self.x_button_template = None
        self.horizon_gezi_template = None
        self.vertical_gezi_template = None
        
        self.load_templates()
    
    def load_templates(self):
        """加载所需的模板图像"""
        # 加载 zhuxian.png 或 challenge.png
        zhuxian_path = os.path.join("number", "zhuxian.png")
        challenge_path = os.path.join("number", "challenge.png")
        
        if os.path.exists(zhuxian_path):
            self.zhuxian_template = cv2.imread(zhuxian_path, cv2.IMREAD_COLOR)
            print(f"已加载 {zhuxian_path}")
        elif os.path.exists(challenge_path):
            self.challenge_template = cv2.imread(challenge_path, cv2.IMREAD_COLOR)
            print(f"已加载 {challenge_path}")
        else:
            print("警告: 未找到 zhuxian.png 或 challenge.png")
        
        # 加载 x_button.png
        x_button_path = os.path.join("number", "x_button.png")
        if os.path.exists(x_button_path):
            self.x_button_template = cv2.imread(x_button_path, cv2.IMREAD_COLOR)
            print(f"已加载 {x_button_path}")
        else:
            print("警告: 未找到 x_button.png")
        
        # 加载 horizon_gezi.png
        horizon_gezi_path = os.path.join("number", "horizon_gezi.png")
        if os.path.exists(horizon_gezi_path):
            self.horizon_gezi_template = cv2.imread(horizon_gezi_path, cv2.IMREAD_COLOR)
            print(f"已加载 {horizon_gezi_path}")
        else:
            print("警告: 未找到 horizon_gezi.png")
        
        # 加载 vertical_gezi.png
        vertical_gezi_path = os.path.join("number", "vertical_gezi.png")
        if os.path.exists(vertical_gezi_path):
            self.vertical_gezi_template = cv2.imread(vertical_gezi_path, cv2.IMREAD_COLOR)
            print(f"已加载 {vertical_gezi_path}")
        else:
            print("警告: 未找到 vertical_gezi.png")
    
    def find_template_in_image(self, image, template, template_name):
        """
        在图像中寻找模板，返回匹配位置和尺寸
        
        Args:
            image: 输入图像
            template: 模板图像
            template_name: 模板名称（用于调试输出）
            
        Returns:
            (x, y, width, height) 或 None
        """
        if template is None:
            return None
        
        # 检查模板尺寸是否不超过输入图像
        template_height, template_width = template.shape[:2]
        image_height, image_width = image.shape[:2]
        
        if template_height > image_height or template_width > image_width:
            print(f"模板 {template_name} 过大，无法匹配")
            return None
        
        # 进行模板匹配
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF)
        _, max_score, _, max_loc = cv2.minMaxLoc(result)
        
        if max_score > 0:  # 确保有正的匹配分数
            x, y = max_loc
            width = template_width
            height = template_height
            print(f"找到 {template_name}: 位置=({x}, {y}), 尺寸={width}x{height}, 匹配分数={max_score:.1f}")
            return (x, y, width, height)
        else:
            print(f"未找到 {template_name}")
            return None
    
    def extract_puzzle_ui(self, image_path):
        """
        从UI图片中截取puzzle界面
        
        Args:
            image_path: UI图片路径
            
        Returns:
            截取的puzzle界面图像，或 None
        """
        # 加载图片
        image = cv2.imread(image_path)
        if image is None:
            print(f"无法加载图片 {image_path}")
            return None
        
        print(f"加载图片: {image_path}")
        print(f"图像尺寸: {image.shape[1]}x{image.shape[0]}")
        
        # 查找 zhuxian 或 challenge 的位置
        header_result = None
        if self.zhuxian_template is not None:
            header_result = self.find_template_in_image(image, self.zhuxian_template, "zhuxian.png")
        
        if header_result is None and self.challenge_template is not None:
            header_result = self.find_template_in_image(image, self.challenge_template, "challenge.png")
        
        if header_result is None:
            print("错误: 未找到页面头部标记")
            return None
        
        header_x, header_y, header_width, header_height = header_result
        puzzle_ui_start_y = header_y + header_height + 3
        print(f"puzzle_ui_start_y = {puzzle_ui_start_y}")
        
        # 查找 x_button 的位置
        button_result = self.find_template_in_image(image, self.x_button_template, "x_button.png")
        
        if button_result is None:
            print("错误: 未找到关闭按钮")
            return None
        
        button_x, button_y, button_width, button_height = button_result
        puzzle_ui_end_y = button_y - 3
        print(f"puzzle_ui_end_y = {puzzle_ui_end_y}")
        
        # 检查坐标的合理性
        if puzzle_ui_start_y >= puzzle_ui_end_y:
            print(f"错误: puzzle界面范围无效 ({puzzle_ui_start_y} >= {puzzle_ui_end_y})")
            return None
        
        # 截取puzzle界面
        puzzle_height = puzzle_ui_end_y - puzzle_ui_start_y
        puzzle_region = image[puzzle_ui_start_y:puzzle_ui_end_y, :]
        
        print(f"截取puzzle界面: 起始Y={puzzle_ui_start_y}, 结束Y={puzzle_ui_end_y}, 高度={puzzle_height}")
        print(f"截取后尺寸: {puzzle_region.shape[1]}x{puzzle_region.shape[0]}")
        
        return puzzle_region
    
    def extract_and_save(self, image_path, output_filename="puzzle_ui.jpg"):
        """
        截取puzzle界面并保存
        
        Args:
            image_path: 输入图片路径
            output_filename: 输出文件名
            
        Returns:
            截取的puzzle界面图像（numpy数组）
        """
        puzzle_region = self.extract_puzzle_ui(image_path)
        
        if puzzle_region is None:
            return None
        
        # 保存截取的图片
        output_path = os.path.join(self.debug_dir, output_filename)
        cv2.imwrite(output_path, puzzle_region)
        print(f"已保存到 {output_path}")
        
        return puzzle_region
    
    def extract_col_puzzle_ui(self, puzzle_ui_image):
        """
        从 puzzle界面中提取列题目区域
        
        Args:
            puzzle_ui_image: puzzle界面图像
            
        Returns:
            列题目区域图像，或 None
        """
        if puzzle_ui_image is None:
            print("错误: puzzle界面图像为None")
            return None
        
        # 在puzzle界面中旧找 horizon_gezi.png
        gezi_result = self.find_template_in_image(puzzle_ui_image, self.horizon_gezi_template, "horizon_gezi.png")
        
        if gezi_result is None:
            print("错误: 未找到 horizon_gezi.png")
            return None
        
        gezi_x, gezi_y, gezi_width, gezi_height = gezi_result
        col_height = gezi_y + 2
        print(f"col_puzzle_ui 高度 = {col_height}")
        
        # 从(0, 0)开始，宽度是puzzle界面的完整宽度
        puzzle_width = puzzle_ui_image.shape[1]
        col_puzzle_ui = puzzle_ui_image[0:col_height, 0:puzzle_width]
        
        print(f"提取 col_puzzle_ui: 宽度={puzzle_width}, 高度={col_height}")
        return col_puzzle_ui
    
    def extract_row_puzzle_ui(self, puzzle_ui_image):
        """
        从 puzzle界面中提取行题目区域
        
        Args:
            puzzle_ui_image: puzzle界面图像
            
        Returns:
            行题目区域图像，或 None
        """
        if puzzle_ui_image is None:
            print("错误: puzzle界面图像为None")
            return None
        
        # 在puzzle界面中寻找 vertical_gezi.png
        gezi_result = self.find_template_in_image(puzzle_ui_image, self.vertical_gezi_template, "vertical_gezi.png")
        
        if gezi_result is None:
            print("错误: 未找到 vertical_gezi.png")
            return None
        
        gezi_x, gezi_y, gezi_width, gezi_height = gezi_result
        row_width = gezi_x + 2
        print(f"row_puzzle_ui 宽度 = {row_width}")
        
        # 从(0, 0)开始，高度是puzzle界面的完整高度
        puzzle_height = puzzle_ui_image.shape[0]
        row_puzzle_ui = puzzle_ui_image[0:puzzle_height, 0:row_width]
        
        print(f"提取 row_puzzle_ui: 宽度={row_width}, 高度={puzzle_height}")
        return row_puzzle_ui
    
    def extract_col_and_row_ui(self, puzzle_ui_image):
        """
        从 puzzle界面中同时提取列题目和行题目区域，并保存debug文件
        
        Args:
            puzzle_ui_image: puzzle界面图像
            
        Returns:
            (列题目图像数组, 行题目图像数组) 或 (None, None)
        """
        col_ui = self.extract_col_puzzle_ui(puzzle_ui_image)
        row_ui = self.extract_row_puzzle_ui(puzzle_ui_image)
        
        # 保存debug文件到pic_debug目录
        if col_ui is not None:
            col_path = os.path.join(self.debug_dir, "col_puzzle_ui.jpg")
            # cv2.imwrite(col_path, col_ui)
            # print(f"col_puzzle_ui.jpg")
        
        if row_ui is not None:
            row_path = os.path.join(self.debug_dir, "row_puzzle_ui.jpg")
            # cv2.imwrite(row_path, row_ui)
            # print(f"row_puzzle_ui.jpg")
        
        return col_ui, row_ui

def test_ui_screenshot(image_path):
    """
    测试UI截取功能
    
    Args:
        image_path: 输入图片路径
    """
    if not os.path.exists(image_path):
        print(f"图片 {image_path} 不存在")
        return
    
    extractor = UIScreenshotExtractor()
    output_path = extractor.extract_and_save(image_path, "puzzle_ui.jpg")
    
    if output_path:
        print(f"\n截取成功: {output_path}")
    else:
        print("\n截取失败")

if __name__ == "__main__":
    # 默认测试
    test_ui_screenshot("pic/screenshot.png")
