import os, shutil
from fastapi import Request, Form, Depends, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import Product, Cart, Order, OrderItem
from auth import get_current_user
from database import get_db

templates = Jinja2Templates(directory="templates")

                   # ГЛАВНАЯ СТРАНИЦА С ТОВАРАМИ
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db) # Получаем текущего пользователя
    if not user:
        return RedirectResponse("/login", status_code=302) # Если не авторизован — перенаправляем на логин
    products = db.query(Product).all() if user.role != "admin" else db.query(Product).all() # Запрашиваем все товары из базы (для всех пользователей)
    return templates.TemplateResponse("index.html", {"request": request, "products": products, "user": user}) # Возвращаем HTML-страницу с товарами и информацией о пользователе

                    # ДОБАВЛЛЕНИЕ ТОВАР (ADMIN)
def add_product(request: Request, name: str = Form(...), price: float = Form(...), quantity: int = Form(...),
                image: UploadFile = File(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db) # Получаем пользователя
    if not user or user.role != "admin": # Проверяем права
        return RedirectResponse("/login", status_code=302)
    image_path = None
    if image:
        os.makedirs("static/images", exist_ok=True) # Создаем папку, если не существует
        path = f"static/images/{image.filename}" # Путь для сохранения файла
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f) # Копируем содержимое загруженного файла в папку
        image_path = f"images/{image.filename}" # Относительный путь для хранения в базе
    product = Product(name=name, price=price, quantity=quantity, image_path=image_path, owner_id=user.id)
    db.add(product) # Добавляем товар в сессию
    db.commit() # Сохраняем в базе
    return RedirectResponse("/", status_code=302) # Перенаправляем на главную

                  #  ФОРМА И ОБРАБОТКА РЕДАКТИРОВАНИЯ ТОВАРА
def edit_product_form(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403) # Доступ запрещен
    product = db.query(Product).get(product_id) # Получаем товар по ID
    return templates.TemplateResponse("edit_product.html", {"request": request, "product": product, "user": user})


def update_product(
        request: Request,
        product_id: int,
        name: str = Form(...),
        price: float = Form(...),
        quantity: int = Form(...),
        description: str = Form(None),
        image: UploadFile = File(None),
        db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403)

    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    product.name = name # Обновляем данные
    product.price = price
    product.quantity = quantity
    product.description = description

    if image and image.filename:
        os.makedirs("static/images", exist_ok=True)
        filename = image.filename
        image_path = f"static/images/{filename}"

        # 💡 открываем именно путь к файлу
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f) # Сохраняем новый файл

        # сохраняем относительный путь
        product.image_path = f"images/{filename}" # Обновляем путь к изображению

    db.commit()# Сохраняем изменения
    return RedirectResponse("/", status_code=302)

              # УДАЛЕНИЕ ТОВАРА
def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product and (user.role == "admin" or product.owner_id == user.id):
        db.delete(product) # Удаляем товар из базы
        db.commit()
    return RedirectResponse("/", status_code=302)

                  #  ПОКАЗАТЬ КОРЗИНУ
def view_cart(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    items = db.query(Cart).filter_by(user_id=user.id).all() # Все товары в корзине пользователя
    cart_products = []
    total = 0
    for item in items:
        subtotal = item.product.price * item.quantity # Цена за выбранное количество
        total += subtotal # Общая сумма корзины
        cart_products.append({"product": item.product, "quantity": item.quantity, "subtotal": subtotal})
    return templates.TemplateResponse("cart.html", {"request": request, "cart_products": cart_products, "user": user, "total": total})

                    # ДОБАВИТЬ ТОВАР В КОРЗИНУ
def add_to_cart(request: Request, product_id: int, quantity: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.quantity < quantity: # Проверяем наличие товара на складе
        return RedirectResponse("/", status_code=302)
    item = db.query(Cart).filter_by(user_id=user.id, product_id=product_id).first()
    if item:
        item.quantity += quantity # Если в корзине уже есть — увеличиваем количество
    else:
        db.add(Cart(user_id=user.id, product_id=product_id, quantity=quantity)) # Иначе создаем новую запись
    db.commit()
    return RedirectResponse("/cart", status_code=302)

                # ОЧИСТИТЬ КОРЗИНУ
def clear_cart(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    db.query(Cart).filter_by(user_id=user.id).delete()  # Удаляем все товары пользователя из корзины
    db.commit()
    return RedirectResponse("/cart", status_code=302)

               # ОФОРМЛЕНИЕ ЗАКАЗА
def create_order(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    cart_items = db.query(Cart).filter_by(user_id=user.id).all()
    if not cart_items:
        return RedirectResponse("/cart", status_code=302) # Если корзина пуста — перенаправляем
    order = Order(user_id=user.id)
    db.add(order) # Создаем заказ
    db.commit()  # Сохраняем, чтобы получить ID заказа
    for item in cart_items:
        db.add(OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.product.price))
        item.product.quantity -= item.quantity # Обновляем количество товара на складе
    db.query(Cart).filter_by(user_id=user.id).delete() # Очищаем корзину после оформления
    db.commit()
    return RedirectResponse("/orders", status_code=302)

                  #  ПРОСМОТР ЗАКАЗОВ ПОЛЬЗОВАТЕЛЯ
def read_orders(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    orders = db.query(Order).filter_by(user_id=user.id).all()
    for order in orders:
        order.total_price = sum(item.price * item.quantity for item in order.items) # Считаем итоговую стоимость заказа
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders, "user": user})

                  # ПРОСМОТР ВСЕХ ПОЛЬЗОВАТЕЛЕЙ И ИХ ЗАКАЗОВ
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403) # Только админ
    from models import User
    users = db.query(User).all()
    return templates.TemplateResponse("admin_users_orders.html", {"request": request, "users": users, "user": user})

               #  ОТМЕНА ЗАКАЗА И ВОЗВРАТ ТОВАРА НА СКЛАД
def cancel_order(request: Request, order_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    order = db.query(Order).filter_by(id=order_id, user_id=user.id).first()
    if not order or order.status != "в обработке":
        raise HTTPException(status_code=403, detail="Нельзя отменить этот заказ")

    # Вернуть товары на склад
    for item in order.items:
        item.product.quantity += item.quantity

    # Обновить статус заказа
    order.status = "отменён"
    db.commit()

    return RedirectResponse("/orders", status_code=302)