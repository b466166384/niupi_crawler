# 文件夹工具类
import os
import re

from utils.mysqlite_util import DownloadFileDB


def get_all_subfolders(folder_path):
    """
    获取指定文件夹内所有子文件夹的名称

    参数:
        folder_path: 目标文件夹路径

    返回:
        包含所有子文件夹名称的列表，如果路径无效则返回空列表
    """
    # 检查路径是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 路径 '{folder_path}' 不存在")
        return []

    # 检查路径是否为文件夹
    if not os.path.isdir(folder_path):
        print(f"错误: '{folder_path}' 不是一个文件夹")
        return []

    subfolders = []
    try:
        # 遍历文件夹内容
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            # 判断是否为文件夹
            if os.path.isdir(item_path):
                subfolders.append(item)
    except PermissionError:
        print(f"错误: 没有访问 '{folder_path}' 的权限")
        return []
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return []

    return subfolders


if __name__ == "__main__":
    # 让用户输入目标文件夹路径
    target_folder = 'D:\\code\\py_place\\BeautyFetcher-master\\美女图集'
    db = DownloadFileDB()
    # 获取所有子文件夹名称
    folders = get_all_subfolders(target_folder)
    pattern = r'\b\d{4}\b'
    yearInt = 0
    if folders:
        print(f"\n'{target_folder}' 中的所有子文件夹:")
        for i, folder in enumerate(folders, 1):
            print(f"{i}. {folder}")
            # 查找匹配的年份
            match = re.search(pattern, folder)
            if match:
                year = match.group()  # 获取匹配到的年份字符串
                yearInt = int(year)
            db.insert(title=folder, year=yearInt)
        print(f"\n共找到 {len(folders)} 个子文件夹")
    else:
        print("\n未找到任何子文件夹或发生错误")