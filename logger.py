"""
统一日志系统 - Unified Logging System
提供统一的日志记录接口，支持控制台和文件输出

功能:
1. 彩色控制台输出
2. 文件日志记录
3. 统一的日志格式
4. 支持emoji图标
"""

import logging
import os
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


# ANSI颜色代码
class Colors:
    """ANSI颜色代码"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED,
    }
    
    def format(self, record):
        # 添加颜色
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        
        # 格式化消息
        message = super().format(record)
        
        # 返回彩色消息
        return f"{color}{message}{Colors.RESET}"


class PlainFormatter(logging.Formatter):
    """纯文本日志格式化器（用于文件）"""
    pass


class AITrackerLogger:
    """AI Tracker 统一日志管理器"""
    
    _instance: Optional['AITrackerLogger'] = None
    _loggers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._log_dir = 'logs'
        self._log_level = logging.INFO
        self._console_enabled = True
        self._file_enabled = True
        
        # 确保日志目录存在
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
    
    def configure(self, 
                  log_level: str = 'INFO',
                  log_dir: str = 'logs',
                  console_enabled: bool = True,
                  file_enabled: bool = True) -> None:
        """
        配置日志系统
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录
            console_enabled: 是否启用控制台输出
            file_enabled: 是否启用文件输出
        """
        self._log_level = getattr(logging, log_level.upper(), logging.INFO)
        self._log_dir = log_dir
        self._console_enabled = console_enabled
        self._file_enabled = file_enabled
        
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
        
        # 更新已存在的日志器
        for logger in self._loggers.values():
            logger.setLevel(self._log_level)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称（通常是模块名）
            
        Returns:
            配置好的日志器
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(f"ai_tracker.{name}")
        logger.setLevel(self._log_level)
        logger.propagate = False  # 防止重复输出
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 添加控制台处理器
        if self._console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self._log_level)
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if self._file_enabled:
            log_file = os.path.join(
                self._log_dir, 
                f"ai_tracker_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(self._log_level)
            file_formatter = PlainFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        self._loggers[name] = logger
        return logger


# 全局日志管理器实例
_logger_manager = AITrackerLogger()


def configure_logging(log_level: str = 'INFO',
                      log_dir: str = 'logs',
                      console_enabled: bool = True,
                      file_enabled: bool = True) -> None:
    """
    配置全局日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
        console_enabled: 是否启用控制台输出
        file_enabled: 是否启用文件输出
    """
    _logger_manager.configure(log_level, log_dir, console_enabled, file_enabled)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 模块名称
        
    Returns:
        日志器实例
    """
    return _logger_manager.get_logger(name)


# 便捷日志函数（带emoji支持）
class LogHelper:
    """日志辅助类，提供带emoji的便捷方法"""
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def info(self, message: str, emoji: str = "ℹ️") -> None:
        """输出信息日志"""
        self._logger.info(f"{emoji} {message}")
    
    def success(self, message: str) -> None:
        """输出成功日志"""
        self._logger.info(f"✅ {message}")
    
    def warning(self, message: str) -> None:
        """输出警告日志"""
        self._logger.warning(f"⚠️ {message}")
    
    def error(self, message: str) -> None:
        """输出错误日志"""
        self._logger.error(f"❌ {message}")
    
    def critical(self, message: str) -> None:
        """输出严重错误日志"""
        self._logger.critical(f"🚨 {message}")
    
    def debug(self, message: str) -> None:
        """输出调试日志"""
        self._logger.debug(f"🔍 {message}")
    
    def step(self, step_num: int, total: int, message: str) -> None:
        """输出步骤日志"""
        self._logger.info(f"【步骤 {step_num}/{total}】{message}")
    
    def start(self, message: str) -> None:
        """输出开始日志"""
        self._logger.info(f"🚀 {message}")
    
    def done(self, message: str) -> None:
        """输出完成日志"""
        self._logger.info(f"✨ {message}")
    
    def data(self, message: str) -> None:
        """输出数据相关日志"""
        self._logger.info(f"📦 {message}")
    
    def web(self, message: str) -> None:
        """输出Web相关日志"""
        self._logger.info(f"🌐 {message}")
    
    def chart(self, message: str) -> None:
        """输出图表相关日志"""
        self._logger.info(f"📊 {message}")
    
    def file(self, message: str) -> None:
        """输出文件相关日志"""
        self._logger.info(f"📄 {message}")
    
    def config(self, message: str) -> None:
        """输出配置相关日志"""
        self._logger.info(f"⚙️ {message}")
    
    def ai(self, message: str) -> None:
        """输出AI/LLM相关日志"""
        self._logger.info(f"🤖 {message}")
    
    def rule(self, message: str) -> None:
        """输出规则相关日志"""
        self._logger.info(f"📝 {message}")
    
    def timing(self, message: str, elapsed: float) -> None:
        """输出耗时日志"""
        self._logger.info(f"⏱️ {message} ({elapsed:.2f}s)")
    
    def progress(self, message: str) -> None:
        """输出进度日志（不换行，用于进度指示）"""
        # 进度日志仅输出到控制台，不记录到文件
        print(f"{message}", end='', flush=True)
    
    def separator(self, char: str = "=", length: int = 60) -> None:
        """输出分隔线"""
        self._logger.info(char * length)
    
    def section(self, title: str, char: str = "=", length: int = 60) -> None:
        """输出带标题的分隔区域"""
        self._logger.info("")
        self._logger.info(char * length)
        self._logger.info(title)
        self._logger.info(char * length)
    
    def menu(self, message: str) -> None:
        """输出菜单项（用户交互，仅控制台）"""
        print(message)
    
    def prompt(self, message: str) -> str:
        """输出提示并获取用户输入"""
        return input(message)


def get_log_helper(name: str) -> LogHelper:
    """
    获取日志辅助器
    
    Args:
        name: 模块名称
        
    Returns:
        日志辅助器实例
    """
    return LogHelper(get_logger(name))


# 模块级别便捷访问
def info(message: str, module: str = "main") -> None:
    """快捷信息日志"""
    get_logger(module).info(message)


def warning(message: str, module: str = "main") -> None:
    """快捷警告日志"""
    get_logger(module).warning(message)


def error(message: str, module: str = "main") -> None:
    """快捷错误日志"""
    get_logger(module).error(message)


def debug(message: str, module: str = "main") -> None:
    """快捷调试日志"""
    get_logger(module).debug(message)
