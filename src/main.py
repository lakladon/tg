import asyncio
import os
import sys

# uvloop is optional and not installed on some systems
# try:
# 	import uvloop
# 	uvloop.install()
# except Exception:
# 	pass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import Config
from .db import Database
from .handlers_user import setup_user_handlers
from .handlers_admin import setup_admin_handlers


async def main() -> None:
	config = Config.load()
	bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
	dp = Dispatcher(storage=MemoryStorage())

	db = Database(config.db_path)
	await db.init(admin_ids=config.admin_ids)

	# Routers
	dp.include_router(setup_user_handlers(db))
	dp.include_router(setup_admin_handlers(db, config.admin_ids))

	print("Bot started.")
	await dp.start_polling(bot, allowed_updates=None)


if __name__ == "__main__":
	asyncio.run(main())