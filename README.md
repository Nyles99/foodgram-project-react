![Cтатус workflow](https://github.com/Nyles99/foodgram-project-react/actions/workflows/yamdb_workflow.yml/badge.svg)

Проект "FOODgram'

Cайт Foodgram, «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.


ПОРЯДОК ДЕЙСТВИЙ:

Клонировать репозиторий:
git clone ...

Добавить в клонированный репозиторий секреты (Settings/Secrets):
Переменная: USER, значение: <имя пользователя для подключения к серверу>
Переменная: HOST, значение: <публичный ip-адрес сервера>
Переменная: SSH, значение: <закрытый ssh-ключ для подключения к серверу>
Переменная: PASSPHRASE, значение: <пароль, если ssh-ключ защищён паролем>
Переменная: DOCKER_USERNAME, значение: <имя пользователя для поключения к DockerHub>
Переменная: DOCKER_PASSWORD, значение: <пароль для поключения к DockerHub>
Переменная: DB_ENGINE, значение: django.db.backends.postgresql
Переменная: DB_HOST, значение: db
Переменная: DB_NAME, значение: postgres
Переменная: DB_PORT, значение: 5432
Переменная: POSTGRES_USER, значение: postgres
Переменная: POSTGRES_PASSWORD, значение: postgres
Переменная: TELEGRAM_TO, значение: <токен Вашего телеграм-аккаунта>
Переменная: TELEGRAM_TOKEN, значение: <токен Вашего телеграм-бота>

Настроить nginx и docker-compose, дальше отправить их на сервер в папку infra/
scp docker-compose.yaml <пользователь_сервера>@<ip-адрес сервера>:/home/<домашняя папка>
scp -r /nginx <пользователь_сервера>@<ip-адрес сервера>:/home/<домашняя папка>

Создайте образ и отправьте его на dockerhub
docker login
docker build -t username/название_образа:latest .
docker push username/название_образа:latest

Чтобы настроить сервер для работы с Docker, подключитесь к нему через консоль. 
Адрес сервера указывается по IP или доменному имени. Команда для подключения вводится в формате:

ssh name@ip

На удаленном сервере выполните:
sudo systemctl stop nginx 
sudo apt install docker.io
sudo docker-compose up -d --build

После запуска контейнеров нужно выполнить миграции, накатить статику и загрузить даныные

sudo docker ps -a 
sudo docker exec -it <имя> python manage.py migrate
sudo docker exec -it <имя> python manage.py collectstatic
sudo docker-compose exec <имя> python manage.py createsuperuser
sudo docker exec -it <имя> python manage.py load_ingredients_json

