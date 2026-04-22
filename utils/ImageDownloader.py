import os
import requests
import urllib3
from colorama import Fore, Style
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def download_image(img_url, save_dir,HEADERS):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    session = create_session()

    try:
        response = session.get(
            url=img_url,
            headers=HEADERS,
            timeout=(30, 60),
            verify=False
        )

        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return "失败"

        # content_type = response.headers.get('Content-Type', '')
        # if content_type and not content_type.startswith('image/'):
        #     print(f"返回内容不是图片，类型: {content_type}")
        #     return "失败"

        img_name = os.path.basename(img_url)
        save_path = os.path.join(save_dir, img_name)

        with open(save_path, 'wb') as f:
            f.write(response.content)
        fileSize = f"{len(response.content) / 1024:.2f}KB"
        return fileSize

    except requests.exceptions.SSLError as e:
        print(f"{Fore.YELLOW}SSL错误，重试中: {str(e)[:50]}{Style.RESET_ALL}")
        import time
        time.sleep(2)
        try:
            response = session.get(
                url=img_url,
                headers=HEADERS,
                timeout=(30, 60),
                verify=False
            )
            if response.status_code == 200:
                img_name = os.path.basename(img_url)
                save_path = os.path.join(save_dir, img_name)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                fileSize = f"{len(response.content) / 1024:.2f}KB"
                return fileSize
        except:
            pass
        print(f"{Fore.RED}下载失败: SSL错误{Style.RESET_ALL}")
        return "失败"
    except Exception as e:
        print(f"{Fore.RED}下载失败: {str(e)[:80]}{Style.RESET_ALL}")
        return "失败"
