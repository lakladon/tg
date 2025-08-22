from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[
			InlineKeyboardButton(text="KV Store", callback_data="admin:kv"),
			InlineKeyboardButton(text="SQL Exec", callback_data="admin:sql"),
		],
	])


def kv_list_item_kb(key: str) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[
			InlineKeyboardButton(text="Edit", callback_data=f"kv:edit:{key}"),
			InlineKeyboardButton(text="Delete", callback_data=f"kv:del:{key}"),
		],
	])


def kv_actions_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[
			InlineKeyboardButton(text="Add New", callback_data="kv:add"),
			InlineKeyboardButton(text="Back", callback_data="admin:back"),
		]
	])


def confirm_sql_kb() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[
			InlineKeyboardButton(text="Run", callback_data="sql:run"),
			InlineKeyboardButton(text="Cancel", callback_data="sql:cancel"),
		]
	])