import random
import re

import cfscrape
import requests
from colorama import Fore, Style
from lxml import etree
import os

import time

from buondua_download import download_image
from utils.common_utils import convert_page_index_to_num, convert_page_index_to_num_size, clean_windows_folder_name
from utils.mysqlite_util import DownloadFileDB

if __name__ == '__main__':
    start_index = 2 #初始值是1
    page_num = 20
    pic_start_index = 2  #初始值是0
    pic_start_page = 7   #初始值是1
    download_fail_list = []
    if not os.path.exists("../../file/buondua"):
        os.makedirs("../../file/buondua")
    a_name = os.path.abspath('../../file/buondua')
    print(f'总路径：{a_name}')
    db = DownloadFileDB()
    scraper = cfscrape.create_scraper()
    # scraper.verify = False
    custom_headers = {
        "Accept-Language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="144", "Chromium";v="144", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": '?0',
        "priority":"u=0, i",
        "referer":"https://buondua.com/",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "sec-fetch-dest":"document",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": '1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/143.0.0.1 Safari/537.37"
    }
    # https://buondua.com/tag/private-photoshoot-12486
    # https://buondua.com/tag/xr-uncensored-11790
    # https://buondua.com/tag/jvid-11832
    url = "https://buondua.com/tag/private-photoshoot-12486?start="
    base_url = "https://buondua.com"
    content_url = url + str((start_index-1)*20)
    print(content_url)
    # 1. 获取原始字节数据（不要先转text）
    page_text = requests.get(url=content_url, headers=custom_headers).text
    parser = etree.HTMLParser(encoding="utf-8")
    tree = etree.HTML(page_text, parser=parser)
    pic_detail_url_list = tree.xpath('//div[@class="item-content"]/div[@class="page-header"]/h2//a/@href')
    pic_detail_url_list = list(dict.fromkeys(pic_detail_url_list))
    # pic_detail_url_list = ['/jvid-li-fei-er-chao-ju-ru-nu-shen-li-fei-er-wen-quan-xing-ai-zhi-lu-chi-du-po-biao-quan-luo-bao-ma-tou-fu-yi-wu-ma-149-photos-33d6472d5414d1b170e36c3588aac747-52467', '/tag/jvid-11832', '/tag/黎菲儿-11964', '/jvid-jie-mi-juice-chao-wan-mei-jiao-qi-shen-qi-lao-po-lao-po-nai-yao-guai-cha-bu-lang-qian-wan-fu-tong-sheng-yi-zhi-zui-yu-ni-jiang-hui-dao-zuo-hui-dao-rang-ni-bu-zai-shi-mei-lu-yong-90-photos-1-video-633b67b962433fc787e9ed2039392aba-52427', '/tag/婕咪-juice-11904', '/jvid-jie-mi-juice-ri-zu-nu-you-you-le-qu-xue-mai-pen-zhangsex-ji-qing-chou-cha-zhong-chu-213-photos-2-videos-bcf0011719876e2150dc6f0f2d27c859-52426', '/jvid-yuan-yuan-zui-qiang-nao-sha-g-cup-yuan-yuan-mi-ren-ju-ru-sai-che-nu-lang-chi-du-da-kai-tiao-dou-ni-shang-chuang-117-photos-1-video-2b5a69a2d05150f685a4377d30d649ea-52399', '/tag/媛媛-12006', '/jvid-jie-mi-juice-bu-neng-fa-chu-sheng-yin-shuang-ma-wei-zai-ci-ni-lin-you-zai-xue-zhang-kua-xia-wan-qi-lai-82-photos-1-video-db0c35ce2663c0e8c4b3f38642a49748-52370', '/jvid-mu-mu-sen-mei-ju-ru-mu-mu-sen-yue-wo-kai-fang-jian-luo-yong-wan-zai-chuang-shang-deng-wo-tan-suo-ta-quan-shen-91-photos-2-videos-33c3968a0918a96a26d313f0eceaf248-52337', '/tag/木木森-12002', '/jvid-jennysuen-quan-luo-shang-kong-sr-deng-ji-tian-mei-de-xiao-jie-jiejenny-wu-hou-de-ju-ru-you-huo-76-photos-05f16c2640c12ab95572262ce25e3f7d-52339', '/tag/jennysuen-14586', '/jvid-rou-baomini-jin-wan-wo-shi-ni-de-bai-se-xiao-mao-wo-men-yi-qi-lai-wan-ba-76-photos-1-video-dae466bf8edcb6f24f49a42c05505487-52301', '/tag/肉包mini-11885', '/jvid-han-fang-yu-desirevol-ji-zheng-da-nai-da-xue-xin-xian-ren-fang-yu-xia-ban-hou-de-qing-se-zhi-dao-53-photos-1-video-0adb29a8a99e361a9a2d64e11cacb1e5-52272', '/tag/韓芳語-12324', '/jvid-li-xiang-wei-xing-tuan-de-shao-nu-lu-chu-xing-wei-ni-you-bian-tai-gen-zong-kuang-hui-jia-141-photos-1-video-daf33b816cab0eff806965a308f32db6-52269', '/tag/梨香-14570', '/jvid-jie-mi-juice-yi-ri-qu-jing-kuai-di-fu-wu-yuan-wo-de-shen-ti-jiu-shi-nin-de-cun-jing-rong-qi-shi-run-nen-xue-te-xie-86-photos-1-video-35f6b1b7fc4a00c856bfc7882ee43b38-52171', '/jvid-li-fei-er-diao-jiao-xing-gan-ju-ru-xiao-mu-gou-qian-yi-wan-qu-ye-dian-jiu-tou-dai-nan-ren-hui-jia-jiu-housm-bei-diao-jiao-cheng-xiao-mu-gou-se-yu-man-manno-xing-nu-yang-cheng-ji-hua-172-photos-1-video-3dcd5fb2a45914e3b0d680688f015b3a-52173', '/tag/黎菲兒-12130', '/jvid-li-fei-er-chao-ju-ru-fei-er-chuan-zhe-chao-xing-gan-fen-se-lian-shen-dong-dong-yong-zhuang-110-photos-1-video-4e47f6a561dbe6724a331cf235f76e8a-52104', '/jvid-tu-tu-ju-ru-niang-ekappu-ju-ru-niangbetty-tu-tu-you-huo-deng-chang-59-photos-1-video-e360396f035a2fe220cde0ac94c411eb-52106', '/tag/兔兔-10494', '/jvid-rou-baomini-san-dian-quan-lu-cuo-rou-huang-jin-bi-li-nen-xiong-yu-ni-de-ri-zu-jiao-qi-129-photos-9f303e64c8b06cbbf6c3b44e28acbd25-52064', '/jvid-agelia-an-ji-bao-ru-feng-su-niang-quan-shen-xin-de-shi-feng-ru-tui-quan-luo-hu-dong-quan-shen-xing-an-mo-wei-nin-fu-wu-body-massage-43-photos-2-videos-975ac04228ee0a0343208119e9838c94-52068', '/tag/agelia安吉-14531', '/jvid-li-fei-er-fei-er-zai-hua-cong-zhong-beng-chu-you-ren-ju-ru-dan-chu-hun-yuan-qiao-tun-ji-xian-bian-yuan-de-tiao-dou-149-photos-ec2424f4619fa9937e224aba21962f0b-52033', '/jvid-guo-bao-bao-he-ni-yi-qi-qu-lu-ying-yi-yan-bu-he-jiu-qi-fus-xiang-jiao-juns-shi-qi-zhi-xi-ft-vlog-ying-pian-158-photos-1-video-297c5d34ea49c4c89da2c1d7a7a62b06-52036', '/tag/果宝宝-11962', '/jvid-rou-baomini-tong-yan-ju-ru-de-xue-sheng-mei-rou-bao-fang-ke-hou-de-te-shu-da-gong-fu-wu-109-photos-07ef5a8d5b17494d6589d66a743cf328-51956', '/jvid-li-yan-li-yan-cai-zhuang-shi-de-jia-qi-li-yan-quan-luo-fang-song-shen-xin-ling-120-photos-dfbd682ae356d6db8440bfc465fd2d96-51954', '/tag/li-yan-9994']
    print(len(pic_detail_url_list))
    print(pic_detail_url_list)
    for detail_index, detail_param in enumerate(pic_detail_url_list):
        if detail_index < pic_start_index:
            continue
        print(f"{Fore.YELLOW}pic_start_index:{detail_index}总{len(pic_detail_url_list)}{Style.RESET_ALL}")
        detail_page_text = requests.get(url=base_url+detail_param, headers=custom_headers).text
        detail_tree = etree.HTML(detail_page_text, parser=parser)
        detail_info = detail_tree.xpath('//div[@class="article-header"]/h1/text()')[0]
        title = detail_info.split("-")[0]
        detail_title = clean_windows_folder_name(title)
        exact_result = db.get_by_title_custom(title=detail_title,table_name="buondua")
        print(f"精确匹配结果：{exact_result}")
        if exact_result:
            print(f"{Fore.YELLOW}目录{detail_title}已下载过了，跳过下载{Style.RESET_ALL}")
            continue  # 直接跳过当前条目的所有后续逻辑（包括下载、创建文件夹）
        save_file_path = os.path.join(a_name, detail_title)
        if not os.path.exists(save_file_path):
            os.makedirs(save_file_path)
            print(f"创建保存路径：{save_file_path}")
        pattern = r'\( Page \d+ / (\d+) \)'
        match = re.search(pattern, detail_info)
        if match:
            detail_total = int(match.group(1))
            print(f"{Fore.GREEN}{detail_title}  detail_total:共{detail_total}页{Style.RESET_ALL}")
            for page_index in range(pic_start_page, detail_total+1):
                if page_index == 1:
                    pic_url_list = detail_tree.xpath('//div[@class="article-fulltext"]//p//img/@src')
                    print(pic_url_list)
                    for index, img_url in enumerate(pic_url_list):
                        img_name = convert_page_index_to_num_size(f"{page_index}_{index}",20)
                        fileSize = download_image(img_url, save_file_path, img_name)
                        # time.sleep(random.uniform(2, 5))
                        if fileSize == "失败":
                            fileSize2 = download_image(img_url, save_file_path, img_name)
                            if fileSize2 == "失败":
                                my_map = {
                                    "url": img_url,
                                    "title": detail_title
                                }
                                download_fail_list.append(my_map)
                                print(f"download_fail_list：{download_fail_list}")
                        else:
                            print(f"第{index + 1}张图片{fileSize}下载完成")
                    print(f"{Fore.BLUE}第{detail_index}个的第{page_index}页{detail_title}下载完成共{detail_total}页{Style.RESET_ALL}")
                else:
                    time.sleep(random.uniform(5, 10))
                    print(f"{Fore.RED}第{page_index}页开始下载{Style.RESET_ALL}")
                    detail_page2_text = requests.get(url=base_url + detail_param + '?page='+str(page_index) , headers=custom_headers).text
                    detail_tree2 = etree.HTML(detail_page2_text, parser=parser)
                    pic_url_list = detail_tree2.xpath('//div[@class="article-fulltext"]//p//img/@src')
                    for index, img_url in enumerate(pic_url_list):
                        img_name = convert_page_index_to_num_size(f"{page_index}_{index}", 20)
                        fileSize = download_image(img_url, save_file_path, img_name)
                        if fileSize == "失败":
                            fileSize2 = download_image(img_url, save_file_path, str(index))
                            if fileSize2 == "失败":
                                my_map = {
                                    "url": img_url,
                                    "title": detail_title
                                }
                                download_fail_list.append(my_map)
                                print(f"download_fail_list：{download_fail_list}")
                        else:
                            print(f"第{index + 1}张图片{fileSize}下载完成")
                    print(f"{Fore.BLUE}第{detail_index}个的第{page_index}页{detail_title}下载完成共{detail_total}页{Style.RESET_ALL}")
            new_id = db.insert_custom(title=detail_title, table_name="buondua")
            print(f"新增记录成功，id：{new_id}")
            if pic_start_page == 1:
                time.sleep(random.uniform(5, 10))
            else:
                exit(0)
    print(download_fail_list)



