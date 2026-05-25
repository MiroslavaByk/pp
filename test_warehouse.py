import pytest
import sqlite3
import os
from warehouse import Database, AddOperation, IncomingOperation, OutgoingOperation, DeleteOperation, Warehouse

@pytest.fixture
def temp_db():
    db = Database("test_warehouse.db")
    yield db
    db.close()
    os.remove("test_warehouse.db")

@pytest.fixture
def warehouse():
    wh = Warehouse()
    wh._db = Database("test_warehouse.db")
    yield wh
    wh.close()
    os.remove("test_warehouse.db")

def test_database_creation(temp_db):
    cursor = temp_db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    assert cursor.fetchone() is not None

def test_insert_product(temp_db):
    temp_db.execute_query("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", ("Тест", 10, 100))
    cursor = temp_db.execute_query("SELECT * FROM products WHERE name='Тест'")
    product = cursor.fetchone()
    assert product is not None
    assert product[1] == "Тест"
    assert product[2] == 10
    assert product[3] == 100

def test_add_operation(temp_db):
    add_op = AddOperation(temp_db)
    add_op.execute("Товар1", 5, 50)
    cursor = temp_db.execute_query("SELECT * FROM products WHERE name='Товар1'")
    product = cursor.fetchone()
    assert product is not None
    assert product[2] == 5

def test_incoming_operation(temp_db):
    temp_db.execute_query("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", ("Товар2", 10, 100))
    incoming_op = IncomingOperation(temp_db)
    incoming_op.execute(1, 5)
    cursor = temp_db.execute_query("SELECT quantity FROM products WHERE id=1")
    quantity = cursor.fetchone()[0]
    assert quantity == 15

def test_outgoing_operation_success(temp_db):
    temp_db.execute_query("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", ("Товар3", 10, 100))
    outgoing_op = OutgoingOperation(temp_db)
    result = outgoing_op.execute(1, 3)
    cursor = temp_db.execute_query("SELECT quantity FROM products WHERE id=1")
    quantity = cursor.fetchone()[0]
    assert result == True
    assert quantity == 7

def test_outgoing_operation_fail(temp_db):
    temp_db.execute_query("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", ("Товар4", 5, 100))
    outgoing_op = OutgoingOperation(temp_db)
    result = outgoing_op.execute(1, 10)
    cursor = temp_db.execute_query("SELECT quantity FROM products WHERE id=1")
    quantity = cursor.fetchone()[0]
    assert result == False
    assert quantity == 5

def test_delete_operation(temp_db):
    temp_db.execute_query("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", ("Товар5", 10, 100))
    delete_op = DeleteOperation(temp_db)
    result = delete_op.execute(1)
    cursor = temp_db.execute_query("SELECT * FROM products WHERE id=1")
    assert result == True
    assert cursor.fetchone() is None

def test_warehouse_add_and_get(warehouse):
    warehouse.add_product("ИнтегрТовар1", 20, 150)
    products = warehouse.get_all_products()
    assert len(products) == 1
    assert products[0][1] == "ИнтегрТовар1"
    assert products[0][2] == 20

def test_warehouse_increase(warehouse):
    warehouse.add_product("ИнтегрТовар2", 10, 100)
    warehouse.increase_quantity(1, 5)
    products = warehouse.get_all_products()
    assert products[0][2] == 15

def test_warehouse_decrease(warehouse):
    warehouse.add_product("ИнтегрТовар3", 10, 100)
    warehouse.decrease_quantity(1, 3)
    products = warehouse.get_all_products()
    assert products[0][2] == 7

def test_warehouse_find_by_name(warehouse):
    warehouse.add_product("Тетрадь", 50, 25.5)
    warehouse.add_product("Ручка", 100, 15)
    warehouse.add_product("Карандаш", 200, 5)
    results = warehouse.find_product_by_name("руч")
    assert len(results) == 1
    assert "Ручка" in results[0][1]
