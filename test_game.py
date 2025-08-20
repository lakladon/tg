#!/usr/bin/env python3
"""
Тестовый файл для демонстрации работы игровой логики
Запустите этот файл для проверки основных функций игры
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BUSINESS_TYPES, IMPROVEMENTS, RANDOM_EVENTS
from game_logic import GameLogic
from advanced_features import AdvancedGameFeatures
from database import GameDatabase

def test_basic_game_logic():
    """Тестирование базовой игровой логики"""
    print("🧪 Тестирование базовой игровой логики...")
    
    game_logic = GameLogic()
    
    # Создаем тестового игрока
    test_player = {
        'user_id': 12345,
        'username': 'test_user',
        'first_name': 'Test',
        'balance': 50000,
        'level': 3,
        'experience': 2500,
        'popularity': 1.2
    }
    
    # Создаем тестовый бизнес
    test_business = {
        'id': 1,
        'user_id': 12345,
        'business_type': 'coffee_shop',
        'name': 'Test Coffee',
        'income': 1000,
        'expenses': 500,
        'level': 2,
        'improvements': ['equipment']
    }
    
    print(f"📊 Тестовый игрок: {test_player['first_name']} (Уровень {test_player['level']})")
    print(f"🏢 Тестовый бизнес: {test_business['name']} ({BUSINESS_TYPES[test_business['business_type']]['emoji']})")
    
    # Тестируем расчеты доходов
    daily_income = game_logic.calculate_daily_income(test_business, test_business['improvements'])
    daily_expenses = game_logic.calculate_daily_expenses(test_business, test_business['improvements'])
    net_income = daily_income - daily_expenses
    
    print(f"\n💰 Базовый доход: {test_business['income']:,} ₽/день")
    print(f"🛠 С улучшениями: {daily_income:,.0f} ₽/день")
    print(f"💸 Расходы: {daily_expenses:,.0f} ₽/день")
    print(f"💵 Чистая прибыль: {net_income:,.0f} ₽/день")
    
    # Тестируем случайные события
    print(f"\n🎲 Тестирование случайных событий...")
    for i in range(3):
        event = game_logic.get_random_event(test_player['level'])
        if event:
            print(f"  {i+1}. {event['title']} - {event['description']}")
        else:
            print(f"  {i+1}. Событий не произошло")
    
    # Тестируем улучшения
    print(f"\n🛠 Тестирование улучшений...")
    for improvement_id, improvement_info in IMPROVEMENTS.items():
        can_afford = game_logic.can_afford_improvement(test_player['balance'], improvement_id)
        status = "✅ Доступно" if can_afford else "❌ Недоступно"
        print(f"  {improvement_info['name']}: {improvement_info['cost']:,} ₽ - {status}")
    
    # Тестируем повышение уровня
    print(f"\n⭐ Тестирование системы уровней...")
    current_exp = test_player['experience']
    current_level = test_player['level']
    required_exp = game_logic.calculate_level_up_experience(current_level)
    
    print(f"  Текущий опыт: {current_exp:,}")
    print(f"  Требуется для {current_level + 1} уровня: {required_exp:,}")
    
    if game_logic.can_level_up(current_exp, current_level):
        level_up_result = game_logic.level_up_player(test_player)
        print(f"  🎉 {level_up_result['message']}")
    else:
        print(f"  📊 Недостаточно опыта для повышения уровня")
    
    print("\n" + "="*50)

def test_advanced_features():
    """Тестирование расширенных функций"""
    print("🚀 Тестирование расширенных функций...")
    
    advanced = AdvancedGameFeatures()
    
    # Тестовый игрок
    test_player = {
        'user_id': 12345,
        'username': 'test_user',
        'first_name': 'Test',
        'balance': 100000,
        'level': 5,
        'experience': 5000,
        'popularity': 1.5,
        'total_income': 15000,
        'total_expenses': 8000
    }
    
    # Тестируем кредитную систему
    print(f"\n🏦 Тестирование кредитной системы...")
    loan_amount = 50000
    eligibility = advanced.calculate_loan_eligibility(test_player, loan_amount)
    
    print(f"  Запрос кредита: {loan_amount:,} ₽")
    print(f"  Кредитный рейтинг: {eligibility['credit_score']}")
    print(f"  Статус: {'✅ Одобрен' if eligibility['eligible'] else '❌ Отклонен'}")
    
    if eligibility['eligible']:
        print(f"  Максимальная сумма: {eligibility['max_amount']:,} ₽")
        print(f"  Процентная ставка: {eligibility['interest_rate']*100:.1f}%/день")
        
        # Обрабатываем кредит
        loan_result = advanced.process_loan(test_player, loan_amount, 7)
        print(f"  📋 {loan_result['message']}")
    
    # Тестируем инвестиции
    print(f"\n💼 Тестирование инвестиций...")
    test_business = {
        'id': 1,
        'business_type': 'it_startup',
        'income': 3000,
        'expenses': 800,
        'improvements': ['equipment', 'staff']
    }
    
    investment_amount = 20000
    investment_potential = advanced.calculate_investment_potential(test_business, investment_amount)
    
    print(f"  Инвестиция в {BUSINESS_TYPES[test_business['business_type']]['emoji']} IT-стартап")
    print(f"  Сумма: {investment_amount:,} ₽")
    print(f"  Ожидаемая доходность: {investment_potential['expected_return']*100:.1f}%")
    print(f"  Уровень риска: {investment_potential['risk_level']}")
    
    # Тестируем PvP
    print(f"\n⚔️ Тестирование PvP системы...")
    player1 = test_player.copy()
    player2 = {
        'user_id': 67890,
        'username': 'opponent',
        'first_name': 'Opponent',
        'balance': 80000,
        'level': 4,
        'experience': 4000,
        'popularity': 1.1
    }
    
    bet_amount = 10000
    pvp_result = advanced.calculate_pvp_outcome(player1, player2, bet_amount)
    
    print(f"  {player1['first_name']} vs {player2['first_name']}")
    print(f"  Ставка: {bet_amount:,} ₽")
    print(f"  Сила {player1['first_name']}: {pvp_result['player1_power']:.0f}")
    print(f"  Сила {player2['first_name']}: {pvp_result['player2_power']:.0f}")
    print(f"  Результат: {pvp_result['outcome'].upper()}")
    
    if pvp_result['winner']:
        print(f"  🏆 Победитель: {pvp_result['winner']['first_name']}")
        print(f"  💰 Награда: {pvp_result['reward']:,.0f} ₽")
    
    # Тестируем рыночные события
    print(f"\n📈 Тестирование рыночных событий...")
    for i in range(2):
        market_event = advanced.generate_market_event(test_player['level'])
        print(f"  {i+1}. {market_event['title']}")
        print(f"     {market_event['description']}")
        print(f"     Эффект: {market_event['effect']}, значение: {market_event['value']}")
    
    # Тестируем синергию бизнесов
    print(f"\n🔗 Тестирование синергии бизнесов...")
    business1 = {'business_type': 'coffee_shop', 'id': 1}
    business2 = {'business_type': 'restaurant', 'id': 2}
    
    synergy = advanced.calculate_business_synergy(business1, business2)
    if synergy['has_synergy']:
        print(f"  ✅ {synergy['synergy_info']['name']}")
        print(f"     {synergy['synergy_info']['description']}")
        print(f"     Бонус к доходу: +{synergy['income_bonus']*100:.0f}%")
        print(f"     Снижение расходов: -{synergy['expense_reduction']*100:.0f}%")
    else:
        print(f"  ❌ Синергии не обнаружено")
    
    print("\n" + "="*50)

def test_business_types():
    """Демонстрация типов бизнеса"""
    print("🏢 Демонстрация типов бизнеса...")
    
    for business_id, business_info in BUSINESS_TYPES.items():
        print(f"\n{business_info['emoji']} {business_info['name']}")
        print(f"  📝 {business_info['description']}")
        print(f"  💰 Базовый доход: {business_info['base_income']:,} ₽/день")
        print(f"  💸 Базовые расходы: {business_info['base_expenses']:,} ₽/день")
        print(f"  📈 Скорость роста: {business_info['growth_rate']}x")
        print(f"  ⚠️ Уровень риска: {business_info['risk_level']}")
    
    print("\n" + "="*50)

def test_improvements():
    """Демонстрация системы улучшений"""
    print("🛠 Демонстрация системы улучшений...")
    
    for improvement_id, improvement_info in IMPROVEMENTS.items():
        print(f"\n{improvement_info['name']}")
        print(f"  💰 Стоимость: {improvement_info['cost']:,} ₽")
        print(f"  📝 {improvement_info['description']}")
        
        if 'income_boost' in improvement_info:
            print(f"  📈 Бонус к доходу: +{improvement_info['income_boost']*100:.0f}%")
        if 'expense_boost' in improvement_info:
            print(f"  💸 Увеличение расходов: +{improvement_info['expense_boost']*100:.0f}%")
        if 'popularity_boost' in improvement_info:
            print(f"  ⭐ Бонус к популярности: +{improvement_info['popularity_boost']*100:.0f}%")
    
    print("\n" + "="*50)

def test_random_events():
    """Демонстрация случайных событий"""
    print("🎲 Демонстрация случайных событий...")
    
    for i, event in enumerate(RANDOM_EVENTS, 1):
        emoji = "✅" if event['type'] == 'positive' else "❌"
        print(f"\n{i}. {emoji} {event['title']}")
        print(f"   📝 {event['description']}")
        
        if 'income_bonus' in event:
            print(f"   💰 Бонус к доходу: +{event['income_bonus']:,} ₽")
        if 'expense_penalty' in event:
            print(f"   💸 Штраф: -{event['expense_penalty']:,} ₽")
        if 'popularity_bonus' in event:
            print(f"   ⭐ Бонус к популярности: +{event['popularity_bonus']*100:.0f}%")
        if 'popularity_penalty' in event:
            print(f"   📉 Штраф к популярности: {event['popularity_penalty']*100:.0f}%")
    
    print("\n" + "="*50)

def main():
    """Главная функция тестирования"""
    print("🎮 ТЕСТИРОВАНИЕ БИЗНЕС-ИМПЕРИИ")
    print("="*50)
    
    try:
        # Тестируем основные функции
        test_basic_game_logic()
        test_advanced_features()
        test_business_types()
        test_improvements()
        test_random_events()
        
        print("\n🎉 Все тесты завершены успешно!")
        print("\n📋 Для запуска бота:")
        print("1. Создайте файл .env с вашим BOT_TOKEN")
        print("2. Установите зависимости: pip install -r requirements.txt")
        print("3. Запустите бота: python bot.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 