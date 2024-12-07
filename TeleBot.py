import os
import time
from datetime import datetime
from modules.logger import setup_logger
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # 替换为您的 Token
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # 替换为您的 Chat ID

class TelegramBot:
    """
    一个用于发送 Telegram 消息的类，包含文件夹内容读取和消息发送功能。
    """

    def __init__(self, bot_token, chat_id):
        """
        初始化 TelegramBot 实例。
        :param bot_token: Telegram Bot 的 Token
        :param chat_id: 目标 Chat 的 Chat ID
        """

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = setup_logger("TelegramBot")

    def send_message(self, message):
        """
        发送消息到 Telegram Bot
        :param message: 要发送的消息
        """
        try:

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"  # 支持 HTML 格式化
            }
            response = requests.post(url, json=payload)
            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 1)
                self.logger.info(f"速率限制，等待 {retry_after} 秒后重试")
                time.sleep(retry_after + 1)
            elif response.status_code == 200:
                self.logger.info("消息发送成功")
            else:
                self.logger.info(f"消息发送失败，状态码：{response.status_code}，原因：{response.text}")

        except Exception as e:
            self.logger.info(f"发送消息时出错：{e}")

    def process_folder(self, folder_path):
        """
        读取指定文件夹中的所有 .txt 文件并发送内容到 Telegram。
        :param folder_path: 文件夹路径
        """
        try:
            if not os.path.exists(folder_path):
                self.logger.info(f"文件夹不存在：{folder_path}")
                return

            today = datetime.now().date()

            # 遍历文件夹中的所有 .txt 文件
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):  # 只处理 .txt 文件
                    file_path = os.path.join(folder_path, filename)

                    # 检查文件的最后修改日期
                    file_modified_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()
                    if file_modified_date != today:  # 如果文件不是今天的，跳过
                        continue

                    # 读取文件内容
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        self.logger.info(f"读取文件：{filename}")

                    # 发送内容到 Telegram
                    self.send_message(content)

        except Exception as e:
            self.logger.info(f"处理文件夹时出错：{e}")


if __name__ == "__main__":
    # 初始化 TelegramBot 类
    bot = TelegramBot(BOT_TOKEN, CHAT_ID)

    # 设置 output 文件夹路径
    OUTPUT_FOLDER = "output"  # 替换为实际路径
    bot.process_folder(OUTPUT_FOLDER)