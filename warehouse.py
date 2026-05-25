import sqlite3
from abc import ABC, abstractmethod


# КЛАСС ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
class Database:
    def __init__(self, db_name="warehouse.db"):
        self._connection = sqlite3.connect(db_name)
        self._cursor = self._connection.cursor()
        self._create_tables()

    def _create_tables(self):
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)
        self._connection.commit()

    def execute_query(self, query, params=()):
        self._cursor.execute(query, params)
        self._connection.commit()
        return self._cursor

    def close(self):
        self._connection.close()


# КЛАСС ТОВАР
class Product:
    def __init__(self, name, quantity, price, product_id=None):
        self._id = product_id
        self._name = name
        self._quantity = quantity
        self._price = price

    def get_info(self):
        return {"id": self._id, "name": self._name, "quantity": self._quantity, "price": self._price}

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def quantity(self):
        return self._quantity

    @property
    def price(self):
        return self._price


# БАЗОВЫЙ АБСТРАКТНЫЙ КЛАСС ОПЕРАЦИЯ
class Operation(ABC):
    def __init__(self, db):
        self._db = db

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass


# ОПЕРАЦИЯ ДОБАВЛЕНИЯ
class AddOperation(Operation):
    def execute(self, name, quantity, price):
        self._db.execute_query(
            "INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)",
            (name, quantity, price)
        )
        print(f"Товар '{name}' успешно добавлен")


# ОПЕРАЦИЯ ПОСТУПЛЕНИЯ
class IncomingOperation(Operation):
    def execute(self, product_id, amount):
        self._db.execute_query(
            "UPDATE products SET quantity = quantity + ? WHERE id = ?",
            (amount, product_id)
        )
        print(f"Поступление: количество товара id={product_id} увеличено на {amount}")


# ОПЕРАЦИЯ СПИСАНИЯ
class OutgoingOperation(Operation):
    def execute(self, product_id, amount):
        cursor = self._db.execute_query("SELECT quantity FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        if result and result[0] >= amount:
            self._db.execute_query(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (amount, product_id)
            )
            print(f"Списание: количество товара id={product_id} уменьшено на {amount}")
            return True
        else:
            print("Ошибка: недостаточно товара на складе")
            return False


# ОПЕРАЦИЯ УДАЛЕНИЯ (ДОБАВЛЕНИЕ 1)
class DeleteOperation(Operation):
    def execute(self, product_id):
        cursor = self._db.execute_query("SELECT name FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        if result:
            self._db.execute_query("DELETE FROM products WHERE id = ?", (product_id,))
            print(f"Товар с id={product_id} успешно удалён")
            return True
        else:
            print(f"Ошибка: товар с id={product_id} не найден")
            return False


# КЛАСС СКЛАД
class Warehouse:
    def __init__(self):
        self._db = Database()
        self._add_op = AddOperation(self._db)
        self._incoming_op = IncomingOperation(self._db)
        self._outgoing_op = OutgoingOperation(self._db)
        self._delete_op = DeleteOperation(self._db)

    def add_product(self, name, quantity, price):
        self._add_op.execute(name, quantity, price)

    def get_all_products(self):
        cursor = self._db.execute_query("SELECT * FROM products")
        return cursor.fetchall()

    def increase_quantity(self, product_id, amount):
        self._incoming_op.execute(product_id, amount)

    def decrease_quantity(self, product_id, amount):
        return self._outgoing_op.execute(product_id, amount)

    def delete_product(self, product_id):
        return self._delete_op.execute(product_id)

    # ПОИСК ТОВАРА (ДОБАВЛЕНИЕ 2)
    def find_product_by_name(self, name):
        cursor = self._db.execute_query(
            "SELECT * FROM products WHERE name LIKE ?", (f"%{name}%",)
        )
        return cursor.fetchall()

    def show_products(self, products=None):
        if products is None:
            products = self.get_all_products()
        if not products:
            print("Список товаров пуст")
            return
        print("\n" + "=" * 65)
        print(f"{'ID':<5} {'Наименование':<30} {'Количество':<12} {'Цена':<10}")
        print("-" * 65)
        for p in products:
            print(f"{p[0]:<5} {p[1]:<30} {p[2]:<12} {p[3]:<10}")
        print("=" * 65 + "\n")

    def close(self):
        self._db.close()


# ФУНКЦИИ ДЛЯ БЕЗОПАСНОГО ВВОДА
def get_positive_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("Ошибка: значение должно быть положительным")
        except ValueError:
            print("Ошибка: введите целое число")


def get_nonnegative_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value >= 0:
                return value
            print("Ошибка: значение не может быть отрицательным")
        except ValueError:
            print("Ошибка: введите целое число")


def get_positive_float(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value >= 0:
                return value
            print("Ошибка: цена не может быть отрицательной")
        except ValueError:
            print("Ошибка: введите число")


# ГЛАВНОЕ МЕНЮ
def main_menu():
    warehouse = Warehouse()
    while True:
        print("\n" + "=" * 55)
        print("        СИСТЕМА СКЛАДСКОГО УЧЁТА")
        print("=" * 55)
        print("1  - Добавить товар")
        print("2  - Просмотреть все товары")
        print("3  - Поступление товара")
        print("4  - Списание товара")
        print("5  - Удалить товар")
        print("6  - Поиск товара по названию")
        print("0  - Выйти")
        print("-" * 55)

        choice = input("Выберите действие: ")

        if choice == "1":
            name = input("Наименование товара: ")
            if not name.strip():
                print("Ошибка: наименование не может быть пустым")
                continue
            quantity = get_nonnegative_int("Количество: ")
            price = get_positive_float("Цена: ")
            warehouse.add_product(name, quantity, price)
        elif choice == "2":
            warehouse.show_products()
        elif choice == "3":
            product_id = get_positive_int("ID товара: ")
            amount = get_positive_int("Количество поступления: ")
            warehouse.increase_quantity(product_id, amount)
        elif choice == "4":
            product_id = get_positive_int("ID товара: ")
            amount = get_positive_int("Количество списания: ")
            warehouse.decrease_quantity(product_id, amount)
        elif choice == "5":
            product_id = get_positive_int("ID товара для удаления: ")
            warehouse.delete_product(product_id)
        elif choice == "6":
            keyword = input("Введите название (или часть названия) товара: ")
            if not keyword.strip():
                print("Ошибка: введите текст для поиска")
                continue
            results = warehouse.find_product_by_name(keyword)
            if not results:
                print(f"Товары, содержащие '{keyword}', не найдены")
            else:
                print(f"\nРезультаты поиска по запросу '{keyword}':")
                warehouse.show_products(results)
        elif choice == "0":
            warehouse.close()
            print("До свидания!")
            break
        else:
            print("Ошибка: выберите пункт от 0 до 6")


if __name__ == "__main__":
    main_menu()