import json
import os
import re
from modules.logger import setup_logger
import pymupdf4llm
from dotenv import load_dotenv
from openai import OpenAI

script_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本所在目录
project_root = os.path.abspath(os.path.join(script_dir, ".."))  # 项目根目录
log = setup_logger("pdf_handler")

try:
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    log.info(f"初始化 OpenAI API 时出错：{e}")


def extract_relevant_pages(pdf_path, keyword="Abstract"):
    """
    提取包含关键词的页面以及前后一共四页的内容。
    :param pdf_path: PDF 文件路径
    :param keyword: 搜索的关键词
    :return: 提取的 Markdown 文本
    """
    try:
        pdf_path = re.sub(r'[\\/*?:"<>|&;]', '_', pdf_path)
        pdf_full_path = os.path.join(project_root, "pdf_storage", pdf_path)
        txt_full_path = pdf_path + ".txt"
        # 打开 PDF 文件
        abstract_page = None
        md_text = pymupdf4llm.to_markdown(pdf_full_path)

        # 以“-----”作为分隔符将该对象分割成多个页面
        pages = md_text.split("-----")
        for page in pages:
            if keyword in page:
                abstract_page = pages.index(page)
                start_page = max(0, abstract_page - 1)
                end_page = min(len(pages), abstract_page + 3)
                break

        if abstract_page is None:
            log.info(f"未找到关键词 '{keyword}' 的页面")
            return None

            # 提取页面文本并转为 Markdown
        page_text = ""
        for page_num in range(start_page, end_page):
            page = pages[page_num]
            page_text += f"# Page {page_num + 1}\n"
            page_text += page + "\n"
            result = gpt_handler(page_text)
            # 保存结果为 .txt 文件
        if result:
            save_result_as_txt(result, txt_full_path)
        return result

    except Exception as e:
        log.info(f"提取页面内容时出错：{e}")
        return None

def gpt_handler(text, model="gpt-4o-mini"):
    """
    调用 GPT API，发送输入数据并返回结果。
    :param text: 要发送的 Markdown 文本
    :param model: 使用的 GPT 模型
    :return: GPT API 的响应内容
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant specialized in processing academic papers in psychology and neuroscience. "
                        "Your task is to accurately extract structured information from the provided content without adding interpretations or modifications. "
                        "Focus on precision. When translating to Chinese, ensure the translation retains the original meaning accurately."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"The following is an excerpt from an academic paper:\n{text}\n\n"
                        "Please perform the following tasks:\n"
                        "1. Extract the 'Abstract' exactly as written in the original text.\n"
                        "2. Translate the abstract into Chinese.\n"
                        "3. Extract the 'Title' of the paper.\n"
                        "4. Extract the 'Authors'.\n"
                        "5. Extract the 'Keywords'.\n"
                        "Return the results in the following JSON format:\n"
                        "{\n"
                        "  'title': 'Original Title',\n"
                        "  'authors': ['Author 1', 'Author 2'],\n"
                        "  'abstract': 'Original Abstract',\n"
                        "  'translation': 'Chinese Translation',\n"
                        "  'keywords': ['Keyword 1', 'Keyword 2']\n"
                        "}"
                    )
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "academic_extraction",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "description": "The title of the academic paper",
                                "type": "string"
                            },
                            "authors": {
                                "description": "A list of authors of the paper",
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "abstract": {
                                "description": "The abstract text as it appears in the paper",
                                "type": "string"
                            },
                            "translation": {
                                "description": "The Chinese translation of the abstract",
                                "type": "string"
                            },
                            "keywords": {
                                "description": "Keywords extracted from the paper",
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["title", "authors", "abstract", "translation", "keywords"]
                    }
                }
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        log.info(f"调用 GPT API 时出错：{e}")
        return None

def save_result_as_txt(result, filename):
    """
    将 JSON 格式的结果规范化输出为易读的 .txt 文件。
    :param result: JSON 数据（字典格式）
    :param filename: 保存的文件名
    """
    try:
        # 确保结果是字典格式
        if isinstance(result, str):
            result = json.loads(result)  # 如果是字符串，先转换为字典

        # 确保保存文件夹存在
        save_folder = os.path.join(project_root, "pdf_storage")
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        txt_full_path = os.path.join(save_folder, filename.replace(".pdf.txt", "") + ".txt")

        with open(txt_full_path, "w", encoding="utf-8") as txt_file:
            txt_file.write("=== Extracted Information ===\n\n")
            txt_file.write(f"Title:\n{result['title']}\n\n")

            txt_file.write("Authors:\n")
            for author in result['authors']:
                txt_file.write(f"- {author}\n")
            txt_file.write("\n")

            txt_file.write("Abstract:\n")
            txt_file.write(f"{result['abstract']}\n\n")

            txt_file.write("Translation (Chinese):\n")
            txt_file.write(f"{result['translation']}\n\n")

            txt_file.write("Keywords:\n")
            for keyword in result['keywords']:
                txt_file.write(f"- {keyword}\n")
            txt_file.write("\n")

        log.info(f"结果已保存到 {txt_full_path}")
    except Exception as e:
        log.info(f"保存结果为 .txt 文件时出错：{e}")

if __name__ == '__main__':
    file_path = "Decision_Processes_in_Continuous-Outcome_Retrieval_from_Visual_Working_Memory.pdf"

    # 提取 Markdown 文本
    markdown_text = extract_relevant_pages(file_path)
    log.info(markdown_text)