from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from .db import Database
from .keyboards import admin_main_kb, kv_list_item_kb, kv_actions_kb, confirm_sql_kb


class KvStates(StatesGroup):
	awaiting_action = State()
	awaiting_new_key = State()
	awaiting_new_value = State()
	awaiting_edit_value = State()


class SqlStates(StatesGroup):
	awaiting_sql = State()
	awaiting_confirm = State()


def setup_admin_handlers(db: Database, admin_ids: set[int]) -> Router:
	router = Router()

	def _is_admin(user_id: int) -> bool:
		return user_id in admin_ids

	@router.message(Command("admin"))
	async def cmd_admin(message: Message) -> None:
		user = message.from_user
		if not user or not _is_admin(user.id):
			return
		await message.answer("Админ панель", reply_markup=admin_main_kb())

	@router.callback_query(lambda c: c.data == "admin:back")
	async def on_admin_back(callback: CallbackQuery) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		await callback.message.edit_text("Админ панель", reply_markup=admin_main_kb())
		await callback.answer()

	# KV Section
	@router.callback_query(lambda c: c.data == "admin:kv")
	async def on_admin_kv(callback: CallbackQuery, state: FSMContext) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		items = await db.kv_list(limit=50)
		text_lines = ["KV Store:"]
		for k, v in items:
			short = v if len(v) <= 40 else v[:37] + "..."
			text_lines.append(f"- {k}: {short}")
		text = "\n".join(text_lines) if items else "KV Store пуст."
		await callback.message.edit_text(text, reply_markup=kv_actions_kb())
		await state.set_state(KvStates.awaiting_action)
		await callback.answer()

	@router.callback_query(lambda c: c.data == "kv:add")
	async def on_kv_add(callback: CallbackQuery, state: FSMContext) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		await callback.message.edit_text("Отправь ключ (строкой).")
		await state.set_state(KvStates.awaiting_new_key)
		await callback.answer()

	@router.message(KvStates.awaiting_new_key)
	async def on_kv_new_key(message: Message, state: FSMContext) -> None:
		await state.update_data(new_key=message.text or "")
		await message.answer("Теперь отправь значение (строкой).")
		await state.set_state(KvStates.awaiting_new_value)

	@router.message(KvStates.awaiting_new_value)
	async def on_kv_new_value(message: Message, state: FSMContext) -> None:
		data = await state.get_data()
		key = data.get("new_key", "")
		value = message.text or ""
		await db.kv_set(key, value)
		await message.answer(f"Сохранено: {key}")
		await state.clear()

	@router.callback_query(lambda c: c.data and c.data.startswith("kv:edit:"))
	async def on_kv_edit(callback: CallbackQuery, state: FSMContext) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		key = callback.data.split(":", 2)[2]
		cur = await db.kv_get(key)
		await state.update_data(edit_key=key)
		await callback.message.edit_text(f"Текущее значение для {key}:\n{cur}\n\nОтправь новое значение.")
		await state.set_state(KvStates.awaiting_edit_value)
		await callback.answer()

	@router.message(KvStates.awaiting_edit_value)
	async def on_kv_edit_value(message: Message, state: FSMContext) -> None:
		data = await state.get_data()
		key = data.get("edit_key")
		await db.kv_set(key, message.text or "")
		await message.answer("Обновлено.")
		await state.clear()

	@router.callback_query(lambda c: c.data and c.data.startswith("kv:del:"))
	async def on_kv_delete(callback: CallbackQuery) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		key = callback.data.split(":", 2)[2]
		ok = await db.kv_delete(key)
		await callback.answer("Удалено" if ok else "Не найдено")
		await callback.message.edit_text("Удалено. Нажми /admin -> KV чтобы обновить список.")

	# SQL Section
	@router.callback_query(lambda c: c.data == "admin:sql")
	async def on_admin_sql(callback: CallbackQuery, state: FSMContext) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		await callback.message.edit_text("Введи SQL запрос. Будь осторожен!", reply_markup=None)
		await state.set_state(SqlStates.awaiting_sql)
		await callback.answer()

	@router.message(SqlStates.awaiting_sql)
	async def on_sql_input(message: Message, state: FSMContext) -> None:
		sql = message.text or ""
		await state.update_data(sql=sql)
		await message.answer("Подтвердить выполнение?", reply_markup=confirm_sql_kb())
		await state.set_state(SqlStates.awaiting_confirm)

	@router.callback_query(lambda c: c.data in ("sql:run", "sql:cancel"))
	async def on_sql_confirm(callback: CallbackQuery, state: FSMContext) -> None:
		if not callback.from_user or not _is_admin(callback.from_user.id):
			return
		data = await state.get_data()
		if callback.data == "sql:cancel":
			await callback.message.edit_text("Отменено.")
			await state.clear()
			await callback.answer()
			return
		sql = data.get("sql", "")
		rows = await db.execute_sql(sql)
		preview = "\n".join([", ".join(map(str, r)) for r in rows[:20]]) or "(no rows)"
		await callback.message.edit_text(f"Выполнено. Первые строки:\n{preview}")
		await state.clear()
		await callback.answer()

	return router