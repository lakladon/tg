import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def _parse_admins(raw: str | None) -> set[int]:
	if not raw:
		return set()
	parts = [p.strip() for p in raw.split(',') if p.strip()]
	admins: set[int] = set()
	for p in parts:
		try:
			admins.add(int(p))
		except ValueError:
			continue
	return admins


@dataclass(frozen=True)
class Config:
	bot_token: str
	admin_ids: set[int]
	db_path: str

	@staticmethod
	def load() -> "Config":
		bot_token = os.getenv("BOT_TOKEN", "").strip()
		if not bot_token:
			raise RuntimeError("BOT_TOKEN is required. Set it in .env")
		admin_ids = _parse_admins(os.getenv("ADMINS"))
		db_path = os.getenv("DB_PATH", "/workspace/data/bot.db")
		os.makedirs(os.path.dirname(db_path), exist_ok=True)
		return Config(bot_token=bot_token, admin_ids=admin_ids, db_path=db_path)