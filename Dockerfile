FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Создание директории для данных
RUN mkdir -p data media

# Генерация баннера
RUN python generate_banner.py

# Авторизация (потребуется интерактивный ввод при первом запуске)
# Для продакшена лучше предварительно создать сессию и скопировать её

# Запуск
ENV WEB_CONCURRENCY=1
CMD ["python", "main.py"]
