import aiosqlite
from typing import Optional, Any


USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY,
	username TEXT,
	first_name TEXT,
	last_name TEXT,
	is_admin INTEGER NOT NULL DEFAULT 0,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

KV_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS kv_store (
	key TEXT PRIMARY KEY,
	value TEXT NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
	def __init__(self, path: str):
		self._path = path
		self._conn: Optional[aiosqlite.Connection] = None

	@property
	def path(self) -> str:
		return self._path

	async def connect(self) -> None:
		if self._conn is None:
			self._conn = await aiosqlite.connect(self._path)
			await self._conn.execute("PRAGMA journal_mode=WAL;")
			await self._conn.execute("PRAGMA foreign_keys=ON;")
			await self._conn.commit()

	async def close(self) -> None:
		if self._conn is not None:
			await self._conn.close()
			self._conn = None

	async def init(self, admin_ids: set[int]) -> None:
		await self.connect()
		assert self._conn is not None
		await self._conn.execute(USER_TABLE_SQL)
		await self._conn.execute(KV_TABLE_SQL)
		await self._conn.commit()
		# Ensure admin flags where users already inserted later
		if admin_ids:
			placeholders = ",".join(["?"] * len(admin_ids))
			await self._conn.execute(
				f"UPDATE users SET is_admin=1 WHERE id IN ({placeholders})",
				tuple(admin_ids),
			)
			await self._conn.commit()

	# Users
	async def upsert_user(self, user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str], is_admin: bool) -> None:
		assert self._conn is not None
		await self._conn.execute(
			"""
			INSERT INTO users (id, username, first_name, last_name, is_admin)
			VALUES (?, ?, ?, ?, ?)
			ON CONFLICT(id) DO UPDATE SET
				username=excluded.username,
				first_name=excluded.first_name,
				last_name=excluded.last_name,
				is_admin=excluded.is_admin
			""",
			(user_id, username, first_name, last_name, 1 if is_admin else 0),
		)
		await self._conn.commit()

	async def is_admin(self, user_id: int) -> bool:
		assert self._conn is not None
		async with self._conn.execute("SELECT is_admin FROM users WHERE id=?", (user_id,)) as cur:
			row = await cur.fetchone()
			return bool(row[0]) if row else False

	# KV CRUD
	async def kv_list(self, limit: int = 50, offset: int = 0) -> list[tuple[str, str]]:
		assert self._conn is not None
		async with self._conn.execute(
			"SELECT key, value FROM kv_store ORDER BY key LIMIT ? OFFSET ?",
			(limit, offset),
		) as cur:
			rows = await cur.fetchall()
			return [(r[0], r[1]) for r in rows]

	async def kv_get(self, key: str) -> Optional[str]:
		assert self._conn is not None
		async with self._conn.execute("SELECT value FROM kv_store WHERE key=?", (key,)) as cur:
			row = await cur.fetchone()
			return row[0] if row else None

	async def kv_set(self, key: str, value: str) -> None:
		assert self._conn is not None
		await self._conn.execute(
			"""
			INSERT INTO kv_store (key, value)
			VALUES (?, ?)
			ON CONFLICT(key) DO UPDATE SET
				value=excluded.value,
				updated_at=CURRENT_TIMESTAMP
			""",
			(key, value),
		)
		await self._conn.commit()

	async def kv_delete(self, key: str) -> bool:
		assert self._conn is not None
		async with self._conn.execute("DELETE FROM kv_store WHERE key=?", (key,)) as cur:
			await self._conn.commit()
			return cur.rowcount > 0

	# Dangerous: SQL exec (admin-only)
	async def execute_sql(self, sql: str) -> list[tuple[Any, ...]]:
		assert self._conn is not None
		async with self._conn.execute(sql) as cur:
			try:
				rows = await cur.fetchall()
			except aiosqlite.ProgrammingError:
				rows = []
		await self._conn.commit()
		return rows