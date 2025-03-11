from pymongo import MongoClient
from faker import Faker
import time
import json


def connect_to_mongo(max_retries=5, delay=2):
    """
    Подключение к MongoDB с повторными попытками.
    """
    retries = 0
    while retries < max_retries:
        try:
            # Подключение к MongoDB
            client = MongoClient('mongodb://root:example@mongo:27017/')
            # Проверка подключения
            client.admin.command('ping')
            print("Успешное подключение к MongoDB!")
            return client
        except Exception as e:
            retries += 1
            print(f"Ошибка подключения: {e}. Повторная попытка {retries}/{max_retries}...")
            time.sleep(delay)
    raise Exception("Не удалось подключиться к MongoDB.")


def main():
    try:
        # Подключение к MongoDB
        client = connect_to_mongo()

        fake = Faker()
        db = client['myDatabase']  # Создаем db
        for i in [100, 1000, 10000]:
            collection = db['myColl']  # создаем коллекцию
            data = []
            for _ in range(i):
                data.append({
                    'name': fake.name(),
                    'email': fake.email(),
                    'address': {
                        'street': fake.street_address(),
                        'city': fake.city(),
                        'zipcode': fake.zipcode()
                    },
                    'orders': [
                        {'product': fake.word(), 'price': fake.random_int(min=10, max=1000)},
                        {'product': fake.word(), 'price': fake.random_int(min=10, max=1000)}
                    ]
                })

            collection.insert_many(data)

            start_time = time.time()
            res = collection.find({'orders.price': {'$lt': 50}}).explain()
            end_time = time.time()
            time_without_index = end_time - start_time
            print(f"Время выполнения запроса без индекса: {time_without_index} секунд")

            with open(f"without_index_{i}.txt", "w", encoding="utf-8") as file:
                json.dump(res, file, ensure_ascii=False, indent=4)

            # Создание индекса на поле orders.price
            collection.create_index([("orders.price", 1)])
            print("Индекс на поле orders.price создан.")

            start_time = time.time()
            res = collection.find({'orders.price': {'$lt': 50}}).explain()
            end_time = time.time()
            time_with_index = end_time - start_time
            print(f"Время выполнения запроса c индекса: {time_with_index} секунд")

            with open(f"with_index_{i}.txt", "w", encoding="utf-8") as file:
                json.dump(res, file, ensure_ascii=False, indent=4)

            # Пример запроса на выборку
            query = {"name": {"$regex": "^John"}}
            results = collection.find(query)
            n = 0
            for doc in results:
                n += 1

            print(f"Документы, где имя начинается на 'John': {n}")

            # Пример обновления данных
            query = {"orders.price": {"$lt": 50}}
            update = {"$inc": {"orders.$.price": 10}}
            collection.update_many(query, update)
            print("Цена заказов меньше 50 увеличена на 10.")

            # Пример удаления поля
            query = {"email": {"$regex": "@example.com$"}}
            update = {"$unset": {"email": ""}}
            collection.update_many(query, update)
            print("Поле 'email' удалено у пользователей с email, заканчивающимся на '@example.com'.")

            collection.drop()

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()
