#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进的数字识别模块，专门用于数图中的数字识别

功能说明：
1. 支持标准数字模板匹配 (1-15)
2. 支持大尺寸数字模板匹配 (1b-10b)
3. 自动缩放模板以适应不同尺寸的输入图像
4. 使用模板匹配算法(TM_CCOEFF)进行数字识别

文件要求：
- 标准模板: number/1.png, number/2.png, ..., number/15.png
- 大尺寸模板: number/1b.png, number/2b.png, ..., number/10b.png

使用方法：
```python
recognizer = ImprovedDigitRecognizer()
digit = recognizer.recognize_single_digit(image)
```
"""

import cv2
import numpy as np
import os
from pathlib import Path

class ImprovedDigitRecognizer:
    def __init__(self):
        """初始化改进的数字识别器"""
        self.templates = {}  # 存储模板图像
        self.template_dir = os.path.join(os.path.dirname(__file__), 'number')
        self.load_templates()
    
    def is_yellow_color(self, pixel):
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
    
    def load_templates(self):
        """从 number 目录中加载模板图像 (1-15)，以及大尺寸模板 (1b-10b)
        
        加载规则：
        1. 标准模板 (1-15): 用于匹配常规尺寸的数字
        2. 大尺寸模板 (1b-10b): 用于匹配较大尺寸的数字
        
        模板存储格式：
        - self.templates[数字] = 图像数组 (标准模板)
        - self.templates[数字+'b'] = 图像数组 (大尺寸模板)
        
        注意：只有存在的模板文件才会被加载
        """
        # 加载标准模板 (1-15)
        for digit in range(1, 16):
            template_path = os.path.join(self.template_dir, f'{digit}.png')
            if os.path.exists(template_path):
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is not None:
                    self.templates[digit] = template
        
        # 加载大尺寸模板 (1b-10b)
        for digit in range(1, 11):
            digit_name = f'{digit}b'
            template_path = os.path.join(self.template_dir, f'{digit_name}.png')
            if os.path.exists(template_path):
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is not None:
                    # 使用 digit_name 作为键（字符串）
                    self.templates[digit_name] = template
    
    def recognize_single_digit(self, digit_image, debug_dir=None, debug_index=-1):
        """
        使用模板匹配识别单个数字图片
        
        识别流程：
        1. 预处理：检查输入图像有效性
        2. 模板匹配：
           - 遍历所有已加载的模板(标准+大尺寸)
           - 如果模板尺寸超过输入图像，进行缩放
           - 使用TM_CCOEFF算法进行模板匹配
        3. 结果选择：选择匹配分数最高的模板
        4. 结果转换：大尺寸模板结果转换为标准数字
        
        Args:
            digit_image: 单个数字的图像（通常是 ~55x55 像素）
            debug_dir: 调试目录
            debug_index: 调试索引
            
        Returns:
            识别出的数字（1-15），如果识别失败返回-1
            
        匹配算法说明：
        - TM_CCOEFF: 相关系数匹配，适合寻找相似的模板
        - 分数值越高表示匹配度越好
        - 自动处理模板与输入图像的尺寸适配
        """
        height, width = digit_image.shape[:2]
        
        if height < 10 or width < 10:
            return -1
        
        # 直接使用原始图像
        processed_img = digit_image
        
        best_digit = -1
        best_score = -1
        all_scores = {}  # 记录所有模板的匹配结果
        
        # 与每个模板进行匹配，找出最接近的数字
        for digit, template in self.templates.items():
            template_height, template_width = template.shape[:2]
            
            # 如果模板尺寸超过输入图像，对模板进行缩放
            if template_height > height or template_width > width:
                # 计算缩放比例，使模板适应输入图像
                scale_h = height / template_height if template_height > 0 else 1.0
                scale_w = width / template_width if template_width > 0 else 1.0
                scale = min(scale_h, scale_w, 1.0)  # 不超过原始尺寸
                
                if scale < 0.5:  # 如果缩放比例太小，跳过此模板
                    continue
                
                # 对模板进行缩放
                new_width = int(template_width * scale)
                new_height = int(template_height * scale)
                scaled_template = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            else:
                scaled_template = template
            
            # 确保模板尺寸不超过输入图像
            scaled_height, scaled_width = scaled_template.shape[:2]
            if scaled_height > height or scaled_width > width:
                continue
            
            # 使用最优候选匹配法进行模板匹配
            result = cv2.matchTemplate(processed_img, scaled_template, cv2.TM_CCOEFF)
            _, score, _, _ = cv2.minMaxLoc(result)
            all_scores[digit] = score
            
            if score > best_score:
                best_score = score
                best_digit = digit
        
        # 打印调试信息：所有模板的匹配结果
        if all_scores:
            print(f"[DEBUG] 数字图像水平={width}, 竖直={height}")
            sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
            for digit, score in sorted_scores:
                print(f"  整数{digit}: 特正序序分={score:.2f}", end="")
                if digit == best_digit:
                    print(" <=== 选中")
                else:
                    print()
        
        # 转换大尺寸模板的结果回原整数 (1b-10b -> 1-10)
        if isinstance(best_digit, str) and best_digit.endswith('b'):
            try:
                best_digit = int(best_digit[:-1])  # 移除最后的'b'，转换为整数
            except ValueError:
                pass
        
        return best_digit

    

def test_improved_digit_recognizer():
    """测试改进的数字识别器"""
    # 这里可以添加测试代码
    pass

if __name__ == "__main__":
    test_improved_digit_recognizer()