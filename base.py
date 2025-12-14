import sqlite3
from typing import List, Tuple, Optional, Union
from datetime import datetime


class SQL:
    def __init__(self, db_name: str = 'game_store.db'):
        """Инициализация подключения к базе данных"""
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self._initialize_database()

    def _initialize_database(self):
        """Создает все необходимые таблицы"""
        self.cursor.executescript("""
        -- Пользователи
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 500,
            status TEXT DEFAULT '',
            admin INTEGER DEFAULT 0,
            temp_name TEXT,
            temp_price INTEGER,
            temp_desc TEXT
        );

        -- Игры
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER NOT NULL,
            description TEXT DEFAULT '',
            status INTEGER DEFAULT 1
        );

        -- Заказы
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            count INTEGER DEFAULT 1,
            status INTEGER DEFAULT 0,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(game_id) REFERENCES games(id)
        );

        -- Неудавшиеся заказы (для админа)
        CREATE TABLE IF NOT EXISTS failed_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_details TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.connection.commit()

    # ============== Методы для пользователей ==============
    def add_user(self, user_id: int) -> bool:
        """Добавляет нового пользователя"""
        try:
            self.cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def user_exists(self, user_id: int) -> bool:
        """Проверяет существование пользователя в БД"""
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return bool(self.cursor.fetchone())
        except sqlite3.Error as e:
            print(f"Ошибка проверки пользователя: {e}")
            return False

    def get_user_data(self, user_id: int, field: str) -> Union[int, str, None]:
        """Получает данные пользователя с обработкой ошибок"""
        try:
            self.cursor.execute(f"SELECT {field} FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            if not result:
                return None
            return result[0]
        except sqlite3.Error as e:
            print(f"Ошибка получения данных пользователя: {e}")
            return None

    def update_user_data(self, user_id: int, field: str, value: Union[int, str]) -> bool:
        """Обновляет данные пользователя"""
        try:
            self.cursor.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user_id))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False





    def checkout(self, user_id: int) -> bool:
        """Оформление заказа"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "UPDATE orders SET status = 1, date = ? WHERE user_id = ? AND status = 0",
                (current_time, user_id)
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка оформления заказа: {e}")
            return False

    # ============== Методы для игр ==============
    def add_game(self, name: str, price: int, description: str = "") -> int:
        """Добавляет новую игру"""
        try:
            self.cursor.execute(
                "INSERT INTO games (name, price, description) VALUES (?, ?, ?)",
                (name, price, description)
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error:
            return -1

    def get_game(self, game_id: int) -> Optional[Tuple]:
        """Получает информацию об игре"""
        self.cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        return self.cursor.fetchone()

    def get_available_games(self) -> List[Tuple]:
        """Получает список доступных игр"""
        self.cursor.execute("SELECT * FROM games WHERE status = 1")
        return self.cursor.fetchall()

    # ============== Методы для корзины и заказов ==============


    def get_balance(self, user_id: int) -> Optional[int]:
        """Безопасное получение баланса"""
        try:
            self.cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Ошибка получения баланса: {e}")
            return None

    def add_user_balance(self, user_id: int, amount: int) -> bool:
        """Пополнение баланса с проверками"""
        try:
            if amount <= 0:
                return False

            self.cursor.execute(
                "UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE id = ?",
                (amount, user_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"SQL Error in add_user_balance: {e}")
            return False

    def update_cart_item(self, order_id: int, change: int) -> bool:
        """Обновление количества товара в корзине"""
        try:
            self.cursor.execute(
                "UPDATE orders SET count = count + ? WHERE id = ? AND status = 0",
                (change, order_id)
            )
            # Удаляем если количество <= 0
            self.cursor.execute("DELETE FROM orders WHERE count <= 0 AND status = 0")
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка обновления корзины: {e}")
            return False

    def remove_from_cart(self, order_id: int) -> bool:
        """Удаление товара из корзины"""
        try:
            self.cursor.execute(
                "DELETE FROM orders WHERE id = ? AND status = 0",
                (order_id,)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Ошибка удаления из корзины: {e}")
            return False

    def checkout(self, user_id: int) -> bool:
        """Оформляет заказ"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                """UPDATE orders SET status = 1, date = ?
                WHERE user_id = ? AND status = 0""",
                (current_time, user_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def add_user_balance(self, user_id: int, amount: int) -> bool:
        """Пополняет баланс пользователя"""
        try:
            self.cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE id = ?",
                (amount, user_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_cart(self, user_id: int) -> List[Tuple]:
        """Получает содержимое корзины с полной информацией о товарах"""
        self.cursor.execute(
            """SELECT o.id, g.id, g.name, g.price, o.count, g.description 
            FROM orders o 
            JOIN games g ON o.game_id = g.id
            WHERE o.user_id = ? AND o.status = 0""",
            (user_id,)
        )
        return self.cursor.fetchall()

    def add_to_cart(self, user_id: int, game_id: int) -> bool:
        """Добавляет товар в корзину или увеличивает количество"""
        try:
            # Проверяем есть ли уже такой товар в корзине
            self.cursor.execute(
                "SELECT id, count FROM orders WHERE user_id=? AND game_id=? AND status=0",
                (user_id, game_id)
            )
            existing = self.cursor.fetchone()

            if existing:
                # Увеличиваем количество
                self.cursor.execute(
                    "UPDATE orders SET count=count+1 WHERE id=?",
                    (existing[0],)
                )
            else:
                # Добавляем новый товар
                self.cursor.execute(
                    "INSERT INTO orders (user_id, game_id) VALUES (?, ?)",
                    (user_id, game_id)
                )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка добавления в корзину: {e}")
            return False

    def update_cart_item(self, order_id: int, user_id: int, change: int) -> bool:
        """Обновляет количество товара в корзине"""
        try:
            # Проверяем что товар принадлежит пользователю
            self.cursor.execute(
                "SELECT 1 FROM orders WHERE id=? AND user_id=? AND status=0",
                (order_id, user_id)
            )
            if not self.cursor.fetchone():
                return False

            if change == -1:
                # Проверяем текущее количество
                self.cursor.execute(
                    "SELECT count FROM orders WHERE id=?",
                    (order_id,)
                )
                current = self.cursor.fetchone()[0]
                if current <= 1:
                    # Удаляем если количество станет 0
                    self.cursor.execute(
                        "DELETE FROM orders WHERE id=?",
                        (order_id,)
                    )
                else:
                    self.cursor.execute(
                        "UPDATE orders SET count=count-1 WHERE id=?",
                        (order_id,)
                    )
            else:
                self.cursor.execute(
                    "UPDATE orders SET count=count+1 WHERE id=?",
                    (order_id,)
                )

            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка обновления корзины: {e}")
            return False

    def remove_from_cart(self, order_id: int, user_id: int) -> bool:
        """Полностью удаляет товар из корзины"""
        try:
            # Проверяем принадлежность товара пользователю
            self.cursor.execute(
                "DELETE FROM orders WHERE id=? AND user_id=? AND status=0",
                (order_id, user_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Ошибка удаления из корзины: {e}")
            return False

    def get_users_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def get_games_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM games")
        return self.cursor.fetchone()[0]

    def get_total_sales(self):
        self.cursor.execute("SELECT SUM(price) FROM purchases")
        result = self.cursor.fetchone()[0]
        return result if result else 0

    def get_all_users(self):
        self.cursor.execute("SELECT user_id, username, balance FROM users")
        return self.cursor.fetchall()

    def get_all_games(self):
        self.cursor.execute("SELECT id, name, price FROM games")
        return self.cursor.fetchall()
    def close(self):
        """Закрывает соединение с БД"""
        try:
            self.connection.close()
        except:
            pass

    def __enter__(self):
        """Для использования с with"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие соединения"""
        self.close()