# telegramm-parser-news
## Telegram messages parser
* `parsing.py` - скрипт который парсит последние сообщения 
из вашего telegram канала,которые содержат текст. и добавляет их в БД, 
используя в качестве СУБД SQLite.
## Web application
* `main.py` - FastAPI приложение возращающая в JSON последние сообщения
* `database.py` - Содержит Класс БД, реализующий необходимый методы по работе с ней
* `models.py` - Содержит структуру сообщения 
## Requirements
* `python3.10`
* `requirements.txt`
## ENV STRUCTURE
приложение оптимизировано для запуска ТОЛЬКО в docker контейнере и все дальнейшие шаги подразумевают его использование, поэтому .env
должно создаваться в директории docker/
### ENV FOR PARSING SERVICE
* CHANNEL_ID = Индификатор канала можно получить в этом [боте](https://t.me/userinfobot)
* CHANNEL_NAME = Название из ссылки только ПУБЛИЧНОГО Telegram канала
* API_ID = Надо создать приложения [Telegram](https://my.telegram.org/auth?to=apps)
* API_HASH = Надо создать приложения [Telegram](https://my.telegram.org/auth?to=apps) 
* TIME_FOR_UPDATE = время(секунды) ожидания повторного парсинга Telegram канала
* CODE = 0 Код подтверждения, придет в 1 раз при включении, при повторном запуске использовать тот же код, по умолчанию ДОЛЖЕН БЫТЬ 0
* PHONE = Номер телефона к которому привязано ваше [Telegram](https://my.telegram.org/auth?to=apps) приложение
* ROOT_DIR = / оставить как есть
* PARSING_ROOT_DIR = / оставить как есть

### ENV FOR WEB API APPLICATION
* WEB_APPLICATION_ROOT_DIR = / оставить как есть
* NAME_DB=messages.db оставить как есть
* DOMAIN = свой домен или ip адрес 
* PROTOCOL = http или https 
* NAME_TABLE_MESSAGES=Messages оставить как есть
* TELEGRAM_CHANNEL = Название ПУБЛИЧНОГО Telegram канала без t.me/
## DOCKER RUN
* переходим в docker/ и собираем 2 образа
```ini  
docker build -f DockerfileApp . -t web-app:v1
docker build -f DockerfileParser . -t parsing:v1
```
* затем запускаем контейнер PARSING (после входа, придет код для в телеграмм, введите его для успешного создания сессии
и выйдите из контейнера, после успешой авторизации, затем замените значение CODE в .env c 0 на введеный код)
```ini 
docker compose run --rm -it PARSING 
```
* останавливаем и удаляем контейнеры
```ini 
docker compose down
```
* Финальным шагом запускаем все контейнеры
```ini 
docker compose up -d
```
## CREATE DAEMON
пример демона который вы можете использовать в своей среде для автоматизации запуска:
```ini
touch news.service
```
заходим и прописываем схожую конфигурацию 
```ini
[Unit]
Description=Docker Compose New Application
Requires=docker.service
After=docker.service

[Service]
Type=simple
WorkingDirectory=/telegramm-parser-bot/docker
ExecStartPre=-/usr/bin/docker compose down
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```
обновлем конфигурацию
```ini
systemctl daemon-reload
```
включаем и запускаем демона
```ini
systemctl enable news
systemctl start news
```
смотрим чтобы все было зеленым
```ini
systemctl status news
``` 
если возникли ошибки проверьте ещё раз конфигурацию


