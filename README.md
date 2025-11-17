# 数图自动解答程序

这是一个使用Python和OpenCV实现的数图（Nonogram）自动解答程序。

## 项目结构

```
.
├── main.py                 # 程序入口
├── requirements.txt        # 依赖包列表
├── rq.txt                  # 需求文档
├── pic/                    # 图片存放目录
├── number/                 # 数字模板目录
├── pic_debug/              # 调试图像输出目录
├── puzzle_clue.txt         # 题目线索文件
├── run_all_puzzles.py      # 数图题目识别主程序
├── solver.py               # 数图求解器和UI界面
├── ui_screenshot.py        # UI截图处理模块
├── clues_splitter.py       # 题目线索分割器
├── horizontal_clues_splitter.py  # 水平题目分割器
├── vertical_clues_splitter.py    # 垂直题目分割器
├── improved_digit_recognizer.py  # 改进的数字识别器
└── tool_backup_project.py  # 项目备份工具
```

## 安装依赖

```bash
pip install -r requirements.txt
```

或者使用Python模块方式安装：

```bash
python3 -m pip install -r requirements.txt
```

## 运行程序

```bash
python3 main.py
```

## 生成测试图片

程序包含一个测试图片生成脚本，可以生成一个简单的10x10数图用于测试：

```bash
python3 generate_test_image.py
```

生成的测试图片将保存在[pic](file:///Users/karmy/Projects/SuduPic/pic/)目录下。

## 使用方法

1. 运行程序：`python3 main.py`
2. 点击"选择图片"按钮选择一张数图图片（可以使用生成的测试图片[pic/test_nonogram.png](file:///Users/karmy/Projects/SuduPic/pic/test_nonogram.png)）
3. 点击"分析"按钮进行数图求解
4. 查看求解结果
5. 可选：点击"保存结果"按钮保存求解后的图片

## 注意事项

- 当前版本为初始版本，核心算法仍在开发中
- 支持10x10和15x15规格的数图
- 支持JPG/PNG/BMP格式的图片
- 图像识别和数图求解算法还有待完善