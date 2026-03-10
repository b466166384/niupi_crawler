import re


def convert_page_index_to_num(s: str) -> int:
    """
    将"page_index"格式的字符串转换为连续数字
    :param s: 输入字符串（如"1_0"、"2_0"）
    :return: 转换后的数字
    """
    # 分割页号和索引
    page_str, index_str = s.split("_")
    # 转为整数
    page = int(page_str)
    index = int(index_str)
    # 核心公式：(页号-1)*10 + 索引
    return (page - 1) * 10 + index

def convert_page_index_to_num_size(s: str,size) -> int:
    """
    将"page_index"格式的字符串转换为连续数字
    :param s: 输入字符串（如"1_0"、"2_0"）
    :return: 转换后的数字
    """
    # 分割页号和索引
    page_str, index_str = s.split("_")
    # 转为整数
    page = int(page_str)
    index = int(index_str)
    # 核心公式：(页号-1)*10 + 索引
    return (page - 1) * size + index


def clean_windows_folder_name(name):
    """
    清除字符串中不符合Windows文件夹命名规则的字符
    :param name: 原始文件夹名称
    :return: 合规的文件夹名称
    """
    if not isinstance(name, str):
        raise TypeError("输入必须是字符串类型")

    # 1. 定义Windows文件夹禁止的字符：< > : " / \ | ? * 以及 ASCII 0-31 控制字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    # 替换所有非法字符为下划线（可根据需求改为空字符串）
    clean_name = re.sub(illegal_chars, '_', name)

    # 2. 移除首尾的空格和句点（Windows不允许文件夹名以空格/句点结尾）
    clean_name = clean_name.strip().rstrip('.')

    # 3. 处理空名称（如果过滤后为空，默认命名为"New Folder"）
    if not clean_name:
        clean_name = "New Folder"

    # 4. 处理过长名称（Windows文件夹名最长255个字符）
    max_length = 255
    if len(clean_name) > max_length:
        clean_name = clean_name[:max_length].rstrip('.').strip()
        # 再次检查是否为空（截断后可能只剩空格/句点）
        if not clean_name:
            clean_name = "New Folder"

    return clean_name
