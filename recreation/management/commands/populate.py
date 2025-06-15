from django.core.management.base import BaseCommand
from faker import Faker
from recreation.models import (
    Booking,
    BookingService,
    Client,
    Employee,
    Event,
    Facility,
    House,
    Payment,
    Position,
    Review,
    Service,
)


class Command(BaseCommand):
    help = "Populate the database with fake data"

    def handle(self, *args, **kwargs):
        fake = Faker("ru_RU")

        # Генерация данных для модели Position
        for _ in range(3):
            Position.objects.create(
                name=fake.job(), responsibilities=fake.text(max_nb_chars=200)
            )

        # Генерация данных для модели Employee
        for _ in range(5):
            Employee.objects.create(
                position_id=Position.objects.order_by("?").first(),
                last_name=fake.last_name(),
                first_name=fake.first_name(),
                patronymic=fake.last_name(),
                contact_info=fake.phone_number(),
            )

        # Генерация данных для модели Client
        for _ in range(10):
            Client.objects.create(
                last_name=fake.last_name(),
                first_name=fake.first_name(),
                patronymic=fake.last_name(),
                phone_number=fake.phone_number(),
                email=fake.email(),
            )

        # Генерация данных для модели House
        for _ in range(5):
            House.objects.create(
                employee_id=Employee.objects.order_by("?").first(),
                name=fake.company(),
                location=f"Свердловская область, {fake.city()}",
                capacity=fake.random_int(min=1, max=10),
                price_per_night=fake.random_int(min=1000, max=5000),
                image="path_to_default_image.jpg",
            )

        # Генерация данных для модели Facility
        for _ in range(10):
            Facility.objects.create(
                house_id=House.objects.order_by("?").first(),
                name=fake.word().capitalize(),
                location=f"Свердловская область, {fake.city()}",
                description=fake.text(max_nb_chars=200),
                status=fake.random_element(
                    elements=("Available", "Occupied", "Maintenance")
                ),
            )

        # Генерация данных для модели Review
        for _ in range(10):
            Review.objects.create(
                client_id=Client.objects.order_by("?").first(),
                house_id=House.objects.order_by("?").first(),
                rating=fake.random_int(min=1, max=5),
                comment=fake.text(max_nb_chars=200),
            )

        # Генерация данных для модели Booking
        for _ in range(10):
            Booking.objects.create(
                client_id=Client.objects.order_by("?").first(),
                house_id=House.objects.order_by("?").first(),
                employee_id=Employee.objects.order_by("?").first(),
                check_in_date=fake.date_this_year(),
                check_out_date=fake.date_this_year(),
                total_cost=fake.random_int(min=1000, max=10000),
            )

        # Генерация данных для модели Event
        for _ in range(10):
            Event.objects.create(
                booking_id=Booking.objects.order_by("?").first(),
                name=fake.word().capitalize(),
                date=fake.date_this_year(),
                location=f"Свердловская область, {fake.city()}",
                image="path_to_default_image.jpg",
            )

        # Генерация данных для модели Service
        for _ in range(5):
            Service.objects.create(
                name=fake.word().capitalize(),
                description=fake.text(max_nb_chars=200),
                price=fake.random_int(min=100, max=1000),
                quantity=fake.random_int(min=1, max=100),
                image="path_to_default_image.jpg",
            )

        # Генерация данных для модели BookingService
        for _ in range(10):
            BookingService.objects.create(
                service_id=Service.objects.order_by("?").first(),
                booking_id=Booking.objects.order_by("?").first(),
                booking_date=fake.date_this_year(),
                return_date=fake.date_this_year(),
            )

        # Генерация данных для модели Payment
        for _ in range(10):
            Payment.objects.create(
                booking_id=Booking.objects.order_by("?").first(),
                amount=fake.random_int(min=1000, max=10000),
                payment_date=fake.date_this_year(),
                payment_method=fake.random_element(
                    elements=("Кредитная карта", "Наличные", "PayPal")
                ),
            )

        self.stdout.write(
            self.style.SUCCESS("Фиктивные данные успешно добавлены в базу данных!")
        )
