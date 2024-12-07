import imaplib
import email
import json
import re
from email.header import decode_header
import ssl
from modules.logger import setup_logger
import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from modules.url_handler import stork_url
from modules.url_handler import getabstract

class EmailClientStork:
    def __init__(self):
        self.server = 'imap.gmail.com'
        self.port = 993
        self.mail = None
        self.logger = setup_logger("EmailClientStork")


    def connect(self):
        try:
            # 从 .env 文件中加载邮箱账号和密码
            load_dotenv()
            EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
            EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

            # 检查账号和密码是否正确加载
            if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
                raise ValueError("邮箱账号或密码未正确加载，请检查 .env 文件。")

            # 使用 SSL 连接到邮箱
            context = ssl.create_default_context()
            self.mail = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=context)
            self.mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            self.logger.info("成功连接到邮箱！")
        except Exception as e:
            self.logger.info(f"邮箱连接失败：{e}")

    def fetch_Stork_emails(self, limit=None, date_range=None):
        """
        获取邮箱中的邮件。
        :param limit: 限制返回的邮件数量，默认为全部。
        :param date_range: 按日期筛选邮件（例如 '10d', '1m', '6m'）。
                          支持最近 N 天（'Nd'）、N 月（'Nm'）、N 年（'Ny'）。
        """
        try:
            self.mail.select("inbox")

            # 根据 date_range 计算筛选日期
            if date_range:
                unit = date_range[-1]  # 获取单位（d, m, y）
                value = int(date_range[:-1])  # 获取时间值
                if unit == 'd':  # 最近 N 天
                    since_date = datetime.now() - timedelta(days=value)
                elif unit == 'm':  # 最近 N 月
                    since_date = datetime.now() - timedelta(days=value * 30)
                elif unit == 'y':  # 最近 N 年
                    since_date = datetime.now() - timedelta(days=value * 365)
                else:
                    raise ValueError("无效的日期范围格式，应为 '10d', '1m' 或 '6m' 等。")

                since_date_str = since_date.strftime("%d-%b-%Y")  # IMAP 日期格式
                status, messages = self.mail.search(None,
                                                    f'(UNSEEN FROM "support@storkapp.me" SINCE "{since_date_str}")')
            else:
                # 如果没有指定日期范围，获取所有符合条件的邮件
                status, messages = self.mail.search(None, '(UNSEEN FROM "support@storkapp.me")')

            email_ids = messages[0].split()
            self.logger.info(f"找到 {len(email_ids)} 封符合条件的邮件。")

            # 如果设置了 limit，则只处理前 limit 封邮件
            if len(email_ids) > 0 and limit:
                if limit:
                    email_ids = email_ids[-limit:]

            # 遍历邮件并提取链接
            link_types = {}

            if len(email_ids) == 0:
                self.logger.info("目前没有新邮件")
                return {}

            for email_id in email_ids:
                status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        # 获取邮件主题
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        # 获取邮件日期
                        date = msg["Date"]
                        # 提取链接和标题
                        links_and_titles = self._extract_body_and_links(msg)
                        # 创建字典存储链接和其类型
                        for link, c in links_and_titles.items():
                            if any(domain in link for domain in
                                   ['book', 'search.proquest.com', 'www.rivisteweb.it', 'jov.arvojournals.org',
                                    'acoustics.org', 'www.researchgate.net']):
                                continue
                            self.logger.info("正在处理链接：")
                            self.logger.info(link)
                            if c['title']:
                                self.logger.info(c['title'])
                                title = c['title']
                            if c['stork_flag']:
                                results = stork_url(link)
                                if isinstance(results, str):
                                    try:
                                        results = json.loads(results)
                                    except json.JSONDecodeError as e:
                                        self.logger.info(f"Error decoding JSON: {e}")
                                        results = {}
                                if isinstance(results, dict):
                                    self.logger.info(results.get('title', 'Unknown'))
                                    link_types[link] = {
                                        "type": ' HTML',
                                        "title": results.get('title', 'Unknown'),
                                        "file_path": "None",
                                        "Authors": ", ".join(results.get('authors', [])) if isinstance(results.get('authors'), list) else 'Unknown',
                                        "Abstract(cn)": results.get('translation', 'Unknown'),
                                        "Abstract": results.get('abstract', 'Unknown'),
                                        "Keywords": ", ".join(results.get('keywords', [])) if isinstance(results.get('authors'), list) else 'Unknown',
                                        "Journal": results.get('journal', None),
                                        "Year": results.get('year', None),
                                        "Volume": results.get('volume', None),
                                        "Issue": results.get('issue', None),
                                        "pages": results.get('pages', None),
                                        "DOI": results.get('doi', None),
                                        "APA Citation": results.get('apa_citation', None)
                                    }
                                else:
                                    self.logger.info(f"Error: Expected a dictionary but got {type(results)}")
                                    self.logger.info(f"Error: {results}")
                            else:
                                results = getabstract(link)
                                if isinstance(results, str):
                                    try:
                                        results = json.loads(results)
                                    except json.JSONDecodeError as e:
                                        self.logger.info(f"Error decoding JSON: {e}")
                                        results = {}
                                if isinstance(results, dict):
                                    link_types[link] = {
                                        "type": 'HTML',
                                        "title": title,
                                        "file_path": 'None',
                                        "Authors": results.get('authors', None),
                                        "Abstract(cn)": results.get('translation', None),
                                        "Abstract": results.get('abstract', None),
                                        "Keywords": results.get('keywords', None),
                                        "Journal": results.get('journal', None),
                                        "Year": results.get('year', None),
                                        "Volume": results.get('volume', None),
                                        "Issue": results.get('issue', None),
                                        "pages": results.get('pages', None),
                                        "DOI": results.get('doi', None),
                                        "APA Citation": results.get('apa_citation', None)
                                    }
                                else:
                                    self.logger.info(f"Error: Expected a dictionary but got {type(results)}")
                                    self.logger.info(f"Error: {results}")
                # 标记邮件为已读
                self.mail.store(email_id, '+FLAGS', '\\Seen')
            self.save_link_types_to_file(link_types)

            return link_types

        except Exception as e:
            self.logger.info(f"获取邮件时出错：{e}，出错位置：{e.__traceback__.tb_lineno}")
            return {}

    def _extract_body_and_links(self, msg):
        """
        提取邮件正文内容并提取 scholar.google.com 的链接中特定的 URL。
        :param msg: MIME 邮件对象
        :return: 包含正文和提取到的链接的字典
        """

        links_and_titles = {}

        try:
            if msg.is_multipart():
                # 如果是 multipart，遍历每个部分
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # 取 text/plain 部分作为正文
                    if content_type == "text/html" and "attachment" not in content_disposition:
                        html_content = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")

                        # 使用 BeautifulSoup 解析 HTML 并提取正文
                        soup = BeautifulSoup(html_content, "html.parser")
                        # 提取链接和标题
                        for div_tag in soup.find_all('div', id=True):
                            a_tag = div_tag.find('a', href=True, target=True)
                            if a_tag and a_tag['href'].startswith('https://www.storkapp.me'):
                                href = a_tag['href']
                                match1 = re.search(r'url=\[pubmed[^\]]+\](https?://[^?\s&]+)', href)
                                match2 = re.search(r'url=(https?://[^\s]+)', href)
                                if match1:
                                    extracted_link = match1.group(1)
                                    title = a_tag.get_text()
                                    if '/pdf/' in extracted_link:
                                        extracted_link = extracted_link.replace('/pdf/', '/full/', 1)
                                    links_and_titles[extracted_link] = {
                                                "title": title,
                                                "stork_flag": False
                                            }
                                if match2:
                                    extracted_link = match2.group(1)
                                    links_and_titles[extracted_link] = {
                                        "title":False,
                                        "stork_flag": True
                                    }


            else:
                # 如果不是 multipart，直接提取正文
                content_type = msg.get_content_type()
                if content_type == "text/html":
                    html_content = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8")

                    soup = BeautifulSoup(html_content, "html.parser")
                    for div_tag in soup.find_all('div', id=True):
                        a_tag = div_tag.find('a', href=True)
                        if a_tag and a_tag['href'].startswith('https://www.storkapp.me'):
                            href = a_tag['href']
                            match1 = re.search(r'url=\[pubmed[^\]]+\](https?://[^?\s&]+)', href)
                            match2 = re.search(r'url=(https?://[^\s]+)', href)
                            if match1:
                                extracted_link = match1.group(1)
                                title = a_tag.get_text()
                                if '/pdf/' in extracted_link:
                                    extracted_link = extracted_link.replace('/pdf/', '/full/', 1)
                                links_and_titles[extracted_link] = {
                                    "title": title,
                                    "stork_flag": False
                                }
                            if match2:
                                extracted_link = match2.group(1)
                                links_and_titles[extracted_link] = {
                                    "title":False,
                                    "stork_flag": True
                                }

        except Exception as e:
            self.logger.info(f"解析邮件正文时出错：{e}")

        return links_and_titles

    def save_link_types_to_file(self, link_types, save_folder="output"):
        """
        将 link_types 中的每个链接对应的字典保存为单独的 txt 文件。
        :param link_types: 链接类型字典
        :param save_folder: 保存文件的文件夹
        """
        try:
            # 确保保存文件夹存在
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)

            for link, details in link_types.items():
                # 使用字典中的 title 作为文件名
                title = details.get("title", "unknown_title")
                title = re.sub(r'[\\/*?:"<>|&;]', '_', title)
                filename = f"{title}.txt"
                file_path = os.path.join(save_folder, filename)

                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"Link: {link}\n")
                    for key, value in details.items():
                        file.write(f"{key}: {value}\n")
                    file.write("\n")
            self.logger.info(f"Link types 已保存到文件夹：{save_folder}")
        except Exception as e:
            self.logger.info(f"保存 link types 文件时出错：{e}")

    def download_pdf(self, link, filename, save_folder="pdf_storage"):
        """
        下载 PDF 文件并保存到本地。
        :param link: PDF 文件链接
        :param filename: 保存的文件名
        :param save_folder: 保存文件的文件夹
        :return: 保存的文件路径
        """
        try:
            # 确保保存文件夹存在
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)

            # 构建完整路径
            filename = re.sub(r'[\\/*?:"<>|&;]', '_', filename)
            file_path = os.path.join(save_folder, filename)

            # 如果文件已存在，跳过下载
            if os.path.exists(file_path):
                self.logger.info(f"文件已存在，跳过下载：{file_path}")
                return None

            # 下载 PDF 文件
            response = requests.get(link, timeout=10, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.logger.info(f"PDF 文件已下载并保存到：{file_path}")
                return file_path
            else:
                self.logger.info(f"下载失败，状态码：{response.status_code}")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{link}\n")
                return None
        except Exception as e:
            self.logger.info(f"下载 PDF 时出错：{link} -> {e}")
            # 将出错链接保存到本地 txt 文件
            with open("error_links.txt", "a", encoding="utf-8") as error_file:
                error_file.write(f"{link}\n")
            return None

    def logout(self):
        # 退出登录
        if self.mail:
            try:
                self.mail.logout()
                self.logger.info("成功断开邮箱连接。")
            except Exception as e:
                self.logger.info(f"断开连接时出错：{e}")

    def check_errortxt(self):
        error_file = os.path.join(os.getcwd(), 'error_links.txt')

        if not os.path.exists(error_file):
            self.logger.info(f"文件不存在:{error_file}")
            return

        links = []
        with open(error_file, 'r', encoding="utf-8") as file:
            links = list(set(line.strip() for line in file if line.strip()))  # 去掉空行并去重

        if len(links) == 0:
            self.logger.info("没有错误链接")
            return []
        else:
            self.logger.info(f"找到 {len(links)} 个错误链接")
            return self.link_process(links, error_file=True)

    def link_process(self, links=None, error_file=None):
        if isinstance(links,list):
            pass
        else:
            raise TypeError(f"Expected a list but got {type(links)}")

        link_types = {}

        for link in links:
            if 'books.google.com' in link or 'search.proquest.com' in link or 'www.rivisteweb.it' in link or '.pdf' in link:
                continue
            self.logger.info("正在处理链接：")
            self.logger.info(link)

            if '/pdf/' in link:
                link = link.replace('/pdf/', '/full/', 1)

            results = getabstract(link)
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except json.JSONDecodeError as e:
                    self.logger.info(f"Error decoding JSON: {e}")
                    results = {}
            if isinstance(results, dict):
                link_types[link] = {
                    "type": 'HTML',
                    "title": results.get('title', None),
                    "file_path": 'None',
                    "Authors": results.get('authors', None),
                    "Abstract(cn)": results.get('translation', None),
                    "Abstract": results.get('abstract', None),
                    "Keywords": results.get('keywords', None),
                    "Journal": results.get('journal', None),
                    "Year": results.get('year', None),
                    "Volume": results.get('volume', None),
                    "Issue": results.get('issue', None),
                    "pages": results.get('pages', None),
                    "DOI": results.get('doi', None),
                    "APA Citation": results.get('apa_citation', None)
                }
                original_link = link.replace('/full/', '/pdf/', 1)
                links.remove(original_link)
            else:
                self.logger.info(f"Error: Expected a dictionary but got {type(results)}")
                self.logger.info(f"Error: {results}")

        self.save_link_types_to_file(link_types)

        if error_file:
            error_file = os.path.join(os.getcwd(), 'error_links.txt')
            with open(error_file, 'w', encoding='utf-8') as file:
                for remaining_link in links:
                    file.write(f"{remaining_link}\n")

        return link_types


if __name__ == "__main__":
    # 创建 EmailClient 实例并测试
    email_client = EmailClientStork()

    # 连接邮箱
    email_client.connect()

    # 获取文章
    emails = email_client.fetch_Stork_emails()

    extra_emails = email_client.check_errortxt()

    # 退出登录
    email_client.logout()
