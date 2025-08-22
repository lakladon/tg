from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from .db import Database


router = Router()


def setup_user_handlers(db: Database) -> Router:
	@router.message(Command("start"))
	async def cmd_start(message: Message) -> None:
		user = message.from_user
		if not user:
			return
		await db.upsert_user(
			user_id=user.id,
			username=user.username,
			first_name=user.first_name,
			last_name=user.last_name,
			is_admin=False,
		)
		await message.answer("Привет! Бот готов. Используй /admin если у тебя есть права админа.")

	return router