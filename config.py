import os

try:
	from dotenv import load_dotenv
except Exception:
	def load_dotenv(*args, **kwargs):
		return False

load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')
# Админы (список user_id через запятую)
ADMIN_IDS = []
_admins_env = os.getenv('ADMIN_IDS', '').strip()
if _admins_env:
    try:
        ADMIN_IDS = [int(x) for x in _admins_env.replace(' ', '').split(',') if x]
    except Exception:
        ADMIN_IDS = []

# Игровые параметры
STARTING_BALANCE = 10000  # Начальный баланс игрока
DAILY_INCOME_MULTIPLIER = 0.1  # Множитель дневного дохода
DAILY_EXPENSE_MULTIPLIER = 0.05  # Множитель дневных расходов

# Типы бизнесов
BUSINESS_TYPES = {
    'coffee_shop': {
        'name': 'Кофейня',
        'emoji': '☕',
        'base_income': 1000,
        'base_expenses': 500,
        'growth_rate': 1.2,
        'risk_level': 'low',
        'description': 'Уютная кофейня в центре города'
    },
    'restaurant': {
        'name': 'Ресторан',
        'emoji': '🍽',
        'base_income': 2000,
        'base_expenses': 1200,
        'growth_rate': 1.3,
        'risk_level': 'medium',
        'description': 'Элитный ресторан с изысканной кухней'
    },
    'factory': {
        'name': 'Фабрика',
        'emoji': '🏭',
        'base_income': 5000,
        'base_expenses': 3000,
        'growth_rate': 1.5,
        'risk_level': 'high',
        'description': 'Производственное предприятие'
    },
    'it_startup': {
        'name': 'IT-стартап',
        'emoji': '💻',
        'base_income': 3000,
        'base_expenses': 800,
        'growth_rate': 2.0,
        'risk_level': 'very_high',
        'description': 'Инновационная технологическая компания'
    },
    'farm': {
        'name': 'Ферма',
        'emoji': '🚜',
        'base_income': 800,
        'base_expenses': 300,
        'growth_rate': 1.1,
        'risk_level': 'low',
        'description': 'Сельскохозяйственное хозяйство'
    }
}

# Случайные события
RANDOM_EVENTS = [
    {
        'type': 'positive',
        'title': 'Блогер посетил ваш бизнес!',
        'description': '+3,000 ₽ и рост популярности',
        'income_bonus': 3000,
        'popularity_bonus': 0.2
    },
    {
        'type': 'positive',
        'title': 'Выгодный контракт!',
        'description': '+5,000 ₽ от крупного клиента',
        'income_bonus': 5000,
        'popularity_bonus': 0.1
    },
    {
        'type': 'negative',
        'title': 'Поломка оборудования',
        'description': '-2,000 ₽ на ремонт',
        'expense_penalty': 2000,
        'popularity_penalty': -0.1
    },
    {
        'type': 'negative',
        'title': 'Кризис спроса',
        'description': 'Доход снижен на 20%',
        'income_multiplier': 0.8,
        'duration': 3
    }
]

# Улучшения для бизнеса
IMPROVEMENTS = {
    'equipment': {
        'name': 'Новое оборудование',
        'cost': 5000,
        'income_boost': 0.2,
        'description': '+20% к доходу'
    },
    'staff': {
        'name': 'Нанять сотрудника',
        'cost': 3000,
        'income_boost': 0.15,
        'expense_boost': 0.1,
        'description': '+15% к доходу, +10% к расходам'
    },
    'advertising': {
        'name': 'Рекламная кампания',
        'cost': 2000,
        'popularity_boost': 0.3,
        'description': '+30% к популярности'
    },
    'branch': {
        'name': 'Открыть филиал',
        'cost': 10000,
        'income_boost': 0.5,
        'expense_boost': 0.3,
        'description': '+50% к доходу, +30% к расходам'
    }
}

# Донат/поддержка
DONATE_URL = os.getenv('DONATE_URL', 'https://buymeacoffee.com/your_page') 