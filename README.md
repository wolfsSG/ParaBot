[![](https://img.shields.io/pypi/pyversions/django-admin-interface.svg?color=3776AB&logo=python&logoColor=white)](https://www.python.org/)


# Parabot
Оригенал бота находится тут <b> https://github.com/YaraKoba/ParaBot </b>

## About: 
```commandline
Я только немного адаптировал этого бота "под себя"
А именно:
Основные исправления затронули отправку сообщений
т.к. Нет возможности отправлять более 4096 символов
пришлось разбивать отправку погоды на несколько сообщений
И еще убрал надоедливую картинку на сайт погоды
Остальное мелочевка, которую и не сразу заметишь )))
```

## Installation
Updating packages
```commandline
sudo apt update && sudo apt upgrade -y
sudo apt install -y wget curl git build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

## Installing pyenv
```commandline
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
sudo reboot
```

## Installing Python 3.10 via pyenv
```commandline
pyenv install 3.10.13  # You can choose another version 3.10+
pyenv global 3.10.13
```

## Examination:
```commandline
python --version # Must be Python 3.10.x
```

## Installing ParaBot
Creating a virtual environment
```commandline
cd ~
python -m venv ~/parabot_venv
source ~/parabot_venv/bin/activate
```

## Cloning a repository
Клонирование оригинала
```commandline
git clone https://github.com/YaraKoba/ParaBot.git
cd ParaBot
```
Или клонирование измененного бота
```commandline
git clone https://github.com/wolfsSG/ParaBot
cd ParaBot
```

## Installing dependencies
```commandline
pip install --upgrade pip
pip install -r requirements.txt
sudo apt install libpq-dev
pip install psycopg2-binary
```

## Setting up a database
```commandline
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE parabot_db;"
sudo -u postgres psql -c "CREATE USER parabot_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE parabot_db TO parabot_user;"
```
When initializing the database, you will need to specify localhost:5432 in the DB_HOST variable.

## install requirements
```commandline
make requirements
```

## Run migrations
```commandline
make migrate
```

## Run create superuser
```commandline
make createsuperuser
```

## Run server
```commandline
make runserver
```

## Create .env and check set up
```commandline
make env_bot
```
fill out .env and setup.py
```commandline
TOKEN = your telegram token
API_KEY = your key for https://openweathermap.org/api
ADMIN_LOGIN = your Django admin login (ранее запускали make createsuperuser)
ADMIN_PASSWORD = your Django admin password (ранее запускали make createsuperuser)
DB_HOST = postgreSQL host (localhost:5432)
DB_NAME = postgreSQL db name
DB_USER = postgreSQL user
DB_PASS = postgreSQL password

Для получения API https://openweathermap.org/
Требуется зарегистрироваться на сайте и далее сверху
справа нажать на свой логин и выбрать My API keys
Если ключа нет, то сгенерировать его.
```

## Creating systemd units
Let's create two separate units - for the bot and the Django server.
```commandline
sudo nano /etc/systemd/system/parabot.service
```
Content
```commandline
[Unit]
Description=ParaBot Telegram Service
After=network.target postgresql.service
[Service]
User=your_user
WorkingDirectory=/home/your_user/ParaBot
Environment="PATH=/home/your_user/parabot_venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStartPre=/usr/bin/python3 -m venv /home/your_user/parabot_venv
ExecStartPre=/bin/bash -c 'source /home/your_user/parabot_venv/bin/activate && pip install -r /home/your_user/ParaBot/requirements.txt'
ExecStart=/home/your_user/parabot_venv/bin/python /home/your_user/ParaBot/para_kzn_bot/bot/main.py
Restart=always
RestartSec=5
StandardOutput=file:/var/log/parabot/bot.log
StandardError=file:/var/log/parabot/bot_error.log
[Install]
WantedBy=multi-user.target
```

```commandline
sudo nano /etc/systemd/system/parabot-django.service
```
Content
```commandline
[Unit]
Description=ParaBot Django Service
After=network.target postgresql.service parabot.service
[Service]
User=your_user
WorkingDirectory=/home/your_user/ParaBot/django_admin/service
Environment="DJANGO_SETTINGS_MODULE=service.settings"
Environment="PATH=/home/your_user/parabot_venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/your_user/parabot_venv/bin/python /home/your_user/ParaBot/django_admin/service/manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=5
StandardOutput=file:/var/log/parabot/django.log
StandardError=file:/var/log/parabot/django_error.log
[Install]
WantedBy=multi-user.target
```

## Setting up rights and logs
```commandline
sudo mkdir -p /var/log/parabot
sudo chown your_user:your_user /var/log/parabot
sudo chmod 755 /var/log/parabot
```

## Activation of services
```commandline
sudo systemctl daemon-reload
sudo systemctl enable parabot.service
sudo systemctl enable parabot-django.service
sudo systemctl start parabot.service
sudo systemctl start parabot-django.service
```

## Проверка работы
```commandline
sudo systemctl status parabot.service
sudo systemctl status parabot-django.service
journalctl -u parabot.service -f
journalctl -u parabot-django.service -f
```

ENJOY!
