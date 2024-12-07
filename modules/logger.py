import logging
import os
from datetime import datetime


class PrintHandler(logging.Handler):
    """
    自定义处理器，当 enable_logging 为 False 时，将日志信息直接打印到控制台。
    """
    def emit(self, record):
        log_entry = self.format(record)
        print(log_entry)

def setup_logger(name, log_folder="logs", enable_logging=True):
    """
    设置日志记录器
    :param name: 日志记录器的名称
    :param log_folder: 日志文件存放的文件夹
    :return: 配置完成的日志记录器
    """
    # 确保日志文件夹存在
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    log_folder = os.path.join(project_root, log_folder)
    os.makedirs(log_folder, exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 如果不启用日志输出，添加 NullHandler
    if not enable_logging:
        print_handler = PrintHandler()
        print_handler.setFormatter(formatter)
        logger.addHandler(print_handler)
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    log_file = os.path.join(log_folder, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger