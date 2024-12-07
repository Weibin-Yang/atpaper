
from GoogleScholar import *
from Hippocampus import *
from Stork import *
from markdown_write import *
from TeleBot import *
from modules.logger import setup_logger
from DrissionPage import ChromiumOptions


if __name__ == '__main__':
    path = r'/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'
    ChromiumOptions().set_browser_path(path).save()
    logger = setup_logger("PaperBot")
    try:
        logger.info("开始执行 PaperBot")
        Google_email_client = EmailClientGoogleScholar()
        Google_email_client.connect()
        Google_emails = Google_email_client.fetch_Google_emails()
        logger.info("Google邮件处理完成。")
        Google_email_client.logout()

        Hippocampus_email_client = EmailClientHippocampus()
        Hippocampus_email_client.connect()
        Hippocampus_emails = Hippocampus_email_client.fetch_Hippocampus_emails()
        Hippocampus_email_client.logout()
        logger.info("Hippocampus邮件处理完成。")

        Stork_email_client = EmailClientStork()
        Stork_email_client.connect()
        Stork_emails = Stork_email_client.fetch_Stork_emails()
        extra_emails = Stork_email_client.check_errortxt()
        logger.info("Stork邮件处理完成。")

        if Google_emails != {} or extra_emails != [] or Stork_emails != {} or Hippocampus_emails != {}:
            bot = TelegramBot(BOT_TOKEN, CHAT_ID)
            OUTPUT_FOLDER = "output"  # 替换为实际路径
            bot.process_folder(OUTPUT_FOLDER)
            logger.info("Telegram 消息处理完成。")

            output_folder = "output"  # 替换为存储 txt 文件的相对路径
            markdown_folder = "/Users/weibin/Documents/Memory/PaperBot"  # Markdown 文件夹的绝对路径

            markdown_handler = MarkdownHandler(output_folder, markdown_folder)
            markdown_handler.process_all_txt_files()
            logger.info("Markdown 文件生成完成。")
        else:
            logger.info("没有新邮件，无需处理")

    except Exception as e:
        logger.info(f"PaperBot 执行时出错：{e}")
    finally:
        logger.info("PaperBot 执行结束。")

