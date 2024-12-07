import os
from datetime import datetime
from pathlib import Path
from modules.logger import setup_logger


class MarkdownHandler:
    def __init__(self, output_folder, markdown_folder):
        """
        初始化 MarkdownHandler
        :param output_folder: 存储 txt 文件的文件夹路径
        :param markdown_folder: 存储生成 markdown 文件的文件夹路径
        """
        self.output_folder = output_folder
        self.markdown_folder = markdown_folder
        self.logger = setup_logger("MarkdownHandler")

        # 确保 markdown 文件夹存在
        Path(self.markdown_folder).mkdir(parents=True, exist_ok=True)

    def process_txt_to_dict(self, txt_path):
        """
        将 txt 文件内容解析为字典
        :param txt_path: txt 文件路径
        :return: 字典
        """
        data_dict = {}
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if ":" in line:
                        key, value = map(str.strip, line.split(":", 1))  # 以冒号分割，最多分割一次
                        data_dict[key] = value
        except Exception as e:
            self.logger.info(f"解析 TXT 文件时出错：{e}")
        return data_dict

    def fill_markdown_template(self, data_dict, filename):
        """
        根据字典填充 markdown 模板
        :param data_dict: 包含内容的字典
        :return: 生成的 markdown 内容
        """
        template = """---
source: {Link}
title: {title}
authors: {Authors}
doi: {doi}
year: {year}
Journal: {Journal}
tags:
  - paperbot
---

Citation：
{citation}

# Abstract(cn)
{Abstract_cn}

# Abstract
{Abstract}
"""

        # 使用字典中的值填充模板，若键不存在则返回空字符串
        return template.format(
            Link=data_dict.get('DOI', '') if 'storkapp.me' in data_dict.get('Link', '') else data_dict.get('Link', ''),
            title=data_dict.get('title', '').replace(":", "").replace(r'[\\/*?:"<>|&;(){}[\]]', '_'),
            Authors=data_dict.get('Authors', '').replace(r'[\\/*?:"<>|&;(){}[\]]', '_'),
            Abstract=data_dict.get('Abstract', ''),
            Abstract_cn=data_dict.get('Abstract(cn)', ''),
            Journal=data_dict.get('Journal', '').replace(r':', ''),
            year=data_dict.get('Year', '').replace(r'[\\/*?:"<>|&;(){}[\]]', '_'),
            doi=data_dict.get('DOI', ''),
            citation=data_dict.get('APA Citation', '')
        )

    def save_markdown_file(self, markdown_content, filename):
        """
        保存 markdown 内容为 .md 文件
        :param markdown_content: 生成的 markdown 内容
        :param filename: 文件名（不包含扩展名）
        """
        markdown_path = os.path.join(self.markdown_folder, f"{filename}.md")
        try:
            with open(markdown_path, 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            self.logger.info(f"Markdown 文件已保存到：{markdown_path}")
        except Exception as e:
            self.logger.info(f"保存 Markdown 文件时出错：{e}")

    def process_all_txt_files(self):
        """
        遍历 output 文件夹中的所有 txt 文件，生成对应的 markdown 文件
        """
        if not os.path.exists(self.output_folder):
            self.logger.info(f"输出文件夹不存在：{self.output_folder}")
            return

        today = datetime.now().date()

        for filename in os.listdir(self.output_folder):
            if filename.endswith('.txt'):
                txt_path = os.path.join(self.output_folder, filename)

                file_modified_date = datetime.fromtimestamp(os.path.getmtime(txt_path)).date()
                if file_modified_date != today:  # 如果文件不是今天的，跳过
                    continue

                # 解析 txt 文件为字典
                data_dict = self.process_txt_to_dict(txt_path)

                # 填充 markdown 模板
                markdown_content = self.fill_markdown_template(data_dict,filename)

                # 保存 markdown 文件
                filename_without_ext = os.path.splitext(filename)[0]
                self.save_markdown_file(markdown_content, filename_without_ext)


if __name__ == "__main__":
    # 配置文件夹路径
    output_folder = "output"  # 替换为存储 txt 文件的相对路径
    markdown_folder = "/Users/weibin/Library/CloudStorage/OneDrive-UniversityofMissouri/Memory/PaperBot"  # Markdown 文件夹的绝对路径

    # 创建并运行 MarkdownHandler
    markdown_handler = MarkdownHandler(output_folder, markdown_folder)
    markdown_handler.process_all_txt_files()
