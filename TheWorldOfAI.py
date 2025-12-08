"""
AI World Tracker - MVP版本
全球AI研究、产品、市场动态追踪应用

主要功能:
1. 数据采集模块 - 从arXiv、GitHub、RSS等源采集AI资讯
2. 内容分类系统 - 自动分类为研究/产品/市场维度（支持LLM和规则两种模式）
3. 智能分析功能 - 生成趋势分析和洞察报告
4. 数据可视化 - 生成各类图表展示数据

作者: AI World Tracker Team
日期: 2025-12-01
更新: 2025-12-06 - 添加LLM分类支持
"""

import sys
import json
import os
import glob
import yaml
from datetime import datetime
from typing import Optional, Dict

# 导入自定义模块
from data_collector import DataCollector
from content_classifier import ContentClassifier
from ai_analyzer import AIAnalyzer
from visualizer import DataVisualizer
from web_publisher import WebPublisher
from manual_reviewer import ManualReviewer
from learning_feedback import LearningFeedback, create_feedback_loop
from i18n import set_language, get_language, t, select_language_interactive
from logger import get_log_helper, configure_logging

# 配置日志
configure_logging(log_level='INFO')

# 模块日志器
log = get_log_helper('main')

# 用户配置文件
CONFIG_FILE = 'ai_tracker_config.json'

# Ollama 启动配置
OLLAMA_STARTUP_TIMEOUT = 10  # 启动等待超时（秒）

