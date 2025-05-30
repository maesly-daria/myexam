from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField
import os

class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name="Название тега"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name

class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')


class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
    ]
    
    title = models.CharField(
        max_length=250,
        verbose_name="Заголовок"
    )
    slug = models.SlugField(
        max_length=250,
        unique_for_date='publish',
        verbose_name="URL-адрес",
        unique=True,
        blank=True  # Разрешаем пустое значение для автозаполнения
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name="Автор"
    )
    body = RichTextField(verbose_name="Содержание")
    publish = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата публикации"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        through='PostTag',
        verbose_name="Теги",
        blank=True
    )
    image = models.ImageField(
        upload_to='post_images/',
        verbose_name="Изображение",
        blank=True,
        null=True
    )

    objects = models.Manager()  # Менеджер по умолчанию
    published = PostManager()  # Кастомный менеджер для опубликованных постов

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        from django.utils.text import slugify
        original_slug = slugify(self.title)
        queryset = Post.objects.all()
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
            
        count = 1
        slug = original_slug
        while queryset.filter(slug=slug).exists():
            slug = f'{original_slug}-{count}'
            count += 1
            
        return slug

    @classmethod
    def filter_posts_by_title(cls, keyword):
        return cls.objects.filter(title__icontains=keyword)

    @classmethod
    def filter_posts_by_status_and_title(cls, status, keyword):
        return cls.objects.filter(status=status).filter(title__icontains=keyword)

    @classmethod
    def update_post_status(cls, post_id, new_status):
        return cls.objects.filter(id=post_id).update(status=new_status)

    @classmethod
    def delete_post_by_id(cls, post_id):
        return cls.objects.filter(id=post_id).delete()

    @classmethod
    def get_post_values(cls):
        return cls.objects.values('title', 'author__username')

    @classmethod
    def get_post_values_list(cls):
        return cls.objects.values_list('title', 'author__username')

    @classmethod
    def count_posts(cls):
        return cls.objects.count()

    @classmethod
    def check_post_exists(cls, post_id):
        return cls.objects.filter(id=post_id).exists()

    @classmethod
    def get_latest_posts(cls, limit=5):
        return cls.published.order_by('-publish')[:limit]

    @classmethod
    def get_posts_per_author(cls):
        return cls.objects.values('author__username').annotate(
            total_posts=Count('id')
        ).order_by('-total_posts')


class PostTag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name="Пост")
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, verbose_name="Тег")

    class Meta:
        verbose_name = "Тег поста"
        verbose_name_plural = "Теги постов"

    def __str__(self):
        return f"{self.post.title} - {self.tag.name}"
    
class CustomUser(AbstractUser):
    phone = models.CharField(
        _('Телефон'),
        max_length=12,
        default='+70000000000',
        help_text=_('Формат: +79991234567')
    )
    last_name = models.CharField(
        _('Фамилия'),
        max_length=100,
        blank=False
    )
    username = models.CharField(
        _('Имя'), 
        max_length=100, 
        unique=True
    )
    
    patronymic = models.CharField(
        _('Отчество'),
        max_length=100,
        blank=True,
        null=True
    )
    
    REQUIRED_FIELDS = ['email', 'phone', 'last_name', 'patronymic']
    
    class Meta:
        db_table = 'recreation_customuser'
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['last_name', 'username']

    def __str__(self):
        return self.get_full_name() or self.username

    def get_full_name(self):
        """Возвращает полное имя в формате 'Фамилия Имя Отчество'"""
        full_name = f"{self.last_name} {self.username}"  # Используем username как имя
        if self.patronymic:
            full_name += f" {self.patronymic}"
        return full_name.strip()
    
    def save(self, *args, **kwargs):
        # Если username не задан, используем email
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class Client(models.Model):
    client_id = models.AutoField(
        primary_key=True,
        verbose_name="ID клиента"
    )
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='client_profile',
        null=True,
        blank=True,
        verbose_name="Учетная запись"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия"
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя"
    )
    patronymic = models.CharField(
        max_length=100,
        verbose_name="Отчество"
    )
    phone_number = models.CharField(
        max_length=15,
        verbose_name="Номер телефона"
    )
    email = models.EmailField(
        max_length=255,
        verbose_name="Email"
    )
    document = models.FileField(
        upload_to='client_documents/%Y/%m/%d/',
        verbose_name="Документ",
        blank=True,
        null=True,
        help_text="Загрузите сканы документов (паспорт, водительские права и т.д.)"
    )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"
    
    def save(self, *args, **kwargs):
        # При создании нового клиента автоматически создаём пользователя
        if not self.pk and not self.user:
            user = CustomUser.objects.create_user(
                username=self.email,  # Используем email как username
                email=self.email,
                last_name=self.last_name,
                patronymic=self.patronymic,
                phone=self.phone_number
            )
            self.user = user
        super().save(*args, **kwargs)

