import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import BUSINESS_TYPES, RANDOM_EVENTS, IMPROVEMENTS, DAILY_INCOME_MULTIPLIER, DAILY_EXPENSE_MULTIPLIER

class GameLogic:
    def __init__(self):
        self.random_events = RANDOM_EVENTS
        self.improvements = IMPROVEMENTS
        self.business_types = BUSINESS_TYPES
    
    def calculate_daily_income(self, business: Dict, improvements: List[str] = None) -> float:
        """Расчет дневного дохода бизнеса с учетом улучшений"""
        base_income = business['income']
        total_boost = 1.0
        
        if improvements:
            for improvement in improvements:
                if improvement in self.improvements:
                    if 'income_boost' in self.improvements[improvement]:
                        total_boost += self.improvements[improvement]['income_boost']
        
        return base_income * total_boost * DAILY_INCOME_MULTIPLIER
    
    def calculate_daily_expenses(self, business: Dict, improvements: List[str] = None) -> float:
        """Расчет дневных расходов бизнеса с учетом улучшений"""
        base_expenses = business['expenses']
        total_boost = 1.0
        
        if improvements:
            for improvement in improvements:
                if improvement in self.improvements:
                    if 'expense_boost' in self.improvements[improvement]:
                        total_boost += self.improvements[improvement]['expense_boost']
        
        # База расходов с учетом множителей
        boosted = base_expenses * total_boost * DAILY_EXPENSE_MULTIPLIER
        # Добавляем фиксированные расходы на персонал, если есть
        staff_salary = float(business.get('staff_salary', 0.0) or 0.0)
        return boosted + staff_salary
    
    def get_random_event(self, player_level: int = 1) -> Optional[Dict]:
        """Получение случайного события"""
        if random.random() < 0.3:  # 30% шанс события
            event = random.choice(self.random_events)
            
            # Модифицируем событие в зависимости от уровня игрока
            modified_event = event.copy()
            if 'income_bonus' in event:
                modified_event['income_bonus'] = int(event['income_bonus'] * (1 + player_level * 0.1))
            if 'expense_penalty' in event:
                modified_event['expense_penalty'] = int(event['expense_penalty'] * (1 + player_level * 0.1))
            
            return modified_event
        
        return None
    
    def apply_random_event(self, player: Dict, business: Dict, event: Dict) -> Dict:
        """Применение случайного события к игроку и бизнесу"""
        result = {
            'message': f"🎲 *{event['title']}*\n{event['description']}",
            'income_change': 0,
            'expense_change': 0,
            'popularity_change': 0
        }
        
        if event['type'] == 'positive':
            if 'income_bonus' in event:
                result['income_change'] = event['income_bonus']
                result['message'] += f"\n💰 +{event['income_bonus']} ₽"
            
            if 'popularity_bonus' in event:
                result['popularity_change'] = event['popularity_bonus']
                result['message'] += f"\n⭐ +{int(event['popularity_bonus'] * 100)}% популярности"
        
        elif event['type'] == 'negative':
            if 'expense_penalty' in event:
                result['expense_change'] = -event['expense_penalty']
                result['message'] += f"\n💸 -{event['expense_penalty']} ₽"
            
            if 'popularity_penalty' in event:
                result['popularity_change'] = event['popularity_penalty']
                result['message'] += f"\n📉 {int(event['popularity_penalty'] * 100)}% популярности"
            
            if 'income_multiplier' in event:
                # Временно снижаем доход
                result['income_change'] = business['income'] * (event['income_multiplier'] - 1)
                result['message'] += f"\n📊 Доход временно снижен"
        
        return result
    
    def can_afford_improvement(self, player_balance: float, improvement_type: str) -> bool:
        """Проверка, может ли игрок позволить себе улучшение"""
        if improvement_type in self.improvements:
            return player_balance >= self.improvements[improvement_type]['cost']
        return False
    
    def apply_improvement(self, business: Dict, improvement_type: str) -> Dict:
        """Применение улучшения к бизнесу"""
        if improvement_type not in self.improvements:
            return {'success': False, 'message': 'Неизвестное улучшение'}
        
        improvement = self.improvements[improvement_type]
        current_improvements = business.get('improvements', [])
        
        if improvement_type in current_improvements:
            return {'success': False, 'message': 'Улучшение уже применено'}
        
        # Применяем улучшение
        new_improvements = current_improvements + [improvement_type]
        
        # Пересчитываем доход и расходы
        new_income = business['income']
        new_expenses = business['expenses']
        
        if 'income_boost' in improvement:
            new_income *= (1 + improvement['income_boost'])
        
        if 'expense_boost' in improvement:
            new_expenses *= (1 + improvement['expense_boost'])
        
        return {
            'success': True,
            'message': f"✅ {improvement['name']} применено!\n{improvement['description']}",
            'new_income': new_income,
            'new_expenses': new_expenses,
            'new_improvements': new_improvements,
            'cost': improvement['cost']
        }
    
    def calculate_business_value(self, business: Dict) -> float:
        """Расчет стоимости бизнеса для продажи"""
        base_value = business['income'] * 30  # 30 дней дохода
        
        # Бонус за уровень
        level_bonus = 1 + (business['level'] - 1) * 0.1
        
        # Бонус за улучшения
        improvements_bonus = 1 + len(business.get('improvements', [])) * 0.05
        
        return base_value * level_bonus * improvements_bonus
    
    def calculate_level_up_experience(self, current_level: int) -> int:
        """Расчет опыта, необходимого для повышения уровня"""
        return current_level * 1000
    
    def can_level_up(self, current_experience: int, current_level: int) -> bool:
        """Проверка, может ли игрок повысить уровень"""
        required_exp = self.calculate_level_up_experience(current_level)
        return current_experience >= required_exp
    
    def level_up_player(self, player: Dict) -> Dict:
        """Повышение уровня игрока"""
        if not self.can_level_up(player['experience'], player['level']):
            return {'success': False, 'message': 'Недостаточно опыта для повышения уровня'}
        
        new_level = player['level'] + 1
        remaining_exp = player['experience'] - self.calculate_level_up_experience(player['level'])
        
        # Бонусы за новый уровень
        level_bonuses = {
            'income_multiplier': 1 + (new_level - 1) * 0.05,
            'popularity_bonus': 0.1,
            'balance_bonus': new_level * 1000
        }
        
        return {
            'success': True,
            'message': f"🎉 Поздравляем! Вы достигли {new_level} уровня!\n💰 +{level_bonuses['balance_bonus']} ₽ бонус\n⭐ +{int(level_bonuses['popularity_bonus'] * 100)}% популярности",
            'new_level': new_level,
            'remaining_experience': remaining_exp,
            'bonuses': level_bonuses
        }
    
    def calculate_competition_bonus(self, player_popularity: float, competitor_popularity: float) -> float:
        """Расчет бонуса в конкурентной борьбе"""
        if player_popularity > competitor_popularity:
            return 1 + (player_popularity - competitor_popularity) * 0.1
        elif player_popularity < competitor_popularity:
            return 1 - (competitor_popularity - player_popularity) * 0.05
        else:
            return 1.0
    
    def generate_business_name(self, business_type: str) -> str:
        """Генерация названия для бизнеса"""
        business_info = self.business_types.get(business_type, {})
        business_name = business_info.get('name', 'Бизнес')
        
        # Простые названия для разных типов бизнеса
        names = {
            'coffee_shop': ['Bean Master', 'Coffee Corner', 'Aroma Cafe', 'Brew House'],
            'restaurant': ['Gourmet Palace', 'Taste Haven', 'Culinary Delight', 'Flavor Fusion'],
            'factory': ['Industrial Power', 'Production Pro', 'Manufacturing Hub', 'Factory Force'],
            'it_startup': ['Tech Vision', 'Digital Dreams', 'Innovation Lab', 'Future Tech'],
            'farm': ['Green Fields', 'Nature\'s Bounty', 'Organic Harvest', 'Farm Fresh']
        }
        
        if business_type in names:
            return f"{random.choice(names[business_type])}"
        else:
            return f"{business_name} #{random.randint(1000, 9999)}"
    
    def calculate_daily_progress(self, player: Dict, businesses: List[Dict]) -> Dict:
        """Расчет дневного прогресса игрока"""
        total_income = 0
        total_expenses = 0
        total_experience = 0
        
        for business in businesses:
            daily_income = self.calculate_daily_income(business, business.get('improvements', []))
            daily_expenses = self.calculate_daily_expenses(business, business.get('improvements', []))
            
            total_income += daily_income
            total_expenses += daily_expenses
            
            # Опыт за активность
            total_experience += int(daily_income * 0.1)
        
        net_income = total_income - total_expenses
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'experience_gained': total_experience
        }
    
    def check_achievements(self, player: Dict, businesses: List[Dict]) -> List[Dict]:
        """Проверка достижений игрока"""
        achievements = []
        
        # Достижения по балансу
        if player['balance'] >= 1000000 and player['level'] >= 5:
            achievements.append({
                'type': 'balance',
                'title': 'Миллионер',
                'description': 'Достиг баланса в 1,000,000 ₽'
            })
        
        if player['balance'] >= 100000:
            achievements.append({
                'type': 'balance',
                'title': 'Сотня тысяч',
                'description': 'Достиг баланса в 100,000 ₽'
            })
        
        # Достижения по количеству бизнесов
        if len(businesses) >= 5:
            achievements.append({
                'type': 'businesses',
                'title': 'Бизнес-магнат',
                'description': 'Владеете 5+ бизнесами'
            })
        
        if len(businesses) >= 10:
            achievements.append({
                'type': 'businesses',
                'title': 'Империя',
                'description': 'Владеете 10+ бизнесами'
            })
        
        # Достижения по уровню
        if player['level'] >= 10:
            achievements.append({
                'type': 'level',
                'title': 'Эксперт',
                'description': 'Достигли 10 уровня'
            })
        
        return achievements 