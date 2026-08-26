# Деплой на Render.com — ПОШАГОВАЯ ИНСТРУКЦИЯ

Самый простой способ запустить бота бесплатно. Следуйте шагам точно.

---

## ШАГ 1. Авторизация на локальном компьютере (5 минут)

1. Откройте командную строку в папке проекта:
   ```bash
   cd C:\Users\unluc\CascadeProjects\spaxrize
   ```

2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```

3. Активируйте его:
   ```bash
   venv\Scripts\activate
   ```

4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

5. Запустите авторизацию:
   ```bash
   python auth.py
   ```

6. Введите номер телефона (с +, например: `+79991234567`)

7. Введите код из Telegram

8. Если спросят пароль 2FA — введите

✅ Готово! Сессия сохранена в `data/watcher_session.session`

---

## ШАГ 2. Загрузка на GitHub (5 минут)

1. Зайдите на [github.com](https://github.com) и войдите

2. Создайте новый репозиторий:
   - Нажмите `+` → `New repository`
   - Name: `spaxrize`
   - Public
   - Нажмите `Create repository`

3. В папке проекта откройте командную строку и выполните:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/ВАШ_НИК/spaxrize.git
   git push -u origin main
   ```

   Замените `ВАШ_НИК` на ваш никнейм в GitHub

✅ Готово! Проект загружен на GitHub

---

## ШАГ 3. Регистрация на Render (2 минуты)

1. Зайдите на [render.com](https://render.com)

2. Нажмите `Sign Up`

3. Войдите через GitHub (проще всего)

4. Подтвердите email если спросят

✅ Готово! Аккаунт создан

---

## ШАГ 4. Создание Web Service (3 минуты)

1. На Render нажмите `New +` → `Web Service`

2. Нажмите `Connect GitHub`

3. Если спросит доступ — разрешите

4. Выберите репозиторий `spaxrize`

5. Заполните форму:
   - **Name**: `spaxrize`
   - **Region**: `Oregon (US West)` или любой другой
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python generate_banner.py`
   - **Start Command**: `python main.py`

6. Нажмите `Advanced` → `Add Environment Variable`

7. Добавьте переменные (по одной):

   ```
   Name: API_ID
   Value: 31576834
   ```

   ```
   Name: API_HASH
   Value: ad6503561fd24c4161fecbef2d17e1c3
   ```

   ```
   Name: BOT_TOKEN
   Value: 8857311670:AAHC89KJO399SGZ3z6OYzwM-N3MmS8FWobE
   ```

   ```
   Name: SESSION
   Value: watcher_session
   ```

   ```
   Name: LOG_LEVEL
   Value: INFO
   ```

   ```
   Name: PORT
   Value: 8080
   ```

   ```
   Name: PING_INTERVAL
   Value: 300
   ```

8. Нажмите `Create Web Service`

✅ Сервис создан! Начнётся сборка (1-2 минуты)

---

## ШАГ 5. Авторизация на Render (5 минут)

1. После сборки сервис упадёт (красный статус) — это нормально

2. Нажмите на сервис → `Logs`

3. Вверху нажмите `Shell` (или `Console`)

4. В открывшемся терминале введите:
   ```bash
   python auth.py
   ```

5. Введите номер телефона (с +)

6. Введите код из Telegram

7. После успешной авторизации закройте Shell

8. Нажмите `Manual Deploy` → `Clear build cache & deploy`

✅ Готово! Сервис запустится

---

## ШАГ 6. Проверка работы (1 минута)

1. На странице сервиса посмотрите статус — должен быть зелёным

2. Откройте Telegram → найдите бота

3. Нажмите `/start`

4. Нажмите кнопку «🩸 Добавить в автоматизацию»

5. Бот должен ответить «✅ Успешно добавлено!»

✅ Бот работает!

---

## ШАГ 7. Дополнительный пинг (опционально, но рекомендуется)

Для надёжности добавьте внешний пинг:

1. Зайдите на [uptimerobot.com](https://uptimerobot.com)

2. Зарегистрируйтесь (бесплатно)

3. Нажмите `Add New Monitor`

4. Заполните:
   - **Monitor Type**: `HTTP`
   - **Friendly Name**: `SPAXRIZE`
   - **URL**: скопируйте URL вашего сервиса на Render (вверху страницы) + `/health`
     - Пример: `https://spaxrize.onrender.com/health`
   - **Interval**: `5 minutes`

5. Нажмите `Create Monitor`

✅ Готово! Теперь бот будет пинговаться каждые 5 минут

---

## Если что-то не работает

**Сервис красный после деплоя:**
- Посмотрите Logs — там написана ошибка
- Скорее всего нет сессии — выполните ШАГ 5

**Бот не отвечает на команды:**
- Проверьте статус сервиса (должен быть зелёным)
- Посмотрите Logs — есть ли ошибки

**Ошибка авторизации:**
- Удалите сессию: в Shell на Render выполните `rm data/watcher_session.session`
- Повторите ШАГ 5

---

## Кратко

1. Авторизуйтесь локально: `python auth.py`
2. Загрузите на GitHub
3. Создайте Web Service на Render
4. Добавьте переменные окружения
5. Авторизуйтесь в Shell на Render
6. Активируйте бота в Telegram

Готово! Бот работает бесплатно на Render.