class Employee(models.Model):
    employee_id = models.AutoField(
        primary_key=True,
        verbose_name="ID сотрудника"
    )
    position_id = models.ForeignKey(
        'Position',
        on_delete=models.CASCADE,
        verbose_name="Должность"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия"
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя"
    )
    patronymic = models.CharField(
        max_length=100,
        verbose_name="Отчество"
    )
    contact_info = models.CharField(
        max_length=255,
        verbose_name="Контактная информация"
    )

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"

class Position(models.Model):
    position_id = models.AutoField(
        primary_key=True,
        verbose_name="ID должности"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Название должности"
    )
    responsibilities = RichTextField(verbose_name="Обязанности")

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"

    def __str__(self):
        return self.name

class House(models.Model):
    house_id = models.AutoField(
        primary_key=True, 
        verbose_name="ID дома"
    )
    employee_id = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ответственный сотрудник"
    )
    name = models.CharField(
        max_length=100, 
        verbose_name="Название коттеджа"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="URL-идентификатор"
    )
    location = models.CharField(
        max_length=100,
        verbose_name="Местоположение"
    )
    capacity = models.IntegerField(
        verbose_name="Вместимость (чел.)"
    )
    price_per_night = models.IntegerField(
        verbose_name="Цена за ночь (руб.)"
    )
    image = models.ImageField(
        upload_to='houses/',
        verbose_name="Изображение",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    
    @property
    def get_image_url(self):
        """Возвращает корректный URL изображения"""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        
        # Проверяем медиа-файлы
        media_path = os.path.join('houses', f'{self.slug}.jpg')
        full_media_path = os.path.join(settings.MEDIA_ROOT, media_path)
        
        if os.path.exists(full_media_path):
            return os.path.join(settings.MEDIA_URL, media_path)
        
        # Проверяем статические файлы
        static_path = os.path.join('images', f'{self.slug}.jpg')
        full_static_path = os.path.join(settings.STATIC_ROOT, static_path)
        
        if os.path.exists(full_static_path):
            return os.path.join(settings.STATIC_URL, static_path)
        
        # Возвращаем изображение по умолчанию
        return os.path.join(settings.STATIC_URL, 'images/image.jpg')

    def image_exists(self):
        """Проверяет существование файла изображения"""
        if self.image and hasattr(self.image, 'url'):
            return True
        
        # Проверяем наличие файла в media
        media_image_path = os.path.join(settings.MEDIA_ROOT, f'houses/{self.slug}.jpg')
        if os.path.exists(media_image_path):
            return True
        
        # Проверяем наличие файла в static
        static_image_path = os.path.join(settings.STATIC_ROOT, 'images', f'{self.slug}.jpg')
        return os.path.exists(static_image_path)
    
    description = RichTextField(
        blank=True,
        verbose_name="Описание"
    )
    amenities = RichTextField(
        blank=True,
        verbose_name="Удобства"
    )

    class Meta:
        verbose_name = "Коттедж"
        verbose_name_plural = "Коттеджи"
        ordering = ['name']

    def __str__(self):
        return self.name

    # В файле models.py в классе House
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
        # Обновляем slug, если он пустой даже после сохранения
        if not self.slug:
            self.slug = slugify(self.name)
            super().save(*args, **kwargs)

    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def get_image_url(self):
        if self.image:
            return self.image.url
        return '/static/images/image.jpg'
    
    def image_exists(self):
        return bool(self.image)
    
    def get_absolute_url(self):
        return reverse('cottage_detail', kwargs={'slug': self.slug})

    def amenities_list(self):
        """Возвращает список удобств для отображения в шаблонах"""
        return [a.strip() for a in self.amenities.split('\n') if a.strip()]

    def __str__(self):
        return self.name

class Facility(models.Model):
    facility_id = models.AutoField(
        primary_key=True,
        verbose_name="ID оборудования"
    )
    house_id = models.ForeignKey(
        'House',
        on_delete=models.CASCADE,
        verbose_name="Коттедж"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Название"
    )
    location = models.CharField(
        max_length=100,
        verbose_name="Расположение"
    )
    description = RichTextField(verbose_name="Описание")
    status = models.CharField(
        max_length=50,
        verbose_name="Статус"
    )

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"

    def __str__(self):
        return self.name

class Review(models.Model):
    review_id = models.AutoField(
        primary_key=True,
        verbose_name="ID отзыва"
    )
    client_id = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name="Клиент"
    )
    house_id = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        verbose_name="Коттедж"
    )
    rating = models.IntegerField(
        verbose_name="Рейтинг"
    )
    comment = RichTextField(
        verbose_name="Комментарий"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    @classmethod
    def get_all_reviews(cls):
        return cls.objects.all().select_related('client_id', 'house_id').order_by('-created_at')
    
    def save(self, *args, **kwargs):
        # Очищаем текст от тегов перед сохранением
        self.comment = strip_tags(self.comment)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.client_id} для {self.house_id}"

