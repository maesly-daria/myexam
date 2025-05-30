import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base_relaction.settings')
import django
django.setup()

from recreation.models import Client, House, Review

# Существующие отзывы с главной страницы
existing_reviews = [
    {
        "author": "Елена З.",
        "comment": "Прекрасное место для отдыха на выходных! Бронировали за 2 дня до самого отдыха, очень приятный персонал обо всем рассказал.",
        "rating": 5
    },
    {
        "author": "Василий Е.",
        "comment": "Спасибо большое администратору за помощь в выборе домика! Расположение базы очень удобное.",
        "rating": 4
    },
    {
        "author": "Иван А.",
        "comment": "Бронировали домик 'Зеленая роща' на 3 дня с компанией, бронирование прошло быстро и без проблем.",
        "rating": 5
    }
]

def import_reviews():
    # Берем первый дом для привязки отзывов
    house = House.objects.first()
    
    for review_data in existing_reviews:
        # Создаем клиента
        last_name, first_letter = review_data["author"].split()
        client = Client.objects.create(
            last_name=last_name,
            first_name=first_letter + ".",
            phone_number="+79110000000",  # Заглушка
            email=f"{last_name.lower()}@example.com"
        )
        
        # Создаем отзыв
        Review.objects.create(
            client_id=client,
            house_id=house,
            rating=review_data["rating"],
            comment=review_data["comment"]
        )
    
    print(f"Импортировано {len(existing_reviews)} отзывов")

if __name__ == '__main__':
    import_reviews()