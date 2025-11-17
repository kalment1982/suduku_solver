import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import shutil
import os


def parse_input(filename):
    """解析输入文件，返回行提示和列提示
    
    支持格式: [[a,b],[c,d],...]或[a,b],[c,d],...的格式
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    def parse_line(line):
        """解析一行数佋提示
        例如: [[7,1],[1,3,1],[9]] 或 [7,1],[1,3,1],[9] -> [[7,1], [1,3,1], [9]]
        """
        line = line.strip()
        if not line:
            return []
        
        # 先尝试使用eval解析Python列表格式
        try:
            result = eval(line)
            if isinstance(result, list) and len(result) > 0:
                # 检查是否为二维数组
                if isinstance(result[0], list):
                    return result
                else:
                    # 是一维数组，挂碩成二维
                    return [result]
        except:
            pass
        
        # 如果eval失败，尝试正则表达式解析
        hints = []
        import re
        matches = re.findall(r'\[([^\]]+)\]', line)
        for match in matches:
            # 将 "7,1" 分解为 [7, 1]
            try:
                hint = [int(x.strip()) for x in match.split(',')]
                hints.append(hint)
            except:
                pass
        
        return hints
    
    # 解析第一行（列提示）
    col_hints = parse_line(lines[0])
    
    # 解析第二行（行提示）
    row_hints = parse_line(lines[1])
    
    return row_hints, col_hints


def get_blocks(line):
    """从一行/列中提取填充块的大小"""
    blocks = []
    current_block = 0
    for cell in line:
        if cell == 1:
            current_block += 1
        elif current_block > 0:
            blocks.append(current_block)
            current_block = 0
    if current_block > 0:
        blocks.append(current_block)
    return blocks if blocks else [0]


def generate_all_patterns(hints, length, marked_state):
    """生成所有与 marked_state 兼容的方案"""
    if not hints or hints == [0]:
        pattern = [0] * length
        for i in range(length):
            if marked_state[i] not in (-1, 0):
                return []
        return [pattern]
    
    valid_patterns = []
    
    def backtrack(pos, block_idx, current_pattern):
        if block_idx == len(hints):
            pattern = current_pattern + [0] * (length - pos)
            for i in range(length):
                if marked_state[i] != -1 and marked_state[i] != pattern[i]:
                    return
            valid_patterns.append(pattern)
            return
        
        block_size = hints[block_idx]
        space_needed = sum(hints[block_idx + 1:]) + len(hints[block_idx + 1:])
        
        for start in range(pos, length - block_size - space_needed + 1):
            new_pattern = current_pattern + [0] * (start - pos) + [1] * block_size
            
            valid = True
            for i in range(len(new_pattern)):
                if marked_state[i] != -1 and marked_state[i] != new_pattern[i]:
                    valid = False
                    break
            
            if valid:
                if block_idx < len(hints) - 1:
                    backtrack(start + block_size + 1, block_idx + 1, new_pattern + [0])
                else:
                    backtrack(start + block_size, block_idx + 1, new_pattern)
    
    backtrack(0, 0, [])
    return valid_patterns


def determine_certain_by_range(hints, length, marked_state, debug_info=""):
    """
    简单方法：依据提示计算每个块的最左最右可能位置，找交集
    不依赖已筚记的状态，适合列推理
    """
    result = marked_state.copy()
    
    if debug_info:
        print(f"\n{debug_info} [方法:简单范围法]")
        print(f"  提示: {hints}")
        print(f"  长度: {length}")
    
    if not hints or hints == [0]:
        for i in range(length):
            if result[i] == -1:
                result[i] = 0
        if debug_info:
            print(f"  提示为[0]，所有格子都标记为留白")
        return result
    
    # 为每个块计算必然填充的范围
    for block_idx, block_size in enumerate(hints):
        # 计算该块最左可能的起始位置
        left_start = sum(hints[:block_idx]) + block_idx  # 前面所有块的大小 + 间隔数
        
        # 计算该块最右可能的起始位置
        right_space = sum(hints[block_idx + 1:]) + len(hints[block_idx + 1:])  # 后面所有块的大小 + 间隔数
        right_start = length - block_size - right_space
        
        # 最左方案的结束位置
        left_end = left_start + block_size - 1
        
        # 交集范围：从最右起始到最左结束
        certain_start = right_start
        certain_end = left_end
        
        if debug_info:
            print(f"  第{block_idx + 1}个块(大小={block_size}):")
            print(f"    最左可能: [{left_start}, {left_end}]")
            print(f"    最右可能: [{right_start}, {right_start + block_size - 1}]")
            if certain_start <= certain_end:
                print(f"    必然填充: [{certain_start}, {certain_end}]")
            else:
                print(f"    无必然填充")
        
        # 标记必然为1的位置
        if certain_start <= certain_end:
            for i in range(max(0, certain_start), min(length, certain_end + 1)):
                if result[i] == -1:
                    result[i] = 1
                    if debug_info:
                        print(f"      标记位置{i}为填充")
    
    return result


def determine_certain_by_patterns(hints, length, marked_state, debug_info=""):
    """
    复杂方法：生成所有兼容的方案，找交集
    考虑已筚记的状态，适合行推理
    """
    result = marked_state.copy()
    
    if debug_info:
        print(f"\n{debug_info} [方法:方案生成法]")
        print(f"  提示: {hints}")
        print(f"  长度: {length}")
    
    if not hints or hints == [0]:
        for i in range(length):
            if result[i] == -1:
                result[i] = 0
        if debug_info:
            print(f"  提示为[0]，所有格子都标记为留白")
        return result
    
    # 生成所有兼容的方案
    all_valid_patterns = generate_all_patterns(hints, length, marked_state)
    
    if not all_valid_patterns:
        if debug_info:
            print(f"  警告：没有找到兼容的方案！")
        return result
    
    if debug_info:
        print(f"  找到 {len(all_valid_patterns)} 个兼容的方案")
    
    # 找出所有方案中一致的位置
    for i in range(length):
        if result[i] == -1:  # 未知位置
            first_val = all_valid_patterns[0][i]
            if all(pattern[i] == first_val for pattern in all_valid_patterns):
                result[i] = first_val
                if debug_info:
                    if first_val == 1:
                        print(f"  标记位置{i}为填充（所有方案一致）")
                    else:
                        print(f"  标记位置{i}为留白（所有方案一致）")
    
    return result


def determine_certain_cells(hints, length, marked_state, debug_info=""):
    """
    绣合函数：根据上下文自动选择推理方法
    - 列推理：使用简单范围法
    - 行推理：使用方案生成法
    """
    result = marked_state.copy()
    
    # 判断是否有已筚记的格子
    has_marked = any(cell != -1 for cell in marked_state)
    
    if has_marked:
        # 有已筚记的格子，使用方案生成法（行推理）
        return determine_certain_by_patterns(hints, length, marked_state, debug_info)
    else:
        # 没有已筚记的格子，使用简单范围法（列推理）
        return determine_certain_by_range(hints, length, marked_state, debug_info)


def is_valid_board(board, row_hints, col_hints):
    """检查棋盘是否有效"""
    num_rows = len(board)
    num_cols = len(board[0]) if num_rows > 0 else 0
    
    for r in range(num_rows):
        row_state = board[r]
        if all(cell != -1 for cell in row_state):
            if get_blocks(row_state) != row_hints[r]:
                return False
    
    for col in range(num_cols):
        col_state = [board[r][col] for r in range(num_rows)]
        if all(cell != -1 for cell in col_state):
            if get_blocks(col_state) != col_hints[col]:
                return False
    
    return True


def solve_with_constraint_propagation(board, row_hints, col_hints):
    """用约束传播进行迭代消除"""
    num_rows = len(board)
    num_cols = len(board[0]) if num_rows > 0 else 0
    
    max_iterations = 1000
    iteration = 0
    changed = True
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        
        for col in range(num_cols):
            col_state = [board[r][col] for r in range(num_rows)]
            new_col_state = determine_certain_cells(col_hints[col], num_rows, col_state)
            
            for r in range(num_rows):
                if board[r][col] != new_col_state[r]:
                    board[r][col] = new_col_state[r]
                    changed = True
        
        for r in range(num_rows):
            row_state = board[r][:]
            new_row_state = determine_certain_cells(row_hints[r], num_cols, row_state)
            
            for col in range(num_cols):
                if board[r][col] != new_row_state[col]:
                    board[r][col] = new_row_state[col]
                    changed = True
    
    return board


def solve_with_backtrack(board, row_hints, col_hints):
    """带回溯的完整求解"""
    board = solve_with_constraint_propagation(board, row_hints, col_hints)
    
    num_rows = len(board)
    num_cols = len(board[0]) if num_rows > 0 else 0
    
    unknown_found = False
    unknown_row, unknown_col = -1, -1
    
    for r in range(num_rows):
        for c in range(num_cols):
            if board[r][c] == -1:
                unknown_found = True
                unknown_row, unknown_col = r, c
                break
        if unknown_found:
            break
    
    if not unknown_found:
        if is_valid_board(board, row_hints, col_hints):
            return board
        else:
            return None
    
    board_copy = [row[:] for row in board]
    board_copy[unknown_row][unknown_col] = 1
    result = solve_with_backtrack(board_copy, row_hints, col_hints)
    if result is not None:
        return result
    
    board_copy = [row[:] for row in board]
    board_copy[unknown_row][unknown_col] = 0
    result = solve_with_backtrack(board_copy, row_hints, col_hints)
    if result is not None:
        return result
    
    return None


def solve(filename):
    """主求解函数"""
    row_hints, col_hints = parse_input(filename)
    
    num_rows = len(row_hints)
    num_cols = len(col_hints)
    
    board = [[-1] * num_cols for _ in range(num_rows)]
    
    return solve_with_backtrack(board, row_hints, col_hints)


class NonogramUI:
    def __init__(self, root, col_hints=None, row_hints=None, png_files_func=None, extract_func=None):
        self.root = root
        self.root.title("数图解题器")
        self.png_files_func = png_files_func
        self.extract_func = extract_func
        # 不分清col和row的传入顺序，站它们位置
        self.row_hints = row_hints if row_hints else []
        self.col_hints = col_hints if col_hints else []
        self.board = None
        self.board_history = []  # 保存每一次迭代的结果
        self.cell_size = 40  # 格子大小
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建顶部工具栏（图片选择和解题）
        if png_files_func and extract_func:
            toolbar_frame = ttk.Frame(main_frame)
            toolbar_frame.pack(fill=tk.X, pady=(0, 10))
            
            label = ttk.Label(toolbar_frame, text="选择图片:")
            label.pack(side=tk.LEFT, padx=(0, 5))
            
            # 获取图片列表
            png_files = png_files_func()
            self.file_list = png_files
            self.file_display_names = [filename for _, filename in png_files]
            
            if png_files:
                self.combo = ttk.Combobox(toolbar_frame, values=self.file_display_names, state="readonly", width=40)
                self.combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.combo.current(0)  # 默认为最新的文件
                
                # 解题按钮
                solve_button = ttk.Button(toolbar_frame, text="解题", command=self.on_solve_clicked)
                solve_button.pack(side=tk.LEFT, padx=(5, 0))
                
                # 刷新文件列表按钮
                refresh_button = ttk.Button(toolbar_frame, text="刷新", command=self.on_refresh_clicked)
                refresh_button.pack(side=tk.LEFT, padx=(5, 0))
            else:
                no_files_label = ttk.Label(toolbar_frame, text="下载目录中找不到PNG文件", foreground="red")
                no_files_label.pack(side=tk.LEFT)
        
        # 创建画布显示棋盘
        self.canvas = tk.Canvas(
            main_frame, 
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 求解
        self.solve_puzzle()
        self.draw_board()
    
    def on_solve_clicked(self):
        """解题按钮回调：载入选定的图片并解题"""
        if not hasattr(self, 'combo') or self.combo.current() < 0:
            return
        if not self.extract_func:
            return
        
        # 清空 pic_debug 文件夹
        self.clear_debug_dir()
        
        index = self.combo.current()
        if index >= 0 and index < len(self.file_list):
            image_path = self.file_list[index][0]
            col_clues, row_clues = self.extract_func(image_path)
            
            if col_clues is not None and row_clues is not None:
                # 直接更新数据，不写文件
                self.row_hints = row_clues
                self.col_hints = col_clues
                self.board = None
                self.board_history = []
                
                # 保存题目到 puzzle_clue.txt
                self.save_clues_to_file()
                
                self.solve_puzzle()
                self.draw_board()
    
    def on_refresh_clicked(self):
        """刷新文件列表按钮回调"""
        if not hasattr(self, 'combo') or not self.png_files_func:
            return
        
        # 重新获取文件列表
        png_files = self.png_files_func()
        self.file_list = png_files
        self.file_display_names = [filename for _, filename in png_files]
        
        # 更新下拉菜单
        self.combo['values'] = self.file_display_names
        if png_files:
            self.combo.current(0)
    
    def save_clues_to_file(self):
        """保存题目线索到 puzzle_clue.txt"""
        try:
            with open('puzzle_clue.txt', 'w') as f:
                # 第一行是列提示
                col_hints_str = str(self.col_hints)
                # 第二行是行提示
                row_hints_str = str(self.row_hints)
                f.write(col_hints_str + '\n')
                f.write(row_hints_str + '\n')
        except Exception as e:
            print(f"保存题目失败: {e}")
    
    def clear_debug_dir(self):
        """清空 pic_debug 文件夹"""
        debug_dir = "pic_debug"
        try:
            if os.path.exists(debug_dir):
                shutil.rmtree(debug_dir)
                os.makedirs(debug_dir)
                print(f"已清空 {debug_dir} 文件夹")
        except Exception as e:
            print(f"清空 {debug_dir} 失败: {e}")
    
    def solve_puzzle(self):
        """求解数图"""
        # 如果没有提示数据，不求解
        if not self.row_hints or not self.col_hints:
            return
        
        num_rows = len(self.row_hints)
        num_cols = len(self.col_hints)
        self.board = [[-1] * num_cols for _ in range(num_rows)]
        self.board_history = []
        
        max_iterations = 10  # 最多迭代1次列+多旤迭代1次行
        
        for iteration in range(max_iterations):
            print(f"\n" + "="*60)
            print(f"开始第{iteration + 1}次迭代")
            print("="*60)
            
            changed = False
            
            # 列推理
            if iteration % 2 == 0:
                print(f"\n>>> 第{iteration + 1}次迭代: 列推理")
                for col in range(num_cols):
                    col_state = [self.board[r][col] for r in range(num_rows)]
                    new_col_state = determine_certain_cells(
                        self.col_hints[col], 
                        num_rows, 
                        col_state,
                        debug_info=f"第{col + 1}列推理"
                    )
                    
                    for r in range(num_rows):
                        if self.board[r][col] != new_col_state[r]:
                            self.board[r][col] = new_col_state[r]
                            changed = True
            
            # 保存本次迭代的结果
            else:
                print(f"\n>>> 第{iteration + 1}次迭代: 行推理")
                for row in range(num_rows):
                    row_state = self.board[row][:]
                    state_str = "".join(['■' if c == 1 else ('×' if c == 0 else '?') for c in row_state])
                    
                    new_row_state = determine_certain_cells(
                        self.row_hints[row],
                        num_cols,
                        row_state,
                        debug_info=f"第{row + 1}行推理 [当前状态: {state_str}]"
                    )
                    
                    for col in range(num_cols):
                        if self.board[row][col] != new_row_state[col]:
                            self.board[row][col] = new_row_state[col]
                            changed = True
            
            # 保存本次迭代的结果
            self.board_history.append([row[:] for row in self.board])
            
            print(f"\n第{iteration + 1}次迭代完成")
            
            # 如果没有变化，则停止迭代
            if not changed:
                print(f"没有新的推理，停止迭代")
                break
    
    def draw_board(self):
        """绘制棋盘"""
        self.canvas.delete("all")
        
        # 如果没有提示数据，不绘制
        if not self.row_hints or not self.col_hints or self.board is None:
            return
        
        num_rows = len(self.board)
        num_cols = len(self.board[0]) if num_rows > 0 else 0
        
        # 计算标签宽度
        row_label_width = max(len(str(hint).replace('[', '').replace(']', '').replace(' ', '')) for hint in self.row_hints)
        col_label_height = max(len(str(hint).replace('[', '').replace(']', '').replace(' ', '')) for hint in self.col_hints)
        
        offset_x = (row_label_width + 1) * 16  # 从8改为16
        offset_y = (col_label_height + 1) * 24  # 从12改为24
        
        # 绘制列题目框（先绘制，避免被文字覆盖）
        for col_idx in range(num_cols):
            x1 = offset_x + col_idx * self.cell_size
            y1 = offset_y - (col_label_height + 1) * 24
            x2 = x1 + self.cell_size
            y2 = offset_y
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="black",
                fill="#ffe6e6"
            )
        
        # 绘制行题目框（先绘制，避免被文字覆盖）
        for row_idx in range(num_rows):
            x1 = 0
            y1 = offset_y + row_idx * self.cell_size
            x2 = offset_x
            y2 = y1 + self.cell_size
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="black",
                fill="#e6f2ff"
            )
        for col_idx, col_hint in enumerate(self.col_hints):
            hint_str = str(col_hint).replace('[', '').replace(']', '').replace(',', '')
            # 从下往上绘制，最后一个字符最接近棋盘
            for char_idx, char in enumerate(hint_str):
                y = offset_y - (len(hint_str) - char_idx) * 24  # 靠下对齐
                x = offset_x + col_idx * self.cell_size + self.cell_size // 2
                self.canvas.create_text(
                    x, y, 
                    text=char, 
                    font=("Arial", 16),
                    fill="red"
                )
        
        # 绘制行数字（靠右对齐）
        for row_idx, row_hint in enumerate(self.row_hints):
            hint_str = str(row_hint).replace('[', '').replace(']', '').replace(',', '')
            x = offset_x - 10  # 靠右对齐，距离棋盘左边10像素
            y = offset_y + row_idx * self.cell_size + self.cell_size // 2
            self.canvas.create_text(
                x, y,
                text=hint_str,
                font=("Arial", 16),
                fill="red",
                anchor="e"  # 右对齐
            )
        
        # 绘制棋盘格子
        for r in range(num_rows):
            for c in range(num_cols):
                x1 = offset_x + c * self.cell_size
                y1 = offset_y + r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                cell_value = self.board[r][c]
                
                # 判断该格子是否是本次迭代新增的
                is_new_this_iteration = False
                if len(self.board_history) >= 2:
                    # 与上一次迭代比较
                    prev_board = self.board_history[-2]
                    if prev_board[r][c] == -1 and cell_value != -1:
                        is_new_this_iteration = True
                
                # 绘制格子边框和背景
                if cell_value == 1:
                    # 确定是填充：如果是本次迭代新增的用红色，否则用蓝色
                    fill_color = "red" if is_new_this_iteration else "blue"
                elif cell_value == 0:
                    # 确定不是：白色背景 + 打×
                    fill_color = "white"
                else:
                    # 不确定：白色
                    fill_color = "white"
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill_color,
                    outline="gray"
                )
                
                # 如果是确定不填充的，画×
                if cell_value == 0:
                    # 判断×的颜色
                    cross_color = "red" if is_new_this_iteration else "gray"
                    # 画对角线×
                    self.canvas.create_line(
                        x1 + 5, y1 + 5, x2 - 5, y2 - 5,
                        fill=cross_color, width=2
                    )
                    self.canvas.create_line(
                        x2 - 5, y1 + 5, x1 + 5, y2 - 5,
                        fill=cross_color, width=2
                    )
        
        # 绘制 5x5 粗框(橙色，宽基4)
        for i in range(0, num_rows, 5):
            for j in range(0, num_cols, 5):
                # 每个 5x5 块的外框
                x1 = offset_x + j * self.cell_size
                y1 = offset_y + i * self.cell_size
                x2 = offset_x + min(j + 5, num_cols) * self.cell_size
                y2 = offset_y + min(i + 5, num_rows) * self.cell_size
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#ff9900",
                    width=4
                )
        
        # 更新画布大小
        width = offset_x + num_cols * self.cell_size + 10
        height = offset_y + num_rows * self.cell_size + 10
        self.canvas.config(width=width, height=height)


if __name__ == "__main__":
    root = tk.Tk()
    app = NonogramUI(root, col_hints=[], row_hints=[])
    root.mainloop()