class Service(models.Model):
    SERVICE_TYPES = [
        ('entertainment', 'Развлечения'),
        ('relax', 'Релакс'),
        ('transport', 'Транспорт'),
        ('other', 'Другое')
    ]
    service_id = models.AutoField(
        primary_key=True,
        verbose_name="ID услуги"
    )
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.IntegerField(verbose_name="Количество")
    image = models.ImageField(upload_to='services/', verbose_name="Изображение")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    type = models.CharField(max_length=20, choices=SERVICE_TYPES, verbose_name="Тип услуги")

    def get_absolute_url(self):
        return f"/services/{self.pk}/"
    
    def __str__(self):
        return self.name
    
    def get_icon(self):
        return {
            'entertainment': 'fa-gamepad',
            'food': 'fa-utensils', 
            'transport': 'fa-car',
            'other': 'fa-star'
        }.get(self.type, 'fa-check')

    @property
    def short_description(self):
        """Сокращенное описание для превью"""
        return (self.description[:100] + '...') if len(self.description) > 100 else self.description

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ['type', 'name']
        
class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True, verbose_name="ID бронирования")
    client_id = models.ForeignKey(
        'Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Клиент'
    )
    house = models.ForeignKey(
        'House',
        on_delete=models.CASCADE,
        verbose_name='Коттедж',
        null=True,  # Temporary
        blank=True,
        db_column='house_id'  # Явно указываем имя колонки в БД
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    check_in_date = models.DateField(verbose_name='Дата заезда')
    check_out_date = models.DateField(verbose_name='Дата выезда')
    guests = models.PositiveIntegerField(verbose_name='Количество гостей')
    phone_number = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email') 
    client_name = models.CharField(
        max_length=255,
        verbose_name='Имя клиента',
        default='Не указано',  # Add default value here
        blank=False,
        null=False
    )
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Базовая стоимость',
        default=0.00  # Add this line
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая стоимость"
    )
    created_at = models.DateTimeField(
        null=True,  # Remove 'default' if present
        verbose_name='Дата создания'
    )
    services = models.ManyToManyField('Service', blank=True, verbose_name='Дополнительные услуги')
    comment = RichTextField(
        verbose_name="Комментарий",
        blank=True,
        null=True
    )

    @property
    def nights(self):
        return (self.check_out_date - self.check_in_date).days

    def __str__(self):
        return f"Бронирование {self.booking_id} для {self.house_id}"
    
    class Meta:
            verbose_name = "Бронирование"
            verbose_name_plural = "Бронирования"

class Event(models.Model):
    event_id = models.AutoField(
        primary_key=True,
        verbose_name="ID мероприятия"
    )
    booking_id = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE,
        verbose_name="Бронирование"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Название"
    )
    date = models.DateField(verbose_name="Дата")
    location = RichTextField(verbose_name="Место проведения")
    image = models.ImageField(
        upload_to='event_images/',
        verbose_name="Изображение"
    )
    event_url = models.URLField(
        blank=True,
        verbose_name="Ссылка на мероприятие"
    )

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def __str__(self):
        return self.name



class BookingService(models.Model):
    service_id = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE,
        verbose_name="Услуга"
    )
    booking_id = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE,
        verbose_name="Бронирование"
    )
    booking_date = models.DateField(
        verbose_name="Дата бронирования"
    )
    return_date = models.DateField(
        verbose_name="Дата возврата"
    )

    class Meta:
        verbose_name = "Бронирование услуги"
        verbose_name_plural = "Бронирования услуг"

    def __str__(self):
        return f"Бронирование услуги {self.service_id} для {self.booking_id}"

class Payment(models.Model):
    payment_id = models.AutoField(
        primary_key=True,
        verbose_name="ID платежа"
    )
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE,
        verbose_name="Бронирование"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Сумма"
    )
    payment_date = models.DateField(verbose_name="Дата платежа")
    payment_method = models.CharField(
        max_length=50,
        verbose_name="Способ оплаты"
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"Платеж {self.payment_id} для бронирования {self.booking.booking_id}"
    
from django.contrib.auth import get_user_model
User = get_user_model()

class DZexam(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название экзамена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    exam_date = models.DateField(verbose_name="Дата проведения экзамена")
    image = models.ImageField(upload_to='exam_images/', verbose_name="Изображение задания", blank=True, null=True)
    users = models.ManyToManyField(User, verbose_name="Пользователи")
    is_public = models.BooleanField(default=False, verbose_name="Опубликовано")

    class Meta:
        verbose_name = "Экзамен"
        verbose_name_plural = "Экзамены"
        ordering = ['-created_at']

    def __str__(self):
        return self.title