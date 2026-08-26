# Деплой SPAXRIZE на VPS (облачный сервер)

Инструкция по запуску бота на облачном сервере для работы 24/7 без включённого ПК.

## Выбор VPS

Рекомендуемые провайдеры (доступны в РФ):
- **Timeweb Cloud** (timeweb.cloud) — от 150₽/мес
- **Selectel** (selectel.ru) — от 200₽/мес
- **Reg.ru** (reg.ru) — от 180₽/мес

Минимальные требования:
- 1 CPU
- 512 MB RAM
- 5 GB SSD
- Ubuntu 22.04 / Debian 12

## Шаг 1. Подготовка локально

### 1.1. Авторизация Telethon

Сначала авторизуйтесь на локальном компьютере:

```bash
cd spaxrize
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python auth.py
```

Введите номер телефона и код из Telegram. Сессия сохранится в `data/watcher_session.session`.

### 1.2. Подготовка файлов для деплоя

Скопируйте следующие файлы на сервер:
- `.env`
- `data/watcher_session.session`
- Все файлы проекта (или используйте git)

## Шаг 2. Настройка VPS

### 2.1. Подключение к серверу

```bash
ssh root@your-server-ip
```

### 2.2. Установка Docker

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка docker-compose
apt install docker-compose -y

# Проверка
docker --version
docker-compose --version
```

### 2.3. Создание директории проекта

```bash
mkdir -p /opt/spaxrize
cd /opt/spaxrize
```

### 2.4. Загрузка файлов на сервер

**Вариант A: Через git**
```bash
git clone <your-repo-url> .
```

**Вариант B: Через scp (с локального компьютера)**
```bash
scp -r . root@your-server-ip:/opt/spaxrize
```

**Вариант C: Через SFTP (WinSCP, FileZilla)**

### 2.5. Проверка .env

Убедитесь, что `.env` на сервере содержит правильные креды:
```ini
API_ID=31576834
API_HASH=ad6503561fd24c4161fecbef2d17e1c3
BOT_TOKEN=8857311670:AAHC89KJO399SGZ3z6OYzwM-N3MmS8FWobE
SESSION=watcher_session
LOG_LEVEL=INFO
```

## Шаг 3. Запуск через Docker

### 3.1. Сборка и запуск

```bash
cd /opt/spaxrize
docker-compose up -d --build
```

### 3.2. Просмотр логов

```bash
docker-compose logs -f
```

### 3.3. Проверка статуса

```bash
docker-compose ps
```

### 3.4. Остановка

```bash
docker-compose down
```

### 3.5. Перезапуск

```bash
docker-compose restart
```

## Шаг 4. Альтернатива: запуск без Docker

Если Docker недоступен:

### 4.1. Установка Python

```bash
apt update
apt install python3 python3-pip python3-venv -y
```

### 4.2. Настройка проекта

```bash
cd /opt/spaxrize
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.3. Создание systemd сервиса

```bash
nano /etc/systemd/system/spaxrize.service
```

Содержимое:
```ini
[Unit]
Description=SPAXRIZE Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/spaxrize
Environment="PATH=/opt/spaxrize/venv/bin"
ExecStart=/opt/spaxrize/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.4. Запуск сервиса

```bash
systemctl daemon-reload
systemctl enable spaxrize
systemctl start spaxrize
systemctl status spaxrize
```

## Шаг 5. Активация бота

1. Откройте бота в Telegram
2. Нажмите `/start`
3. Нажмите «🩸 Добавить в автоматизацию»

## Мониторинг

### Просмотр логов (Docker)
```bash
docker-compose logs -f
```

### Просмотр логов (systemd)
```bash
journalctl -u spaxrize -f
```

### Проверка ресурсов
```bash
htop
```

## Обновление

### Docker
```bash
cd /opt/spaxrize
git pull
docker-compose down
docker-compose up -d --build
```

### Systemd
```bash
cd /opt/spaxrize
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart spaxrize
```

## Безопасность

1. **Закройте ненужные порты** (оставьте только 22 для SSH)
2. **Используйте SSH-ключи** вместо паролей
3. **Настройте firewall** (UFW):
   ```bash
   ufw allow 22
   ufw enable
   ```
4. **Регулярно обновляйте систему**:
   ```bash
   apt update && apt upgrade -y
   ```

## Решение проблем

### Бот не запускается
- Проверьте наличие сессии `data/watcher_session.session`
- Проверьте креды в `.env`
- Посмотрите логи: `docker-compose logs`

### Ошибка авторизации
- Удалите `data/watcher_session.session`
- Запустите `python auth.py` локально
- Скопируйте новую сессию на сервер

### Бот не присылает уведомления
- Проверьте `/status` в боте
- Проверьте логи на сервере
- Убедитесь, что контейнер/сервис работает

## Стоимость

Примерная стоимость VPS в месяц:
- Timeweb: 150-300₽
- Selectel: 200-400₽
- Reg.ru: 180-350₽

Этого достаточно для работы бота 24/7.
