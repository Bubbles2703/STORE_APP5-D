from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

#                  МОДЕЛЬ ДЛЯ ХРАНЕНИЯ ПОЛЬЗОВАТЕЛЕЙ

              #  ХРАНИТ ПОЛЬЗОВАТЕЛЕЙ (id, username, role, и др.)
class User(Base):
    __tablename__ = "users" # Имя таблицы в базе
    id = Column(Integer, primary_key=True) # Уникальный ID пользователя (первичный ключ)
    username = Column(String, unique=True, index=True) # Логин пользователя, уникальный и индексированный
    password = Column(String) # Хэш пароля пользователя
    role = Column(String, default="customer") # Роль пользователя, по умолчанию "customer"
    is_admin = Column(Boolean, default=False) # Флаг, является ли пользователь админом

    # Связь с таблицей товаров, которые созданы этим пользователем
    products = relationship("Product", back_populates="owner")
    # Связь с корзиной — список товаров, добавленных пользователем
    cart_items = relationship("Cart", back_populates="user")
    # Связь с заказами пользователя
    orders = relationship("Order", back_populates="user")

               # ТОВАРЫ
class Product(Base):
    __tablename__ = "products" # Имя таблицы товаров
    id = Column(Integer, primary_key=True) # Уникальный ID товара
    name = Column(String) # Название товара
    price = Column(Float) # Цена товара
    quantity = Column(Integer, default=0) # Количество товара на складе, по умолчанию 0
    image_path = Column(String, nullable=True) # Путь к изображению товара (может быть пустым)
    description = Column(String, nullable=True) # Описание товара (может быть пустым)
    owner_id = Column(Integer, ForeignKey("users.id"))  # Владелец товара (пользователь, id из таблицы users)

    # Связь с владельцем товара
    owner = relationship("User", back_populates="products")
    # Связь с элементами корзины, где этот товар добавлен
    cart_items = relationship("Cart", back_populates="product")
    # Связь с элементами заказов, где этот товар был куплен
    order_items = relationship("OrderItem", back_populates="product")

                # СВЯЗЬ ПОЛЬЗОВАТЕЛЬ–ТОВАР С КОЛИЧЕСТВОМ
class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True) # Уникальный ID записи в корзине
    user_id = Column(Integer, ForeignKey("users.id"))  # Пользователь, которому принадлежит корзина
    product_id = Column(Integer, ForeignKey("products.id")) # Товар, который добавлен в корзину
    quantity = Column(Integer) # Количество данного товара в корзине

    # Связь с пользователем
    user = relationship("User", back_populates="cart_items")
    # Связь с товаром
    product = relationship("Product", back_populates="cart_items")

              # ЗАКАЗЫ
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="в обработке") # Статус заказа, по умолчанию "в обработке"
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата и время создания заказа (UTC)


    # Связь с пользователем, сделавшим заказ
    user = relationship("User", back_populates="orders")
    # Связь с элементами заказа (товарами в заказе)
    items = relationship("OrderItem", back_populates="order")

                    # СВЯЗЬ ЗАКАЗ–ТОВАР
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id")) # ID товара в заказе
    quantity = Column(Integer) # Количество товара в заказе
    price = Column(Float) # Цена товара на момент заказа (фиксируется)

    # Связь с заказом
    order = relationship("Order", back_populates="items")
    # Связь с товаром
    product = relationship("Product", back_populates="order_items")
