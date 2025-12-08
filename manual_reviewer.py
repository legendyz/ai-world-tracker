"""
人工审核模块 - Manual Review Module
用于人工审核和修正低置信度的内容分类

功能:
1. 筛选需要审核的内容（低置信度）
2. 交互式修改分类
3. 保存审核历史
4. 批量审核模式
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

# 数据存储目录
def _get_exports_dir():
    """获取导出目录路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    exports_dir = os.path.join(base_dir, 'data', 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    return exports_dir

DATA_EXPORTS_DIR = _get_exports_dir()


class ManualReviewer:
    """人工审核器"""
    
    def __init__(self):
        self.review_history = []
        self.valid_categories = ['research', 'developer', 'product', 'market', 'leader', 'community']
    
    def get_items_for_review(self, items: List[Dict], 
                            min_confidence: float = 0.6,
                            max_items: Optional[int] = None) -> List[Dict]:
        """
        获取需要审核的内容
        
        Args:
            items: 分类后的内容列表
            min_confidence: 置信度阈值（低于此值需要审核）
            max_items: 最多返回多少条（None表示全部）
            
        Returns:
            需要审核的内容列表
        """
        review_items = [
            item for item in items 
            if item.get('confidence', 1.0) < min_confidence or item.get('needs_review', False)
        ]
        
        if max_items:
            review_items = review_items[:max_items]
        
        return review_items
    
    def review_item(self, item: Dict, show_details: bool = True) -> Dict:
        """
        交互式审核单个内容
        
        Args:
            item: 待审核的内容项
            show_details: 是否显示详细信息
            
        Returns:
            审核后的内容项
        """
        print("\n" + "="*70)
        print("📝 内容审核")
        print("="*70)
        
        # 保存原始信息用于学习反馈
        original_category = item.get('content_type')
        original_confidence = item.get('confidence', 0)
        
        # 显示内容信息
        print(f"\n标题: {item.get('title', 'N/A')}")
        print(f"来源: {item.get('source', 'N/A')}")
        
        # 显示链接（如果有）
        link = item.get('link') or item.get('url')
        if link:
            print(f"🔗 链接: {link}")
        
        if show_details:
            summary = item.get('summary', item.get('description', 'N/A'))
            if summary != 'N/A' and len(summary) > 200:
                summary = summary[:200] + "..."
            print(f"摘要: {summary}")
        
        print(f"\n当前分类: {item.get('content_type', 'N/A')}")
        print(f"置信度: {item.get('confidence', 0):.1%}")
        
        if item.get('secondary_labels'):
            secondary_labels_str = ', '.join(item['secondary_labels'])
            print(f"次要标签: {secondary_labels_str}")
        
        tech_categories_str = ', '.join(item.get('tech_categories', ['N/A']))
        print(f"技术领域: {tech_categories_str}")
        print(f"地区: {item.get('region', 'N/A')}")
        
        # 显示操作选项
        print("\n" + "-"*70)
        print("操作选项:")
        print("  1. 保持当前分类")
        print("  2. 修改分类")
        print("  3. 修改技术领域")
        print("  4. 修改地区")
        print("  5. 标记为垃圾内容（删除）")
        if link:
            print("  6. 在浏览器中打开链接")
        print("  0. 跳过（稍后处理）")
        print("-"*70)
        
        while True:
            choice = input("\n请选择操作 (0-6): ").strip()
            
            if choice == '0':
                print("⏭️  已跳过")
                return item
            
            elif choice == '1':
                # 保持分类，但标记已审核
                item['manually_reviewed'] = True
                item['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                item['needs_review'] = False
                self._add_to_history(item, '保持分类')
                print("✅ 已确认分类")
                return item
            
            elif choice == '2':
                # 修改分类
                new_category = self._select_category()
                if new_category:
                    old_category = item.get('content_type')
                    item['content_type'] = new_category
                    item['confidence'] = 1.0  # 人工审核后置信度为100%
                    item['manually_reviewed'] = True
                    item['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    item['needs_review'] = False
                    item['original_category'] = original_category  # 保存原始分类用于学习
                    item['original_confidence'] = original_confidence  # 保存原始置信度
                    self._add_to_history(item, f'修改分类: {old_category} → {new_category}')
                    print(f"✅ 分类已更新为: {new_category}")
                    return item
            
            elif choice == '3':
                # 修改技术领域
                new_tech = self._input_tech_categories()
                if new_tech:
                    item['tech_categories'] = new_tech
                    item['manually_reviewed'] = True
                    item['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._add_to_history(item, f'修改技术领域: {new_tech}')
                    print(f"✅ 技术领域已更新")
                    return item
            
            elif choice == '4':
                # 修改地区
                new_region = self._select_region()
                if new_region:
                    item['region'] = new_region
                    item['manually_reviewed'] = True
                    item['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._add_to_history(item, f'修改地区: {new_region}')
                    print(f"✅ 地区已更新为: {new_region}")
                    return item
            
            elif choice == '5':
                # 标记为垃圾内容
                confirm = input("⚠️  确定要删除此内容吗? (Y/N): ").strip().lower()
                if confirm == 'y':
                    item['is_spam'] = True
                    item['manually_reviewed'] = True
                    item['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._add_to_history(item, '标记为垃圾')
                    print("🗑️  已标记为垃圾内容")
                    return item
            
            elif choice == '6' and link:
                # 在浏览器中打开链接
                import webbrowser
                try:
                    webbrowser.open(link)
                    print(f"🌐 已在浏览器中打开链接")
                    print("   查看完内容后，继续选择操作...")
                    # 不返回，继续显示选项让用户做决定
                except Exception as e:
                    print(f"❌ 无法打开链接: {e}")
            
            else:
                print("❌ 无效选择，请重新输入")
    
    def batch_review(self, items: List[Dict], 
                    min_confidence: float = 0.6,
                    auto_skip_high: bool = True) -> List[Dict]:
        """
        批量审核模式
        
        Args:
            items: 所有内容列表
            min_confidence: 置信度阈值
            auto_skip_high: 是否自动跳过高置信度内容
            
        Returns:
            审核后的内容列表
        """
        review_items = self.get_items_for_review(items, min_confidence)
        
        if not review_items:
            print("\n✅ 没有需要审核的内容！")
            return items
        
        print(f"\n📋 共有 {len(review_items)} 条内容需要审核")
        print(f"总内容数: {len(items)}")
        print(f"审核比例: {len(review_items)/len(items):.1%}")
        
        start = input("\n是否开始批量审核? (Y/N): ").strip().lower()
        if start != 'y':
            print("❌ 已取消审核")
            return items
        
        reviewed_count = 0
        modified_count = 0
        spam_count = 0
        
        for i, item in enumerate(review_items, 1):
            print(f"\n[{i}/{len(review_items)}]")
            
            original_category = item.get('content_type')
            reviewed_item = self.review_item(item, show_details=True)
            
            if reviewed_item.get('manually_reviewed'):
                reviewed_count += 1
                
                if reviewed_item.get('is_spam'):
                    spam_count += 1
                elif reviewed_item.get('content_type') != original_category:
                    modified_count += 1
            
            # 更新原列表中的项
            item_index = items.index(item)
            items[item_index] = reviewed_item
            
            # 每5条询问是否继续
            if i % 5 == 0 and i < len(review_items):
                cont = input("\n继续审核? (Y/N/Q-退出): ").strip().lower()
                if cont == 'n' or cont == 'q':
                    print(f"\n⏸️  审核暂停，已完成 {i}/{len(review_items)} 条")
                    break
        
        # 移除垃圾内容
        if spam_count > 0:
            items = [item for item in items if not item.get('is_spam', False)]
        
        # 显示统计
        print("\n" + "="*70)
        print("📊 审核统计")
        print("="*70)
        print(f"审核数量: {reviewed_count}/{len(review_items)}")
        print(f"修改分类: {modified_count} 条")
        print(f"删除垃圾: {spam_count} 条")
        print(f"剩余内容: {len(items)} 条")
        
        return items
    
    def _select_category(self) -> Optional[str]:
        """选择内容类型"""
        print("\n可选分类:")
        for i, cat in enumerate(self.valid_categories, 1):
            print(f"  {i}. {cat}")
        
        choice = input("\n请选择分类 (1-6, 0=取消): ").strip()
        
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(self.valid_categories):
                return self.valid_categories[idx - 1]
        except ValueError:
            pass
        
        print("❌ 无效选择")
        return None
    
    def _select_region(self) -> Optional[str]:
        """选择地区"""
        regions = ['China', 'USA', 'Europe', 'Global']
        
        print("\n可选地区:")
        for i, region in enumerate(regions, 1):
            print(f"  {i}. {region}")
        
        choice = input("\n请选择地区 (1-4, 0=取消): ").strip()
        
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(regions):
                return regions[idx - 1]
        except ValueError:
            pass
        
        print("❌ 无效选择")
        return None
    
    def _input_tech_categories(self) -> Optional[List[str]]:
        """输入技术领域"""
        common_techs = [
            'NLP', 'Computer Vision', 'Reinforcement Learning', 
            'Generative AI', 'MLOps', 'AI Ethics', 'General AI'
        ]
        
        print("\n常用技术领域:")
        for i, tech in enumerate(common_techs, 1):
            print(f"  {i}. {tech}")
        
        print("\n可以输入编号（用逗号分隔，如: 1,4）或直接输入名称")
        choice = input("请输入: ").strip()
        
        if not choice:
            return None
        
        # 尝试解析编号
        if ',' in choice or choice.isdigit():
            try:
                indices = [int(x.strip()) for x in choice.split(',')]
                techs = [common_techs[i-1] for i in indices if 1 <= i <= len(common_techs)]
                return techs if techs else None
            except (ValueError, IndexError):
                pass
        
        # 直接使用输入的名称
        return [x.strip() for x in choice.split(',')]
    
    def _add_to_history(self, item: Dict, action: str):
        """添加到审核历史"""
        self.review_history.append({
            'title': item.get('title', 'N/A'),
            'action': action,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def save_review_history(self, filename: str = None):
        """保存审核历史到 data/exports 目录"""
        if not filename:
            filename = f"review_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 确保保存到 data/exports 目录
        if not os.path.dirname(filename):
            filename = os.path.join(DATA_EXPORTS_DIR, filename)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.review_history, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 审核历史已保存到: {filename}")
    
    def get_review_summary(self) -> Dict:
        """获取审核摘要"""
        if not self.review_history:
            return {'total': 0, 'actions': {}}
        
        actions = {}
        for record in self.review_history:
            action = record['action'].split(':')[0]  # 获取动作类型
            actions[action] = actions.get(action, 0) + 1
        
        return {
            'total': len(self.review_history),
            'actions': actions
        }


if __name__ == "__main__":
    # 测试示例
    reviewer = ManualReviewer()
    
    test_items = [
        {
            'title': 'Test Article 1',
            'summary': 'This is a test article about AI',
            'content_type': 'product',
            'confidence': 0.45,
            'needs_review': True,
            'tech_categories': ['Generative AI'],
            'region': 'USA',
            'source': 'Test Source'
        },
        {
            'title': 'Test Article 2',
            'summary': 'Another test about machine learning',
            'content_type': 'research',
            'confidence': 0.85,
            'needs_review': False,
            'tech_categories': ['NLP'],
            'region': 'China',
            'source': 'Test Source 2'
        }
    ]
    
    print("🧪 人工审核模块测试")
    print("="*70)
    
    review_items = reviewer.get_items_for_review(test_items)
    print(f"\n需要审核的内容: {len(review_items)} 条")
    
    for item in review_items:
        print(f"\n- {item['title']} (置信度: {item['confidence']:.1%})")
    
    print("\n提示: 在实际使用中，调用 batch_review() 进行交互式审核")
