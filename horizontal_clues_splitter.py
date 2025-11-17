#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
横向题目图片的纵向分割和数字识别模块
"""

import cv2
import numpy as np
import os
import sys
import pytesseract
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_digit_recognizer import ImprovedDigitRecognizer

class HorizontalCluesSplitter:
    def __init__(self, debug_dir="pic_debug", debug=False):
        """初始化横向题目分割器
        
        Args:
            debug_dir: 调试目录
            debug: 是否打印调试信息（默认False）
        """
        self.digit_recognizer = ImprovedDigitRecognizer()
        self.debug_dir = debug_dir
        self.debug = debug
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def is_image_color(self, pixel):
        """
        判断像素是否是黄色数字区域（不是分割线）
        
        Args:
            pixel: BGR格式的像素值
            
        Returns:
            True如果是黄色区域，False否则
        """
        b, g, r = int(pixel[0]), int(pixel[1]), int(pixel[2])
        
        # 根据分析，黄色数字区域的颜色约为 BGR: (98, 174, 197)
        # 白色分割线的颜色约为 BGR: (181, 234, 247)
        # 黄色区域特征：B较小(～98)，G和R较大但接近(～174, ~197)
        # 白色分割线特征：B、G、R都很大且接近(都>180)
        
        # 黄色区域的识别标准
        # 绿色通道较大，红色通道最大，蓝色通道最小
        if b < 150 and g > 100 and r > 150:
            # 这是黄色区域（数字）
            return True
        
        return False
    
    def find_column_boundaries(self, image):
        """
        从左边开始向右匹配，找出每一列题目的左右边界
        
        Args:
            image: 横向题目的图像
            
        Returns:
            列的边界列表，每个元素为(left, right)
        """
        height, width = image.shape[:2]
        print(f"图像尺寸: {width}x{height}")
        
        # 计算每个x位置处黄色像素的比例
        column_yellowness = []
        
        for x in range(width):
            # 计算这一列的黄色像素比例
            yellow_count = 0
            for y in range(height):
                if self.is_image_color(image[y, x]):
                    yellow_count += 1
            
            yellow_ratio = yellow_count / height if height > 0 else 0
            column_yellowness.append((x, yellow_ratio))
        
        # 使用平滑处理以减少噪声
        smoothed_yellowness = []
        window_size = 7
        for i in range(len(column_yellowness)):
            start = max(0, i - window_size // 2)
            end = min(len(column_yellowness), i + window_size // 2 + 1)
            avg = sum(y[1] for y in column_yellowness[start:end]) / (end - start)
            smoothed_yellowness.append((column_yellowness[i][0], avg))
        
        # 找出所有的列
        columns = []
        in_white_area = True  # 开始时假设在白色分割线区域
        left_boundary = 0
        
        threshold = 0.3  # 黄色像素比例的阈值（降低以捕捉更多列）
        
        for x, ratio in smoothed_yellowness:
            if in_white_area:
                # 当前在白色区域，寻找第一个黄色列
                if ratio > threshold:
                    # 找到黄色区域的开始
                    left_boundary = x
                    in_white_area = False
            else:
                # 当前在黄色区域，寻找白色分割线
                if ratio < threshold:
                    # 找到黄色区域的结束
                    right_boundary = x - 1
                    if right_boundary - left_boundary > 5:  # 至少有一定宽度
                        columns.append((left_boundary, right_boundary))
                    in_white_area = True
        
        # 处理最后一列（如果以黄色区域结尾）
        if not in_white_area:
            columns.append((left_boundary, width - 1))
        
        print(f"找到 {len(columns)} 列题目")
        for i, (left, right) in enumerate(columns):
            print(f"列 {i+1}: 左边界={left}, 右边界={right}, 宽度={right-left+1}")
        
        return columns
    
    def split_and_extract_clues(self, image_input):
        """
        分割横向题目图片并提取数字
        
        Args:
            image_input: 横向题目图片路径（字符串）或numpy数组
            
        Returns:
            包含每列数字的列表
        """
        # 加载图片
        if isinstance(image_input, str):
            # 从文件路径加载
            image = cv2.imread(image_input)
            if image is None:
                print(f"无法加载图片 {image_input}")
                return None
            print(f"加载图片: {image_input}")
        else:
            # 直接使用numpy数组
            image = image_input
            print(f"使用敵数组：尺寸={image.shape[1]}x{image.shape[0]}")
        
        # 找出列的边界
        columns = self.find_column_boundaries(image)
        
        # 在原图上绘制列的边界（用红色矩形框框起来）
        marked_image = image.copy()
        for i, (left, right) in enumerate(columns):
            # 绘制红色矩形框
            cv2.rectangle(marked_image, (left, 0), (right, image.shape[0]), (0, 0, 255), 2)
            # 添加列号标签
            cv2.putText(marked_image, str(i+1), (left+5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 保存标记后的图片
        marked_image_path = os.path.join(self.debug_dir, "horizontal_clues_marked.jpg")
        cv2.imwrite(marked_image_path, marked_image)
        print(f"已保存标记后的图片到 {marked_image_path}")
        
        # 提取每列的数字
        all_clues = []
        for i, (left, right) in enumerate(columns):
            # 提取列的区域
            col_region = image[:, left:right, :]
            
            # 保存列的区域图片
            col_image_path = os.path.join(self.debug_dir, f"column_{i+1:02d}.jpg")
            cv2.imwrite(col_image_path, col_region)
            
            # 识别数字（从上到下）
            if i < 6:  # 对前6列进行纵向切割并保存
                digit_images = self.split_column_vertically(col_region)
                for j, digit_img in enumerate(digit_images):
                    digit_path = os.path.join(self.debug_dir, f"column_{i+1:02d}_digit_{j+1:02d}.jpg")
                    cv2.imwrite(digit_path, digit_img)
            
            clues = self.recognize_clues_in_column(col_region, i)
            all_clues.append(clues)
            
            # 打印结果
            print(f"列 {i+1}: {clues}")
        
        return all_clues
    
    def recognize_clues_in_column(self, column_image, column_index=-1):
        """
        识别列中的数字
        先进行纵向切割以分离每个数字，然后进行识别
        
        Args:
            column_image: 列的图像区域
            column_index: 列的索引（用于调试输出）
            
        Returns:
            按从上到下顺序排列的数字列表
        """
        # 第一步：纵向切割，分离每个数字的图像
        digit_images = self.split_column_vertically(column_image)
        
        # 第二步：对每个数字图像进行识别
        digits = []
        for j, digit_img in enumerate(digit_images):
            # 使用pytesseract识别每个单个数字
            # 如果是前6列，需要保存填充结果
            debug_index = (column_index * 100 + j) if column_index >= 0 else -1
            digit = self.digit_recognizer.recognize_single_digit(digit_img, self.debug_dir, debug_index)
            if digit != -1:  # 只添加成功识别的数字
                digits.append(digit)
        
        return digits
    
    def split_column_vertically(self, column_image):
        """
        将列图像纵向切割，上下分离每个数字
        利用数字的黑色轮廓来识别数字边界
        
        Args:
            column_image: 列的图像区域
            
        Returns:
            刐分好的数字图像列表
        """
        height, width = column_image.shape[:2]
        if self.debug:
            print(f"[DEBUG] 列图像尺寸: {width}x{height}")
        
        # 计算每一行的黑色像素比例（数字的黑色轮廓）
        row_black_ratio = []
        for y in range(height):
            black_count = 0
            
            for x in range(width):
                b, g, r = int(column_image[y, x, 0]), int(column_image[y, x, 1]), int(column_image[y, x, 2])
                
                # 黑色判断（数字的轮廓）
                if b < 80 and g < 80 and r < 80:
                    black_count += 1
            
            black_ratio = black_count / width if width > 0 else 0
            row_black_ratio.append(black_ratio)
            
            # 打印所有行的黑色像素比例
            #print(f"[DEBUG] 第{y}行黑色占比: {black_ratio:.2f}")
        
        # 找出有黑色轮廓的连续区域（数字区域）
        digit_regions = []
        in_digit = False
        start_y = 0
        
        black_threshold = 0.01  # 降低阈值到02%
        
        for y in range(height):
            if row_black_ratio[y] >= black_threshold and not in_digit:
                # 开始一个新的数字区域
                start_y = y
                in_digit = True
                if self.debug:
                    print(f"[DEBUG] 第{y}行开始新数字区域")
            elif row_black_ratio[y] < black_threshold and in_digit:
                # 检查是否是真正的分隔（连续5行没有黑色）
                is_separator = True
                check_count = 3
                if y + check_count <= height:
                    for check_y in range(y, min(y + check_count, height)):
                        if row_black_ratio[check_y] >= black_threshold:
                            is_separator = False
                            break
                
                if is_separator:
                    # 结束当前数字区域
                    if y - start_y >= 15:  # 数字区域至少15个像素高
                        digit_regions.append((start_y, y - 1))
                        if self.debug:
                            print(f"[DEBUG] 找到数字区域: [{start_y}, {y-1}], 高度={y - start_y}")
                    in_digit = False
        
        # 处理最后一个数字区域
        if in_digit:
            if height - start_y >= 15:
                digit_regions.append((start_y, height - 1))
                if self.debug:
                    print(f"[DEBUG] 找到数字区域: [{start_y}, {height-1}], 高度={height - start_y}")
        
        if self.debug:
            print(f"[DEBUG] 总共找到 {len(digit_regions)} 个数字区域")
        
        # 为每个数字区域提取对应的图像
        digit_images = []
        for start_y, end_y in digit_regions:
            # 检查原始数字区域的高度，如果太小（<35像素）则跳过
            raw_height = end_y - start_y + 1
            if raw_height < 15:
                if self.debug:
                    print(f"[DEBUG] 数字区域过小({raw_height}px)，跳过")
                continue
            
            # 上下各加5行
            padded_start = max(0, start_y - 5)
            padded_end = min(height - 1, end_y + 5)
            digit_img = column_image[padded_start:padded_end+1, :, :]
            
            # 如果宽度大于60，则只在右边8像素
            img_width = digit_img.shape[1]
            if img_width > 60:
                digit_img = digit_img[:, :-8, :]
                if self.debug:
                    print(f"[DEBUG] 切割数字: [{padded_start}, {padded_end}], 高度={padded_end - padded_start + 1}, 宽度={img_width} -> {img_width - 8}")
            else:
                if self.debug:
                    print(f"[DEBUG] 切割数字: [{padded_start}, {padded_end}], 高度={padded_end - padded_start + 1}, 宽度={img_width}")
            
            # 容错处理：如果宽度或高度不足45像素，补齐到45像素
            final_height, final_width = digit_img.shape[:2]
            if final_width < 45 or final_height < 45:
                target_width = max(45, final_width)
                target_height = max(45, final_height)
                
                # 创建一个新的画布，用背景色填充
                padded_img = np.full((target_height, target_width, 3), [200, 150, 100], dtype=np.uint8)  # 橙色背景
                
                # 将原图居中放置
                y_offset = (target_height - final_height) // 2
                x_offset = (target_width - final_width) // 2
                padded_img[y_offset:y_offset+final_height, x_offset:x_offset+final_width] = digit_img
                
                digit_img = padded_img
                if self.debug:
                    print(f"[DEBUG] 补齐尺寸: {final_width}x{final_height} -> {target_width}x{target_height}")
            
            digit_images.append(digit_img)
        
        return digit_images

def test_split_horizontal_clues():
    """测试横向题目分割功能"""
    image_path = "pic/heng.png"
    
    if not os.path.exists(image_path):
        print(f"图片 {image_path} 不存在")
        return
    
    splitter = HorizontalCluesSplitter()
    all_clues = splitter.split_and_extract_clues(image_path)
    
    if all_clues:
        print("\n所有列的数字:")
        expected = [
            [2, 3, 1, 1], 
            [2, 6, 1, 2], 
            [2, 3, 2], 
            [2, 6, 1, 2], 
            [1, 2, 1, 3], 
            [1, 4], 
            [3, 5], 
            [2, 3, 4], 
            [3, 4, 1, 1], 
            [3, 4, 2], 
            [3, 6, 1], 
            [3, 8, 1], 
            [2, 8, 1], 
            [1, 4, 2, 2], 
            [3, 5]
        ]
        
        for i, (clues, expect) in enumerate(zip(all_clues, expected)):
            print(f"列 {i+1}: 识别结果={clues}, 期望结果={expect}")

if __name__ == "__main__":
    test_split_horizontal_clues()