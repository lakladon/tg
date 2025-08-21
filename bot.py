import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import html

from config import BOT_TOKEN, BUSINESS_TYPES, IMPROVEMENTS, ADMIN_IDS
from database import GameDatabase
from game_logic import GameLogic
from advanced_features import AdvancedGameFeatures

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Инициализация базы данных и игровой логики
db = GameDatabase()
game_logic = GameLogic()
advanced = AdvancedGameFeatures()

# Состояния FSM
class GameStates(StatesGroup):
    choosing_business = State()
    business_name = State()
    main_menu = State()
    business_management = State()
    improvements = State()
    competitors = State()
    adding_business = State()
# Клавиатуры
def get_main_menu_keyboard(user_id: int = None):
    """Главное меню игры"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="💰 Мой профиль", callback_data="profile"))
    keyboard.add(InlineKeyboardButton(text="🏢 Мои бизнесы", callback_data="businesses"))
    keyboard.add(InlineKeyboardButton(text="🛠 Улучшения", callback_data="improvements"))
    keyboard.add(InlineKeyboardButton(text="➕ Новый бизнес", callback_data="add_business"))
    keyboard.add(InlineKeyboardButton(text="📊 Рейтинг", callback_data="rating"))
    keyboard.add(InlineKeyboardButton(text="🎯 Достижения", callback_data="achievements"))
    keyboard.add(InlineKeyboardButton(text="🎲 Случайное событие", callback_data="random_event"))
    keyboard.add(InlineKeyboardButton(text="📈 Ежедневный доход", callback_data="daily_income"))
    keyboard.add(InlineKeyboardButton(text="🏦 Кредиты", callback_data="loans"))
    keyboard.add(InlineKeyboardButton(text="💼 Инвестиции", callback_data="investments"))
    keyboard.add(InlineKeyboardButton(text="⚔️ PvP", callback_data="pvp"))
    keyboard.row(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))
    # Делим на строки по 2 кнопки, затем последнюю строку отдельно
    keyboard.adjust(2, 2, 2, 1)
    return keyboard.as_markup()

def get_business_choice_keyboard():
    """Выбор типа бизнеса"""
    keyboard = InlineKeyboardBuilder()
    for business_id, business_info in BUSINESS_TYPES.items():
        text = f"{business_info['emoji']} {business_info['name']}"
        keyboard.add(InlineKeyboardButton(text=text, callback_data=f"business_{business_id}"))
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    # По одной кнопке в строке для читабельности
    keyboard.adjust(1)
    return keyboard.as_markup()

@router.callback_query(F.data == "add_business")
async def add_business_flow(callback: types.CallbackQuery, state: FSMContext):
    """Старт добавления второго бизнеса"""
    user_id = callback.from_user.id
    businesses = db.get_player_businesses(user_id)
    if len(businesses) >= 2:
        await callback.answer("У вас уже 2 бизнеса", show_alert=True)
        return
    await state.set_state(GameStates.choosing_business)
    await callback.message.edit_text("Выберите тип нового бизнеса:", reply_markup=get_business_choice_keyboard())


def get_business_management_keyboard(business_id: int):
    """Управление конкретным бизнесом"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_{business_id}"))
    keyboard.add(InlineKeyboardButton(text="🛠 Улучшить", callback_data=f"improve_{business_id}"))
    keyboard.add(InlineKeyboardButton(text="📦 Продукция", callback_data=f"prod_menu_{business_id}"))
    keyboard.add(InlineKeyboardButton(text="💰 Продать", callback_data=f"sell_{business_id}"))
    keyboard.row(InlineKeyboardButton(text="🔙 К списку", callback_data="businesses"))
    return keyboard.as_markup()

def get_improvements_keyboard(business_id: int, player_balance: float):
    """Клавиатура улучшений"""
    keyboard = InlineKeyboardBuilder()
    for improvement_id, improvement_info in IMPROVEMENTS.items():
        can_afford = game_logic.can_afford_improvement(player_balance, improvement_id)
        text = f"{improvement_info['name']} ({improvement_info['cost']} ₽)"
        if not can_afford:
            text += " ❌"
        keyboard.add(InlineKeyboardButton(text=text, callback_data=f"buy_improvement_{business_id}_{improvement_id}"))
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="businesses"))
    keyboard.adjust(1)
    return keyboard.as_markup()

# Обработчики команд
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "Player"
    
    # Добавляем игрока в базу данных
    db.add_player(user_id, username, first_name)
    
    # Проверяем, есть ли у игрока бизнесы
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    
    if not businesses:
        # Новый игрок - предлагаем выбрать бизнес
        await state.set_state(GameStates.choosing_business)
        await message.answer(
            f"🎮 Добро пожаловать в *Бизнес-Империю*!\n\n"
            f"👋 Привет, {first_name}! Вы начинаете свой путь предпринимателя.\n"
            f"💰 Начальный капитал: {player['balance']:,.0f} ₽\n\n"
            f"Выберите тип бизнеса для начала:",
            reply_markup=get_business_choice_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # У игрока уже есть бизнесы - показываем главное меню
        await state.set_state(GameStates.main_menu)
        await show_main_menu(message, user_id)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = """
🎮 *Бизнес-Империя - Помощь*

*Основные команды:*
/start - Начать игру
/profile - Ваш профиль
/businesses - Ваши бизнесы
/rating - Рейтинг игроков
/achievements - Достижения

*Как играть:*
1. Выберите тип бизнеса
2. Управляйте финансами
3. Улучшайте производство
4. Конкурируйте с другими
5. Развивайте империю

*Типы бизнеса:*
☕ Кофейня - стабильный доход, низкий риск
🍽 Ресторан - средний доход, средний риск
🏭 Фабрика - высокий доход, высокий риск
💻 IT-стартап - огромный потенциал, очень высокий риск
🚜 Ферма - скромный доход, очень низкий риск

*Улучшения:*
🛠 Новое оборудование - +20% к доходу
👥 Сотрудники - +15% к доходу, +10% к расходам
📢 Реклама - +30% к популярности
🏢 Филиал - +50% к доходу, +30% к расходам

*Случайные события:*
🎲 Происходят автоматически и могут принести бонусы или штрафы

Удачи в построении вашей бизнес-империи! 🚀
"""
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещен")
        return
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="👥 Игроки", callback_data="admin_players"))
    kb.add(InlineKeyboardButton(text="💰 Изменить баланс", callback_data="admin_set_balance"))
    kb.add(InlineKeyboardButton(text="⭐ Добавить опыт", callback_data="admin_grant_xp"))
    kb.add(InlineKeyboardButton(text="🗑 Удалить игрока", callback_data="admin_delete_player"))
    kb.add(InlineKeyboardButton(text="📊 Инвестиции/Кредиты", callback_data="admin_finance"))
    kb.add(InlineKeyboardButton(text="⚔️ PvP", callback_data="admin_pvp"))
    kb.adjust(2,2,2)
    await message.answer("🔧 Админ-панель", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("admin_"))
