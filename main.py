from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine
import auth, api

# Создаёт все таблицы в базе данных, которые описаны в моделях, связанных с Base
Base.metadata.create_all(bind=engine)# Создаёт таблицы в базе

# Создаём экземпляр приложения FastAPI
app = FastAPI()
# Монтируем директорию "static" для обслуживания статических файлов ( изображений и т.д.)
app.mount("/static", StaticFiles(directory="static"), name="static")# Обслуживает статические файлы

#                              --- Аутентификация ---
app.get("/login")(auth.login_page) # Обрабатывает GET-запросы на /login, вызывает функцию отображения страницы логина
app.post("/login")(auth.login) # Обрабатывает POST-запросы на /login, вызывает функцию обработки логина
app.get("/logout")(auth.logout) # Обрабатывает GET-запросы на /logout, вызывает функцию выхода из системы
app.post("/register")(auth.register) # Обрабатывает POST-запросы на /register, вызывает функцию регистрации пользователя

#                                   --- Товары и страницы ---
app.get("/")(api.index) # Главная страница со списком товаров, GET-запрос на "/"
app.post("/add")(api.add_product) # Добавление нового товара, POST-запрос на "/add"
app.post("/delete/{product_id}")(api.delete_product) # Удаление товара по его id, POST-запрос на "/delete/{product_id}"
app.get("/admin/edit/{product_id}")(api.edit_product_form) # Форма редактирования товара, GET-запрос на "/admin/edit/{product_id}"
app.post("/admin/edit/{product_id}")(api.update_product) # Обработка обновления товара, POST-запрос на "/admin/edit/{product_id}"
app.get("/admin/users")(api.admin_dashboard) # Админская панель для просмотра пользователей и их заказов, GET-запрос на "/admin/users"


#                              --- Корзина ---
app.get("/cart")(api.view_cart) # Просмотр корзины пользователя, GET-запрос на "/cart"
app.post("/cart/add/{product_id}")(api.add_to_cart) # Добавление товара в корзину, POST-запрос на "/cart/add/{product_id}"
app.post("/cart/clear")(api.clear_cart) # Очистка корзины пользователя, POST-запрос на "/cart/clear"

#                                --- Заказы ---
app.post("/orders/create")(api.create_order) # Создание заказа из корзины, POST-запрос на "/orders/create"
app.get("/orders")(api.read_orders) # Просмотр списка заказов пользователя, GET-запрос на "/orders"
app.post("/orders/{order_id}/cancel")(api.cancel_order) # Отмена заказа по его id, POST-запрос на "/orders/{order_id}/cancel"