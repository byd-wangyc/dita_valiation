"""
DITA文件转JSON处理脚本
输入：DITA文件夹路径
输出：JSON文件夹和一个Excel文件（excel1.xlsx）

使用方法：
python dita2json.py <dita_folder_path> <json_output_folder> <excel_output_path>

参数说明：
- dita_folder_path: 输入的DITA文件夹路径
- json_output_folder: 输出的JSON文件夹路径
- excel_output_path: 输出的Excel文件路径
"""

import sys
import os
from pathlib import Path

# TODO: 在这里实现你的dita2json.py逻辑
# 以下是示例框架，请根据你的实际需求进行修改

def process_dita_folder(dita_folder_path, json_output_folder, excel_output_path):
    """
    处理DITA文件夹，转换为JSON并生成Excel
    
    支持的文件夹结构：
    - 根目录下有.dita文件（如DTA1000.dita, DTA2000.dita）
    - out/子目录下有infotree.xml文件
    
    Args:
        dita_folder_path: DITA文件夹路径（根目录，包含.dita文件）
        json_output_folder: JSON输出文件夹路径
        excel_output_path: Excel输出文件路径
    """
    dita_folder = Path(dita_folder_path)
    json_folder = Path(json_output_folder)
    excel_path = Path(excel_output_path)
    
    # 确保输出目录存在
    json_folder.mkdir(parents=True, exist_ok=True)
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 查找infotree.xml文件（可能在根目录或out/子目录）
    infotree_file = None
    if (dita_folder / "out" / "infotree.xml").exists():
        infotree_file = dita_folder / "out" / "infotree.xml"
        print(f"找到infotree.xml文件: {infotree_file}")
    elif (dita_folder / "infotree.xml").exists():
        infotree_file = dita_folder / "infotree.xml"
        print(f"找到infotree.xml文件: {infotree_file}")
    else:
        print("警告: 未找到infotree.xml文件")
    
    # 读取根目录下的所有.dita文件（忽略空文件夹）
    dita_files = []
    for dita_file in dita_folder.glob("*.dita"):
        if dita_file.is_file():
            dita_files.append(dita_file)
    
    print(f"处理DITA文件夹: {dita_folder}")
    print(f"找到 {len(dita_files)} 个DITA文件")
    print(f"JSON输出文件夹: {json_folder}")
    print(f"Excel输出文件: {excel_path}")
    
    if len(dita_files) == 0:
        print("错误: 未找到任何.dita文件")
        return
    
    # TODO: 实现你的处理逻辑
    # 1. 读取DITA文件夹中的.dita文件（在根目录）
    # 2. 读取infotree.xml文件（在根目录或out/子目录）
    # 3. 解析DITA文件
    # 4. 转换为JSON格式并保存到json_folder
    # 5. 生成Excel文件并保存到excel_path
    
    # 示例代码框架：
    # if infotree_file:
    #     # 读取infotree.xml
    #     with open(infotree_file, 'r', encoding='utf-8') as f:
    #         infotree_content = f.read()
    #         # 解析infotree.xml
    #         pass
    
    # for dita_file in dita_files:
    #     # 读取并解析DITA文件
    #     with open(dita_file, 'r', encoding='utf-8') as f:
    #         dita_content = f.read()
    #         # 解析DITA文件
    #         # 转换为JSON
    #         # 保存JSON文件到json_folder
    #         pass
    
    # 生成Excel文件
    # 这里需要你实现Excel生成逻辑
    # 例如使用pandas或openpyxl库
    
    print("处理完成！")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("错误: 参数数量不正确")
        print("使用方法: python dita2json.py <dita_folder_path> <json_output_folder> <excel_output_path>")
        sys.exit(1)
    
    dita_folder_path = sys.argv[1]
    json_output_folder = sys.argv[2]
    excel_output_path = sys.argv[3]
    
    if not os.path.exists(dita_folder_path):
        print(f"错误: DITA文件夹不存在: {dita_folder_path}")
        sys.exit(1)
    
    try:
        process_dita_folder(dita_folder_path, json_output_folder, excel_output_path)
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

