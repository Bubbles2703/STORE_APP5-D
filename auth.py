from fastapi import Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from models import User
from database import get_db

templates = Jinja2Templates(directory="templates")

            # ВОЗВРАЩАЕТ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ из cookie.
def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id") # Извлекаем cookie с именем "user_id" из запроса
    # Если cookie есть, ищем пользователя с таким ID в базе, иначе возвращаем None
    return db.query(User).filter(User.id == int(user_id)).first() if user_id else None

#                  СТРАНИЦА ЛОГИНА (возвращает HTML форму)
def login_page(request: Request):
    # Возвращаем шаблон "login.html" с контекстом, чтобы шаблон мог использовать request
    return templates.TemplateResponse("login.html", {"request": request})

#                  ОБРАБОТКА ЛОГИНА (входа пользователя)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Ищем пользователя по username в базе
    user = db.query(User).filter(User.username == username).first()
    # Проверяем, что пользователь существует и пароль совпадает (сравнение через bcrypt)
    if not user or not bcrypt.verify(password, user.password):
        # Если данные неверны, перенаправляем обратно на страницу логина
        return RedirectResponse("/login", status_code=302)
    # Если всё успешно, создаём редирект на главную страницу
    response = RedirectResponse("/", status_code=302)
    # Устанавливаем cookie с user_id для идентификации пользователя в последующих запросах
    response.set_cookie("user_id", str(user.id))
    return response

               # УДАЛЯЕТ COOKIE
def logout(): # Создаём редирект на страницу логина
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("user_id") # Удаляем cookie "user_id" — пользователь больше не авторизован
    return response


def register(username: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    # Проверяем, нет ли уже пользователя с таким именем
    if db.query(User).filter(User.username == username).first():
        # Если пользователь есть, перенаправляем на страницу логина (регистрация не удалась)
        return RedirectResponse("/login", status_code=302)
    # Хэшируем пароль для безопасности (не хранить пароль в открытом виде!)
    hashed = bcrypt.hash(password)
    # Создаём нового пользователя с хэшированным паролем и указанной ролью
    user = User(username=username, password=hashed, role=role, is_admin=(role == "admin"))
    db.add(user) # Добавляем пользователя в базу
    db.commit() # Сохраняем изменения
    # Перенаправляем на страницу логина, чтобы пользователь мог войти
    return RedirectResponse("/login", status_code=302)