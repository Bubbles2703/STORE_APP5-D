# Dockerfile - инструкции для запуска
#  указываем язык программирования
FROM python:3.12
# рабочая папка в контейнере
WORKDIR /store_app4
# указываем что и куда копируем
COPY . /store_app4
# занимаем порт
EXPOSE 8000
# перечисляем необходимые команды для запуска
RUN pip install --no-cache-dir -r requirements.txt
# запуск проекта
CMD ["uvicorn", "main:app","--reload"]