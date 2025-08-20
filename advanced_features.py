import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import BUSINESS_TYPES

class AdvancedGameFeatures:
    def __init__(self):
        self.loan_rates = {
            'short_term': 0.05,  # 5% в день
            'medium_term': 0.03,  # 3% в день
            'long_term': 0.02     # 2% в день
        }
        
        self.investment_returns = {
            'conservative': 0.08,  # 8% в день
            'balanced': 0.12,      # 12% в день
            'aggressive': 0.18     # 18% в день
        }
        
        self.pvp_rewards = {
            'win': 0.1,      # 10% от капитала противника
            'loss': -0.05,   # -5% от собственного капитала
            'draw': 0.02     # 2% от ставки
        }
    
    def calculate_loan_eligibility(self, player: Dict, loan_amount: float) -> Dict:
        """Расчет возможности получения кредита"""
        credit_score = self._calculate_credit_score(player)
        max_loan = player['balance'] * 2  # Максимум 2x от баланса
        
        if loan_amount > max_loan:
            return {
                'eligible': False,
                'reason': f'Сумма кредита превышает максимально допустимую ({max_loan:,.0f} ₽)',
                'max_amount': max_loan
            }
        
        if credit_score < 500:
            return {
                'eligible': False,
                'reason': 'Недостаточный кредитный рейтинг',
                'credit_score': credit_score
            }
        
        return {
            'eligible': True,
            'credit_score': credit_score,
            'max_amount': max_loan,
            'interest_rate': self._get_interest_rate(credit_score)
        }
    
    def _calculate_credit_score(self, player: Dict) -> int:
        """Расчет кредитного рейтинга игрока"""
        score = 300  # Базовый рейтинг
        
        # Бонус за уровень
        score += player['level'] * 50
        
        # Бонус за опыт
        score += min(player['experience'] // 1000, 200)
        
        # Бонус за популярность
        score += int(player['popularity'] * 100)
        
        # Штраф за долги (если есть)
        if player.get('total_expenses', 0) > player.get('total_income', 0):
            score -= 100
        
        return max(score, 100)  # Минимум 100
    
    def _get_interest_rate(self, credit_score: int) -> float:
        """Получение процентной ставки по кредиту"""
        if credit_score >= 800:
            return 0.02  # 2% в день
        elif credit_score >= 600:
            return 0.03  # 3% в день
        elif credit_score >= 400:
            return 0.04  # 4% в день
        else:
            return 0.05  # 5% в день
    
    def process_loan(self, player: Dict, loan_amount: float, term_days: int) -> Dict:
        """Обработка выдачи кредита"""
        eligibility = self.calculate_loan_eligibility(player, loan_amount)
        
        if not eligibility['eligible']:
            return {
                'success': False,
                'message': eligibility['reason']
            }
        
        interest_rate = eligibility['interest_rate']
        total_interest = loan_amount * interest_rate * term_days
        total_payment = loan_amount + total_interest
        
        loan_info = {
            'amount': loan_amount,
            'interest_rate': interest_rate,
            'term_days': term_days,
            'total_interest': total_interest,
            'total_payment': total_payment,
            'issued_at': datetime.now(),
            'due_date': datetime.now() + timedelta(days=term_days)
        }
        
        return {
            'success': True,
            'message': f"Кредит одобрен! Сумма: {loan_amount:,.0f} ₽, ставка: {interest_rate*100:.1f}%/день",
            'loan_info': loan_info
        }
    
    def calculate_investment_potential(self, business: Dict, investment_amount: float) -> Dict:
        """Расчет потенциала инвестиций в бизнес"""
        business_info = BUSINESS_TYPES.get(business['business_type'], {})
        
        # Базовый потенциал роста
        growth_potential = business_info.get('growth_rate', 1.0)
        
        # Модификаторы от улучшений
        improvement_bonus = 1.0
        if business.get('improvements'):
            improvement_bonus += len(business['improvements']) * 0.1
        
        # Расчет ожидаемой доходности
        expected_return = growth_potential * improvement_bonus * 0.15  # 15% базовый доход
        
        # Риск инвестиций
        risk_level = business_info.get('risk_level', 'medium')
        risk_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.3,
            'very_high': 1.6
        }
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        # Финальный расчет
        final_return = expected_return * risk_multiplier
        
        return {
            'expected_return': final_return,
            'risk_level': risk_level,
            'growth_potential': growth_potential,
            'improvement_bonus': improvement_bonus,
            'recommended_investment': min(investment_amount, business['income'] * 5)
        }
    
    def process_investment(self, investor: Dict, business: Dict, investment_amount: float) -> Dict:
        """Обработка инвестиции в бизнес"""
        if investment_amount > investor['balance']:
            return {
                'success': False,
                'message': 'Недостаточно средств для инвестиции'
            }
        
        investment_potential = self.calculate_investment_potential(business, investment_amount)
        
        # Создаем инвестицию
        investment = {
            'investor_id': investor['user_id'],
            'business_id': business['id'],
            'amount': investment_amount,
            'expected_return': investment_potential['expected_return'],
            'risk_level': investment_potential['risk_level'],
            'invested_at': datetime.now(),
            'status': 'active'
        }
        
        return {
            'success': True,
            'message': f"Инвестиция размещена! Ожидаемая доходность: {investment_potential['expected_return']*100:.1f}%",
            'investment': investment,
            'potential': investment_potential
        }
    
    def calculate_pvp_outcome(self, player1: Dict, player2: Dict, bet_amount: float) -> Dict:
        """Расчет результата PvP сражения"""
        # Факторы, влияющие на исход
        player1_power = self._calculate_player_power(player1)
        player2_power = self._calculate_player_power(player2)
        
        # Добавляем независимую случайность и «удачу»
        rand1 = random.uniform(0.85, 1.15)
        rand2 = random.uniform(0.85, 1.15)
        luck1 = random.gauss(0, 0.05)
        luck2 = random.gauss(0, 0.05)
        
        # Финальная сила
        final_power1 = player1_power * rand1 * (1 + luck1)
        final_power2 = player2_power * rand2 * (1 + luck2)
        
        # Порог ничьей, если силы очень близки
        close_threshold = 0.02 * max(final_power1, final_power2, 1)
        if abs(final_power1 - final_power2) <= close_threshold:
            winner = None
            loser = None
            outcome = 'draw'
        elif final_power1 > final_power2:
            winner = player1
            loser = player2
            outcome = 'win'
        else:
            winner = player2
            loser = player1
            outcome = 'loss'
        
        # Расчет наград/штрафов
        if outcome == 'win':
            reward = bet_amount * self.pvp_rewards['win']
            penalty = -bet_amount * 0.05
        elif outcome == 'loss':
            reward = -bet_amount * self.pvp_rewards['loss']
            penalty = -bet_amount * 0.1
        else:  # draw
            reward = bet_amount * self.pvp_rewards['draw']
            penalty = 0
        
        return {
            'outcome': outcome,
            'winner': winner,
            'loser': loser,
            'player1_power': player1_power,
            'player2_power': player2_power,
            'final_power1': final_power1,
            'final_power2': final_power2,
            'reward': reward,
            'penalty': penalty,
            'bet_amount': bet_amount
        }
    
    def _calculate_player_power(self, player: Dict) -> float:
        """Расчет силы игрока для PvP"""
        power = 0
        
        # Базовая сила от уровня
        power += player['level'] * 100
        
        # Сила от опыта
        power += player['experience'] * 0.1
        
        # Сила от популярности
        power += player['popularity'] * 500
        
        # Сила от баланса (логарифмическая)
        power += min(player['balance'] / 1000, 1000)
        
        return power
    
    def generate_market_event(self, player_level: int = 1) -> Dict:
        """Генерация рыночного события"""
        events = [
            {
                'type': 'bull_market',
                'title': 'Бычий рынок! 📈',
                'description': 'Акции растут, все бизнесы получают бонус к доходу',
                'effect': 'income_multiplier',
                'value': 1.5,
                'duration': 3
            },
            {
                'type': 'bear_market',
                'title': 'Медвежий рынок 📉',
                'description': 'Рынок падает, доходы снижаются',
                'effect': 'income_multiplier',
                'value': 0.7,
                'duration': 2
            },
            {
                'type': 'inflation',
                'title': 'Инфляция 💸',
                'description': 'Цены растут, расходы увеличиваются',
                'effect': 'expense_multiplier',
                'value': 1.3,
                'duration': 4
            },
            {
                'type': 'economic_boom',
                'title': 'Экономический бум 🚀',
                'description': 'Экономика процветает, все показатели растут',
                'effect': 'all_multiplier',
                'value': 1.2,
                'duration': 5
            }
        ]
        
        event = random.choice(events)
        
        # Модифицируем событие в зависимости от уровня
        if player_level > 5:
            event['value'] *= 1.1  # Более сильный эффект для опытных игроков
        
        return event
    
    def calculate_business_synergy(self, business1: Dict, business2: Dict) -> Dict:
        """Расчет синергии между двумя бизнесами"""
        business_types = [business1['business_type'], business2['business_type']]
        
        # Определяем синергетические пары
        synergies = {
            ('coffee_shop', 'restaurant'): {
                'name': 'Ресторанный кластер',
                'bonus': 0.15,
                'description': 'Кофейня и ресторан дополняют друг друга'
            },
            ('farm', 'restaurant'): {
                'name': 'Ферма-ресторан',
                'bonus': 0.20,
                'description': 'Свежие продукты для ресторана'
            },
            ('factory', 'it_startup'): {
                'name': 'Технологическая синергия',
                'bonus': 0.25,
                'description': 'IT-решения для производства'
            },
            ('coffee_shop', 'farm'): {
                'name': 'Кофейная ферма',
                'bonus': 0.18,
                'description': 'Выращивание кофе для кофейни'
            }
        }
        
        # Проверяем синергию
        business_pair = tuple(sorted(business_types))
        if business_pair in synergies:
            synergy = synergies[business_pair]
            return {
                'has_synergy': True,
                'synergy_info': synergy,
                'income_bonus': synergy['bonus'],
                'expense_reduction': synergy['bonus'] * 0.5
            }
        
        return {
            'has_synergy': False,
            'synergy_info': None
        }
    
    def calculate_empire_value(self, player: Dict, businesses: List[Dict]) -> Dict:
        """Расчет общей стоимости бизнес-империи"""
        total_value = 0
        business_values = []
        
        for business in businesses:
            # Базовая стоимость бизнеса
            base_value = business['income'] * 30
            
            # Бонус за уровень
            level_bonus = 1 + (business['level'] - 1) * 0.1
            
            # Бонус за улучшения
            improvements_bonus = 1 + len(business.get('improvements', [])) * 0.05
            
            # Бонус за синергию с другими бизнесами
            synergy_bonus = 1.0
            for other_business in businesses:
                if other_business['id'] != business['id']:
                    synergy = self.calculate_business_synergy(business, other_business)
                    if synergy['has_synergy']:
                        synergy_bonus += 0.05
            
            business_value = base_value * level_bonus * improvements_bonus * synergy_bonus
            business_values.append({
                'business_id': business['id'],
                'name': business['name'],
                'value': business_value,
                'synergy_bonus': synergy_bonus
            })
            
            total_value += business_value
        
        # Бонус за размер империи
        empire_bonus = 1 + (len(businesses) - 1) * 0.05
        
        # Бонус за уровень игрока
        player_bonus = 1 + (player['level'] - 1) * 0.02
        
        final_value = total_value * empire_bonus * player_bonus
        
        return {
            'total_value': final_value,
            'business_values': business_values,
            'empire_bonus': empire_bonus,
            'player_bonus': player_bonus,
            'empire_size': len(businesses)
        } 