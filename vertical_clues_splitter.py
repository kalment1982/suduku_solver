#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
纵向题目图片的横向分割和数字识别模块
"""

import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_digit_recognizer import ImprovedDigitRecognizer

class VerticalCluesSplitter:
    def __init__(self, debug_dir="pic_debug", debug=False):
        """初始化纵向题目分割器
        
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
    
    def find_row_boundaries(self, image):
        """
        从上开始向下匹配，找出每一行题目的上下边界
        
        Args:
            image: 纵向题目的图像
            
        Returns:
            行的边界列表，每个元素为(top, bottom)
        """
        height, width = image.shape[:2]
        print(f"图像尺寸: {width}x{height}")
        
        # 计算每个y位置处黄色像素的比例
        row_yellowness = []
        
        for y in range(height):
            # 计算这一行的黄色像素比例
            yellow_count = 0
            for x in range(width):
                if self.is_image_color(image[y, x]):
                    yellow_count += 1
            
            yellow_ratio = yellow_count / width if width > 0 else 0
            row_yellowness.append((y, yellow_ratio))
        
        # 使用平滑处理以减少噪声
        smoothed_yellowness = []
        window_size = 7
        for i in range(len(row_yellowness)):
            start = max(0, i - window_size // 2)
            end = min(len(row_yellowness), i + window_size // 2 + 1)
            avg = sum(y[1] for y in row_yellowness[start:end]) / (end - start)
            smoothed_yellowness.append((row_yellowness[i][0], avg))
        
        # 找出所有的行
        rows = []
        in_white_area = True  # 开始时假设在白色分割线区域
        top_boundary = 0
        
        threshold = 0.3  # 黄色像素比例的阈值
        
        for y, ratio in smoothed_yellowness:
            if in_white_area:
                # 当前在白色区域，寻找第一个黄色行
                if ratio > threshold:
                    # 找到黄色区域的开始
                    top_boundary = y
                    in_white_area = False
            else:
                # 当前在黄色区域，寻找白色分割线
                if ratio < threshold:
                    # 找到黄色区域的结束
                    bottom_boundary = y - 1
                    if bottom_boundary - top_boundary > 5:  # 至少有一定高度
                        rows.append((top_boundary, bottom_boundary))
                    in_white_area = True
        
        # 处理最后一行（如果以黄色区域结尾）
        if not in_white_area:
            rows.append((top_boundary, height - 1))
        
        print(f"找到 {len(rows)} 行题目")
        for i, (top, bottom) in enumerate(rows):
            print(f"行 {i+1}: 上边界={top}, 下边界={bottom}, 高度={bottom-top+1}")
        
        return rows
    
    def split_and_extract_clues(self, image_input):
        """
        分割纵向题目图片并提取数字
        
        Args:
            image_input: 纵向题目图片路径（字符串）或numpy数组
            
        Returns:
            包含每行数字的列表
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
            print(f"使用numpy数组：尺寸={image.shape[1]}x{image.shape[0]}")
        
        # 找出行的边界
        rows = self.find_row_boundaries(image)
        
        # 在原图上绘制行的边界（用红色矩形框框起来）
        marked_image = image.copy()
        for i, (top, bottom) in enumerate(rows):
            # 绘制红色矩形框
            cv2.rectangle(marked_image, (0, top), (image.shape[1], bottom), (0, 0, 255), 2)
            # 添加行号标签
            cv2.putText(marked_image, str(i+1), (5, top+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 保存标记后的图片
        marked_image_path = os.path.join(self.debug_dir, "vertical_clues_marked.jpg")
        cv2.imwrite(marked_image_path, marked_image)
        print(f"已保存标记后的图片到 {marked_image_path}")
        
        # 提取每行的数字
        all_clues = []
        for i, (top, bottom) in enumerate(rows):
            # 提取行的区域
            row_region = image[top:bottom+1, :, :]
            
            # 保存行的区域图片
            row_image_path = os.path.join(self.debug_dir, f"row_{i+1:02d}.jpg")
            cv2.imwrite(row_image_path, row_region)
            
            # 识别数字（从左到右）
            if i < 6:  # 对前6行进行横向切割并保存
                digit_images = self.split_row_horizontally(row_region)
                for j, digit_img in enumerate(digit_images):
                    digit_path = os.path.join(self.debug_dir, f"row_{i+1:02d}_digit_{j+1:02d}.jpg")
                    cv2.imwrite(digit_path, digit_img)
            
            clues = self.recognize_clues_in_row(row_region, i)
            all_clues.append(clues)
            
            # 打印结果
            print(f"行 {i+1}: {clues}")
        
        return all_clues
    
    def recognize_clues_in_row(self, row_image, row_index=-1):
        """
        识别行中的数字
        先进行横向切割以分离每个数字，然后进行识别
        
        Args:
            row_image: 行的图像区域
            row_index: 行的索引（用于调试输出）
            
        Returns:
            按从左到右顺序排列的数字列表
        """
        # 第一步：横向切割，分离每个数字的图像
        digit_images = self.split_row_horizontally(row_image)
        
        # 保存所有15行的数字图像（用于调试）
        if row_index >= 0:
            for j, digit_img in enumerate(digit_images):
                debug_path = os.path.join(self.debug_dir, f"row{row_index+1:02d}_digit_{j+1:02d}.jpg")
                cv2.imwrite(debug_path, digit_img)
        
        # 第二步：对每个数字图像进行识别
        digits = []
        for j, digit_img in enumerate(digit_images):
            # 使用模板匹配识别每个单个数字
            # 如果是前6行，需要保存填充结果
            debug_index = (row_index * 100 + j) if row_index >= 0 else -1
            digit = self.digit_recognizer.recognize_single_digit(digit_img, self.debug_dir, debug_index)
            if digit != -1:  # 只添加成功识别的数字
                digits.append(digit)
        
        return digits
    
    def split_row_horizontally(self, row_image):
        """
        将行图像横向切割，左右分离每个数字
        利用数字的黑色轮廓来识别数字边界
        
        Args:
            row_image: 行的图像区域
            
        Returns:
            切分好的数字图像列表
        """
        height, width = row_image.shape[:2]
        if self.debug:
            print(f"[DEBUG] 行图像尺寸: {width}x{height}")
        
        # 计算每一列的黑色像素比例（数字的黑色轮廓）
        col_black_ratio = []
        for x in range(width):
            black_count = 0
            
            for y in range(height):
                b, g, r = int(row_image[y, x, 0]), int(row_image[y, x, 1]), int(row_image[y, x, 2])
                
                # 黑色判断（数字的轮廓）
                if b < 80 and g < 80 and r < 80:
                    black_count += 1
            
            black_ratio = black_count / height if height > 0 else 0
            col_black_ratio.append(black_ratio)
        
        # 找出有黑色轮廓的连续区域（数字区域）
        digit_regions = []
        in_digit = False
        start_x = 0
        
        black_threshold = 0.01  # 阈值
        
        for x in range(width):
            if col_black_ratio[x] >= black_threshold and not in_digit:
                # 开始一个新的数字区域
                start_x = x
                in_digit = True
                if self.debug:
                    print(f"[DEBUG] 第{x}列开始新数字区域")
            elif col_black_ratio[x] < black_threshold and in_digit:
                # 检查是否是真正的分隔（连续5列没有黑色）
                is_separator = True
                check_count = 3
                if x + check_count <= width:
                    for check_x in range(x, min(x + check_count, width)):
                        if col_black_ratio[check_x] >= black_threshold:
                            is_separator = False
                            break
                
                if is_separator:
                    # 结束当前数字区域
                    if x - start_x >= 15:  # 数字区域至少15个像素宽
                        digit_regions.append((start_x, x - 1))
                        if self.debug:
                            print(f"[DEBUG] 找到数字区域: [{start_x}, {x-1}], 宽度={x - start_x}")
                    in_digit = False
        
        # 处理最后一个数字区域
        if in_digit:
            if width - start_x >= 15:
                digit_regions.append((start_x, width - 1))
                if self.debug:
                    print(f"[DEBUG] 找到数字区域: [{start_x}, {width-1}], 宽度={width - start_x}")
        
        if self.debug:
            print(f"[DEBUG] 总共找到 {len(digit_regions)} 个数字区域")
        
        # 为每个数字区域提取对应的图像
        digit_images = []
        for start_x, end_x in digit_regions:
            # 检查原始数字区域的宽度，如果太小（<15像素）则跳过
            raw_width = end_x - start_x + 1
            if raw_width < 15:
                if self.debug:
                    print(f"[DEBUG] 数字区域过小({raw_width}px)，跳过")
                continue
            
            # 左右各加5列
            padded_start = max(0, start_x - 5)
            padded_end = min(width - 1, end_x + 5)
            digit_img = row_image[:, padded_start:padded_end+1, :]
            
            # 如果高度大于60，则只在下边裁8像素
            img_height = digit_img.shape[0]
            if img_height > 60:
                digit_img = digit_img[:-8, :, :]
                if self.debug:
                    print(f"[DEBUG] 切割数字: [{padded_start}, {padded_end}], 宽度={padded_end - padded_start + 1}, 高度={img_height} -> {img_height - 8}")
            else:
                if self.debug:
                    print(f"[DEBUG] 切割数字: [{padded_start}, {padded_end}], 宽度={padded_end - padded_start + 1}, 高度={img_height}")
            
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

def test_split_vertical_clues():
    """测试纵向题目分割功能"""
    image_path = "pic/zong.png"
    
    if not os.path.exists(image_path):
        print(f"图片 {image_path} 不存在")
        return
    
    splitter = VerticalCluesSplitter()
    all_clues = splitter.split_and_extract_clues(image_path)
    
    if all_clues:
        print("\n所有行的数字:")
        for i, clues in enumerate(all_clues):
            print(f"行 {i+1}: {clues}")

if __name__ == "__main__":
    test_split_vertical_clues()
