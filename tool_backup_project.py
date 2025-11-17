import os
import zipfile
import platform
import shutil
from datetime import datetime

def zip_zombiescript():
    # -------------------------- 1. 定义基础配置（按需求修改）--------------------------
    # 各系统的目标目录路径
    target_dirs = {
        "Darwin": "/Users/karmy/Projects/SuduPic",  # macOS（Darwin是macOS的系统名称）
        "Windows": "E:\\Projects\\SuduPic"          # Windows（注意双反斜杠转义）
    }
    # 压缩包命名格式：zs_月日_HHMMDD.zip（月日 → 月份日期，HHMMDD → 24小时制）
    zip_name = f"suduku_{datetime.now().strftime('%m%d_%H%M%S')}.zip"

    # -------------------------- 2. 自动识别系统，获取目标目录 --------------------------
    system = platform.system()
    if system not in target_dirs:
        print(f"❌ 不支持的系统：{system}（仅支持macOS和Windows）")
        return

    target_dir = target_dirs[system]
    # 检查目标目录是否存在
    if not os.path.exists(target_dir):
        print(f"❌ 目标目录不存在：{target_dir}")
        return

    # -------------------------- 3. 清理 Screenshot_Debug 目录 --------------------------
    debug_dir = os.path.join(target_dir, "Screenshot_Debug")
    if os.path.exists(debug_dir):
        print(f"🗑️  正在清理 Screenshot_Debug 目录...")
        try:
            # 删除目录下的所有文件
            for item in os.listdir(debug_dir):
                item_path = os.path.join(debug_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"  ✔️  已删除: {item}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"  ✔️  已删除目录: {item}")
            print(f"✅ Screenshot_Debug 目录清理完成\n")
        except Exception as e:
            print(f"⚠️  清理 Screenshot_Debug 目录失败: {e}")
    else:
        print(f"ℹ️  Screenshot_Debug 目录不存在，跳过清理\n")

    # -------------------------- 4. 确定压缩包保存路径（上一级目录）--------------------------
    # 获取目标目录的上一级目录（如 macOS 下 → /Users/karmy/Projects）
    parent_dir = os.path.dirname(target_dir)
    zip_save_path = os.path.join(parent_dir, zip_name)

    # 避免重复命名（如果当天已生成，添加序号）
    index = 1
    temp_zip_path = zip_save_path
    while os.path.exists(temp_zip_path):
        temp_zip_path = os.path.join(parent_dir, f"sudu_{datetime.now().strftime('%m%d_%H%M%S')}_{index}.zip")
        index += 1
    zip_save_path = temp_zip_path

    # -------------------------- 5. 开始压缩目录 --------------------------
    print(f"📁 开始压缩目录：{target_dir}")
    print(f"💾 压缩包将保存到：{zip_save_path}")

    # 统计文件数量（可选，用于进度提示）
    file_count = 0
    for root, dirs, files in os.walk(target_dir):
        file_count += len(files)
    print(f"🔍 共发现 {file_count} 个文件待压缩...")

    # 执行压缩（保留目录结构，不包含顶层目录本身）
    with zipfile.ZipFile(zip_save_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                # 构建文件的绝对路径
                file_path = os.path.join(root, file)
                # 构建压缩包内的相对路径（去掉 target_dir 的前缀，保留子目录结构）
                arcname = os.path.relpath(file_path, target_dir)
                # 添加文件到压缩包
                zipf.write(file_path, arcname)
                print(f"✅ 已添加：{arcname}")

    # -------------------------- 6. 压缩完成提示 --------------------------
    zip_size = os.path.getsize(zip_save_path) / (1024 * 1024)  # 转换为 MB
    print(f"\n🎉 压缩完成！")
    print(f"📦 压缩包名称：{os.path.basename(zip_save_path)}")
    print(f"📊 压缩包大小：{zip_size:.2f} MB")
    print(f"📍 保存路径：{zip_save_path}")

if __name__ == "__main__":
    try:
        zip_zombiescript()
    except Exception as e:
        print(f"\n❌ 压缩失败：{str(e)}")

