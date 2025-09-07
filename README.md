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
* CHANNEL_ID = Индификатор канала можно получить в этом [боте](https://t.me/userinfobot)
* API_ID = Надо создать приложения [Telegram](https://my.telegram.org/auth?to=apps) 
* API_HASH= Надо создать приложения [Telegram](https://my.telegram.org/auth?to=apps)
* TIME_FOR_UPDATE = время(секунды) ожидания повторного парсинга Telegram канала
* CODE = Код подтверждения, придет в 1 раз при включении, при повторном запуске использовать тот же код 
* PHONE =  Номер телефона к которому привязано ваше [Telegram](https://my.telegram.org/auth?to=apps) приложение
* ROOT_DIR = полный путь до директории в которую склонирован репозиторий
* NAME_DB = название базы данных с включенным расширением .db
* DOMAIN =  доменное имя вашего серверва
* PROTOCOL = http или https
* NAME_TABLE_MESSAGES = название таблицы 
* TELEGRAM_CHANNEL = Название из ссылки только ПУБЛИЧНОГО Telegram канала

