#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一的题目线索分割和数字识别模块
支持水平（列）和垂直（行）两种方向
"""

import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from improved_digit_recognizer import ImprovedDigitRecognizer


class CluesSplitter:
    def __init__(self, direction='horizontal', debug_dir="pic_debug", debug=False):
        """初始化线索分割器
        
        Args:
            direction: 'horizontal'（水平-列题目）或 'vertical'（垂直-行题目）
            debug_dir: 调试目录
            debug: 是否打印调试信息（默认False）
        """
        if direction not in ('horizontal', 'vertical'):
            raise ValueError("direction must be 'horizontal' or 'vertical'")
        
        self.direction = direction
        self.is_horizontal = (direction == 'horizontal')
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
        
        # 黄色区域的识别标准：B较小，G和R较大但接近
        if b < 150 and g > 100 and r > 150:
            return True
        
        return False
    
    def find_boundaries(self, image):
        """
        查找区域边界（列或行）
        
        Args:
            image: 题目的图像
            
        Returns:
            区域的边界列表，每个元素为(start, end)
        """
        height, width = image.shape[:2]
        print(f"图像尺寸: {width}x{height}")
        
        if self.is_horizontal:
            return self._find_column_boundaries(image, width, height)
        else:
            return self._find_row_boundaries(image, width, height)
    
    def _find_column_boundaries(self, image, width, height):
        """查找列边界（水平方向）"""
        # 计算每个x位置处黄色像素的比例
        column_yellowness = []
        
        for x in range(width):
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
        in_white_area = True
        left_boundary = 0
        threshold = 0.3
        
        for x, ratio in smoothed_yellowness:
            if in_white_area:
                if ratio > threshold:
                    left_boundary = x
                    in_white_area = False
            else:
                if ratio < threshold:
                    right_boundary = x - 1
                    if right_boundary - left_boundary > 5:
                        columns.append((left_boundary, right_boundary))
                    in_white_area = True
        
        if not in_white_area:
            columns.append((left_boundary, width - 1))
        
        print(f"找到 {len(columns)} 列题目")
        for i, (left, right) in enumerate(columns):
            print(f"列 {i+1}: 左边界={left}, 右边界={right}, 宽度={right-left+1}")
        
        return columns
    
    def _find_row_boundaries(self, image, width, height):
        """查找行边界（垂直方向）"""
        # 计算每个y位置处黄色像素的比例
        row_yellowness = []
        
        for y in range(height):
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
        in_white_area = True
        top_boundary = 0
        threshold = 0.3
        
        for y, ratio in smoothed_yellowness:
            if in_white_area:
                if ratio > threshold:
                    top_boundary = y
                    in_white_area = False
            else:
                if ratio < threshold:
                    bottom_boundary = y - 1
                    if bottom_boundary - top_boundary > 5:
                        rows.append((top_boundary, bottom_boundary))
                    in_white_area = True
        
        if not in_white_area:
            rows.append((top_boundary, height - 1))
        
        print(f"找到 {len(rows)} 行题目")
        for i, (top, bottom) in enumerate(rows):
            print(f"行 {i+1}: 上边界={top}, 下边界={bottom}, 高度={bottom-top+1}")
        
        return rows
    
    def split_and_extract_clues(self, image_input):
        """
        分割题目图片并提取数字
        
        Args:
            image_input: 题目图片路径（字符串）或numpy数组
            
        Returns:
            包含每行/每列数字的列表
        """
        # 加载图片
        if isinstance(image_input, str):
            image = cv2.imread(image_input)
            if image is None:
                print(f"无法加载图片 {image_input}")
                return None
            print(f"加载图片: {image_input}")
        else:
            image = image_input
            print(f"使用numpy数组：尺寸={image.shape[1]}x{image.shape[0]}")
        
        # 找出区域边界
        boundaries = self.find_boundaries(image)
        
        # 绘制和保存标记图片
        self._save_marked_image(image, boundaries)
        
        # 提取每个区域的数字
        all_clues = []
        for i, boundary in enumerate(boundaries):
            region = self._extract_region(image, boundary)
            self._save_region_image(region, i)
            
            # 保存该区域的所有数字图像（用于调试）
            if self.is_horizontal:
                digit_images = self.split_perpendicular(region)
                for j, digit_img in enumerate(digit_images):
                    digit_path = os.path.join(self.debug_dir, f"column_{i+1:02d}_digit_{j+1:02d}.jpg")
                    cv2.imwrite(digit_path, digit_img)
            else:
                digit_images = self.split_perpendicular(region)
                for j, digit_img in enumerate(digit_images):
                    digit_path = os.path.join(self.debug_dir, f"row{i+1:02d}_digit_{j+1:02d}.jpg")
                    cv2.imwrite(digit_path, digit_img)
            
            clues = self.recognize_clues(region, i)
            all_clues.append(clues)
            
            # 打印结果
            if self.is_horizontal:
                print(f"列 {i+1}: {clues}")
            else:
                print(f"行 {i+1}: {clues}")
        
        return all_clues
    
    def _save_marked_image(self, image, boundaries):
        """保存标记后的图片"""
        marked_image = image.copy()
        
        if self.is_horizontal:
            for i, (left, right) in enumerate(boundaries):
                cv2.rectangle(marked_image, (left, 0), (right, image.shape[0]), (0, 0, 255), 2)
                cv2.putText(marked_image, str(i+1), (left+5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            marked_image_path = os.path.join(self.debug_dir, "horizontal_clues_marked.jpg")
        else:
            for i, (top, bottom) in enumerate(boundaries):
                cv2.rectangle(marked_image, (0, top), (image.shape[1], bottom), (0, 0, 255), 2)
                cv2.putText(marked_image, str(i+1), (5, top+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            marked_image_path = os.path.join(self.debug_dir, "vertical_clues_marked.jpg")
        
        cv2.imwrite(marked_image_path, marked_image)
        print(f"已保存标记后的图片到 {marked_image_path}")
    
    def _extract_region(self, image, boundary):
        """提取区域图片（列或行）"""
        if self.is_horizontal:
            left, right = boundary
            return image[:, left:right, :]
        else:
            top, bottom = boundary
            return image[top:bottom+1, :, :]
    
    def _save_region_image(self, region, index):
        """保存区域图片"""
        if self.is_horizontal:
            region_image_path = os.path.join(self.debug_dir, f"column_{index+1:02d}.jpg")
        else:
            region_image_path = os.path.join(self.debug_dir, f"row_{index+1:02d}.jpg")
        cv2.imwrite(region_image_path, region)
    
    def recognize_clues(self, region_image, region_index=-1):
        """
        识别区域中的数字
        先进行切割以分离每个数字，然后进行识别
        
        Args:
            region_image: 区域的图像（列或行）
            region_index: 区域的索引（用于调试输出）
            
        Returns:
            按顺序排列的数字列表
        """
        # 第一步：切割，分离每个数字的图像
        digit_images = self.split_perpendicular(region_image)
        
        # 第二步：对每个数字图像进行识别
        digits = []
        for j, digit_img in enumerate(digit_images):
            debug_index = (region_index * 100 + j) if region_index >= 0 else -1
            digit = self.digit_recognizer.recognize_single_digit(digit_img, self.debug_dir, debug_index)
            if digit != -1:  # 只添加成功识别的数字
                digits.append(digit)
        
        return digits
    
    def split_perpendicular(self, region_image):
        """
        垂直方向切割（水平对应纵向，垂直对应横向）
        
        Args:
            region_image: 区域的图像
            
        Returns:
            切分好的数字图像列表
        """
        if self.is_horizontal:
            return self._split_column_vertically(region_image)
        else:
            return self._split_row_horizontally(region_image)
    
    def _split_column_vertically(self, column_image):
        """将列图像纵向切割，上下分离每个数字"""
        height, width = column_image.shape[:2]
        if self.debug:
            print(f"[DEBUG] 列图像尺寸: {width}x{height}")
        
        # 计算每一行的黑色像素比例
        row_black_ratio = []
        for y in range(height):
            black_count = 0
            for x in range(width):
                b, g, r = int(column_image[y, x, 0]), int(column_image[y, x, 1]), int(column_image[y, x, 2])
                if b < 80 and g < 80 and r < 80:
                    black_count += 1
            
            black_ratio = black_count / width if width > 0 else 0
            row_black_ratio.append(black_ratio)
        
        return self._find_digit_regions_and_extract(row_black_ratio, height, width, column_image, is_horizontal=True)
    
    def _split_row_horizontally(self, row_image):
        """将行图像横向切割，左右分离每个数字"""
        height, width = row_image.shape[:2]
        if self.debug:
            print(f"[DEBUG] 行图像尺寸: {width}x{height}")
        
        # 计算每一列的黑色像素比例
        col_black_ratio = []
        for x in range(width):
            black_count = 0
            for y in range(height):
                b, g, r = int(row_image[y, x, 0]), int(row_image[y, x, 1]), int(row_image[y, x, 2])
                if b < 80 and g < 80 and r < 80:
                    black_count += 1
            
            black_ratio = black_count / height if height > 0 else 0
            col_black_ratio.append(black_ratio)
        
        return self._find_digit_regions_and_extract(col_black_ratio, width, height, row_image, is_horizontal=False)
    
    def _find_digit_regions_and_extract(self, ratio_list, primary_len, secondary_len, image, is_horizontal=True):
        """查找数字区域并提取"""
        digit_regions = []
        in_digit = False
        start_pos = 0
        black_threshold = 0.01
        
        for pos in range(primary_len):
            if ratio_list[pos] >= black_threshold and not in_digit:
                start_pos = pos
                in_digit = True
                if self.debug:
                    pos_name = "行" if is_horizontal else "列"
                    print(f"[DEBUG] 第{pos}{pos_name}开始新数字区域")
            elif ratio_list[pos] < black_threshold and in_digit:
                is_separator = True
                check_count = 3 if not is_horizontal else 3
                if pos + check_count <= primary_len:
                    for check_pos in range(pos, min(pos + check_count, primary_len)):
                        if ratio_list[check_pos] >= black_threshold:
                            is_separator = False
                            break
                
                if is_separator:
                    min_size = 15
                    if pos - start_pos >= min_size:
                        digit_regions.append((start_pos, pos - 1))
                        if self.debug:
                            pos_name = "高度" if is_horizontal else "宽度"
                            print(f"[DEBUG] 找到数字区域: [{start_pos}, {pos-1}], {pos_name}={pos - start_pos}")
                    in_digit = False
        
        if in_digit:
            if primary_len - start_pos >= 15:
                digit_regions.append((start_pos, primary_len - 1))
                if self.debug:
                    pos_name = "高度" if is_horizontal else "宽度"
                    print(f"[DEBUG] 找到数字区域: [{start_pos}, {primary_len-1}], {pos_name}={primary_len - start_pos}")
        
        if self.debug:
            print(f"[DEBUG] 总共找到 {len(digit_regions)} 个数字区域")
        
        # 提取数字图像
        digit_images = []
        for start_pos, end_pos in digit_regions:
            if is_horizontal:
                raw_size = end_pos - start_pos + 1
                if raw_size < 15:
                    if self.debug:
                        print(f"[DEBUG] 数字区域过小({raw_size}px)，跳过")
                    continue
                
                padded_start = max(0, start_pos - 5)
                padded_end = min(secondary_len - 1, end_pos + 5)
                digit_img = image[padded_start:padded_end+1, :, :]
                
                img_width = digit_img.shape[1]
                if img_width > 60:
                    digit_img = digit_img[:, :-8, :]
            else:
                raw_size = end_pos - start_pos + 1
                if raw_size < 15:
                    if self.debug:
                        print(f"[DEBUG] 数字区域过小({raw_size}px)，跳过")
                    continue
                
                padded_start = max(0, start_pos - 5)
                padded_end = min(secondary_len - 1, end_pos + 5)
                digit_img = image[:, padded_start:padded_end+1, :]
                
                img_height = digit_img.shape[0]
                if img_height > 60:
                    digit_img = digit_img[:-8, :, :]
            
            # 容错处理：补齐到45像素
            final_height, final_width = digit_img.shape[:2]
            if final_width < 45 or final_height < 45:
                target_width = max(45, final_width)
                target_height = max(45, final_height)
                
                padded_img = np.full((target_height, target_width, 3), [200, 150, 100], dtype=np.uint8)
                
                y_offset = (target_height - final_height) // 2
                x_offset = (target_width - final_width) // 2
                padded_img[y_offset:y_offset+final_height, x_offset:x_offset+final_width] = digit_img
                
                digit_img = padded_img
                if self.debug:
                    print(f"[DEBUG] 补齐尺寸: {final_width}x{final_height} -> {target_width}x{target_height}")
            
            digit_images.append(digit_img)
        
        return digit_images


def test_clues_splitter():
    """测试整合后的线索分割器"""
    # 测试水平方向（列题目）
    print("=" * 60)
    print("测试水平方向（列题目）")
    print("=" * 60)
    splitter_h = CluesSplitter(direction='horizontal')
    col_clues = splitter_h.split_and_extract_clues("pic/heng.png")
    
    if col_clues:
        print("\n所有列的数字:")
        for i, clues in enumerate(col_clues):
            print(f"列 {i+1}: {clues}")
    
    # 测试垂直方向（行题目）
    print("\n" + "=" * 60)
    print("测试垂直方向（行题目）")
    print("=" * 60)
    splitter_v = CluesSplitter(direction='vertical')
    row_clues = splitter_v.split_and_extract_clues("pic/zong.png")
    
    if row_clues:
        print("\n所有行的数字:")
        for i, clues in enumerate(row_clues):
            print(f"行 {i+1}: {clues}")


if __name__ == "__main__":
    test_clues_splitter()
