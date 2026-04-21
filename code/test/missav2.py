import urllib3
import json
import cfscrape
# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from colorama import Fore, Style
from lxml import etree
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
from urllib.parse import unquote
from selenium import webdriver
# from playwright_stealth import Stealth





if __name__ == '__main__':
    # args = sys.argv[1:]
    # if len(args) >= 1:
    #     missav_url = args[0]
    missav_url = "https://missav123.com/cn/search/IPZZ-020"
    # scraper.verify = False
    custom_headers = {
        "Accept-Language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="144", "Chromium";v="144", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": '?0',
        "priority":"u=0, i",
        "referer":"https://missav123.com/",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "sec-fetch-dest":"document",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": '1',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/143.0.0.1 Safari/537.37"
    }
    # 使用Playwright访问页面
    with sync_playwright() as p:
        try:
            proxy_server = "http://127.0.0.1:7890"
            # 启动浏览器（无头模式，可改为False调试）
            browser = p.chromium.launch(
                headless=True,
                # 添加更多浏览器参数，模拟真实环境
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-gpu",
                    "--disable-plugins",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
                ]
            )

            # 创建带代理的上下文（Context）
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                http_credentials=None,
                proxy={
                    "server": proxy_server,
                    # 如果代理需要认证，取消注释下面两行：
                    # "username": "your_username",
                    # "password": "your_password"
                }
            )

            # 创建页面并设置更真实的浏览器环境
            page = context.new_page()
            # stealth = Stealth()
            # stealth.apply_to_page(page)
            # 添加更真实的浏览器行为
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Google Chrome";v="141", "Chromium";v="141", "Not A(Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })

            # 1. 先访问页面域名（确保localStorage作用域正确）
            page.goto(missav_url, timeout=240000)  # 等待网络空闲
            # 检查是否还有Cloudflare挑战
            current_content = page.content()
            page_content = page.content()
            parser = etree.HTMLParser(encoding="utf-8")
            tree = etree.HTML(page_content, parser=parser)
            pic_detail_url_list = tree.xpath('//a[@class="text-secondary group-hover:text-primary"]/@href')
            if pic_detail_url_list:
                detail_url = pic_detail_url_list[0]
                if not detail_url.startswith('http'):
                    detail_url = 'https://missav123.com' + detail_url

                print(f"尝试访问详情页: {detail_url}")

                # 使用同一个 page 实例（不要新建），避免 localStorage/cookie 上下文丢失
                max_detail_retries = 3
                detail_success = False

                for detail_attempt in range(max_detail_retries):
                    try:
                        print(f"第 {detail_attempt + 1} 次尝试访问详情页...")

                        # 导航到详情页，等待网络空闲（比 domcontentloaded 更可靠）
                        page.goto(detail_url, timeout=180000, wait_until='load')

                        # 模拟人类行为：等待 + 滚动 + 鼠标移动
                        page.wait_for_timeout(3000)  # 初始等待

                        # 检查是否还在 Cloudflare 挑战页
                        title = page.title()
                        content = page.content()
                        print(f"内容片段: {content[:200]}...")  # 打印前 200 个字符

                        if "Just a moment" in title or "challenge-platform" in content or "Checking your browser" in content:
                            print("检测到 Cloudflare 挑战，等待自动完成...")
                            
                            # 等待最多 15 秒，看是否自动跳转
                            for _ in range(15):
                                page.wait_for_timeout(1000)
                                new_title = page.title()
                                new_content = page.content()
                                if "Just a moment" not in new_title and "challenge-platform" not in new_content:
                                    print("Cloudflare 挑战已通过！")
                                    detail_success = True
                                    break
                            else:
                                print("等待超时，仍未通过 Cloudflare 挑战")
                                if detail_attempt < max_detail_retries - 1:
                                    print("刷新页面重试...")
                                    page.reload(wait_until='networkidle')
                                    continue
                                else:
                                    raise Exception("所有重试均未能绕过 Cloudflare")
                        else:
                            print("直接加载成功，无 Cloudflare 拦截")
                            detail_success = True

                        if detail_success:
                            break

                    except Exception as e:
                        print(f"访问详情页失败: {e}")
                        if detail_attempt < max_detail_retries - 1:
                            page.wait_for_timeout(3000)
                            page.reload(wait_until='networkidle')
                        else:
                            raise

                # 成功后解析内容
                final_content = page.content()
                parser = etree.HTMLParser(encoding="utf-8")
                detail_tree = etree.HTML(final_content, parser=parser)

                title_elems = detail_tree.xpath('//h1[@class="text-base lg:text-lg text-nord6"]/text()') or detail_tree.xpath('//h1/text()')
                date_elems = detail_tree.xpath('//div[@class="space-y-2"]//time/text()')

                data = {
                    "title": title_elems[0].strip() if title_elems else "",
                    "date": date_elems[0].strip() if date_elems else ""
                }
                print(json.dumps(data, ensure_ascii=False))                                 
            # except Exception as e:
            #     print(f"cfscrape访问失败: {str(e)}")
        except Exception as e:
            print(f"操作失败：{str(e)}")
        finally:
            # 确保浏览器关闭
            if 'browser' in locals():
                browser.close()
            # 关闭数据库连接（如果需要）
            # db.close()






