async def admin_router(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    action = callback.data
    if action == "admin_players":
        players = db.admin_list_players(20)
        text = "👥 Игроки (топ по балансу):\n\n"
        for p in players:
            name = p['first_name'] or p['username'] or str(p['user_id'])
            text += f"{name} — {p['balance']:,.0f} ₽ | ур.{p['level']} | xp {p['experience']:,} (id:{p['user_id']})\n"
        await callback.message.edit_text(text)
    elif action == "admin_set_balance":
        await state.set_state(GameStates.business_name)
        await state.update_data(action="admin_set_balance")
        await callback.message.edit_text("Введите: user_id новый_баланс")
    elif action == "admin_grant_xp":
        await state.set_state(GameStates.business_name)
        await state.update_data(action="admin_grant_xp")
        await callback.message.edit_text("Введите: user_id xp")
    elif action == "admin_delete_player":
        await state.set_state(GameStates.business_name)
        await state.update_data(action="admin_delete_player")
        await callback.message.edit_text("Введите: user_id для удаления")
    elif action == "admin_finance":
        await callback.message.edit_text("Раздел в разработке")
    elif action == "admin_pvp":
        top = db.get_pvp_top(10)
        text = "⚔️ Топ PvP:\n\n"
        for row in top:
            nm = row['first_name'] or row['username']
            text += f"{row['rank']}. {nm} — {row['rating']:.0f} (W:{row['wins']}/L:{row['losses']})\n"
        await callback.message.edit_text(text)

# Обработчики callback-запросов
@router.callback_query(F.data.startswith("business_"))
async def process_business_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа бизнеса"""
    # Извлекаем тип бизнеса после префикса 'business_' целиком (может содержать '_')
    business_type = callback.data[len("business_"):]
    business_info = BUSINESS_TYPES[business_type]
    
    await state.set_state(GameStates.business_name)
    await state.update_data(business_type=business_type)
    
    await callback.message.edit_text(
        f"🎯 Вы выбрали: {business_info['emoji']} *{business_info['name']}*\n\n"
        f"📝 {business_info['description']}\n"
        f"💰 Базовый доход: {business_info['base_income']:,} ₽/день\n"
        f"💸 Базовые расходы: {business_info['base_expenses']:,} ₽/день\n"
        f"📈 Скорость роста: {business_info['growth_rate']}x\n"
        f"⚠️ Уровень риска: {business_info['risk_level']}\n\n"
        f"Теперь придумайте название для вашего бизнеса:",
        parse_mode="Markdown"
    )

@router.message(GameStates.business_name)
async def process_business_name(message: types.Message, state: FSMContext):
    """Обработка названия бизнеса"""
    business_name = message.text.strip()
    if len(business_name) < 2:
        await message.answer("Название должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    business_type = data['business_type']
    business_info = BUSINESS_TYPES[business_type]
    
    user_id = message.from_user.id
    player = db.get_player(user_id)
    
    existing = db.get_player_businesses(user_id)
    if len(existing) >= 2:
        await message.answer("Лимит: у вас уже 2 бизнеса.", reply_markup=get_main_menu_keyboard())
        await state.set_state(GameStates.main_menu)
        return
    # Создаем бизнес
    business_id = db.add_business(
        user_id, 
        business_type, 
        business_name, 
        business_info['base_income'], 
        business_info['base_expenses']
    )
    
    if business_id:
        # Обновляем баланс игрока (вычитаем стоимость бизнеса)
        startup_cost = business_info['base_expenses'] * 10  # Стоимость запуска
        db.update_player_balance(user_id, -startup_cost, "business_startup", f"Запуск бизнеса '{business_name}'")
        
        await state.set_state(GameStates.main_menu)
        await message.answer(
            f"🎉 Поздравляем! Ваш бизнес *{business_name}* успешно создан!\n\n"
            f"💰 Стоимость запуска: {startup_cost:,.0f} ₽\n"
            f"💵 Текущий баланс: {(player['balance'] - startup_cost):,.0f} ₽\n\n"
            f"Теперь вы можете управлять своим бизнесом!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer("Произошла ошибка при создании бизнеса. Попробуйте еще раз.")

@router.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    """Показать профиль игрока"""
    user_id = callback.from_user.id
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    
    # Рассчитываем дневной прогресс
    daily_progress = game_logic.calculate_daily_progress(player, businesses)
    
    profile_text = f"""
👤 *Ваш профиль*

💰 Баланс: {player['balance']:,.0f} ₽
⭐ Уровень: {player['level']}
📊 Опыт: {player['experience']:,} / {game_logic.calculate_level_up_experience(player['level']):,}
📈 Популярность: {int(player['popularity'] * 100)}%

🏢 *Бизнесы: {len(businesses)}*
📈 Общий доход: {daily_progress['total_income']:,.0f} ₽/день
💸 Общие расходы: {daily_progress['total_expenses']:,.0f} ₽/день
💵 Чистая прибыль: {daily_progress['net_income']:,.0f} ₽/день

📅 Дата регистрации: {player['created_at'][:10]}
🕐 Последняя активность: {player['last_active'][:16]}
"""
    
    await callback.message.edit_text(profile_text, reply_markup=get_main_menu_keyboard(user_id), parse_mode="Markdown")

@router.callback_query(F.data == "businesses")
async def show_businesses(callback: types.CallbackQuery):
    """Показать список бизнесов игрока"""
    user_id = callback.from_user.id
    businesses = db.get_player_businesses(user_id)
    
    if not businesses:
        await callback.message.edit_text(
            "🏢 У вас пока нет бизнесов.\n\n"
            "Начните с создания первого бизнеса!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    businesses_text = "🏢 *Ваши бизнесы:*\n\n"
    keyboard = InlineKeyboardBuilder()
    
    for business in businesses:
        business_info = BUSINESS_TYPES[business['business_type']]
        daily_income = game_logic.calculate_daily_income(business, business['improvements'])
        daily_expenses = game_logic.calculate_daily_expenses(business, business['improvements'])
        net_income = daily_income - daily_expenses
        
        businesses_text += (
            f"{business_info['emoji']} *{business['name']}*\n"
            f"📊 Уровень: {business['level']}\n"
            f"💰 Доход: {daily_income:,.0f} ₽/день\n"
            f"💸 Расходы: {daily_expenses:,.0f} ₽/день\n"
            f"💵 Прибыль: {net_income:,.0f} ₽/день\n"
            f"🛠 Улучшения: {len(business['improvements'])}\n\n"
        )
        
        keyboard.add(InlineKeyboardButton(
            text=f"Управлять {business['name']}", 
            callback_data=f"manage_{business['id']}"
        ))
    
    # Кнопка добавления нового бизнеса (ограничение до 2)
    if len(businesses) < 2:
        keyboard.row(InlineKeyboardButton(text="➕ Добавить второй бизнес", callback_data="add_business"))
    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    keyboard.adjust(1)
    
    await callback.message.edit_text(businesses_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "improvements")
async def improvements_menu(callback: types.CallbackQuery):
    """Меню улучшений из главного меню: предлагается выбрать бизнес"""
    user_id = callback.from_user.id
    businesses = db.get_player_businesses(user_id)
    if not businesses:
        await callback.answer("У вас нет бизнесов для улучшений")
        return
    text = "🛠 Выберите бизнес для улучшений:\n\n"
    keyboard = InlineKeyboardBuilder()
    for business in businesses:
        text += f"- {business['name']} (улучшений: {len(business['improvements'])})\n"
        keyboard.add(InlineKeyboardButton(text=f"Улучшить {business['name']}", callback_data=f"improve_{business['id']}"))
    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    keyboard.adjust(1)
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())

# ---------------- Кредиты ----------------
@router.callback_query(F.data == "loans")
async def loans_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = db.get_player(user_id)
    loans = db.get_active_loans(user_id)
    text = "🏦 Кредиты\n\n"
    if loans:
        for l in loans:
            text += (f"#{l['id']}: Остаток {l['remaining']:,.0f} ₽ | Ставка {l['interest_rate']*100:.1f}%/д | "+
                     f"До {l['due_date'][:10]}\n")
    else:
        text += "Активных кредитов нет\n"
    text += "\nВыберите действие:"
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Взять 50 000 ₽ на 7 дней", callback_data="loan_take_50000_7"))
    # Кнопки погашения по каждому кредиту
    for l in loans:
        keyboard.add(InlineKeyboardButton(text=f"Погасить 10 000 ₽ по #{l['id']}", callback_data=f"loan_repay_{l['id']}_10000"))
    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    keyboard.adjust(1)
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("loan_take_"))
async def take_preset_loan(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split("_")  # loan_take_50000_7
    amount = float(parts[2])
    term = int(parts[3])
    eligibility = advanced.calculate_loan_eligibility(db.get_player(user_id), amount)
    if not eligibility['eligible']:
        await callback.answer(eligibility.get('reason', 'Кредит не одобрен'), show_alert=True)
        return
    loan = advanced.process_loan(db.get_player(user_id), amount, term)
    if not loan['success']:
        await callback.answer("Не удалось оформить кредит", show_alert=True)
        return
    info = loan['loan_info']
    from datetime import datetime
    loan_id = db.create_loan(user_id, amount, info['interest_rate'], term,
                             info['issued_at'].strftime('%Y-%m-%d %H:%M:%S'),
                             info['due_date'].strftime('%Y-%m-%d %H:%M:%S'))
    if loan_id:
        db.update_player_balance(user_id, amount, "loan", f"Кредит #{loan_id}")
        await callback.message.edit_text(
            f"✅ Кредит оформлен! ID {loan_id}\nСумма: {amount:,.0f} ₽\nСтавка: {info['interest_rate']*100:.1f}%/д\nСрок: {term} дн.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.answer("Ошибка сохранения кредита", show_alert=True)

@router.callback_query(F.data.startswith("loan_repay_"))
async def loan_repay_quick(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, _, loan_id_str, amount_str = callback.data.split("_")
    loan_id = int(loan_id_str); amount = float(amount_str)
    loan = db.get_loan_by_id(user_id, loan_id)
    if not loan:
        await callback.answer("Кредит не найден", show_alert=True)
        return
    if amount > loan['remaining']:
        amount = loan['remaining']
    if db.repay_loan(user_id, loan_id, amount):
        db.update_player_balance(user_id, -amount, "loan_repay", f"Погашение кредита #{loan_id}")
        await loans_menu(callback)
    else:
        await callback.answer("Ошибка погашения", show_alert=True)

@router.message(GameStates.business_name)
async def handle_text_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data.get('action')
    # --- админ операции ---
    if action == 'admin_set_balance':
        try:
            uid_str, bal_str = message.text.strip().split()
            uid = int(uid_str); bal = float(bal_str)
        except Exception:
            await message.answer("Неверный формат. Пример: 123456789 100000")
            return
        ok = db.admin_set_balance(uid, bal)
        await message.answer("✅ Баланс обновлен" if ok else "❌ Ошибка", reply_markup=get_main_menu_keyboard())
        await state.clear(); return
    if action == 'admin_grant_xp':
        try:
            uid_str, xp_str = message.text.strip().split()
            uid = int(uid_str); xp = int(xp_str)
        except Exception:
            await message.answer("Неверный формат. Пример: 123456789 5000")
            return
        ok = db.admin_grant_experience(uid, xp)
        await message.answer("✅ Опыт добавлен" if ok else "❌ Ошибка", reply_markup=get_main_menu_keyboard())
        await state.clear(); return
    if action == 'admin_delete_player':
        try:
            uid = int(message.text.strip())
        except Exception:
            await message.answer("Неверный формат. Пример: 123456789")
            return
        ok = db.admin_delete_player(uid)
        await message.answer("✅ Игрок удален" if ok else "❌ Ошибка", reply_markup=get_main_menu_keyboard())
        await state.clear(); return
    if action == 'repay_loan':
        try:
            loan_id_str, amount_str = message.text.strip().split()
            loan_id = int(loan_id_str)
            amount = float(amount_str)
        except Exception:
            await message.answer("Неверный формат. Пример: 1 10000")
            return
        user_id = message.from_user.id
        if db.repay_loan(user_id, loan_id, amount):
            db.update_player_balance(user_id, -amount, "loan_repay", f"Погашение кредита #{loan_id}")
            await message.answer("✅ Платеж принят", reply_markup=get_main_menu_keyboard())
        else:
            await message.answer("❌ Не удалось погасить кредит", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return
    if action == 'claim_investment':
        try:
            inv_id = int(message.text.strip())
        except Exception:
            await message.answer("Неверный формат. Пример: 1")
            return
        user_id = message.from_user.id
        amount = db.claim_investment(user_id, inv_id)
        if amount is None:
            await message.answer("❌ Инвестиция не готова или не найдена")
        else:
            db.update_player_balance(user_id, amount, "investment_income", f"Доход по инвестиции #{inv_id}")
            await message.answer(f"✅ Получено: {amount:,.0f} ₽", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return
    # иначе это ввод названия бизнеса из онбординга — передаем в существующий обработчик
    await process_business_name(message, state)

# ---------------- Инвестиции ----------------
@router.callback_query(F.data == "investments")
async def investments_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Обновим статусы и текущие цены
    db.mark_matured_investments()
    try:
        db.update_investment_prices()
    except Exception:
        pass
    inv = db.get_investments(user_id)
    text = "💼 Инвестиции\n\n"
    if inv:
        for i in inv:
            current_val = i.get('current_value', i['amount'])
            text += (f"#{i['id']}: вложено {i['amount']:,.0f} ₽ | текущая {current_val:,.0f} ₽ | "+
                     f"статус {i['status']} до {i['matures_at'][:10]}\n")
    else:
        text += "Активных инвестиций нет\n"
    text += "\nВыберите действие:"
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Вложить 20 000 ₽ (сбаланс.)", callback_data="inv_take_balanced_20000"))
    # Кнопки для получения и вывода
    for i in inv:
        if i['status'] == 'matured':
            keyboard.add(InlineKeyboardButton(text=f"Забрать по #{i['id']}", callback_data=f"inv_claim_{i['id']}"))
        if i['status'] in ('active','matured'):
            keyboard.add(InlineKeyboardButton(text=f"Вывести по #{i['id']}", callback_data=f"inv_withdraw_{i['id']}"))
    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    keyboard.adjust(1)
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("inv_take_"))
async def take_investment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split("_")  # inv_take_balanced_20000
    strategy = parts[2]
    amount = float(parts[3])
    player = db.get_player(user_id)
    if amount > player['balance']:
        await callback.answer("Недостаточно средств", show_alert=True)
        return
    expected = amount * advanced.investment_returns.get(strategy, 0.12)
    from datetime import datetime, timedelta
    matures = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
    inv_id = db.create_investment(user_id, None, strategy, amount, expected, matures)
    if inv_id:
        db.update_player_balance(user_id, -amount, "investment", f"Инвестиция #{inv_id}")
        await callback.message.edit_text(
            f"✅ Инвестиция создана! ID {inv_id}\nСумма: {amount:,.0f} ₽\nОжидаемый доход: {expected:,.0f} ₽\nСрок: 3 дня",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.answer("Ошибка создания инвестиции", show_alert=True)

@router.callback_query(F.data.startswith("inv_claim_"))
async def inv_claim_quick(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    inv_id = int(callback.data.split("_")[2])
    amount = db.claim_investment(user_id, inv_id)
    if amount is None:
        await callback.answer("Инвестиция не готова", show_alert=True)
        return
    db.update_player_balance(user_id, amount, "investment_income", f"Доход по инвестиции #{inv_id}")
    await investments_menu(callback)

@router.callback_query(F.data.startswith("inv_withdraw_"))
async def inv_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    inv_id = int(callback.data.split("_")[2])
    res = db.withdraw_investment(user_id, inv_id)
    if not res:
        await callback.answer("Инвестиция недоступна", show_alert=True)
        return
    payout, prev_status = res
    if prev_status == 'active':
        msg = f"✅ Досрочный вывод: {payout:,.0f} ₽ (учтен штраф 5%)"
    else:
        msg = f"✅ Вывод: {payout:,.0f} ₽"
    db.update_player_balance(user_id, payout, "investment_withdraw", f"Вывод по инвестиции #{inv_id}")
    try:
        db.update_investment_prices()
    except Exception:
        pass
    await callback.answer(msg, show_alert=True)
    await investments_menu(callback)

    

# ---------------- PvP (заглушка-дуэль) ----------------
@router.callback_query(F.data == "pvp")
async def pvp_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = db.get_player(user_id)
    db.ensure_pvp_profile(user_id)
    opponents = db.get_top_players(10)
    text = "⚔️ PvP Дуэли\nВыберите соперника из топа (ставка 10 000 ₽, кулдаун 30с):\n\n"
    keyboard = InlineKeyboardBuilder()
    for op in opponents:
        if op['user_id'] != user_id:
            name = op['first_name'] or op['username']
            text += f"{name} (ур. {op['level']} | {op['balance']:,.0f} ₽)\n"
            keyboard.add(InlineKeyboardButton(text=f"Сразиться с {name}", callback_data=f"pvp_fight_{op['user_id']}"))
    # Топ по PvP рейтингу
    pvp_top = db.get_pvp_top(5)
    if pvp_top:
        text += "\n<b>Топ PvP:</b>\n"
        for row in pvp_top:
            nm = row['first_name'] or row['username']
            text += f"{row['rank']}. {nm} — {row['rating']:.0f} (W:{row['wins']}/L:{row['losses']})\n"
    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    keyboard.adjust(1)
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("pvp_fight_"))
async def pvp_fight(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    opponent_id = int(callback.data.split("_")[2])
    bet = 10000
    player = db.get_player(user_id)
    opponent = db.get_player(opponent_id)
    if not opponent:
        await callback.answer("Соперник недоступен", show_alert=True)
        return
    # Ограничим ставку доступными балансами сторон
    bet = min(bet, max(0, player['balance'] // 2), max(0, opponent['balance'] // 2)) or 1000
    # Кулдаун
    db.ensure_pvp_profile(user_id)
    remain = db.pvp_cooldown_remaining(user_id)
    if remain > 0:
        await callback.answer(f"Подождите {remain}с до следующего боя", show_alert=True)
        return
    result = advanced.calculate_pvp_outcome(player, opponent, bet)
    # Записываем бой
    db.record_pvp_match(user_id, opponent_id, result['winner']['user_id'] if result['winner'] else None,
                        result['loser']['user_id'] if result['loser'] else None, bet,
                        result['player1_power'], result['player2_power'], result['outcome'])
    if result['outcome'] == 'win':
        db.update_player_balance(user_id, bet, "pvp_win", f"Победа над {opponent.get('username') or opponent.get('first_name')}")
        db.update_player_balance(opponent_id, -bet, "pvp_loss", f"Поражение от {player.get('username') or player.get('first_name')}")
        db.update_pvp_ratings_after_match(user_id, opponent_id)
        msg = f"🏆 Победа! Вы получили {bet:,.0f} ₽"
    elif result['outcome'] == 'loss':
        db.update_player_balance(user_id, -bet, "pvp_loss", f"Поражение от {opponent.get('username') or opponent.get('first_name')}")
        db.update_player_balance(opponent_id, bet, "pvp_win", f"Победа над {player.get('username') or player.get('first_name')}")
        db.update_pvp_ratings_after_match(opponent_id, user_id)
        msg = f"❌ Поражение. Вы потеряли {bet:,.0f} ₽"
    else:
        msg = "🤝 Ничья. Ставки возвращены"
    # Кулдаун 30с после боя
    db.set_pvp_cooldown(user_id, 30)
    await callback.message.edit_text(msg, reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await show_main_menu(callback, callback.from_user.id)

@router.callback_query(F.data.startswith("manage_"))
async def manage_business(callback: types.CallbackQuery):
    """Управление конкретным бизнесом"""
    business_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    businesses = db.get_player_businesses(user_id)
    business = next((b for b in businesses if b['id'] == business_id), None)
    
    if not business:
        await callback.answer("Бизнес не найден!")
        return
    
    business_info = BUSINESS_TYPES[business['business_type']]
    daily_income = game_logic.calculate_daily_income(business, business['improvements'])
    daily_expenses = game_logic.calculate_daily_expenses(business, business['improvements'])
    net_income = daily_income - daily_expenses
    
    business_text = f"""
🏢 *{business['name']}*

📊 Тип: {business_info['emoji']} {business_info['name']}
⭐ Уровень: {business['level']}
💰 Доход: {daily_income:,.0f} ₽/день
💸 Расходы: {daily_expenses:,.0f} ₽/день
💵 Прибыль: {net_income:,.0f} ₽/день
🛠 Улучшения: {len(business['improvements'])}

📈 *Примененные улучшения:*
"""
    
    if business['improvements']:
        for improvement in business['improvements']:
            if improvement in IMPROVEMENTS:
                business_text += f"✅ {IMPROVEMENTS[improvement]['name']}\n"
    else:
        business_text += "Нет улучшений\n"
    
    await callback.message.edit_text(
        business_text, 
        reply_markup=get_business_management_keyboard(business_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("prod_menu_"))
async def prod_menu(callback: types.CallbackQuery):
    business_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    businesses = db.get_player_businesses(user_id)
    business = next((b for b in businesses if b['id'] == business_id), None)
    if not business:
        await callback.answer("Бизнес не найден!", show_alert=True); return
    prods = db.get_business_productions(business_id)
    text = f"📦 Продукция {business['name']}\n\n"
    if prods:
        for p in prods:
            ready = p['ready_at'][:16]
            status = p['status']
            line = f"#{p['id']} {p['name']} v{p['version']} — {p['prod_type']} | {status} до {ready}"
            text += line + "\n"
    else:
        text += "Пока нет активной продукции\n"
    kb = InlineKeyboardBuilder()
    # Предустановленные задания по типу
    btype = business['business_type']
    if btype == 'it_startup':
        kb.add(InlineKeyboardButton(text="Собрать программу", callback_data=f"prod_start_{business_id}_it_app"))
        kb.add(InlineKeyboardButton(text="Система управления", callback_data=f"prod_start_{business_id}_it_erp"))
    elif btype == 'farm':
        kb.add(InlineKeyboardButton(text="Посеять культуры", callback_data=f"prod_start_{business_id}_farm_crops"))
        kb.add(InlineKeyboardButton(text="Сбор урожая", callback_data=f"prod_start_{business_id}_farm_harvest"))
    elif btype == 'factory':
        kb.add(InlineKeyboardButton(text="Запустить продукт", callback_data=f"prod_start_{business_id}_factory_product"))
    # Общие действия
    for p in prods:
        if p['status'] != 'collected':
            kb.add(InlineKeyboardButton(text=f"Забрать #{p['id']}", callback_data=f"prod_collect_{p['id']}"))
    kb.row(InlineKeyboardButton(text="🔙 К бизнесу", callback_data=f"manage_{business_id}"))
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("prod_start_"))
async def prod_start(callback: types.CallbackQuery):
    parts = callback.data.split("_")  # prod_start_{business_id}_{code}
    business_id = int(parts[2])
    code = "_".join(parts[3:])
    # Параметры по коду
    from datetime import datetime, timedelta
    if code == 'it_app':
        name, prod_type, dur_min, qty, version = 'Приложение', 'IT', 30, 1, 1
    elif code == 'it_erp':
        name, prod_type, dur_min, qty, version = 'ERP система', 'IT', 60, 1, 1
    elif code == 'farm_crops':
        name, prod_type, dur_min, qty, version = 'Посев', 'FARM', 45, 100, 1
    elif code == 'farm_harvest':
        name, prod_type, dur_min, qty, version = 'Урожай', 'FARM', 60, 200, 1
    elif code == 'factory_product':
        name, prod_type, dur_min, qty, version = 'Продукт', 'FACTORY', 40, 50, 1
    else:
        await callback.answer("Неизвестное задание", show_alert=True); return
    ready_at = (datetime.now() + timedelta(minutes=dur_min)).strftime('%Y-%m-%d %H:%M:%S')
    prod_id = db.create_production(business_id, prod_type, name, version, ready_at, qty, meta={})
    if prod_id:
        await callback.answer("Задание запущено")
        await prod_menu(callback)
    else:
        await callback.answer("Ошибка запуска", show_alert=True)

@router.callback_query(F.data.startswith("prod_collect_"))
async def prod_collect(callback: types.CallbackQuery):
    prod_id = int(callback.data.split("_")[2])
    info = db.collect_production(prod_id, callback.from_user.id)
    if not info:
        await callback.answer("Не готово или не найдено", show_alert=True); return
    # Награда: денег за продукцию (простая формула)
    base = 0
    if info['prod_type'] == 'IT':
        base = 20000
    elif info['prod_type'] == 'FARM':
        base = info['quantity'] * 50
    elif info['prod_type'] == 'FACTORY':
        base = info['quantity'] * 120
          # Случайный множитель: логнормальное распределение с обрезкой и шансом отрицательного результата
    import random, math
    # 10% шанс провала: убыток 20-80% от базы
    if random.random() < 0.10:
        factor = -random.uniform(0.2, 0.8)
    else:
        # Успех: медиана около 1.0, хвосты до 5-10x редко
        factor = min(10.0, max(0.2, random.lognormvariate(0.0, 0.6)))
    reward = float(base) * factor
    # Узнаем владельца бизнеса
    # Упростим: по prod_id -> business_id уже есть в info
    # Найдем бизнес
    # Для кредитования баланса нужен user_id владельца
    # Получим через businesses
    # Это упрощение: прочитаем бизнес и его владельца
    # (быстрый запрос не реализован; используем обходной путь)
    reward = float(reward)
    # Найдем владельца через все бизнесы игрока (ограничение: только для текущего пользователя)
    user_id = callback.from_user.id
    db.update_player_balance(user_id, reward, 'production', f"Операция по продукции: {info['name']}")
    prefix = "+" if reward >= 0 else "-"
    amount_str = f"{abs(reward):,.0f} ₽"
    await callback.message.edit_text(f"📦 Результат продукции: {prefix}{amount_str}", reply_markup=get_main_menu_keyboard())
    

@router.callback_query(F.data.startswith("stats_"))
async def show_stats(callback: types.CallbackQuery):
    business_id = int(callback.data.split("_")[1])
    await callback.answer("Статистика в разработке", show_alert=True)

@router.callback_query(F.data.startswith("sell_"))
async def sell_business(callback: types.CallbackQuery):
    business_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
        
        # Получаем информацию о бизнесе для подтверждения
    businesses = db.get_player_businesses(user_id)
    business = next((b for b in businesses if b['id'] == business_id), None)
        
    if not business:
         await callback.answer("Бизнес не найден!", show_alert=True)
         return
        
        # Рассчитываем предполагаемую стоимость продажи
    base_value = business['income'] * 10
    improvements_value = 0
        
    for improvement in business['improvements']:
        if improvement in IMPROVEMENTS:
            improvements_value += IMPROVEMENTS[improvement]['cost'] * 0.7
        
        level_bonus = (business['level'] - 1) * 1000
        estimated_value = base_value + improvements_value + level_bonus
        
        # Создаем клавиатуру подтверждения
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="✅ Подтвердить продажу", callback_data=f"confirm_sell_{business_id}"))
        keyboard.add(InlineKeyboardButton(text="❌ Отмена", callback_data=f"manage_{business_id}"))
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"💰 *Продажа бизнеса*\n\n"
            f"🏢 {business['name']}\n"
            f"📊 Уровень: {business['level']}\n"
            f"💵 Ежедневный доход: {business['income']:,.0f} ₽\n"
            f"💸 Ежедневные расходы: {business['expenses']:,.0f} ₽\n"
            f"🛠 Улучшений: {len(business['improvements'])}\n\n"
            f"💰 *Цена продажи: {estimated_value:,.0f} ₽*\n\n"
            f"⚠️ После продажи бизнес будет удален навсегда!",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    @router.callback_query(F.data.startswith("confirm_sell_"))
    async def confirm_sell_business(callback: types.CallbackQuery):
        """Подтверждение продажи бизнеса"""
        business_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        result = db.sell_business(user_id, business_id)
        
        if result['success']:
            await callback.message.edit_text(
                f"✅ *Бизнес успешно продан!*\n\n"
                f"💰 Получено: {result['sale_price']:,.0f} ₽\n\n"
                f"Деньги добавлены на ваш баланс.",
                reply_markup=get_main_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
        else:
            await callback.answer(result['message'], show_alert=True)

@router.callback_query(F.data.startswith("improve_"))
async def show_improvements(callback: types.CallbackQuery):
    """Показать доступные улучшения"""
    business_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    business = next((b for b in businesses if b['id'] == business_id), None)
    
    if not business:
        await callback.answer("Бизнес не найден!")
        return
    
    improvements_text = f"""
🛠 *Улучшения для {business['name']}*

💰 Ваш баланс: {player['balance']:,.0f} ₽
📊 Текущий доход: {business['income']:,.0f} ₽/день
💸 Текущие расходы: {business['expenses']:,.0f} ₽/день

*Доступные улучшения:*
"""
    
    for improvement_id, improvement_info in IMPROVEMENTS.items():
        can_afford = game_logic.can_afford_improvement(player['balance'], improvement_id)
        already_applied = improvement_id in business['improvements']
        
        status = "✅ Применено" if already_applied else "💰 Доступно" if can_afford else "❌ Недоступно"
        improvements_text += f"\n{improvement_info['name']} ({improvement_info['cost']:,} ₽)\n"
        improvements_text += f"📝 {improvement_info['description']}\n"
        improvements_text += f"🔧 Статус: {status}\n"
    
    await callback.message.edit_text(
        improvements_text,
        reply_markup=get_improvements_keyboard(business_id, player['balance']),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("buy_improvement_"))
async def buy_improvement(callback: types.CallbackQuery):
    """Покупка улучшения"""
    parts = callback.data.split("_")
    business_id = int(parts[2])
    improvement_id = parts[3]
    user_id = callback.from_user.id
    
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    business = next((b for b in businesses if b['id'] == business_id), None)
    
    if not business:
        await callback.answer("Бизнес не найден!")
        return
    
    if improvement_id in business['improvements']:
        await callback.answer("Это улучшение уже применено!")
        return
    
    if not game_logic.can_afford_improvement(player['balance'], improvement_id):
        await callback.answer("Недостаточно средств!")
        return
    
    # Применяем улучшение
    result = game_logic.apply_improvement(business, improvement_id)
    
    if result['success']:
        # Обновляем бизнес в базе данных
        db.update_business(
            business_id,
            income=result['new_income'],
            expenses=result['new_expenses'],
            improvements=result['new_improvements']
        )
        
        # Списываем стоимость улучшения
        db.update_player_balance(user_id, -result['cost'], "improvement", f"Улучшение {IMPROVEMENTS[improvement_id]['name']}")
        
        await callback.message.edit_text(
            f"✅ {result['message']}\n\n"
            f"💰 Стоимость: {result['cost']:,.0f} ₽\n"
            f"📈 Новый доход: {result['new_income']:,.0f} ₽/день\n"
            f"💸 Новые расходы: {result['new_expenses']:,.0f} ₽/день",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.answer(result['message'])

@router.callback_query(F.data == "rating")
async def show_rating(callback: types.CallbackQuery):
    """Показать рейтинг игроков"""
    top_players = db.get_top_players(10)
    # Используем HTML и экранируем имена, добавляем бизнес и тип
    rating_text = "<b>🏆 Топ-10 игроков по капиталу:</b>\n\n"
    for p in top_players:
        medal = "🥇" if p['rank'] == 1 else "🥈" if p['rank'] == 2 else "🥉" if p['rank'] == 3 else f"{p['rank']}."
        username_raw = p['first_name'] or p['username'] or "Игрок"
        username = html.escape(username_raw)
        # Берем лучший бизнес по доходу (если есть)
        businesses = db.get_player_businesses(p['user_id'])
        biz_part = ""
        if businesses:
            best = max(businesses, key=lambda b: b.get('income', 0) or 0)
            b_type = BUSINESS_TYPES.get(best['business_type'], {'emoji': '🏢', 'name': 'Бизнес'})
            b_name = html.escape(best['name'])
            biz_part = f"\n{b_type['emoji']} {b_name} — {b_type['name']}"
        rating_text += f"{medal} {username}{biz_part}\n"
        rating_text += f"💰 {p['balance']:,.0f} ₽ | ⭐ Уровень {p['level']}\n\n"

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    await callback.message.edit_text(rating_text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "achievements")
async def show_achievements(callback: types.CallbackQuery):
    """Показать достижения игрока"""
    user_id = callback.from_user.id
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    
    # Проверяем достижения
    achievements = game_logic.check_achievements(player, businesses)
    earned_achievements = db.get_player_achievements(user_id)
    
    achievements_text = "🎯 *Достижения:*\n\n"
    
    if achievements:
        achievements_text += "*Новые достижения:*\n"
        for achievement in achievements:
            achievements_text += f"🏆 {achievement['title']}\n"
            achievements_text += f"📝 {achievement['description']}\n\n"
            
            # Добавляем достижение в базу данных
            db.add_achievement(user_id, achievement['type'], achievement['title'], achievement['description'])
    
    if earned_achievements:
        achievements_text += "*Полученные достижения:*\n"
        for achievement in earned_achievements:
            achievements_text += f"✅ {achievement['title']}\n"
            achievements_text += f"📝 {achievement['description']}\n"
            achievements_text += f"📅 {achievement['earned_at'][:10]}\n\n"
    
    if not achievements and not earned_achievements:
        achievements_text += "У вас пока нет достижений. Продолжайте развивать свой бизнес!"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    
    await callback.message.edit_text(achievements_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "random_event")
async def trigger_random_event(callback: types.CallbackQuery):
    """Запуск случайного события"""
    user_id = callback.from_user.id
     # Проверяем кулдаун
    cooldown_remaining = db.get_cooldown_remaining(user_id, "random_event")
    if cooldown_remaining > 0:
        minutes = cooldown_remaining // 60
        seconds = cooldown_remaining % 60
        await callback.answer(
            f"⏰ Случайное событие доступно через {minutes}м {seconds}с", 
            show_alert=True
        )
        return
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    
    if not businesses:
        await callback.answer("У вас нет бизнесов для событий!")
        return
    
    # Выбираем случайный бизнес
    business = random.choice(businesses)
    
    # Получаем случайное событие
    event = game_logic.get_random_event(player['level'])
    
    if event:
        # Применяем событие
        result = game_logic.apply_random_event(player, business, event)
        
        # Обновляем баланс игрока
        if result['income_change'] != 0:
            db.update_player_balance(user_id, result['income_change'], "random_event", event['title'])
        
        # Обновляем популярность
        if result['popularity_change'] != 0:
            db.update_player_popularity(user_id, result['popularity_change'])
        # Устанавливаем кулдаун на 30 минут
        db.set_cooldown(user_id, "random_event", 30)
        await callback.message.edit_text(
            f"🎲 *Случайное событие!*\n\n{result['message']}\n\n"
            f"⏰ Следующее событие будет доступно через 30 минут",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode="Markdown"
        )
    else:
         # Даже если событие не произошло, ставим кулдаун
        db.set_cooldown(user_id, "random_event", 30)
        await callback.message.edit_text(
            "🎲 *Случайное событие*\n\n"
            "Сегодня ничего особенного не произошло, но завтра может быть удача!\n\n"
            "⏰ Следующее событие будет доступно через 30 минут",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "daily_income")
async def collect_daily_income(callback: types.CallbackQuery):
    """Сбор ежедневного дохода"""
    user_id = callback.from_user.id
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    
    if not businesses:
        await callback.answer("У вас нет бизнесов для получения дохода!")
        return
    
    # Рассчитываем дневной прогресс
    daily_progress = game_logic.calculate_daily_progress(player, businesses)
    
    # Обновляем баланс игрока
    db.update_player_balance(user_id, daily_progress['net_income'], "daily_income", "Ежедневный доход")
    
    # Добавляем опыт и, при необходимости, повышаем уровень
    new_exp = db.add_experience(user_id, daily_progress['experience_gained'])
    if new_exp is not None:
        # перечитываем игрока и проверяем уровень
        player = db.get_player(user_id)
        if game_logic.can_level_up(player['experience'], player['level']):
            level_up_result = game_logic.level_up_player(player)
            if level_up_result['success']:
                bonuses = level_up_result['bonuses']
                db.apply_level_up(
                    user_id,
                    level_up_result['new_level'],
                    level_up_result['remaining_experience'],
                    bonuses['balance_bonus'],
                    bonuses['popularity_bonus']
                )
                await callback.message.edit_text(
                    f"💰 *Ежедневный доход получен!*\n\n"
                    f"📈 Доход: +{daily_progress['total_income']:,.0f} ₽\n"
                    f"💸 Расходы: -{daily_progress['total_expenses']:,.0f} ₽\n"
                    f"💵 Чистая прибыль: +{daily_progress['net_income']:,.0f} ₽\n"
                    f"📊 Опыт: +{daily_progress['experience_gained']}\n\n"
                    f"{level_up_result['message']}",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                return
    
    await callback.message.edit_text(
        f"💰 *Ежедневный доход получен!*\n\n"
        f"📈 Доход: +{daily_progress['total_income']:,.0f} ₽\n"
        f"💸 Расходы: -{daily_progress['total_expenses']:,.0f} ₽\n"
        f"💵 Чистая прибыль: +{daily_progress['net_income']:,.0f} ₽\n"
        f"📊 Опыт: +{daily_progress['experience_gained']}",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    """Показать главное меню"""
    await show_main_menu(callback, callback.from_user.id)

async def show_main_menu(message_or_callback, user_id: int):
    """Показать главное меню (общая функция)"""
    player = db.get_player(user_id)
    businesses = db.get_player_businesses(user_id)
    
    if not businesses:
        await message_or_callback.answer(
            "🏢 У вас пока нет бизнесов.\n\n"
            "Начните с создания первого бизнеса!",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    # Рассчитываем дневной прогресс
    daily_progress = game_logic.calculate_daily_progress(player, businesses)
    
    menu_text = f"""
🎮 *Бизнес-Империя*

💰 Баланс: {player['balance']:,.0f} ₽
⭐ Уровень: {player['level']}
📊 Опыт: {player['experience']:,} / {game_logic.calculate_level_up_experience(player['level']):,}

🏢 *Бизнесы: {len(businesses)}*
📈 Доход: {daily_progress['total_income']:,.0f} ₽/день
💸 Расходы: {daily_progress['total_expenses']:,.0f} ₽/день
💵 Прибыль: {daily_progress['net_income']:,.0f} ₽/день

Выберите действие:
"""
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(menu_text, reply_markup=get_main_menu_keyboard(user_id), parse_mode="Markdown")
    else:
        await message_or_callback.message.edit_text(menu_text, reply_markup=get_main_menu_keyboard(user_id), parse_mode="Markdown")

@router.callback_query(F.data == "help")
async def show_help(callback: types.CallbackQuery):
    """Показать справку"""
    help_text = """
🎮 *Бизнес-Империя - Помощь*

*Основные команды:*
/start - Начать игру
/profile - Ваш профиль
/businesses - Ваши бизнесы
/rating - Рейтинг игроков
/achievements - Достижения

*Как играть:*
1. Выберите тип бизнеса
2. Управляйте финансами
3. Улучшайте производство
4. Конкурируйте с другими
5. Развивайте империю

*Типы бизнеса:*
☕ Кофейня - стабильный доход, низкий риск
🍽 Ресторан - средний доход, средний риск
🏭 Фабрика - высокий доход, высокий риск
💻 IT-стартап - огромный потенциал, очень высокий риск
🚜 Ферма - скромный доход, очень низкий риск

*Улучшения:*
🛠 Новое оборудование - +20% к доходу
👥 Сотрудники - +15% к доходу, +10% к расходам
📢 Реклама - +30% к популярности
🏢 Филиал - +50% к доходу, +30% к расходам

*Случайные события:*
🎲 Происходят автоматически и могут принести бонусы или штрафы

Удачи в построении вашей бизнес-империи! 🚀
"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    
    await callback.message.edit_text(help_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

# Фолбэк для необработанных callback данных
@router.callback_query()
async def unknown_callback(callback: types.CallbackQuery):
    logging.info(f"Unhandled callback data: {callback.data}")
    await callback.answer("Кнопка пока не поддерживается", show_alert=False)

# Регистрация роутера
dp.include_router(router)

# Главная функция
async def main():
    """Главная функция бота"""
    logger.info("Запуск бота Бизнес-Империя...")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 
