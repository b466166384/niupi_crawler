def save_list_to_txt(lst, file_path):
    try:
        path = r"/"
        path_a = path+'\\'+file_path
        with open(path_a, 'a', encoding='utf-8') as file:
            for item in lst:
                if file_path == "24fa爬美图.txt":
                    item = "https://www.24fa.com/" + item
                file.write(item + '\n')
        print("数据已成功保存到文件。")
    except Exception as e:
        print(f"保存文件时出现错误: {e}")








# # 示例列表
# my_list = ["apple", "banana", "cherry"]
# # 示例文件路径
# file_path = "example.txt"
#
# save_list_to_txt(my_list, file_path)