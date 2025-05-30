import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Настройка Django окружения должна быть ПЕРЕД любыми импортами Django
project_path = Path(__file__).resolve().parent.parent
sys.path.append(str(project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base_relaction.settings')

import django
django.setup()

# Только после django.setup() можно импортировать модели Django
from django.utils import timezone
from django.core.files import File
from django.contrib.auth.models import User

from recreation.models import (
    Client, Service, Event, House, Review, Booking, 
    BookingService, Payment, Employee, Position, Facility,
    Post, Tag, PostTag
)

def safe_get_or_create(model, **kwargs):
    """Безопасное создание объекта с обработкой исключений"""
    try:
        obj, created = model.objects.get_or_create(**kwargs)
        if created:
            print(f"✓ Создан {model.__name__}: {str(obj)}")
        return obj
    except Exception as e:
        print(f"× Ошибка при создании {model.__name__}: {str(e)}")
        return None

def create_positions():
    """Создание должностей"""
    positions = [
        {"name": "Администратор", "responsibilities": "Управление базой отдыха, работа с клиентами"},
        {"name": "Горничная", "responsibilities": "Уборка коттеджей и территории"},
        {"name": "Повар", "responsibilities": "Приготовление блюд для гостей"},
        {"name": "Аниматор", "responsibilities": "Проведение мероприятий и развлечений"},
        {"name": "Охранник", "responsibilities": "Обеспечение безопасности гостей"},
        {"name": "Массажист", "responsibilities": "Проведение массажных процедур"},
        {"name": "Бармен", "responsibilities": "Обслуживание в баре, приготовление напитков"},
        {"name": "Экскурсовод", "responsibilities": "Проведение экскурсий по окрестностям"},
    ]
    
    print("\n=== Создание должностей ===")
    for pos in positions:
        safe_get_or_create(Position, **pos)
    return Position.objects.all()

def create_employees(positions):
    """Создание сотрудников"""
    employees = [
        {"last_name": "Иванова", "first_name": "Ольга", "patronymic": "Сергеевна", "position": positions[0], "contact_info": "+79111234567"},
        {"last_name": "Петров", "first_name": "Иван", "patronymic": "Алексеевич", "position": positions[1], "contact_info": "+79119876543"},
        {"last_name": "Сидорова", "first_name": "Анна", "patronymic": "Петровна", "position": positions[2], "contact_info": "+79112345678"},
        {"last_name": "Кузнецов", "first_name": "Алексей", "patronymic": "Дмитриевич", "position": positions[3], "contact_info": "+79118765432"},
        {"last_name": "Смирнов", "first_name": "Дмитрий", "patronymic": "Игоревич", "position": positions[4], "contact_info": "+79113456789"},
        {"last_name": "Васильева", "first_name": "Елена", "patronymic": "Викторовна", "position": positions[5], "contact_info": "+79117654321"},
        {"last_name": "Николаев", "first_name": "Андрей", "patronymic": "Сергеевич", "position": positions[6], "contact_info": "+79114567890"},
        {"last_name": "Орлова", "first_name": "Виктория", "patronymic": "Андреевна", "position": positions[7], "contact_info": "+79115678901"},
    ]
    
    print("\n=== Создание сотрудников ===")
    for emp in employees:
        safe_get_or_create(
            Employee,
            last_name=emp["last_name"],
            first_name=emp["first_name"],
            patronymic=emp["patronymic"],
            defaults={
                "position_id": emp["position"],
                "contact_info": emp["contact_info"]
            }
        )
    return Employee.objects.all()

def create_clients():
    """Создание клиентов"""
    clients = [
        {"last_name": "Иванов", "first_name": "Алексей", "patronymic": "Игоревич", "email": "ivanov@mail.ru", "phone_number": "+79120000001"},
        {"last_name": "Петрова", "first_name": "Мария", "patronymic": "Сергеевна", "email": "petrova@mail.ru", "phone_number": "+79120000002"},
        {"last_name": "Сидоров", "first_name": "Дмитрий", "patronymic": "Алексеевич", "email": "sidorov@mail.ru", "phone_number": "+79120000003"},
        {"last_name": "Кузнецова", "first_name": "Анна", "patronymic": "Дмитриевна", "email": "kuznetsova@mail.ru", "phone_number": "+79120000004"},
        {"last_name": "Смирнов", "first_name": "Иван", "patronymic": "Петрович", "email": "smirnov@mail.ru", "phone_number": "+79120000005"},
        {"last_name": "Васильева", "first_name": "Елена", "patronymic": "Ивановна", "email": "vasileva@mail.ru", "phone_number": "+79120000006"},
        {"last_name": "Николаев", "first_name": "Андрей", "patronymic": "Викторович", "email": "nikolaev@mail.ru", "phone_number": "+79120000007"},
        {"last_name": "Орлова", "first_name": "Виктория", "patronymic": "Александровна", "email": "orlova@mail.ru", "phone_number": "+79120000008"},
        {"last_name": "Федоров", "first_name": "Сергей", "patronymic": "Николаевич", "email": "fedorov@mail.ru", "phone_number": "+79120000009"},
        {"last_name": "Жукова", "first_name": "Ольга", "patronymic": "Сергеевна", "email": "zhukova@mail.ru", "phone_number": "+79120000010"},
    ]
    
    print("\n=== Создание клиентов ===")
    for client in clients:
        safe_get_or_create(
            Client,
            email=client["email"],
            defaults={
                "last_name": client["last_name"],
                "first_name": client["first_name"],
                "patronymic": client["patronymic"],
                "phone_number": client["phone_number"]
            }
        )
    return Client.objects.all()

def create_houses(employees):
    """Создание коттеджей"""
    houses = [
        {
            "name": "Дубовый", "slug": "duboviy", "capacity": 2, "price_per_night": 3500,
            "description": "Уютный однокомнатный коттедж с двуспальной кроватью, собственной ванной комнатой и мини-кухней.",
            "amenities": "Двуспальная кровать\nСобственная ванная\nМини-кухня\nТелевизор\nWi-Fi\nКондиционер\nЧайный набор",
            "employee": employees[0], "image": "duboviy.jpg"
        },
        {
            "name": "Сосновый", "slug": "sosnoviy", "capacity": 4, "price_per_night": 5000,
            "description": "Просторный коттедж с видом на сосновый бор. Идеально подходит для семьи или компании друзей.",
            "amenities": "2 спальни\nГостиная зона\nПолностью оборудованная кухня\nКамин\nТелевизор\nWi-Fi\nТерраса",
            "employee": employees[1], "image": "sosnoviy.jpg"
        },
        {
            "name": "Березовый", "slug": "berezoviy", "capacity": 6, "price_per_night": 7000,
            "description": "Большой коттедж с тремя спальнями и просторной гостиной. Есть собственная сауна.",
            "amenities": "3 спальни\nГостиная\nКухня-столовая\nСауна\nТелевизор\nWi-Fi\nБольшая терраса\nМангал",
            "employee": employees[2], "image": "berezoviy.jpg"
        },
        {
            "name": "Ёлки", "slug": "yolki", "capacity": 8, "price_per_night": 9000,
            "description": "Просторный двухэтажный коттедж с четырьмя спальнями. Идеален для больших компаний.",
            "amenities": "4 спальни\n2 гостиные\nКухня-столовая\n2 ванные комнаты\nКамин\nТелевизор\nWi-Fi\nТерраса",
            "employee": employees[3], "image": "yolki.jpg"
        },
        {
            "name": "Бао-бао", "slug": "bao-bao", "capacity": 10, "price_per_night": 12000,
            "description": "Роскошный коттедж премиум-класса с пятью спальнями и собственным бассейном.",
            "amenities": "5 спален\n3 гостиные\nКухня-столовая\n3 ванные комнаты\nБассейн\nСауна\nДжакузи\nКинотеатр",
            "employee": employees[4], "image": "bao-bao.jpg"
        },
        {
            "name": "Зеленая роща", "slug": "zelenaya-roshcha", "capacity": 12, "price_per_night": 15000,
            "description": "Элитный коттедж для VIP-отдыха. Шесть спален, домашний кинотеатр и SPA-зона.",
            "amenities": "6 спален\n4 ванные комнаты\nКухня с островом\nДомашний кинотеатр\nSPA-зона\nБильярд\nТерраса с барбекю",
            "employee": employees[5], "image": "zelenaya-roshcha.jpg"
        },
    ]
    
    print("\n=== Создание коттеджей ===")
    for house in houses:
        safe_get_or_create(
            House,
            name=house["name"],
            defaults={
                "slug": house["slug"],
                "capacity": house["capacity"],
                "price_per_night": house["price_per_night"],
                "description": house["description"],
                "amenities": house["amenities"],
                "employee_id": house["employee"],
                "image": house["image"]
            }
        )
    return House.objects.all()

def create_facilities(houses):
    """Создание удобств"""
    facilities = [
        {"name": "Банный комплекс", "description": "Сауна, бассейн, комнаты отдыха", "status": "Работает", "house": houses[0]},
        {"name": "Мангальная зона", "description": "Место для барбекю у реки", "status": "Работает", "house": houses[1]},
        {"name": "Детская площадка", "description": "Игровая зона для детей", "status": "Работает", "house": houses[2]},
        {"name": "SPA-центр", "description": "Массаж, косметические процедуры", "status": "Работает", "house": houses[3]},
        {"name": "Фитнес-зал", "description": "Тренажеры, йога-студия", "status": "Работает", "house": houses[4]},
        {"name": "Конференц-зал", "description": "Помещение для мероприятий", "status": "Работает", "house": houses[5]},
    ]
    
    print("\n=== Создание удобств ===")
    for fac in facilities:
        safe_get_or_create(
            Facility,
            name=fac["name"],
            house_id=fac["house"],
            defaults={
                "description": fac["description"],
                "status": fac["status"]
            }
        )
    return Facility.objects.all()

def create_services():
    """Создание услуг"""
    services = [
        {"name": "Завтрак", "description": "Континентальный завтрак", "price": 500, "quantity": 20, "image": "breakfast.jpg"},
        {"name": "Ужин", "description": "Трехразовое питание", "price": 1500, "quantity": 20, "image": "dinner.jpg"},
        {"name": "Банный чан", "description": "Аренда банного чана на 2 часа", "price": 3000, "quantity": 5, "image": "banya.jpg"},
        {"name": "Массаж", "description": "Спа-массаж (60 мин)", "price": 2500, "quantity": 4, "image": "massage.jpg"},
        {"name": "Экскурсия", "description": "Пешая экскурсия по окрестностям", "price": 1000, "quantity": 10, "image": "excursion.jpg"},
        {"name": "Трансфер", "description": "Доставка от/до города", "price": 2000, "quantity": 3, "image": "transfer.jpg"},
        {"name": "Аренда велосипеда", "description": "На весь день", "price": 1500, "quantity": 8, "image": "bike.jpg"},
        {"name": "Рыбалка", "description": "Аренда снастей и лодки", "price": 2500, "quantity": 6, "image": "fishing.jpg"},
    ]
    
    print("\n=== Создание услуг ===")
    for service in services:
        safe_get_or_create(
            Service,
            name=service["name"],
            defaults={
                "description": service["description"],
                "price": service["price"],
                "quantity": service["quantity"],
                "image": service["image"]
            }
        )
    return Service.objects.all()

def create_events(bookings):
    """Создание мероприятий"""
    events = [
        {
            "name": "Корпоратив", "date": timezone.now() + timedelta(days=15), 
            "location": "Банкетный зал", "booking": bookings[0], "image": "corporate.jpg"
        },
        {
            "name": "Свадьба", "date": timezone.now() + timedelta(days=30), 
            "location": "Летняя площадка", "booking": bookings[1], "image": "wedding.jpg"
        },
        {
            "name": "Детский праздник", "date": timezone.now() + timedelta(days=45), 
            "location": "Игровая зона", "booking": bookings[2], "image": "kids_party.jpg"
        },
        {
            "name": "Фестиваль барбекю", "date": timezone.now() + timedelta(days=60), 
            "location": "Мангальная зона", "booking": bookings[3], "image": "bbq.jpg"
        },
    ]
    
    print("\n=== Создание мероприятий ===")
    for event in events:
        safe_get_or_create(
            Event,
            name=event["name"],
            booking_id=event["booking"],
            defaults={
                "date": event["date"],
                "location": event["location"],
                "image": event["image"]
            }
        )
    return Event.objects.all()

def create_bookings(clients, houses, employees):
    """Создание бронирований"""
    bookings = []
    for i in range(20):  # Создаем 20 бронирований
        client = clients[i % len(clients)]
        house = houses[i % len(houses)]
        employee = employees[i % len(employees)]
        
        check_in = timezone.now() + timedelta(days=random.randint(1, 30))
        check_out = check_in + timedelta(days=random.randint(2, 14))
        total_cost = house.price_per_night * (check_out - check_in).days
        
        bookings.append({
            "client": client,
            "house": house,
            "employee": employee,
            "check_in_date": check_in.date(),
            "check_out_date": check_out.date(),
            "total_cost": total_cost
        })
    
    print("\n=== Создание бронирований ===")
    created_bookings = []
    for booking in bookings:
        obj = safe_get_or_create(
            Booking,
            client_id=booking["client"],
            house_id=booking["house"],
            check_in_date=booking["check_in_date"],
            defaults={
                "employee_id": booking["employee"],
                "check_out_date": booking["check_out_date"],
                "total_cost": booking["total_cost"]
            }
        )
        if obj:
            created_bookings.append(obj)
    
    return created_bookings

def create_booking_services(bookings, services):
    """Создание бронирований услуг"""
    booking_services = []
    for booking in bookings:
        # Каждому бронированию добавляем 1-3 услуги
        num_services = random.randint(1, 3)
        for _ in range(num_services):
            service = random.choice(services)
            booking_date = booking.check_in_date
            return_date = booking_date + timedelta(days=random.randint(1, 3))
            
            booking_services.append({
                "booking": booking,
                "service": service,
                "booking_date": booking_date,
                "return_date": return_date
            })
    
    print("\n=== Создание бронирований услуг ===")
    created_bs = []
    for bs in booking_services:
        obj = safe_get_or_create(
            BookingService,
            booking=bs["booking"],
            service=bs["service"],
            booking_date=bs["booking_date"],
            defaults={
                "return_date": bs["return_date"]
            }
        )
        if obj:
            created_bs.append(obj)
    
    return created_bs

def create_payments(bookings, booking_services):
    """Создание платежей"""
    payments = []
    for booking in bookings:
        # Основной платеж за бронирование
        payments.append({
            "booking": booking,
            "amount": booking.total_cost,
            "payment_date": booking.check_in_date - timedelta(days=random.randint(1, 7)),
            "payment_method": random.choice(["Карта", "Наличные", "Перевод"])
        })
        
        # Платежи за услуги (если есть)
        for bs in booking_services:
            if bs.booking == booking:
                payments.append({
                    "booking": booking,
                    "service_booking": bs,
                    "amount": bs.service.price,
                    "payment_date": booking.check_in_date,
                    "payment_method": random.choice(["Карта", "Наличные"])
                })
    
    print("\n=== Создание платежей ===")
    created_payments = []
    for payment in payments:
        if "service_booking" in payment:
            obj = safe_get_or_create(
                Payment,
                booking=payment["booking"],
                service_booking=payment["service_booking"],
                defaults={
                    "amount": payment["amount"],
                    "payment_date": payment["payment_date"],
                    "payment_method": payment["payment_method"]
                }
            )
        else:
            obj = safe_get_or_create(
                Payment,
                booking=payment["booking"],
                payment_date=payment["payment_date"],
                defaults={
                    "amount": payment["amount"],
                    "payment_method": payment["payment_method"]
                }
            )
        
        if obj:
            created_payments.append(obj)
    
    return created_payments

def create_reviews(clients, houses):
    """Создание отзывов"""
    reviews = []
    for i in range(30):  # Создаем 30 отзывов
        client = clients[i % len(clients)]
        house = houses[i % len(houses)]
        
        reviews.append({
            "client": client,
            "house": house,
            "rating": random.randint(3, 5),
            "comment": random.choice([
                "Отличное место для отдыха!",
                "Очень понравилось, обязательно вернемся!",
                "Хороший сервис и уютные домики.",
                "Прекрасное место для семейного отдыха.",
                "Отдыхали с друзьями, всем понравилось.",
                "Чисто, уютно, красивая природа.",
                "Персонал вежливый, все на высшем уровне.",
                "Рекомендую для романтического отдыха.",
                "Отличное соотношение цены и качества.",
                "Были с детьми, всем очень понравилось."
            ]),
            "created_at": timezone.now() - timedelta(days=random.randint(1, 365))
        })
    
    print("\n=== Создание отзывов ===")
    created_reviews = []
    for review in reviews:
        obj = safe_get_or_create(
            Review,
            client_id=review["client"],
            house_id=review["house"],
            defaults={
                "rating": review["rating"],
                "comment": review["comment"],
                "created_at": review["created_at"]
            }
        )
        if obj:
            created_reviews.append(obj)
    
    return created_reviews

def create_posts():
    """Создание постов и тегов"""
    print("\n=== Создание тегов ===")
    tags = [
        {"name": "Отдых"},
        {"name": "Акции"},
        {"name": "Новости"},
        {"name": "События"},
        {"name": "Советы"},
    ]
    for tag in tags:
        safe_get_or_create(Tag, **tag)
    
    # Создаем тестового пользователя для автора постов
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
    
    print("\n=== Создание постов ===")
    posts = [
        {
            "title": "Новый сезон открыт!",
            "slug": "new-season",
            "body": "Мы рады сообщить об открытии нового сезона на нашей базе отдыха. В этом году мы подготовили для вас много интересных нововведений и специальных предложений.",
            "status": "published",
            "author": user,
            "image": "post1.jpg",
            "tags": ["Отдых", "Новости"]
        },
        {
            "title": "Специальное предложение для молодоженов",
            "slug": "wedding-offer",
            "body": "В этом сезоне мы предлагаем специальные условия для проведения свадебных мероприятий. Скидка 15% на аренду коттеджей для молодоженов!",
            "status": "published",
            "author": user,
            "image": "post2.jpg",
            "tags": ["Акции", "События"]
        },
        {
            "title": "Как подготовиться к отдыху на природе",
            "slug": "preparation-tips",
            "body": "В этой статье мы расскажем, что взять с собой на отдых в наш комплекс, чтобы ничего не забыть и получить максимум удовольствия.",
            "status": "published",
            "author": user,
            "image": "post3.jpg",
            "tags": ["Советы", "Отдых"]
        },
        {
            "title": "Новые услуги в SPA-центре",
            "slug": "new-spa-services",
            "body": "Наш SPA-центр расширяет перечень услуг. Теперь доступны новые виды массажа и косметические процедуры.",
            "status": "published",
            "author": user,
            "image": "post4.jpg",
            "tags": ["Новости", "События"]
        },
        {
            "title": "Фестиваль барбекю - 2023",
            "slug": "bbq-festival",
            "body": "Приглашаем всех на ежегодный фестиваль барбекю, который пройдет 15-17 июля. В программе: мастер-классы, конкурсы и дегустации.",
            "status": "published",
            "author": user,
            "image": "post5.jpg",
            "tags": ["События", "Акции"]
        },
    ]
    
    created_posts = []
    for post in posts:
        p = safe_get_or_create(
            Post,
            title=post["title"],
            slug=post["slug"],
            defaults={
                "body": post["body"],
                "status": post["status"],
                "author": post["author"],
                "image": post["image"]
            }
        )
        
        if p:
            for tag_name in post["tags"]:
                tag = Tag.objects.get(name=tag_name)
                p.tags.add(tag)
            created_posts.append(p)
    
    return created_posts

def main():
    """Основная функция создания данных"""
    print("\n=== Начало создания тестовых данных ===")
    
    # Создаем базовые данные
    positions = create_positions()
    employees = create_employees(positions)
    clients = create_clients()
    houses = create_houses(employees)
    facilities = create_facilities(houses)
    services = create_services()
    
    # Создаем данные, зависящие от предыдущих
    bookings = create_bookings(clients, houses, employees)
    booking_services = create_booking_services(bookings, services)
    payments = create_payments(bookings, booking_services)
    events = create_events(bookings)
    reviews = create_reviews(clients, houses)
    posts = create_posts()
    
    # Выводим итоговую статистику
    print("\n=== Итоговая статистика ===")
    print(f"Должности: {positions.count()}")
    print(f"Сотрудники: {employees.count()}")
    print(f"Клиенты: {clients.count()}")
    print(f"Коттеджи: {houses.count()}")
    print(f"Удобства: {facilities.count()}")
    print(f"Услуги: {services.count()}")
    print(f"Бронирования: {len(bookings)}")
    print(f"Бронирования услуг: {len(booking_services)}")
    print(f"Платежи: {len(payments)}")
    print(f"Мероприятия: {events.count()}")
    print(f"Отзывы: {len(reviews)}")
    print(f"Посты: {len(posts)}")
    print(f"Теги: {Tag.objects.count()}")
    
    print("\n=== Тестовые данные успешно созданы! ===")

if __name__ == '__main__':
    main()