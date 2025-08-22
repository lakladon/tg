import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class GameDatabase:
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        pizdabol = conn.cursor()
        
        # Таблица игроков
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 10000,
                total_income REAL DEFAULT 0,
                total_expenses REAL DEFAULT 0,
                popularity REAL DEFAULT 1.0,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица бизнесов
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                business_type TEXT,
                name TEXT,
                income REAL,
                expenses REAL,
                level INTEGER DEFAULT 1,
                improvements TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')
        
        # Таблица транзакций
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                business_id INTEGER,
                type TEXT,
                amount REAL,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players (user_id),
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
        ''')
        
        # Таблица достижений
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_type TEXT,
                title TEXT,
                description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')
        
        # Таблица рейтингов
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                score REAL,
                rank INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')

        # Таблица кредитов
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                interest_rate REAL NOT NULL,
                term_days INTEGER NOT NULL,
                issued_at TIMESTAMP NOT NULL,
                due_date TIMESTAMP NOT NULL,
                remaining REAL NOT NULL,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')

        # Таблица инвестиций
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                business_id INTEGER,
                strategy TEXT NOT NULL,
                amount REAL NOT NULL,
                expected_return REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                matures_at TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                -- дополнительные поля для динамической стоимости
                current_value REAL,
                volatility REAL,
                last_price_update TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players (user_id),
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
        ''')

        # Мягкая миграция: добавляем отсутствующие колонки для динамической стоимости инвестиций
        try:
            pizdabol.execute("PRAGMA table_info('investments')")
            columns = [row[1] for row in pizdabol.fetchall()]
            if 'current_value' not in columns:
                pizdabol.execute("ALTER TABLE investments ADD COLUMN current_value REAL")
            if 'volatility' not in columns:
                pizdabol.execute("ALTER TABLE investments ADD COLUMN volatility REAL")
            if 'last_price_update' not in columns:
                pizdabol.execute("ALTER TABLE investments ADD COLUMN last_price_update TIMESTAMP")
            # Инициализация текущей стоимости для уже существующих записей
            pizdabol.execute("UPDATE investments SET current_value = amount WHERE current_value IS NULL")
        except Exception as e:
            # Без падения приложения
            print(f"Миграция таблицы investments пропущена: {e}")

        # Таблица продукции (производственные задания)
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS productions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                prod_type TEXT NOT NULL,
                name TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                status TEXT DEFAULT 'in_progress',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ready_at TIMESTAMP NOT NULL,
                quantity REAL DEFAULT 0,
                meta TEXT DEFAULT '{}',
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
        ''')

        # Таблица сотрудников
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT,
                salary REAL DEFAULT 0,
                performance REAL DEFAULT 1.0,
                hired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
        ''')

        # Таблица посетителей
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                visitor_name TEXT,
                spent REAL DEFAULT 0,
                rating INTEGER,
                reviewed INTEGER DEFAULT 0,
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
        ''')

        # Таблица отзывов
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                visitor_name TEXT,
                rating INTEGER NOT NULL,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
        ''')

        # PvP профили
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS pvp_profiles (
                user_id INTEGER PRIMARY KEY,
                rating REAL DEFAULT 1000,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_fight_at TIMESTAMP,
                cooldown_until TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')

        # История PvP матчей
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS pvp_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER NOT NULL,
                opponent_id INTEGER NOT NULL,
                winner_id INTEGER,
                loser_id INTEGER,
                bet REAL NOT NULL,
                challenger_power REAL,
                opponent_power REAL,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (challenger_id) REFERENCES players (user_id),
                FOREIGN KEY (opponent_id) REFERENCES players (user_id)
            )
        ''')
        
        # Таблица кулдаунов
        pizdabol.execute('''
            CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                PRIMARY KEY (user_id, action_type),
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_player(self, user_id: int, username: str, first_name: str) -> bool:
        """Добавление нового игрока"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                INSERT OR IGNORE INTO players (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении игрока: {e}")
            return False
    
    def get_player(self, user_id: int) -> Optional[Dict]:
        """Получение информации об игроке"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                SELECT * FROM players WHERE user_id = ?
            ''', (user_id,))
            
            row = pizdabol.fetchone()
            # Получаем список колонок ДО закрытия соединения
            columns = [description[0] for description in pizdabol.description] if row else None
            conn.close()
            
            if row and columns:
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Ошибка при получении игрока: {e}")
            return None
    
    def update_player_balance(self, user_id: int, amount: float, transaction_type: str, description: str = ""):
        """Обновление баланса игрока и запись транзакции"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            # Обновляем баланс
            pizdabol.execute('''
                UPDATE players 
                SET balance = balance + ?, 
                    total_income = total_income + CASE WHEN ? > 0 THEN ? ELSE 0 END,
                    total_expenses = total_expenses + CASE WHEN ? < 0 THEN ABS(?) ELSE 0 END,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (amount, amount, amount, amount, amount, user_id))
            
            # Записываем транзакцию
            pizdabol.execute('''
                INSERT INTO transactions (user_id, type, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, transaction_type, amount, description))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении баланса: {e}")
            return False
    
    def add_business(self, user_id: int, business_type: str, name: str, income: float, expenses: float) -> Optional[int]:
        """Добавление нового бизнеса"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                INSERT INTO businesses (user_id, business_type, name, income, expenses)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, business_type, name, income, expenses))
            
            business_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return business_id
        except Exception as e:
            print(f"Ошибка при добавлении бизнеса: {e}")
            return None
    
    def get_player_businesses(self, user_id: int) -> List[Dict]:
        """Получение всех бизнесов игрока"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                SELECT * FROM businesses WHERE user_id = ?
            ''', (user_id,))
            
            rows = pizdabol.fetchall()
            conn.close()
            
            businesses = []
            if rows:
                columns = [description[0] for description in pizdabol.description]
                for row in rows:
                    business = dict(zip(columns, row))
                    business['improvements'] = json.loads(business['improvements'])
                    businesses.append(business)
            
            return businesses
        except Exception as e:
            print(f"Ошибка при получении бизнесов: {e}")
            return []
    
    def update_business(self, business_id: int, income: float = None, expenses: float = None, 
                       level: int = None, improvements: List[str] = None):
        """Обновление бизнеса"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            updates = []
            values = []
            
            if income is not None:
                updates.append("income = ?")
                values.append(income)
            if expenses is not None:
                updates.append("expenses = ?")
                values.append(expenses)
            if level is not None:
                updates.append("level = ?")
                values.append(level)
            if improvements is not None:
                updates.append("improvements = ?")
                values.append(json.dumps(improvements))
            
            if updates:
                values.append(business_id)
                query = f"UPDATE businesses SET {', '.join(updates)} WHERE id = ?"
                pizdabol.execute(query, values)
                
                conn.commit()
                conn.close()
                return True
            
            return False
        except Exception as e:
            print(f"Ошибка при обновлении бизнеса: {e}")
            return False
    
    def get_top_players(self, limit: int = 10) -> List[Dict]:
        """Получение топ игроков по балансу"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                SELECT user_id, username, first_name, balance, level
                FROM players 
                ORDER BY balance DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = pizdabol.fetchall()
            conn.close()
            
            top_players = []
            for i, row in enumerate(rows):
                top_players.append({
                    'rank': i + 1,
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'balance': row[3],
                    'level': row[4]
                })
            
            return top_players
        except Exception as e:
            print(f"Ошибка при получении топ игроков: {e}")
            return []

    # ------------------- Админ операции -------------------
    def admin_set_balance(self, user_id: int, new_balance: float) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('UPDATE players SET balance = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (new_balance, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка admin_set_balance: {e}")
            return False

    def admin_grant_experience(self, user_id: int, xp: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('UPDATE players SET experience = experience + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (xp, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка admin_grant_experience: {e}")
            return False

    def admin_delete_player(self, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM businesses WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM achievements WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM ratings WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM loans WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM investments WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM pvp_profiles WHERE user_id = ?', (user_id,))
            pizdabol.execute('DELETE FROM pvp_matches WHERE challenger_id = ? OR opponent_id = ?', (user_id, user_id))
            pizdabol.execute('DELETE FROM players WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка admin_delete_player: {e}")
            return False

    def admin_list_players(self, limit: int = 50) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('SELECT user_id, username, first_name, balance, level, experience FROM players ORDER BY balance DESC LIMIT ?', (limit,))
            rows = pizdabol.fetchall()
            conn.close()
            res = []
            for row in rows:
                res.append({'user_id': row[0], 'username': row[1], 'first_name': row[2], 'balance': row[3], 'level': row[4], 'experience': row[5]})
            return res
        except Exception as e:
            print(f"Ошибка admin_list_players: {e}")
            return []
    
    def add_achievement(self, user_id: int, achievement_type: str, title: str, description: str):
        """Добавление достижения игроку"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                INSERT INTO achievements (user_id, achievement_type, title, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, achievement_type, title, description))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении достижения: {e}")
            return False
    
    def get_player_achievements(self, user_id: int) -> List[Dict]:
        """Получение достижений игрока"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            pizdabol.execute('''
                SELECT * FROM achievements WHERE user_id = ?
                ORDER BY earned_at DESC
            ''', (user_id,))
            
            rows = pizdabol.fetchall()
            conn.close()
            
            achievements = []
            if rows:
                columns = [description[0] for description in pizdabol.description]
                for row in rows:
                    achievements.append(dict(zip(columns, row)))
            
            return achievements
        except Exception as e:
            print(f"Ошибка при получении достижений: {e}")
            return []
    
    def update_rating(self, user_id: int, category: str, score: float):
        """Обновление рейтинга игрока"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            # Обновляем или добавляем рейтинг
            pizdabol.execute('''
                INSERT OR REPLACE INTO ratings (user_id, category, score, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, category, score))
            
            # Пересчитываем ранги
            pizdabol.execute('''
                UPDATE ratings 
                SET rank = (
                    SELECT COUNT(*) + 1 
                    FROM ratings r2 
                    WHERE r2.category = ratings.category 
                    AND r2.score > ratings.score
                )
                WHERE category = ?
            ''', (category,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении рейтинга: {e}")
            return False 

    # ------------------- Сотрудники -------------------
    def add_employee(self, business_id: int, full_name: str, role: str, salary: float, performance: float = 1.0) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                INSERT INTO employees (business_id, full_name, role, salary, performance)
                VALUES (?, ?, ?, ?, ?)
            ''', (business_id, full_name, role, salary, performance))
            emp_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return emp_id
        except Exception as e:
            print(f"Ошибка при добавлении сотрудника: {e}")
            return None

    def get_business_employees(self, business_id: int) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, full_name, role, salary, performance, hired_at
                FROM employees
                WHERE business_id = ?
                ORDER BY id DESC
            ''', (business_id,))
            rows = pizdabol.fetchall()
            conn.close()
            res = []
            for row in rows:
                res.append({
                    'id': row[0], 'full_name': row[1], 'role': row[2],
                    'salary': row[3], 'performance': row[4], 'hired_at': row[5]
                })
            return res
        except Exception as e:
            print(f"Ошибка при получении сотрудников: {e}")
            return []

    def delete_employee(self, employee_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при удалении сотрудника: {e}")
            return False

    def get_total_employees_salary(self, user_id: int) -> float:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT COALESCE(SUM(e.salary), 0)
                FROM employees e
                JOIN businesses b ON b.id = e.business_id
                WHERE b.user_id = ?
            ''', (user_id,))
            total = pizdabol.fetchone()[0] or 0.0
            conn.close()
            return float(total)
        except Exception as e:
            print(f"Ошибка при расчете зарплат: {e}")
            return 0.0

    # ------------------- Посетители и отзывы -------------------
    def add_visitor(self, business_id: int, visitor_name: str, spent: float, rating: Optional[int] = None) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                INSERT INTO visitors (business_id, visitor_name, spent, rating, reviewed)
                VALUES (?, ?, ?, ?, ?)
            ''', (business_id, visitor_name, spent, rating, 1 if rating is not None else 0))
            visitor_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return visitor_id
        except Exception as e:
            print(f"Ошибка при добавлении посетителя: {e}")
            return None

    def add_review(self, business_id: int, visitor_name: str, rating: int, text: str) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                INSERT INTO reviews (business_id, visitor_name, rating, text)
                VALUES (?, ?, ?, ?)
            ''', (business_id, visitor_name, rating, text))
            review_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return review_id
        except Exception as e:
            print(f"Ошибка при добавлении отзыва: {e}")
            return None

    def get_business_reviews(self, business_id: int, limit: int = 20) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, visitor_name, rating, text, created_at
                FROM reviews
                WHERE business_id = ?
                ORDER BY id DESC
                LIMIT ?
            ''', (business_id, limit))
            rows = pizdabol.fetchall()
            conn.close()
            res = []
            for row in rows:
                res.append({
                    'id': row[0], 'visitor_name': row[1], 'rating': row[2], 'text': row[3], 'created_at': row[4]
                })
            return res
        except Exception as e:
            print(f"Ошибка при получении отзывов: {e}")
            return []

    def get_business_rating(self, business_id: int) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT COALESCE(AVG(rating), 0), COUNT(*)
                FROM reviews
                WHERE business_id = ?
            ''', (business_id,))
            row = pizdabol.fetchone()
            conn.close()
            avg_rating = float(row[0] or 0)
            count = int(row[1] or 0)
            return {'avg_rating': avg_rating, 'reviews_count': count}
        except Exception as e:
            print(f"Ошибка при расчете рейтинга: {e}")
            return {'avg_rating': 0.0, 'reviews_count': 0}

    def get_top_businesses_by_reviews(self, limit: int = 10, min_reviews: int = 3) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT b.id, b.user_id, b.name, b.business_type,
                       COALESCE(AVG(r.rating), 0) as avg_rating,
                       COUNT(r.id) as reviews_count
                FROM businesses b
                LEFT JOIN reviews r ON r.business_id = b.id
                GROUP BY b.id
                HAVING reviews_count >= ?
                ORDER BY avg_rating DESC, reviews_count DESC
                LIMIT ?
            ''', (min_reviews, limit))
            rows = pizdabol.fetchall()
            conn.close()
            res = []
            for row in rows:
                res.append({
                    'business_id': row[0], 'user_id': row[1], 'name': row[2], 'business_type': row[3],
                    'avg_rating': float(row[4] or 0), 'reviews_count': int(row[5] or 0)
                })
            return res
        except Exception as e:
            print(f"Ошибка при получении рейтинга по отзывам: {e}")
            return []

    # ------------------- Новые механики: кредиты -------------------
    def create_loan(self, user_id: int, amount: float, interest_rate: float, term_days: int,
                    issued_at: str, due_date: str) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                INSERT INTO loans (user_id, amount, interest_rate, term_days, issued_at, due_date, remaining, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (user_id, amount, interest_rate, term_days, issued_at, due_date, amount))
            loan_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return loan_id
        except Exception as e:
            print(f"Ошибка при создании кредита: {e}")
            return None

    def get_active_loans(self, user_id: int) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, amount, interest_rate, term_days, issued_at, due_date, remaining, status
                FROM loans WHERE user_id = ? AND status = 'active'
                ORDER BY issued_at DESC
            ''', (user_id,))
            rows = pizdabol.fetchall()
            conn.close()
            loans = []
            for row in rows:
                loans.append({
                    'id': row[0],
                    'amount': row[1],
                    'interest_rate': row[2],
                    'term_days': row[3],
                    'issued_at': row[4],
                    'due_date': row[5],
                    'remaining': row[6],
                    'status': row[7]
                })
            return loans
        except Exception as e:
            print(f"Ошибка при получении кредитов: {e}")
            return []

    def get_loan_by_id(self, user_id: int, loan_id: int) -> Optional[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, amount, interest_rate, term_days, issued_at, due_date, remaining, status
                FROM loans WHERE id = ? AND user_id = ?
            ''', (loan_id, user_id))
            row = pizdabol.fetchone()
            conn.close()
            if not row:
                return None
            return {
                'id': row[0],
                'amount': row[1],
                'interest_rate': row[2],
                'term_days': row[3],
                'issued_at': row[4],
                'due_date': row[5],
                'remaining': row[6],
                'status': row[7]
            }
        except Exception as e:
            print(f"Ошибка get_loan_by_id: {e}")
            return None

    def repay_loan(self, user_id: int, loan_id: int, amount: float) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            # Снижаем остаток
            pizdabol.execute('''
                UPDATE loans SET remaining = MAX(remaining - ?, 0)
                WHERE id = ? AND user_id = ? AND status = 'active'
            ''', (amount, loan_id, user_id))
            # Закрываем если выплачен
            pizdabol.execute('''
                UPDATE loans SET status = 'closed'
                WHERE id = ? AND user_id = ? AND remaining <= 0 AND status = 'active'
            ''', (loan_id, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при погашении кредита: {e}")
            return False

    # ------------------- Новые механики: инвестиции -------------------
    def create_investment(self, user_id: int, business_id: Optional[int], strategy: str,
                          amount: float, expected_return: float, matures_at: str) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            # Волатильность зависит от стратегии
            strategy_volatility = {
                'conservative': 0.02,
                'balanced': 0.05,
                'aggressive': 0.10
            }.get(strategy, 0.05)
            pizdabol.execute('''
                INSERT INTO investments (
                    user_id, business_id, strategy, amount, expected_return,
                    matures_at, status, current_value, volatility, last_price_update
                )
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, business_id, strategy, amount, expected_return, matures_at, amount, strategy_volatility))
            investment_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return investment_id
        except Exception as e:
            print(f"Ошибка при создании инвестиции: {e}")
            return None

    def get_investments(self, user_id: int) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, business_id, strategy, amount, expected_return, created_at, matures_at, status,
                       COALESCE(current_value, amount) as current_value, COALESCE(volatility, 0.05) as volatility
                FROM investments WHERE user_id = ? AND status IN ('active','matured')
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = pizdabol.fetchall()
            conn.close()
            result = []
            for row in rows:
                result.append({
                    'id': row[0],
                    'business_id': row[1],
                    'strategy': row[2],
                    'amount': row[3],
                    'expected_return': row[4],
                    'created_at': row[5],
                    'matures_at': row[6],
                    'status': row[7],
                    'current_value': row[8],
                    'volatility': row[9]
                })
            return result
        except Exception as e:
            print(f"Ошибка при получении инвестиций: {e}")
            return []

    def mark_matured_investments(self):
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                UPDATE investments SET status = 'matured'
                WHERE status = 'active' AND datetime(matures_at) <= datetime('now')
            ''')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении статуса инвестиций: {e}")
            return False

    def claim_investment(self, user_id: int, investment_id: int) -> Optional[float]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT amount, expected_return, status, COALESCE(current_value, amount) as current_value FROM investments
                WHERE id = ? AND user_id = ?
            ''', (investment_id, user_id))
            row = pizdabol.fetchone()
            if not row:
                conn.close()
                return None
            amount, expected_return, status, current_value = row
            if status != 'matured':
                conn.close()
                return None
            # Выплачиваем текущую стоимость (динамическую)
            total = max(0.0, float(current_value))
            pizdabol.execute('''
                UPDATE investments SET status = 'claimed' WHERE id = ? AND user_id = ?
            ''', (investment_id, user_id))
            conn.commit()
            conn.close()
            return total
        except Exception as e:
            print(f"Ошибка при получении инвестиции: {e}")
            return None

    def update_investment_prices(self) -> bool:
        """Случайно обновляет стоимость активных инвестиций в пределах волатильности."""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, COALESCE(current_value, amount) as current_value, COALESCE(volatility, 0.05) as volatility
                FROM investments
                WHERE status = 'active'
            ''')
            rows = pizdabol.fetchall()
            for inv_id, current_value, volatility in rows:
                try:
                    current_value = float(current_value or 0)
                    volatility = float(volatility or 0.05)
                    # Случайное изменение в диапазоне [-volatility, +volatility]
                    change_ratio = random.uniform(-volatility, volatility)
                    new_value = max(0.0, current_value * (1.0 + change_ratio))
                    pizdabol.execute('''
                        UPDATE investments
                        SET current_value = ?, last_price_update = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (new_value, inv_id))
                except Exception as _:
                    continue
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении стоимости инвестиций: {e}")
            return False

    def withdraw_investment(self, user_id: int, investment_id: int) -> Optional[Tuple[float, str]]:
        """Досрочный вывод средств. Возвращает (сумма_к_выплате, статус_до) или None."""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT status, COALESCE(current_value, amount) as current_value
                FROM investments
                WHERE id = ? AND user_id = ? AND status IN ('active','matured')
            ''', (investment_id, user_id))
            row = pizdabol.fetchone()
            if not row:
                conn.close()
                return None
            status, current_value = row
            current_value = max(0.0, float(current_value))
            # Штраф 5% при досрочном выводе, без штрафа если уже matured
            penalty = 0.0 if status == 'matured' else 0.05
            payout = max(0.0, current_value * (1.0 - penalty))
            pizdabol.execute('''
                UPDATE investments SET status = 'withdrawn' WHERE id = ? AND user_id = ?
            ''', (investment_id, user_id))
            conn.commit()
            conn.close()
            return (payout, status)
        except Exception as e:
            print(f"Ошибка при досрочном выводе инвестиций: {e}")
            return None

    # ------------------- Вспомогательные обновления игрока -------------------
    def update_player_popularity(self, user_id: int, delta: float) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                UPDATE players SET popularity = MAX(popularity + ?, 0), last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (delta, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении популярности: {e}")
            return False

    def add_experience(self, user_id: int, gained: int) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                UPDATE players SET experience = experience + ?, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (gained, user_id))
            pizdabol.execute('SELECT experience FROM players WHERE user_id = ?', (user_id,))
            exp = pizdabol.fetchone()[0]
            conn.commit()
            conn.close()
            return exp
        except Exception as e:
            print(f"Ошибка при добавлении опыта: {e}")
            return None

    def apply_level_up(self, user_id: int, new_level: int, remaining_experience: int,
                       balance_bonus: float, popularity_bonus: float) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                UPDATE players
                SET level = ?, experience = ?,
                    balance = balance + ?, popularity = popularity + ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_level, remaining_experience, balance_bonus, popularity_bonus, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при применении повышения уровня: {e}")
            return False

    # ------------------- Продукция -------------------
    def create_production(self, business_id: int, prod_type: str, name: str, version: int,
                          ready_at: str, quantity: float, meta: Dict) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                INSERT INTO productions (business_id, prod_type, name, version, ready_at, quantity, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (business_id, prod_type, name, version, ready_at, quantity, json.dumps(meta or {})))
            prod_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return prod_id
        except Exception as e:
            print(f"Ошибка create_production: {e}")
            return None

    def get_business_productions(self, business_id: int) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, prod_type, name, version, status, started_at, ready_at, quantity, meta
                FROM productions
                WHERE business_id = ?
                ORDER BY id DESC
            ''', (business_id,))
            rows = pizdabol.fetchall()
            conn.close()
            res = []
            for row in rows:
                res.append({
                    'id': row[0], 'prod_type': row[1], 'name': row[2], 'version': row[3], 'status': row[4],
                    'started_at': row[5], 'ready_at': row[6], 'quantity': row[7], 'meta': json.loads(row[8] or '{}')
                })
            return res
        except Exception as e:
            print(f"Ошибка get_business_productions: {e}")
            return []

    def set_production_status(self, prod_id: int, status: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('UPDATE productions SET status = ? WHERE id = ?', (status, prod_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка set_production_status: {e}")
            return False

    def collect_production(self, prod_id: int, user_id_check: int) -> Optional[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT p.business_id, p.prod_type, p.name, p.version, p.status, p.ready_at, p.quantity, p.meta, b.user_id
                FROM productions p
                JOIN businesses b ON b.id = p.business_id
                WHERE p.id = ?
            ''', (prod_id,))
            row = pizdabol.fetchone()
            if not row:
                conn.close()
                return None
            business_id, prod_type, name, version, status, ready_at, quantity, meta, user_id = row
            # Проверка владельца
            if user_id != user_id_check:
                conn.close()
                return None
            # Помечаем как collected, но только если уже готово и ранее не было собрано
            # Помечаем как collected, но только если уже готово
            pizdabol.execute('''
                UPDATE productions SET status = 'collected' 
                WHERE id = ? AND datetime(ready_at) <= datetime('now') AND status != 'collected'
            ''', (prod_id,))
            updated = pizdabol.rowcount
            conn.commit()
            conn.close()
            if updated == 0:
                # Не готово или уже собрано
                return None
            return {
                'business_id': business_id,
                'prod_type': prod_type,
                'name': name,
                'version': version,
                'quantity': quantity,
                'meta': json.loads(meta or '{}'),
                'user_id': user_id  
            }
        except Exception as e:
            print(f"Ошибка collect_production: {e}")
            return None

    # ------------------- PvP: профили и матчи -------------------
    def ensure_pvp_profile(self, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('INSERT OR IGNORE INTO pvp_profiles (user_id) VALUES (?)', (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка ensure_pvp_profile: {e}")
            return False

    def get_pvp_profile(self, user_id: int) -> Optional[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('SELECT user_id, rating, wins, losses, streak, cooldown_until FROM pvp_profiles WHERE user_id = ?', (user_id,))
            row = pizdabol.fetchone()
            conn.close()
            if not row:
                return None
            return {
                'user_id': row[0],
                'rating': row[1],
                'wins': row[2],
                'losses': row[3],
                'streak': row[4],
                'cooldown_until': row[5]
            }
        except Exception as e:
            print(f"Ошибка get_pvp_profile: {e}")
            return None

    def record_pvp_match(self, challenger_id: int, opponent_id: int, winner_id: Optional[int], loser_id: Optional[int],
                         bet: float, challenger_power: float, opponent_power: float, outcome: str) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                INSERT INTO pvp_matches (challenger_id, opponent_id, winner_id, loser_id, bet, challenger_power, opponent_power, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (challenger_id, opponent_id, winner_id, loser_id, bet, challenger_power, opponent_power, outcome))
            match_id = pizdabol.lastrowid
            conn.commit()
            conn.close()
            return match_id
        except Exception as e:
            print(f"Ошибка record_pvp_match: {e}")
            return None

    def update_pvp_ratings_after_match(self, winner_id: int, loser_id: int, k_factor: float = 32.0) -> Tuple[Optional[float], Optional[float]]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('INSERT OR IGNORE INTO pvp_profiles (user_id) VALUES (?)', (winner_id,))
            pizdabol.execute('INSERT OR IGNORE INTO pvp_profiles (user_id) VALUES (?)', (loser_id,))
            pizdabol.execute('SELECT rating FROM pvp_profiles WHERE user_id = ?', (winner_id,))
            w_rating = pizdabol.fetchone()[0]
            pizdabol.execute('SELECT rating FROM pvp_profiles WHERE user_id = ?', (loser_id,))
            l_rating = pizdabol.fetchone()[0]
            import math
            expected_w = 1.0 / (1.0 + math.pow(10, (l_rating - w_rating) / 400.0))
            expected_l = 1.0 - expected_w
            new_w = w_rating + k_factor * (1 - expected_w)
            new_l = l_rating + k_factor * (0 - expected_l)
            pizdabol.execute('''
                UPDATE pvp_profiles SET rating = ?, wins = wins + 1, streak = CASE WHEN streak >= 0 THEN streak + 1 ELSE 1 END,
                    last_fight_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_w, winner_id))
            pizdabol.execute('''
                UPDATE pvp_profiles SET rating = ?, losses = losses + 1, streak = CASE WHEN streak <= 0 THEN streak - 1 ELSE -1 END,
                    last_fight_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_l, loser_id))
            conn.commit()
            conn.close()
            return new_w, new_l
        except Exception as e:
            print(f"Ошибка update_pvp_ratings_after_match: {e}")
            return None, None

    def get_pvp_matches(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT id, challenger_id, opponent_id, winner_id, loser_id, bet, challenger_power, opponent_power, outcome, created_at
                FROM pvp_matches
                WHERE challenger_id = ? OR opponent_id = ?
                ORDER BY id DESC LIMIT ?
            ''', (user_id, user_id, limit))
            rows = pizdabol.fetchall()
            conn.close()
            result = []
            for row in rows:
                result.append({
                    'id': row[0],
                    'challenger_id': row[1],
                    'opponent_id': row[2],
                    'winner_id': row[3],
                    'loser_id': row[4],
                    'bet': row[5],
                    'challenger_power': row[6],
                    'opponent_power': row[7],
                    'outcome': row[8],
                    'created_at': row[9]
                })
            return result
        except Exception as e:
            print(f"Ошибка get_pvp_matches: {e}")
            return []

    def get_pvp_top(self, limit: int = 10) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                SELECT p.user_id, p.username, p.first_name, pp.rating, pp.wins, pp.losses
                FROM pvp_profiles pp
                JOIN players p ON p.user_id = pp.user_id
                ORDER BY pp.rating DESC
                LIMIT ?
            ''', (limit,))
            rows = pizdabol.fetchall()
            conn.close()
            result = []
            for i, row in enumerate(rows):
                result.append({
                    'rank': i + 1,
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'rating': row[3],
                    'wins': row[4],
                    'losses': row[5]
                })
            return result
        except Exception as e:
            print(f"Ошибка get_pvp_top: {e}")
            return []

    def set_pvp_cooldown(self, user_id: int, seconds: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('''
                UPDATE pvp_profiles SET cooldown_until = datetime('now', ?)
                WHERE user_id = ?
            ''', (f'+{seconds} seconds', user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка set_pvp_cooldown: {e}")
            return False

    def pvp_cooldown_remaining(self, user_id: int) -> int:
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            pizdabol.execute('SELECT COALESCE((strftime("%s", cooldown_until) - strftime("%s", "now")), 0) FROM pvp_profiles WHERE user_id = ?', (user_id,))
            row = pizdabol.fetchone()
            conn.close()
            if not row or row[0] is None:
                return 0
            remaining = int(row[0])
            return remaining if remaining > 0 else 0
        except Exception as e:
            print(f"Ошибка pvp_cooldown_remaining: {e}")
            return 0
    def set_cooldown(self, user_id: int, action_type: str, minutes: int) -> bool:
            """Установить кулдаун для действия"""
            try:
                conn = sqlite3.connect(self.db_path)
                pizdabol = conn.cursor()
                pizdabol.execute('''
                    INSERT OR REPLACE INTO cooldowns (user_id, action_type, expires_at)
                    VALUES (?, ?, datetime('now', '+{} minutes'))
                '''.format(minutes), (user_id, action_type))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Ошибка set_cooldown: {e}")
                return False

    def get_cooldown_remaining(self, user_id: int, action_type: str) -> int:
                """Получить оставшееся время кулдауна в секундах"""
                try:
                    conn = sqlite3.connect(self.db_path)
                    pizdabol = conn.cursor()
                    pizdabol.execute('''
                        SELECT COALESCE((strftime("%s", expires_at) - strftime("%s", "now")), 0)
                        FROM cooldowns 
                        WHERE user_id = ? AND action_type = ?
                    ''', (user_id, action_type))
                    row = pizdabol.fetchone()
                    conn.close()
                    if not row or row[0] is None:
                        return 0
                    remaining = int(row[0])
                    return remaining if remaining > 0 else 0
                except Exception as e:
                    print(f"Ошибка get_cooldown_remaining: {e}")
                    return 0

    def sell_business(self, user_id: int, business_id: int) -> Dict:
        """Продаём бизнес ((((Я мистер бiзnуs))))"""
        try:
            conn = sqlite3.connect(self.db_path)
            pizdabol = conn.cursor()
            
            # Получаем информацию о бизнесе
            pizdabol.execute('''
                SELECT business_type, level, improvements, income, expenses
                FROM businesses 
                WHERE id = ? AND user_id = ?
            ''', (business_id, user_id))
            business_data = pizdabol.fetchone()
            
            if not business_data:
                conn.close()
                return {'success': False, 'message': 'Бизнес не найден'}
            
            business_type, level, improvements_json, income, expenses = business_data
            improvements = json.loads(improvements_json) if improvements_json else []
            
            # Рассчитываем стоимость продажи
            # Базовая стоимость = доход * 10 + стоимость улучшений * 0.7
            base_value = income * 10
            improvements_value = 0
            
            from config import IMPROVEMENTS
            for improvement in improvements:
                if improvement in IMPROVEMENTS:
                    improvements_value += IMPROVEMENTS[improvement]['cost'] * 0.7
            
            # Бонус за уровень бизнеса
            level_bonus = (level - 1) * 1000
            
            total_value = base_value + improvements_value + level_bonus
            
            # Обновляем баланс игрока
            pizdabol.execute('''
                UPDATE players 
                SET balance = balance + ?
                WHERE user_id = ?
            ''', (total_value, user_id))
            
            # Удаляем бизнес
            pizdabol.execute('DELETE FROM businesses WHERE id = ?', (business_id,))
            
            # Записываем транзакцию
            pizdabol.execute('''
                INSERT INTO transactions (user_id, business_id, type, amount, description)
                VALUES (?, ?, 'business_sale', ?, 'Продажа бизнеса')
            ''', (user_id, business_id, total_value))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True, 
                'sale_price': total_value,
                'message': f'Бизнес продан за {total_value:,.0f} ₽'
            }
            
        except Exception as e:
            print(f"Ошибка sell_business: {e}")
            return {'success': False, 'message': 'Ошибка при продаже бизнеса'}
