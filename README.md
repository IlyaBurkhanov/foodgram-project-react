## Шаги по наполнению созданию БД и наполнению данными 
1. python manage.py makemigrations

2. python manage.py migrate

3. python manage.py createsuperuser (для админки)

4. python manage.py load_ingredients --path data/ingredients.csv  (загрузка ингредиетов)



## Сервер:

- http://51.250.22.7/

админ: http://51.250.22.7/admin/ :: user: ilya / password: 123 /email: ilya@ilya.ru / 

Тестовые юзеры:
ilya2@ilya.ru
ilya3@ilya.ru

пароль для всех 123


## Запуск в контейнере:
1. Заходим в /infra
2. Запускаем docker-compose up;
3. Выполняем шаги из пункта выше;
4. Радуемся.
