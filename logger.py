"""
统一日志系统 - Unified Logging System
提供统一的日志记录接口，支持控制台和文件输出

功能:
1. 彩色控制台输出
2. 文件日志记录
3. 统一的日志格式
4. 支持emoji图标
5. 自动日志清理
6. 从配置文件加载设置
"""

import logging
import os
import glob
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
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


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器（用于结构化日志）"""
    
    def format(self, record):
        import json
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


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
        self._max_size_mb = 10
        self._backup_count = 5
        self._retention_days = 30
        self._log_format = 'standard'  # 'standard' or 'json'
        
        # 确保日志目录存在
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
    
    def configure(self, 
                  log_level: str = 'INFO',
                  log_dir: str = 'logs',
                  console_enabled: bool = True,
                  file_enabled: bool = True,
                  max_size_mb: int = 10,
                  backup_count: int = 5,
                  retention_days: int = 30,
                  log_format: str = 'standard') -> None:
        """
        配置日志系统
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录
            console_enabled: 是否启用控制台输出
            file_enabled: 是否启用文件输出
            max_size_mb: 单个日志文件最大大小(MB)
            backup_count: 日志文件备份数量
            retention_days: 日志文件保留天数
            log_format: 日志格式 ('standard' 或 'json')
        """
        self._log_level = getattr(logging, log_level.upper(), logging.INFO)
        self._log_dir = log_dir
        self._console_enabled = console_enabled
        self._file_enabled = file_enabled
        self._max_size_mb = max_size_mb
        self._backup_count = backup_count
        self._retention_days = retention_days
        self._log_format = log_format
        
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
        
        # 清理过期日志文件
        self._cleanup_old_logs()
        
        # 更新已存在的日志器
        for logger in self._loggers.values():
            logger.setLevel(self._log_level)
    
    def configure_from_yaml(self, config_path: str = 'config.yaml') -> None:
        """
        从YAML配置文件加载日志设置
        
        Args:
            config_path: 配置文件路径
        """
        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    logging_config = config.get('logging', {})
                    
                    self.configure(
                        log_level=logging_config.get('level', 'INFO'),
                        log_dir=logging_config.get('dir', 'logs'),
                        console_enabled=logging_config.get('console', True),
                        file_enabled=logging_config.get('file', True),
                        max_size_mb=logging_config.get('max_size_mb', 10),
                        backup_count=logging_config.get('backup_count', 5),
                        retention_days=logging_config.get('retention_days', 30),
                        log_format=logging_config.get('format', 'standard')
                    )
        except Exception:
            pass  # 配置文件加载失败时使用默认配置
    
    def _cleanup_old_logs(self) -> None:
        """清理过期的日志文件"""
        if not os.path.exists(self._log_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=self._retention_days)
        log_pattern = os.path.join(self._log_dir, 'ai_tracker_*.log*')
        
        for log_file in glob.glob(log_pattern):
            try:
                # 从文件名中提取日期
                filename = os.path.basename(log_file)
                # 支持格式: ai_tracker_YYYYMMDD.log 或 ai_tracker_YYYYMMDD_HHMMSS.log
                date_str = filename.replace('ai_tracker_', '').split('.')[0][:8]
                if len(date_str) >= 8 and date_str.isdigit():
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                    if file_date < cutoff_date:
                        os.remove(log_file)
            except (ValueError, OSError):
                continue  # 跳过无法解析或删除的文件
    
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
                maxBytes=self._max_size_mb * 1024 * 1024,
                backupCount=self._backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self._log_level)
            
            # 根据配置选择格式化器
            if self._log_format == 'json':
                file_formatter = JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S')
            else:
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

# 尝试从配置文件加载设置
_logger_manager.configure_from_yaml()


def configure_logging(log_level: str = 'INFO',
                      log_dir: str = 'logs',
                      console_enabled: bool = True,
                      file_enabled: bool = True,
                      max_size_mb: int = 10,
                      backup_count: int = 5,
                      retention_days: int = 30,
                      log_format: str = 'standard') -> None:
    """
    配置全局日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
        console_enabled: 是否启用控制台输出
        file_enabled: 是否启用文件输出
        max_size_mb: 单个日志文件最大大小(MB)
        backup_count: 日志文件备份数量
        retention_days: 日志文件保留天数
        log_format: 日志格式 ('standard' 或 'json')
    """
    _logger_manager.configure(
        log_level, log_dir, console_enabled, file_enabled,
        max_size_mb, backup_count, retention_days, log_format
    )


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
    
    # 常用 emoji 集合，用于检测消息是否已包含 emoji
    COMMON_EMOJIS = {
        '✅', '❌', '⚠️', '🚀', '✨', '📦', '🤖', '⏱️', '⚙️', '📊', '📋', '📥',
        '💾', '📄', '🌐', '🔥', '⏳', '🎓', '📝', '🔍', '💡', 'ℹ️', '🗑️', '💻',
        '⭐', '🧪', '🔄', '🎨', '👋', '📁', '🚨', '⏰', '📈', '🌍', '🔻', '💪'
    }
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def _has_emoji(self, message: str) -> bool:
        """检测消息开头是否已包含 emoji"""
        if not message:
            return False
        # 检查消息前几个字符是否包含已知 emoji
        prefix = message[:4]  # emoji 通常在前几个字符
        return any(emoji in prefix for emoji in self.COMMON_EMOJIS)
    
    def _format_message(self, message: str, default_emoji: str) -> str:
        """格式化消息，避免 emoji 重复"""
        if self._has_emoji(message):
            return message
        return f"{default_emoji} {message}"
    
    def info(self, message: str, emoji: str = "ℹ️") -> None:
        """输出信息日志"""
        self._logger.info(self._format_message(message, emoji))
    
    def success(self, message: str) -> None:
        """输出成功日志"""
        self._logger.info(self._format_message(message, "✅"))
    
    def warning(self, message: str) -> None:
        """输出警告日志"""
        self._logger.warning(self._format_message(message, "⚠️"))
    
    def error(self, message: str) -> None:
        """输出错误日志"""
        self._logger.error(self._format_message(message, "❌"))
    
    def exception(self, message: str, exc_info: bool = True) -> None:
        """
        输出异常日志，包含完整堆栈信息
        
        Args:
            message: 错误消息
            exc_info: 是否包含异常堆栈信息（默认True）
        """
        self._logger.exception(self._format_message(message, "💥"), exc_info=exc_info)
    
    def critical(self, message: str) -> None:
        """输出严重错误日志"""
        self._logger.critical(self._format_message(message, "🚨"))
    
    def debug(self, message: str) -> None:
        """输出调试日志"""
        self._logger.debug(self._format_message(message, "🔍"))
    
    def step(self, step_num: int, total: int, message: str) -> None:
        """输出步骤日志"""
        # 检测 message 是否已包含步骤格式
        if message.startswith('【步骤') or message.startswith('[Step'):
            self._logger.info(message)
        else:
            self._logger.info(f"【步骤 {step_num}/{total}】{message}")
    
    def start(self, message: str) -> None:
        """输出开始日志"""
        self._logger.info(self._format_message(message, "🚀"))
    
    def done(self, message: str) -> None:
        """输出完成日志"""
        self._logger.info(self._format_message(message, "✨"))
    
    def data(self, message: str) -> None:
        """输出数据相关日志"""
        self._logger.info(self._format_message(message, "📦"))
    
    def web(self, message: str) -> None:
        """输出Web相关日志"""
        self._logger.info(self._format_message(message, "🌐"))
    
    def chart(self, message: str) -> None:
        """输出图表相关日志"""
        self._logger.info(self._format_message(message, "📊"))
    
    def file(self, message: str) -> None:
        """输出文件相关日志"""
        self._logger.info(self._format_message(message, "📄"))
    
    def config(self, message: str) -> None:
        """输出配置相关日志"""
        self._logger.info(self._format_message(message, "⚙️"))
    
    def ai(self, message: str) -> None:
        """输出AI/LLM相关日志"""
        self._logger.info(self._format_message(message, "🤖"))
    
    def rule(self, message: str) -> None:
        """输出规则相关日志"""
        self._logger.info(self._format_message(message, "📝"))
    
    def timing(self, message: str, elapsed: float) -> None:
        """输出耗时日志"""
        formatted = self._format_message(message, "⏱️")
        # 如果消息已包含耗时信息，不再追加
        if '(' in formatted and 's)' in formatted:
            self._logger.info(formatted)
        else:
            self._logger.info(f"{formatted} ({elapsed:.2f}s)")
    
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
    
    # ===== 双输出方法 (控制台 + 日志文件) =====
    
    def _log_to_file_only(self, level: int, message: str) -> None:
        """仅输出到日志文件，不显示在控制台"""
        import sys
        # 临时禁用控制台处理器
        console_handlers = []
        for h in self._logger.handlers:
            # 检查是否为控制台处理器（输出到 stdout 或 stderr）
            if isinstance(h, logging.StreamHandler) and hasattr(h, 'stream'):
                if h.stream in (sys.stdout, sys.stderr):
                    console_handlers.append(h)
                    self._logger.removeHandler(h)
        
        # 输出日志（仅到文件）
        self._logger.log(level, message)
        
        # 恢复控制台处理器
        for h in console_handlers:
            self._logger.addHandler(h)
    
    def dual_info(self, message: str, emoji: str = "ℹ️") -> None:
        """双输出：控制台显示 + 日志记录"""
        formatted = self._format_message(message, emoji)
        print(formatted)  # 控制台
        self._log_to_file_only(logging.INFO, formatted)  # 日志文件
    
    def dual_success(self, message: str) -> None:
        """双输出：成功消息"""
        formatted = self._format_message(message, "✅")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_warning(self, message: str) -> None:
        """双输出：警告消息"""
        formatted = self._format_message(message, "⚠️")
        print(formatted)
        self._log_to_file_only(logging.WARNING, formatted)
    
    def dual_error(self, message: str) -> None:
        """双输出：错误消息"""
        formatted = self._format_message(message, "❌")
        print(formatted)
        self._log_to_file_only(logging.ERROR, formatted)
    
    def dual_start(self, message: str) -> None:
        """双输出：开始操作"""
        formatted = self._format_message(message, "🚀")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_done(self, message: str) -> None:
        """双输出：完成操作"""
        formatted = self._format_message(message, "✨")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_data(self, message: str) -> None:
        """双输出：数据信息"""
        formatted = self._format_message(message, "📦")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_timing(self, message: str, elapsed: float) -> None:
        """双输出：耗时信息"""
        formatted = self._format_message(message, "⏱️")
        if '(' not in formatted or 's)' not in formatted:
            formatted = f"{formatted} ({elapsed:.2f}s)"
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_separator(self, char: str = "=", length: int = 60) -> None:
        """双输出：分隔线"""
        line = char * length
        print(line)
        self._log_to_file_only(logging.INFO, line)
    
    def dual_section(self, title: str, char: str = "=", length: int = 60) -> None:
        """双输出：带标题的分隔区域"""
        print()
        print(char * length)
        print(title)
        print(char * length)
        self._log_to_file_only(logging.INFO, "")
        self._log_to_file_only(logging.INFO, char * length)
        self._log_to_file_only(logging.INFO, title)
        self._log_to_file_only(logging.INFO, char * length)
    
    def dual_chart(self, message: str) -> None:
        """双输出：图表信息"""
        formatted = self._format_message(message, "📊")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_file(self, message: str) -> None:
        """双输出：文件信息"""
        formatted = self._format_message(message, "📄")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_rule(self, message: str) -> None:
        """双输出：规则信息"""
        formatted = self._format_message(message, "📝")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_ai(self, message: str) -> None:
        """双输出：AI/LLM信息"""
        formatted = self._format_message(message, "🤖")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_config(self, message: str) -> None:
        """双输出：配置信息"""
        formatted = self._format_message(message, "⚙️")
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)
    
    def dual_step(self, step_num: int, total: int, message: str) -> None:
        """双输出：步骤信息"""
        if message.startswith('【步骤') or message.startswith('[Step'):
            formatted = message
        else:
            formatted = f"【步骤 {step_num}/{total}】{message}"
        print(formatted)
        self._log_to_file_only(logging.INFO, formatted)


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