# 数据目录配置（从config.yaml加载）
def _load_data_paths():
    """加载数据目录配置"""
    exports_dir = 'data/exports'
    cache_dir = 'data/cache'
    
    try:
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                data_config = config.get('data', {})
                exports_dir = data_config.get('exports_dir', exports_dir)
                cache_dir = data_config.get('cache_dir', cache_dir)
    except Exception:
        pass
    
    # 确保目录存在
    os.makedirs(exports_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    
    return exports_dir, cache_dir

DATA_EXPORTS_DIR, DATA_CACHE_DIR = _load_data_paths()

# LLM分类器（可选导入）
try:
    from llm_classifier import LLMClassifier, check_ollama_status, AVAILABLE_MODELS, LLMProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    log.warning(t('llm_not_installed'))


class AIWorldTracker:
    """AI世界追踪器主应用"""
    
    def __init__(self, auto_mode: bool = False):
        """
        初始化AI世界追踪器
        
        Args:
            auto_mode: 是否为自动模式，自动模式下跳过交互式提示
        """
        self.auto_mode = auto_mode
        
        log.dual_section(f"     {t('app_title')}\n     {t('app_subtitle')}")
        
        self.collector = DataCollector()
        self.classifier = ContentClassifier()  # 规则分类器
        self.llm_classifier = None  # LLM分类器（按需初始化）
        self.analyzer = AIAnalyzer()
        self.visualizer = DataVisualizer()
        self.web_publisher = WebPublisher()
        self.reviewer = ManualReviewer()
        self.learner = LearningFeedback()
        
        self.data = []
        self.trends = {}
        self.chart_files = {}
        
        # 分类模式: 'rule' 或 'llm'
        self.classification_mode = 'rule'
        self.llm_provider = 'ollama'
        self.llm_model = 'qwen3:8b'
        
        # 自动模式下强制使用规则分类，跳过LLM相关初始化
        if self.auto_mode:
            log.dual_config(t('auto_mode'))
            self._load_latest_data()
            return
        
        # 加载用户配置（包括上次的分类模式）
        self._load_user_config()
        
        # 尝试加载最新数据
        self._load_latest_data()
        
        # 检查LLM可用性（自动模式下跳过交互式提示）
        if LLM_AVAILABLE:
            self._check_llm_availability()
        
        # 尝试恢复上次的LLM分类器
        self._try_restore_llm_classifier()
    
    def _load_user_config(self):
        """加载用户配置（包括上次的分类模式选择）"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 恢复分类模式设置
                saved_mode = config.get('classification_mode', 'rule')
                saved_provider = config.get('llm_provider', 'ollama')
                saved_model = config.get('llm_model', 'qwen3:8b')
                
                # 验证模式有效性
                if saved_mode in ['rule', 'llm']:
                    self.classification_mode = saved_mode
                    self.llm_provider = saved_provider
                    self.llm_model = saved_model
                    
                    if saved_mode == 'llm':
                        log.config(t('config_loaded_llm', provider=saved_provider, model=saved_model))
                    else:
                        log.config(t('config_loaded_rule'))
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # 配置文件损坏或不存在，使用默认值
            pass
    
    def _save_user_config(self):
        """保存用户配置"""
        try:
            config = {
                'classification_mode': self.classification_mode,
                'llm_provider': self.llm_provider,
                'llm_model': self.llm_model,
                'last_updated': datetime.now().isoformat()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(t('config_save_failed', error=str(e)))
    
    def cleanup(self):
        """清理资源，释放内存/显存"""
        # 卸载LLM模型（如果已加载）
        if self.llm_classifier is not None:
            try:
                self.llm_classifier.unload_model()
            except Exception as e:
                log.warning(t('cleanup_error', error=str(e)))
        
        # 保存采集历史缓存
        try:
            self.collector._save_history_cache()
        except Exception:
            pass
    
    def _try_restore_llm_classifier(self, clear_cache: bool = False):
        """尝试恢复上次的LLM分类器
        
        Args:
            clear_cache: 是否在初始化前强制清除缓存文件
        """
        if self.classification_mode == 'llm' and LLM_AVAILABLE:
            try:
                # 强制清除缓存文件（如果需要）
                if clear_cache:
                    self._force_clear_llm_cache()
                    
                # 检查Ollama服务是否可用
                if self.llm_provider == 'ollama':
                    status = check_ollama_status()
                    if status['running'] and self.llm_model in status.get('models', []):
                        self.llm_classifier = LLMClassifier(
                            provider='ollama',
                            model=self.llm_model
                        )
                        log.dual_success(t('llm_restored', model=self.llm_model))
                    else:
                        log.warning(t('llm_restore_failed'))
                        self.classification_mode = 'rule'
                        self._save_user_config()
                else:
                    # OpenAI/Anthropic 等云服务，需要用户手动配置
                    log.warning(t('llm_cloud_reconfig', provider=self.llm_provider))
                    self.classification_mode = 'rule'
            except Exception as e:
                log.error(t('llm_restore_error', error=str(e)))
                self.classification_mode = 'rule'
                self._save_user_config()
    
    def _force_clear_llm_cache(self):
        """强制清除LLM分类缓存文件"""
        cache_file = os.path.join(DATA_CACHE_DIR, 'llm_classification_cache.json')
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                log.success(t('llm_cache_force_cleared'))
            else:
                log.info(t('llm_cache_not_found'), emoji="ℹ️")
        except Exception as e:
            log.error(t('llm_cache_clear_error', error=str(e)))
    
    def _clear_export_history(self):
        """清除采集结果历史（需要用户确认）"""
        import glob
        
        # 查找所有导出文件
        json_pattern = os.path.join(DATA_EXPORTS_DIR, 'ai_tracker_data_*.json')
        txt_pattern = os.path.join(DATA_EXPORTS_DIR, 'ai_tracker_report_*.txt')
        
        json_files = glob.glob(json_pattern)
        txt_files = glob.glob(txt_pattern)
        all_files = json_files + txt_files
        
        if not all_files:
            log.info(t('clear_export_history_empty'), emoji="ℹ️")
            return
        
        # 显示警告并请求确认
        log.warning(t('clear_export_history_confirm'))
        log.info(f"   📁 {len(json_files)} JSON + {len(txt_files)} TXT = {len(all_files)} files", emoji="")
        
        confirm = input(f"\n{t('clear_export_history_prompt')}").strip().lower()
        
        if confirm != 'y':
            log.info(t('clear_export_history_cancelled'), emoji="")
            return
        
        # 执行删除
        deleted_count = 0
        for f in all_files:
            try:
                os.remove(f)
                deleted_count += 1
            except Exception as e:
                log.error(f"Failed to delete {f}: {e}")
        
        # 清空内存中的数据
        self.data = []
        self.trends = {}
        self.chart_files = {}
        
        log.success(t('clear_export_history_done', count=deleted_count))
    
    def _clear_review_history(self):
        """清除人工审核记录和学习报告（需要用户确认）"""
        import glob
        
        # 查找所有审核历史和学习报告文件
        review_pattern = os.path.join(DATA_EXPORTS_DIR, 'review_history_*.json')
        learning_pattern = os.path.join(DATA_EXPORTS_DIR, 'learning_report_*.json')
        
        review_files = glob.glob(review_pattern)
        learning_files = glob.glob(learning_pattern)
        all_files = review_files + learning_files
        
        if not all_files:
            log.dual_info(t('clear_review_history_empty'), emoji="ℹ️")
            return
        
        # 显示警告并请求确认
        log.dual_warning(t('clear_review_history_confirm'))
        log.dual_info(f"   📁 {len(review_files)} review_history + {len(learning_files)} learning_report = {len(all_files)} files", emoji="")
        
        confirm = input(f"\n{t('clear_export_history_prompt')}").strip().lower()
        
        if confirm != 'y':
            log.dual_info(t('clear_export_history_cancelled'), emoji="")
            return
        
        # 执行删除
        deleted_count = 0
        for f in all_files:
            try:
                os.remove(f)
                deleted_count += 1
            except Exception as e:
                log.dual_error(f"Failed to delete {f}: {e}")
        
        log.dual_success(t('clear_review_history_done', count=deleted_count))
    
    def _clear_all_data(self):
        """清除所有数据（需要用户二次确认）"""
        import glob
        
        # 显示严重警告
        log.dual_separator()
        log.dual_warning(t('clear_all_data_confirm'))
        print(t('clear_all_data_list'))
        log.file(t('clear_all_data_list'))  # 日志记录
        print()
        log.dual_warning(t('clear_all_data_warning'))
        log.dual_separator()
        
        # 要求输入 "YES" 确认
        confirm = input(f"\n{t('clear_all_data_prompt')}").strip()
        
        if confirm != 'YES':
            log.dual_info(t('clear_all_data_cancelled'), emoji="")
            return
        
        print()
        log.file("User confirmed: clearing all data...")  # 日志记录用户确认
        deleted_total = 0
        
        # 1. 清除LLM分类缓存
        cache_file = os.path.join(DATA_CACHE_DIR, 'llm_classification_cache.json')
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                deleted_total += 1
                log.dual_success(t('llm_cache_force_cleared'))
            except Exception as e:
                log.dual_error(f"Failed to delete LLM cache: {e}")
        
        # 2. 清除采集历史缓存
        self.collector.clear_history_cache()
        deleted_total += 1
        
        # 3. 清除采集结果历史
        json_pattern = os.path.join(DATA_EXPORTS_DIR, 'ai_tracker_data_*.json')
        txt_pattern = os.path.join(DATA_EXPORTS_DIR, 'ai_tracker_report_*.txt')
        export_files = glob.glob(json_pattern) + glob.glob(txt_pattern)
        for f in export_files:
            try:
                os.remove(f)
                deleted_total += 1
            except Exception as e:
                log.dual_error(f"Failed to delete {f}: {e}")
        
        if export_files:
            log.dual_info(f"Cleared {len(export_files)} export files", emoji="🗑️")
        
        # 4. 清除人工审核记录
        review_pattern = os.path.join(DATA_EXPORTS_DIR, 'review_history_*.json')
        learning_pattern = os.path.join(DATA_EXPORTS_DIR, 'learning_report_*.json')
        review_files = glob.glob(review_pattern) + glob.glob(learning_pattern)
        for f in review_files:
            try:
                os.remove(f)
                deleted_total += 1
            except Exception as e:
                log.dual_error(f"Failed to delete {f}: {e}")
        
        if review_files:
            log.dual_info(f"Cleared {len(review_files)} review files", emoji="🗑️")
        
        # 清空内存中的数据
        self.data = []
        self.trends = {}
        self.chart_files = {}
        
        print()
        log.dual_success(t('clear_all_data_done'))
        log.dual_info(f"   📁 {deleted_total} files deleted", emoji="")
    
    def _check_llm_availability(self):
        """检查LLM服务可用性，提供启动帮助"""
        status = check_ollama_status()
        
        if status['running']:
            if status['models']:
                log.dual_success(t('ollama_running') + ", " + t('ollama_available_models', models=', '.join(status['models'][:3])))
                if status['recommended']:
                    self.llm_model = status['recommended']
            else:
                log.warning(t('ollama_no_models_warning'))
                log.dual_info(t('ollama_install_hint'), emoji="💡")
                log.dual_info(t('ollama_no_llm_hint'), emoji="ℹ️")
        else:
            log.warning(t('ollama_not_running_info'))
            self._offer_ollama_startup_help()
    
    def _start_ollama_service(self, show_progress: bool = True) -> dict:
        """
        启动 Ollama 服务的核心逻辑（公共方法）
        
        Args:
            show_progress: 是否显示进度点
            
        Returns:
            dict: {
                'success': bool,      # 是否启动成功
                'status': dict|None,  # Ollama状态信息（成功时）
                'error': str|None     # 错误类型: 'timeout', 'not_found', 或具体错误信息
            }
        """
        import subprocess
        import platform
        import time
        
        try:
            # 根据操作系统选择启动方式
            system = platform.system()
            if system == 'Windows':
                subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            # 等待服务启动
            for _ in range(OLLAMA_STARTUP_TIMEOUT):
                time.sleep(1)
                if show_progress:
                    print('.', end='', flush=True)
                status = check_ollama_status()
                if status['running']:
                    return {'success': True, 'status': status, 'error': None}
            
            return {'success': False, 'status': None, 'error': 'timeout'}
            
        except FileNotFoundError:
            return {'success': False, 'status': None, 'error': 'not_found'}
        except Exception as e:
            return {'success': False, 'status': None, 'error': str(e)}
    
    def _handle_ollama_start_error(self, error: str, indent: str = ""):
        """
        统一处理 Ollama 启动错误
        
        Args:
            error: 错误类型或信息
            indent: 输出缩进
        """
        if error == 'timeout':
            print(f"\n{indent}" + t('ollama_timeout'))
        elif error == 'not_found':
            print(f"\n{indent}" + t('ollama_not_found'))
            print(f"{indent}" + t('ollama_download'))
        else:
            print(f"\n{indent}" + t('ollama_start_failed', error=error))
            print(f"{indent}" + t('ollama_manual_start'))
    
    def _offer_ollama_startup_help(self):
        """提供Ollama启动帮助"""
        print("\n   " + t('ollama_hint'))
        
        # 自动模式下跳过交互式提示
        if self.auto_mode:
            print("   " + t('ollama_skip_auto'))
            return
        
        prompt = "   " + t('ollama_start_prompt')
        choice = input(prompt).strip().lower()
        
        if choice == 'y':
            print("\n   " + t('ollama_starting'))
            print("   " + t('ollama_waiting'), end='', flush=True)
            
            result = self._start_ollama_service(show_progress=True)
            
            if result['success']:
                print("\n   " + t('ollama_started'))
                status = result['status']
                if status.get('models'):
                    print(f"   " + t('ollama_available_models', models=', '.join(status['models'][:3])))
                    if status.get('recommended'):
                        self.llm_model = status['recommended']
                else:
                    print("   " + t('no_models'))
                    print("   " + t('ollama_no_local_llm'))
            else:
                self._handle_ollama_start_error(result['error'], indent="   ")
                if result['error'] == 'not_found':
                    print("   " + t('ollama_no_local_llm'))
        else:
            print("   " + t('ollama_no_local_llm'))
            print("   " + t('ollama_later_hint'))
    
    def _offer_ollama_startup_help_in_menu(self):
        """在菜单中提供Ollama启动帮助（简化版）"""
        prompt = "Start Ollama service? (y/n) [n]: " if get_language() == 'en' else "是否尝试启动Ollama服务? (y/n) [n]: "
        choice = input(prompt).strip().lower()
        
        if choice == 'y':
            print("\n" + t('ollama_starting'))
            log.info(t('ollama_waiting'), emoji="⏳")
            
            result = self._start_ollama_service(show_progress=True)
            
            if result['success']:
                print("\n" + t('ollama_started'))
            else:
                self._handle_ollama_start_error(result['error'], indent="")
    
    def _install_ollama_model(self, model_name: str):
        """安装Ollama模型"""
        import subprocess
        
        print("\n" + t('model_installing', model=model_name))
        log.info(t('model_install_wait'), emoji="⏳")
        print()
        
        try:
            # 实时显示下载进度
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                print(f"  {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print("\n" + t('model_installed', model=model_name))
                self.llm_model = model_name
            else:
                print("\n" + t('model_install_failed', code=process.returncode))
                
        except FileNotFoundError:
            print("\n" + t('ollama_not_found'))
        except Exception as e:
            print("\n" + t('model_install_error', error=str(e)))
    
    def _load_latest_data(self):
        """尝试加载最新的数据文件"""
        try:
            # 从 exports 目录加载数据
            if not os.path.exists(DATA_EXPORTS_DIR):
                return
            files = [f for f in os.listdir(DATA_EXPORTS_DIR) if f.startswith('ai_tracker_data_') and f.endswith('.json')]
            if not files:
                return
            
            latest_file = os.path.join(DATA_EXPORTS_DIR, max(files))
            log.data(t('loading_history', file=os.path.basename(latest_file)))
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                
            self.data = saved_data.get('data', [])
            self.trends = saved_data.get('trends', {})
            
            # 尝试加载图表文件
            if os.path.exists('visualizations'):
                self.chart_files = {
                    'tech_hotspots': os.path.join('visualizations', 'tech_hotspots.png'),
                    'content_distribution': os.path.join('visualizations', 'content_distribution.png'),
                    'region_distribution': os.path.join('visualizations', 'region_distribution.png'),
                    'daily_trends': os.path.join('visualizations', 'daily_trends.png'),
                    'dashboard': os.path.join('visualizations', 'dashboard.png')
                }
                # 验证文件是否存在
                self.chart_files = {k: v for k, v in self.chart_files.items() if os.path.exists(v)}
            
            log.dual_success(t('history_loaded', count=len(self.data)))
        except Exception as e:
            log.warning(t('history_load_failed', error=str(e)))
    
    def run_full_pipeline(self):
        """运行完整数据处理流程"""
        import time
        start_time = time.time()
        timing_stats = {}  # 收集耗时统计
        
        log.dual_start(t('start_pipeline'))
        
        # 步骤1: 数据采集
        step_start = time.time()
        log.step(1, 5, t('step_collect'))
        raw_data = self.collector.collect_all()
        
        # 合并所有数据
        all_items = []
        for category, items in raw_data.items():
            all_items.extend(items)
        
        timing_stats['data_collection'] = round(time.time() - step_start, 1)
        log.data(t('collected_items', count=len(all_items)))
        
        # 步骤2: 内容分类（根据当前模式选择分类器）
        step_start = time.time()
        log.step(2, 5, t('step_classify'))
        self.data = self._classify_data(all_items)
        timing_stats['classification'] = round(time.time() - step_start, 1)
        log.timing(t('classification_time', time=timing_stats['classification']), timing_stats['classification'])
        
        # 步骤3: 智能分析
        step_start = time.time()
        log.step(3, 5, t('step_analyze'))
        self.trends = self.analyzer.analyze_trends(self.data)
        timing_stats['analysis'] = round(time.time() - step_start, 1)
        
        # 步骤4: 数据可视化
        step_start = time.time()
        log.step(4, 5, t('step_visualize'))
        self.chart_files = self.visualizer.visualize_all(self.trends)
        timing_stats['visualization'] = round(time.time() - step_start, 1)
        
        # 步骤5: 生成Web页面
        step_start = time.time()
        log.step(5, 5, t('step_web'))
        web_file = self.web_publisher.generate_html_page(self.data, self.trends, self.chart_files)
        timing_stats['web_generation'] = round(time.time() - step_start, 1)
        
        # 计算总耗时
        timing_stats['total'] = round(time.time() - start_time, 1)
        
        # 生成报告
        report = self.analyzer.generate_report(self.data, self.trends)
        
        # 保存数据和报告（包含耗时统计）
        self._save_results(report, web_file, timing_stats)
        
        log.dual_separator()
        log.dual_done(t('process_complete'))
        log.dual_separator()
        log.dual_chart(t('charts_generated', count=len([f for f in self.chart_files.values() if f])))
        log.dual_file(t('report_saved'))
        log.dual_data(t('data_saved'))
        log.dual_info(t('web_generated'), emoji="🌐")
        
        # 询问是否在浏览器中打开网页
        self._ask_open_web_page(web_file)
        
        return report
    
    def show_menu(self):
        """显示交互菜单"""
        while True:
            # 显示当前分类模式
            mode_str = self._get_mode_display()
            
            log.dual_section(t('menu_title') + f"\n   {t('menu_current_mode')}: {mode_str}")
            log.menu(t('menu_option_1'))
            log.menu(t('menu_option_2'))
            log.menu(t('menu_option_3'))
            log.menu(t('menu_option_4'))
            log.menu(t('menu_option_5'))
            log.menu(t('menu_option_0'))
            log.dual_separator()
            
            choice = input(f"\n{t('menu_choice')}: ").strip()
            
            if choice == '1':
                self.run_full_pipeline()
            elif choice == '2':
                self._generate_web_page()
            elif choice == '3':
                self._manual_review()
            elif choice == '4':
                self._learning_feedback()
            elif choice == '5':
                self._switch_classification_mode()
            elif choice == '0':
                log.dual_success(t('menu_goodbye'))
                break
            else:
                log.warning(t('menu_invalid'))
    
    def _get_mode_display(self) -> str:
        """获取当前模式的显示字符串"""
        if self.classification_mode == 'llm':
            if get_language() == 'en':
                return f"🤖 LLM Mode ({self.llm_provider}/{self.llm_model})"
            return f"🤖 LLM模式 ({self.llm_provider}/{self.llm_model})"
        else:
            if get_language() == 'en':
                return "📝 Rule Mode (Rule-based)"
            return "📝 规则模式 (Rule-based)"
    
    def _switch_classification_mode(self):
        """设置与管理菜单"""
        log.section(t('switch_mode_title'))
        
        log.menu(f"\n{t('current_mode')}: {self._get_mode_display()}")
        
        # 分类模式分组
        log.menu(f"\n{t('settings_classification_mode')}:")
        log.menu(f"  1. {t('mode_rule_desc')}")
        
        if LLM_AVAILABLE:
            log.menu(f"  2. {t('mode_ollama_desc')}")
            log.menu(f"  3. {t('mode_openai_desc')}")
        else:
            log.menu(f"  {t('llm_not_available')}")
        
        # 数据维护分组
        log.menu(f"\n{t('settings_data_maintenance')}:")
        if LLM_AVAILABLE:
            log.menu(f"  4. {t('clear_llm_cache')}")
        log.menu(f"  5. {t('clear_collection_cache')}")
        log.menu(f"  6. {t('clear_export_history')}")
        log.menu(f"  7. {t('clear_review_history')}")
        log.menu(f"  8. {t('clear_all_data')}")
        
        log.menu(f"\n  0. {t('back_to_main_menu')}")
        
        choice = input(f"\n{t('select_model')} (0-8): ").strip()
        
        if choice == '0' or choice == '':
            return  # 返回主菜单
        
        elif choice == '1':
            self.classification_mode = 'rule'
            self.llm_classifier = None
            self._save_user_config()
            log.success(t('switched_to_rule'))
        
        elif choice == '2' and LLM_AVAILABLE:
            self._setup_ollama_mode()
        
        elif choice == '3' and LLM_AVAILABLE:
            self._setup_openai_mode()
        
        elif choice == '4' and LLM_AVAILABLE:
            self._force_clear_llm_cache()
            # 重新加载LLM分类器（如果当前是LLM模式）
            if self.llm_classifier:
                log.ai(t('reinit_llm_classifier'))
                self._try_restore_llm_classifier(clear_cache=False)  # 不需要再清除，已经清除了
        
        elif choice == '5':
            self.collector.clear_history_cache()
        
        elif choice == '6':
            self._clear_export_history()
        
        elif choice == '7':
            self._clear_review_history()
        
        elif choice == '8':
            self._clear_all_data()
        
        else:
            log.warning(t('invalid_choice'))
    
    def _setup_ollama_mode(self):
        """设置Ollama模式"""
        status = check_ollama_status()
        
        if not status['running']:
            log.warning(t('ollama_not_running'))
            self._offer_ollama_startup_help_in_menu()
            
            # 重新检查状态
            status = check_ollama_status()
            if not status['running']:
                log.error(t('ollama_cannot_connect'))
                return
        
        log.success(t('ollama_running'))
        log.menu(f"\n{t('available_models')}:")
        
        models = status['models']
        if not models:
            log.menu("  " + t('no_models'))
            log.menu("  " + t('install_model_hint'))
            
            prompt = "\nInstall recommended model qwen3:8b now? (y/n) [n]: " if get_language() == 'en' else "\n是否现在安装推荐模型 qwen3:8b? (y/n) [n]: "
            choice = input(prompt).strip().lower()
            if choice == 'y':
                self._install_ollama_model('qwen3:8b')
                # 重新获取模型列表
                status = check_ollama_status()
                models = status['models']
            
            if not models:
                log.warning(t('no_available_models'))
                return
        
        # 显示可用模型
        recommended_label = " ⭐ " + ("recommended" if get_language() == 'en' else "推荐")
        for i, model in enumerate(models, 1):
            recommended = recommended_label if model == status['recommended'] else ""
            log.menu(f"  {i}. {model}{recommended}")
        
        prompt = f"\n{t('select_model')} (1-{len(models)}) [" + ("default: 1" if get_language() == 'en' else "默认: 1") + "]: "
        model_choice = input(prompt).strip() or '1'
        
        try:
            idx = int(model_choice) - 1
            selected_model = models[idx] if 0 <= idx < len(models) else models[0]
        except (ValueError, IndexError):
            selected_model = models[0]
        
        # 初始化LLM分类器
        self.classification_mode = 'llm'
        self.llm_provider = 'ollama'
        self.llm_model = selected_model
        
        try:
            self.llm_classifier = LLMClassifier(
                provider='ollama',
                model=selected_model,
                enable_cache=True,
                max_workers=3,  # 默认并发数，GPU模式自动提升至6
                batch_size=5    # 启用批量分类
            )
            self._save_user_config()
            log.success(t('switched_to_llm', provider='Ollama', model=selected_model))
            
            # 预热模型
            warmup_prompt = "\nWarm up the model now? (Y/n): " if get_language() == 'en' else "\n是否现在预热模型? (Y/n): "
            warmup = input(warmup_prompt).strip().lower()
            if warmup != 'n':
                self.llm_classifier.warmup_model()
                
        except Exception as e:
            log.error(t('llm_init_failed', error=str(e)))
            self.classification_mode = 'rule'
            self._save_user_config()
    
    def _setup_openai_mode(self):
        """设置Azure OpenAI模式"""
        # 直接调用Azure OpenAI设置
        self._setup_azure_openai_mode()
    
    def _setup_standard_openai_mode(self):
        """设置标准OpenAI模式"""
        is_zh = get_language() == 'zh'
        
        # 收集 API Key
        log.info("请输入OpenAI API密钥:" if is_zh else "Enter OpenAI API key:", emoji="🔑")
        api_key = input("API Key: ").strip()
        if not api_key:
            log.info("已取消设置" if is_zh else "Setup cancelled", emoji="ℹ️")
            return
        
        # 显示可用模型
        log.menu("\n" + t('available_openai_models'))
        models = list(AVAILABLE_MODELS[LLMProvider.OPENAI].keys())
        for i, model in enumerate(models, 1):
            info = AVAILABLE_MODELS[LLMProvider.OPENAI][model]
            log.menu(f"  {i}. {info['name']} - {info['description']}")
        
        # 选择模型
        prompt = f"\n" + ("请选择模型" if is_zh else "Select model") + f" (1-{len(models)}): "
        model_choice = input(prompt).strip()
        
        try:
            idx = int(model_choice) - 1
            if not (0 <= idx < len(models)):
                log.warning("无效选择" if is_zh else "Invalid choice")
                return
            selected_model = models[idx]
        except (ValueError, IndexError):
            log.warning("无效选择" if is_zh else "Invalid choice")
            return
        
        # 创建分类器
        self.classification_mode = 'llm'
        self.llm_provider = 'openai'
        self.llm_model = selected_model
        
        try:
            self.llm_classifier = LLMClassifier(
                provider='openai',
                model=selected_model,
                api_key=api_key,
                enable_cache=True,
                max_workers=3
            )
            self._save_user_config()
            log.success(t('switched_to_llm', provider='OpenAI', model=selected_model))
        except Exception as e:
            log.error(t('llm_init_failed', error=str(e)))
            self.classification_mode = 'rule'
            self._save_user_config()
    
    def _setup_azure_openai_mode(self):
        """设置Azure OpenAI模式 - 需要收集所有必要参数"""
        is_zh = get_language() == 'zh'
        
        log.section("Azure OpenAI " + ("配置" if is_zh else "Configuration"))
        log.info("请依次输入以下参数 (从Azure门户获取):" if is_zh else "Enter the following parameters (from Azure Portal):", emoji="📋")
        
        # 1. 收集 Endpoint
        log.menu("\n1. Azure OpenAI Endpoint")
        log.menu("   " + ("格式: https://你的资源名.openai.azure.com/" if is_zh else "Format: https://your-resource-name.openai.azure.com/"))
        endpoint = input("Endpoint: ").strip()
        if not endpoint:
            log.info("已取消设置" if is_zh else "Setup cancelled", emoji="ℹ️")
            return
        
        # 验证endpoint格式
        if not endpoint.startswith('https://') or not endpoint.endswith('.openai.azure.com/'):
            if not endpoint.endswith('/'):
                endpoint += '/'
            if not endpoint.startswith('https://'):
                log.warning("Endpoint应以 https:// 开头" if is_zh else "Endpoint should start with https://")
        
        # 2. 收集 API Key
        log.menu("\n2. Azure OpenAI API Key")
        log.menu("   " + ("从 Azure门户 -> 你的OpenAI资源 -> 密钥和终结点 获取" if is_zh else "Get from Azure Portal -> Your OpenAI Resource -> Keys and Endpoint"))
        api_key = input("API Key: ").strip()
        if not api_key:
            log.info("已取消设置" if is_zh else "Setup cancelled", emoji="ℹ️")
            return
        
        # 3. 收集 Deployment Name
        log.menu("\n3. Deployment Name (" + ("部署名称" if is_zh else "Deployment Name") + ")")
        log.menu("   " + ("这是你在Azure中创建的模型部署名称，不是模型名称" if is_zh else "This is the deployment name you created in Azure, not the model name"))
        deployment_name = input("Deployment Name: ").strip()
        if not deployment_name:
            log.info("已取消设置" if is_zh else "Setup cancelled", emoji="ℹ️")
            return
        
        # 4. 收集 API Version
        log.menu("\n4. API Version")
        log.menu("   " + ("常用版本: 2024-02-15-preview, 2024-05-01-preview, 2024-08-01-preview" if is_zh else "Common versions: 2024-02-15-preview, 2024-05-01-preview, 2024-08-01-preview"))
        api_version = input("API Version: ").strip()
        if not api_version:
            log.info("已取消设置" if is_zh else "Setup cancelled", emoji="ℹ️")
            return
        
        # 显示配置摘要
        log.section("配置摘要" if is_zh else "Configuration Summary")
        log.menu(f"  Endpoint: {endpoint}")
        log.menu(f"  API Key: {api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else f"  API Key: ***")
        log.menu(f"  Deployment: {deployment_name}")
        log.menu(f"  API Version: {api_version}")
        
        confirm = input("\n" + ("确认配置? (y/N): " if is_zh else "Confirm configuration? (y/N): ")).strip().lower()
        if confirm != 'y':
            log.info("已取消设置" if is_zh else "Setup cancelled", emoji="ℹ️")
            return
        
        # 创建分类器
        self.classification_mode = 'llm'
        self.llm_provider = 'azure_openai'
        self.llm_model = deployment_name
        
        try:
            self.llm_classifier = LLMClassifier(
                provider='azure_openai',
                model=deployment_name,
                api_key=api_key,
                azure_endpoint=endpoint,
                azure_api_version=api_version,
                enable_cache=True,
                max_workers=3
            )
            self._save_user_config()
            log.success(t('switched_to_llm', provider='Azure OpenAI', model=deployment_name))
        except Exception as e:
            log.error(t('llm_init_failed', error=str(e)))
            self.classification_mode = 'rule'
            self._save_user_config()
    
    def _setup_anthropic_mode(self):
        """设置Anthropic模式"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            log.warning(t('llm_api_key_missing', provider='ANTHROPIC'))
            prompt = "Enter Anthropic API key (or press Enter to cancel): " if get_language() == 'en' else "请输入Anthropic API密钥 (或按Enter取消): "
            api_key = input(prompt).strip()
            if not api_key:
                return
        
        log.menu("\n" + t('available_anthropic_models'))
        models = list(AVAILABLE_MODELS[LLMProvider.ANTHROPIC].keys())
        for i, model in enumerate(models, 1):
            info = AVAILABLE_MODELS[LLMProvider.ANTHROPIC][model]
            log.menu(f"  {i}. {info['name']} - {info['description']}")
        
        prompt = f"\n{t('select_model')} (1-{len(models)}) [" + ("default: 1" if get_language() == 'en' else "默认: 1") + "]: "
        model_choice = input(prompt).strip() or '1'
        
        try:
            idx = int(model_choice) - 1
            selected_model = models[idx] if 0 <= idx < len(models) else models[0]
        except (ValueError, IndexError):
            selected_model = models[0]
        
        self.classification_mode = 'llm'
        self.llm_provider = 'anthropic'
        self.llm_model = selected_model
        
        try:
            self.llm_classifier = LLMClassifier(
                provider='anthropic',
                model=selected_model,
                api_key=api_key,
                enable_cache=True,
                max_workers=3
            )
            self._save_user_config()
            log.success(t('switched_to_llm', provider='Anthropic', model=selected_model))
        except Exception as e:
            log.error(t('llm_init_failed', error=str(e)))
            self.classification_mode = 'rule'
            self._save_user_config()
    
    def _classify_data(self, items: list) -> list:
        """根据当前模式分类数据"""
        if self.classification_mode == 'llm' and self.llm_classifier:
            print(f"\n" + t('using_llm', provider=self.llm_provider, model=self.llm_model))
            return self.llm_classifier.classify_batch(items)
        else:
            print("\n" + t('using_rule'))
            return self.classifier.classify_batch(items)
    
    def _collect_only(self):
        """仅采集数据"""
        print("\n" + t('collecting') + "\n")
        raw_data = self.collector.collect_all()
        
        all_items = []
        for items in raw_data.values():
            all_items.extend(items)
        
        self.data = self.classifier.classify_batch(all_items)
        print(f"\n" + t('collect_done', count=len(self.data)))
    
    def _show_statistics(self):
        """显示数据统计"""
        if not self.data:
            print("\n" + t('no_data'))
            return
        
        print("\n" + t('stats_overview'))
        print("   " + t('stats_total', count=len(self.data)))
        
        # 内容类型统计
        type_count = {}
        for item in self.data:
            ct = item.get('content_type', 'unknown')
            type_count[ct] = type_count.get(ct, 0) + 1
        
        print("\n   " + t('stats_by_type'))
        for ctype, count in type_count.items():
            print("   " + t('stats_item', name=ctype, count=count))
        
        # 地区统计
        region_count = {}
        for item in self.data:
            region = item.get('region', 'unknown')
            region_count[region] = region_count.get(region, 0) + 1
        
        print("\n   " + t('stats_by_region'))
        for region, count in region_count.items():
            print("   " + t('stats_item', name=region, count=count))
    
    def _generate_visualizations(self):
        """生成可视化图表"""
        if not self.data:
            print("\n" + t('no_data'))
            return
        
        if not self.trends:
            print("\n" + t('analyzing'))
            self.trends = self.analyzer.analyze_trends(self.data)
        
        print("\n" + t('generating_charts'))
        self.chart_files = self.visualizer.visualize_all(self.trends)
    
    def _show_report(self):
        """显示分析报告"""
        if not self.data:
            print("\n" + t('no_data'))
            return
        
        if not self.trends:
            print("\n" + t('generating_analysis'))
            self.trends = self.analyzer.analyze_trends(self.data)
        
        report = self.analyzer.generate_report(self.data, self.trends)
        print("\n" + report)
    
    def _filter_data(self):
        """按条件筛选数据"""
        if not self.data:
            print("\n" + t('no_data'))
            return
        
        print("\n" + t('filter_title'))
        print(t('filter_by_type'))
        print(t('filter_by_region'))
        print(t('filter_by_tech'))
        
        filter_prompt = "\nSelect filter method (1-3): " if get_language() == 'en' else "\n选择筛选方式 (1-3): "
        filter_choice = input(filter_prompt).strip()
        
        if filter_choice == '1':
            ctype_prompt = "Enter content type (research/product/market): " if get_language() == 'en' else "输入内容类型 (research/product/market): "
            ctype = input(ctype_prompt).strip()
            filtered = self.classifier.get_filtered_items(self.data, content_type=ctype)
        elif filter_choice == '2':
            region_prompt = "Enter region (China/USA/Europe/Global): " if get_language() == 'en' else "输入地区 (China/USA/Europe/Global): "
            region = input(region_prompt).strip()
            filtered = self.classifier.get_filtered_items(self.data, region=region)
        elif filter_choice == '3':
            tech_prompt = "Enter tech field (e.g., NLP, Computer Vision): " if get_language() == 'en' else "输入技术领域 (如: NLP, Computer Vision): "
            tech = input(tech_prompt).strip()
            filtered = self.classifier.get_filtered_items(self.data, tech_category=tech)
        else:
            log.warning(t('invalid_choice'))
            return
        
        print(f"\n" + t('filter_result', count=len(filtered)) + "\n")
        
        # 显示前5条
        for i, item in enumerate(filtered[:5], 1):
            print(f"{i}. {item.get('title', 'No title')}")
            type_label = "Type" if get_language() == 'en' else "类型"
            region_label = "Region" if get_language() == 'en' else "地区"
            source_label = "Source" if get_language() == 'en' else "来源"
            date_label = "Date" if get_language() == 'en' else "日期"
            print(f"   {type_label}: {item.get('content_type')} | {region_label}: {item.get('region')}")
            print(f"   {source_label}: {item.get('source')} | {date_label}: {item.get('published', 'N/A')}\n")
        
        if len(filtered) > 5:
            print("   " + t('filter_more', count=len(filtered) - 5))
    
    def _ask_open_web_page(self, web_file: str):
        """询问用户是否在浏览器中打开网页"""
        if not web_file or not os.path.exists(web_file):
            return
        
        try:
            import webbrowser
            prompt = "\nOpen web page in browser? (Y/N): " if get_language() == 'en' else "\n是否在浏览器中打开Web页面? (Y/N): "
            choice = input(prompt).strip().lower()
            if choice in ['y', 'yes', '是']:
                webbrowser.open(f'file://{os.path.abspath(web_file)}')
                log.success(t('opened_browser'))
        except Exception as e:
            log.error(t('browser_error', error=str(e)))
            log.info(t('manual_open', file=os.path.abspath(web_file)), emoji="📄")
    
    def _generate_web_page(self):
        """生成Web页面"""
        if not self.data:
            print("\n" + t('no_data'))
            return
        
        if not self.trends:
            print("\n" + t('generating_analysis'))
            self.trends = self.analyzer.analyze_trends(self.data)
        
        if not self.chart_files:
            print("\n" + t('generating_charts'))
            self.chart_files = self.visualizer.visualize_all(self.trends)
        
        print("\n" + t('generating_web'))
        web_file = self.web_publisher.generate_html_page(self.data, self.trends, self.chart_files)
        
        # 询问是否在浏览器中打开
        self._ask_open_web_page(web_file)
    
    def _manual_review(self):
        """人工审核分类"""
        if not self.data:
            print("\n" + t('no_data'))
            return
        
        print("\n" + "="*60)
        print(t('manual_review_title'))
        print("="*60)
        
        # 检查需要审核的内容
        review_items = self.reviewer.get_items_for_review(self.data, min_confidence=0.6)
        
        print(f"\n" + t('review_stats'))
        print("   " + t('review_total', count=len(self.data)))
        print("   " + t('review_need', count=len(review_items), percent=f"{len(review_items)/len(self.data):.1%}"))
        
        if not review_items:
            print("\n" + t('review_not_needed'))
            return
        
        # 显示需要审核的内容概览
        print("\n" + t('review_list'))
        conf_label = "confidence" if get_language() == 'en' else "置信度"
        for i, item in enumerate(review_items[:5], 1):
            print(f"   {i}. {item.get('title', 'N/A')[:50]}... ({conf_label}: {item.get('confidence', 0):.1%})")
        
        if len(review_items) > 5:
            print("   " + t('review_more', count=len(review_items)-5))
        
        print("\n" + t('review_options'))
        print("   " + t('review_opt_1'))
        print("   " + t('review_opt_2'))
        print("   " + t('review_opt_3'))
        print("   " + t('review_opt_0'))
        
        choice_prompt = "\nPlease select (0-3): " if get_language() == 'en' else "\n请选择 (0-3): "
        choice = input(choice_prompt).strip()
        
        if choice == '1':
            # 批量审核
            self.data = self.reviewer.batch_review(self.data, min_confidence=0.6)
            
            # 保存审核后的数据
            save_prompt = "\nSave reviewed data? (Y/N): " if get_language() == 'en' else "\n是否保存审核后的数据? (Y/N): "
            save = input(save_prompt).strip().lower()
            if save == 'y':
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.join(DATA_EXPORTS_DIR, f'ai_tracker_data_reviewed_{timestamp}.json')
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': {
                            'timestamp': timestamp,
                            'total_items': len(self.data),
                            'reviewed': True
                        },
                        'data': self.data,
                        'trends': self.trends
                    }, f, ensure_ascii=False, indent=2)
                log.file(t('review_saved', file=os.path.basename(filename)))
            
            # 保存审核历史
            self.reviewer.save_review_history()
            
            # 显示审核摘要
            summary = self.reviewer.get_review_summary()
            print(f"\n" + t('review_summary'))
            print("   " + t('review_summary_total', count=summary['total']))
            for action, count in summary['actions'].items():
                print(f"   - {action}: {count}")
            
            # 询问是否重新生成分析和Web页面
            print("\n" + "="*60)
            regen_prompt = "\nRegenerate report and web page based on reviewed data? (Y/N): " if get_language() == 'en' else "\n是否基于审核后的数据重新生成报告和Web页面? (Y/N): "
            regenerate = input(regen_prompt).strip().lower()
            if regenerate == 'y':
                self._regenerate_after_review()
        
        elif choice == '2':
            # 自定义阈值
            try:
                threshold_prompt = "\nEnter confidence threshold (0.0-1.0, e.g., 0.7): " if get_language() == 'en' else "\n请输入置信度阈值 (0.0-1.0, 如 0.7): "
                threshold = float(input(threshold_prompt).strip())
                if 0 <= threshold <= 1:
                    self.data = self.reviewer.batch_review(self.data, min_confidence=threshold)
                else:
                    log.warning(t('review_threshold_error'))
            except ValueError:
                log.error(t('review_input_error'))
        
        elif choice == '3':
            # 仅查看列表
            print("\n" + "="*70)
            print(t('review_list_title'))
            print("="*70)
            cat_label = "Category" if get_language() == 'en' else "分类"
            conf_label = "Confidence" if get_language() == 'en' else "置信度"
            source_label = "Source" if get_language() == 'en' else "来源"
            for i, item in enumerate(review_items, 1):
                print(f"\n[{i}] {item.get('title', 'N/A')}")
                print(f"    {cat_label}: {item.get('content_type')} | {conf_label}: {item.get('confidence', 0):.1%}")
                print(f"    {source_label}: {item.get('source', 'N/A')}")
        
        elif choice == '0':
            return
        else:
            log.warning(t('invalid_choice'))
    
    def _regenerate_after_review(self):
        """审核后重新生成分析和Web页面"""
        print("\n" + "="*60)
        print(t('regenerate_title'))
        print("="*60)
        
        try:
            # 步骤1: 重新分析
            print("\n" + t('regenerate_step1'))
            self.trends = self.analyzer.analyze_trends(self.data)
            
            # 步骤2: 重新生成图表
            log.step(2, 3, t('regenerate_step2'))
            self.chart_files = self.visualizer.visualize_all(self.trends)
            
            # 步骤3: 重新生成Web页面
            log.step(3, 3, t('regenerate_step3'))
            web_file = self.web_publisher.generate_html_page(self.data, self.trends, self.chart_files)
            
            # 生成报告
            report = self.analyzer.generate_report(self.data, self.trends)
            
            # 保存（使用reviewed标记）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            data_file = os.path.join(DATA_EXPORTS_DIR, f'ai_tracker_data_reviewed_{timestamp}.json')
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'timestamp': timestamp,
                        'total_items': len(self.data),
                        'reviewed': True
                    },
                    'data': self.data,
                    'trends': self.trends
                }, f, ensure_ascii=False, indent=2)
            
            report_file = os.path.join(DATA_EXPORTS_DIR, f'ai_tracker_report_reviewed_{timestamp}.txt')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print("\n" + t('regenerate_done'))
            print("   " + t('regenerate_data', file=os.path.basename(data_file)))
            print("   " + t('regenerate_report', file=os.path.basename(report_file)))
            print("   " + t('regenerate_web', file=web_file))
            
            # 询问是否打开
            import webbrowser
            open_prompt = "\nOpen updated web page in browser? (Y/N): " if get_language() == 'en' else "\n是否在浏览器中打开更新后的Web页面? (Y/N): "
            choice = input(open_prompt).strip().lower()
            if choice == 'y':
                webbrowser.open(f'file://{os.path.abspath(web_file)}')
                log.success(t('regenerate_opened'))
        
        except Exception as e:
            print("\n" + t('regenerate_failed', error=str(e)))
    
    def _learning_feedback(self):
        """学习反馈分析"""
        print("\n" + "="*60)
        print(t('learning_title'))
        print("="*60)
        
        # 查找审核历史文件和审核后数据文件（都在 data/exports 目录）
        review_pattern = os.path.join(DATA_EXPORTS_DIR, 'review_history_*.json')
        review_files = sorted(glob.glob(review_pattern), reverse=True)
        # 从 exports 目录查找审核后的数据文件
        data_pattern = os.path.join(DATA_EXPORTS_DIR, 'ai_tracker_data_reviewed_*.json')
        data_files = sorted(glob.glob(data_pattern), reverse=True)
        
        if not review_files:
            print("\n" + t('learning_no_history'))
            log.info(t('learning_do_review'), emoji="💡")
            return
        
        if not data_files:
            print("\n" + t('learning_no_data'))
            log.info(t('learning_do_save'), emoji="💡")
            return
        
        print(f"\n" + t('learning_found'))
        print("   " + t('learning_history_count', count=len(review_files)))
        print("   " + t('learning_data_count', count=len(data_files)))
        
        # 显示最近的文件
        print(f"\n" + t('learning_recent'))
        for i, (review_file, data_file) in enumerate(zip(review_files[:3], data_files[:3]), 1):
            print(f"   {i}. {review_file}")
        
        print("\n" + t('learning_options'))
        print("   " + t('learning_opt_1'))
        print("   " + t('learning_opt_2'))
        print("   " + t('learning_opt_0'))
        
        choice_prompt = "\nPlease select (0-2): " if get_language() == 'en' else "\n请选择 (0-2): "
        choice = input(choice_prompt).strip()
        
        if choice == '1':
            # 分析最近一次
            review_file = review_files[0]
            data_file = data_files[0]
            
            print(f"\n" + t('learning_analyzing', file=review_file))
            
            try:
                report_file = create_feedback_loop(
                    review_file,
                    data_file,
                    self.classifier
                )
                
                print(f"\n" + t('learning_done'))
                log.file(t('learning_report', file=report_file))
                
                # 询问是否查看建议
                view_prompt = "\nView improvement suggestions? (Y/N): " if get_language() == 'en' else "\n是否查看改进建议? (Y/N): "
                view = input(view_prompt).strip().lower()
                if view == 'y':
                    self._show_improvement_suggestions(report_file)
                
            except Exception as e:
                print(f"\n" + t('learning_failed', error=str(e)))
        
        elif choice == '2':
            # 选择特定文件
            print("\n" + t('learning_files'))
            for i, file in enumerate(review_files, 1):
                print(f"   {i}. {file}")
            
            try:
                file_prompt = "\nSelect file number: " if get_language() == 'en' else "\n选择文件编号: "
                idx = int(input(file_prompt).strip()) - 1
                if 0 <= idx < len(review_files):
                    review_file = review_files[idx]
                    data_file = data_files[idx] if idx < len(data_files) else data_files[0]
                    
                    report_file = create_feedback_loop(
                        review_file,
                        data_file,
                        self.classifier
                    )
                    
                    print(f"\n" + t('learning_done') + " " + t('learning_report', file=report_file))
                else:
                    log.warning(t('invalid_choice'))
            except (ValueError, IndexError) as e:
                log.error(t('review_input_error') + f": {e}")
        
        elif choice == '0':
            return
        else:
            log.warning(t('invalid_choice'))
    
    def _show_improvement_suggestions(self, report_file: str):
        """显示改进建议"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            suggestions = report.get('improvement_suggestions', [])
            
            if not suggestions:
                print("\n" + t('learning_good'))
                return
            
            print("\n" + "="*70)
            log.info(t('learning_suggestions'), emoji="💡")
            print("="*70)
            
            for i, sug in enumerate(suggestions, 1):
                print(f"\n" + t('learning_sug_num', i=i))
                print("   " + t('learning_sug_type', type=sug.get('type')))
                
                if sug.get('category'):
                    print("   " + t('learning_sug_cat', cat=sug.get('category')))
                
                if sug.get('issue'):
                    print("   " + t('learning_sug_issue', issue=sug.get('issue')))
                
                if sug.get('suggestion'):
                    print("   " + t('learning_sug_suggestion', suggestion=sug.get('suggestion')))
                
                if sug.get('keywords'):
                    keywords_str = ', '.join(sug['keywords'])
                    print("   " + t('learning_sug_keywords', keywords=keywords_str))
                
                if sug.get('severity'):
                    print("   " + t('learning_sug_severity', severity=sug.get('severity')))
            
            print("\n" + "="*70)
            log.info(t('learning_note'), emoji="📝")
            print("   " + t('learning_note_1'))
            print("   " + t('learning_note_2'))
            print("="*70)
            
        except Exception as e:
            log.error(t('learning_read_error', error=str(e)))
    
    def _save_results(self, report: str, web_file: Optional[str] = None, timing_stats: Optional[Dict] = None):
        """保存结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 构建metadata
        metadata = {
            'timestamp': timestamp,
            'total_items': len(self.data),
            'classification_mode': self.classification_mode
        }
        
        # 添加耗时统计（如果有）
        if timing_stats:
            metadata['timing'] = timing_stats
        
        # 如果是LLM模式，记录模型信息
        if self.classification_mode == 'llm':
            metadata['llm_provider'] = self.llm_provider
            metadata['llm_model'] = self.llm_model
        
        # 保存JSON数据到 exports 目录
        data_file = os.path.join(DATA_EXPORTS_DIR, f'ai_tracker_data_{timestamp}.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': metadata,
                'data': self.data,
                'trends': self.trends
            }, f, ensure_ascii=False, indent=2)
        
        log.data(t('data_saved_to', file=os.path.basename(data_file)))
        
        # 保存文本报告到 exports 目录
        report_file = os.path.join(DATA_EXPORTS_DIR, f'ai_tracker_report_{timestamp}.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        log.file(t('report_saved_to', file=os.path.basename(report_file)))
        
        if web_file:
            log.web(t('web_saved_to', file=web_file))


def main():
    """主函数"""
    tracker = None
    try:
        # 检查是否为自动模式
        auto_mode = '--auto' in sys.argv
        
        # 语言设置：自动模式强制英文，交互模式让用户选择
        if auto_mode:
            set_language('en')
        else:
            select_language_interactive()
        
        tracker = AIWorldTracker(auto_mode=auto_mode)
        
        # 检查命令行参数
        if '--auto' in sys.argv:
            # 自动运行完整流程
            tracker.run_full_pipeline()
        elif '--help' in sys.argv:
            print(f"\n{t('app_title')} - {t('help_usage')}")
            print(f"\n{t('help_params')}")
            print(f"  --auto    {t('help_auto')}")
            print(f"  --help    {t('help_info')}")
            print(f"\n{t('help_no_params')}\n")
        else:
            # 交互式菜单
            tracker.show_menu()
    except KeyboardInterrupt:
        # 用户按 Ctrl+C 中断
        print("\n")
        try:
            log.warning(t('user_interrupted'))
        except:
            print("⚠️ 用户中断程序")
    except Exception as e:
        print(f"\n" + t('program_error', error=str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 确保资源被清理
        if tracker is not None:
            tracker.cleanup()


if __name__ == "__main__":
    main()
