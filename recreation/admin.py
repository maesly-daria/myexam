from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils.html import format_html
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from .models import Client, House, Facility, Review, Employee, Position, Booking, Event, Service, BookingService, Payment, Post, Tag, PostTag, CustomUser
from django.contrib.auth.admin import UserAdmin
from django.conf import settings
from ckeditor.widgets import CKEditorWidget
from django.contrib.admin import DateFieldListFilter
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserChangeForm, CustomUserCreationForm
import os

# Общие настройки админ-панели
admin.site.site_header = _('Администрирование базы отдыха "FurTree"')
admin.site.site_title = _('База отдыха')
admin.site.index_title = _('Управление базой отдыха')

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('id', 'username', 'last_name', 'patronymic', 'email', 'phone', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'phone', 'last_name')
    ordering = ('last_name', 'username')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': ('last_name', 'patronymic', 'email', 'phone')
        }),
        ('Права', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('last_name', 'username', 'patronymic', 'email', 'phone',  'password1', 'password2'),
        }),
    )
    
    search_fields = ('last_name', 'username', 'patronymic', 'email', 'phone')
    ordering = ('last_name', 'username')

admin.site.register(CustomUser, CustomUserAdmin)

@admin.display(description=_('Изображение'))
def image_preview(self, obj):
    if obj.image:
        image_path = os.path.join(settings.STATIC_ROOT, 'images', obj.image)
        if os.path.exists(image_path):
            return format_html(
                '<img src="/static/images/{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image
            )
    return "-"

class PostTagInline(admin.TabularInline):
    model = PostTag
    extra = 1
    verbose_name = _('Тег')
    verbose_name_plural = _('Теги')

class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status', 'custom_method']
    list_filter = ('status', 'created', 'publish', 'author')
    search_fields = ('title', 'body', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    inlines = [PostTagInline]
    list_display_links = ('title', 'slug')
    readonly_fields = ('created', 'updated')
    verbose_name = _('Пост')
    verbose_name_plural = _('Посты')

    @admin.display(description=_('Пользовательский метод'))
    def custom_method(self, obj):
        return _("Пользовательское значение для {}").format(obj.title)

    @admin.display(description=_('Изображение'))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />',
                obj.image.url
            )
        return "-"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('print_post/<int:id>/', self.admin_site.admin_view(self.print_post), name='print_post'),
        ]
        return custom_urls + urls

    def print_post(self, request, id):
        post = Post.objects.get(id=id)
        if post.image:
            post.image_url = request.build_absolute_uri(post.image.url)

        html = render_to_string('post_print.html', {'post': post})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename=post_{post.id}.pdf'
        css = CSS(string='''
            @page { size: A4; margin: 1cm; }
            img { max-width: 100%; height: auto; }
        ''')
        HTML(string=html).write_pdf(response, stylesheets=[css])
        return response

    def print_post_action(self, request, queryset):
        if queryset.count() == 1:
            post = queryset.first()
            return self.print_post(request, post.id)
        else:
            self.message_user(request, _("Пожалуйста, выберите только одну публикацию для печати."))

    print_post_action.short_description = _("Генерация PDF документа")
    actions = [print_post_action]

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'last_name', 'first_name', 'patronymic', 'phone_number', 'email', 'full_name')
    search_fields = ('last_name', 'first_name', 'email', 'phone_number')
    list_display_links = ('last_name', 'first_name')
    list_filter = ('last_name',)
    readonly_fields = ('client_id',)
    verbose_name = _('Клиент')
    verbose_name_plural = _('Клиенты')

    @admin.display(description=_('Полное имя'))
    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.patronymic}"

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('house_id', 'name', 'location', 'capacity', 'price_per_night', 'image_preview', 'employee_info')
    search_fields = ('name', 'location', 'description')
    list_display_links = ('name',)
    list_filter = ('capacity', 'employee_id__last_name')
    readonly_fields = ('house_id', 'image_preview_large')
    raw_id_fields = ['employee_id']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'location', 'employee_id')
        }),
        (_('Характеристики'), {
            'fields': ('capacity', 'price_per_night')
        }),
        (_('Описание и изображение'), {
            'fields': ('description', 'image', 'amenities', 'image_preview_large')
        }),
    )
    verbose_name = _('Коттедж')
    verbose_name_plural = _('Коттеджи')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = "Превью"

    @admin.display(description=_('Изображение'))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="/static/images/{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image
            )
        return "-"

    @admin.display(description=_('Изображение (превью)'))
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="/static/images/{}" style="max-height: 300px;" />',
                obj.image
            )
        return _("Нет изображения")

    @admin.display(description=_('Ответственный'))
    def employee_info(self, obj):
        if obj.employee_id:
            return f"{obj.employee_id.last_name} {obj.employee_id.first_name[0]}."
        return "-"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee_id')

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('facility_id', 'house_link', 'name', 'description', 'status')
    search_fields = ('name', 'description')
    list_display_links = ('name',)
    list_filter = ('status',)
    readonly_fields = ('facility_id',)
    raw_id_fields = ['house_id']
    verbose_name = _('Удобство')
    verbose_name_plural = _('Удобства')

    @admin.display(description=_('Коттедж'))
    def house_link(self, obj):
        return format_html(
            '<a href="/admin/recreation/house/{}/change/">{}</a>',
            obj.house_id.house_id,
            obj.house_id.name
        )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'client_link', 'house_link', 'rating', 'short_comment', 'created_at')
    search_fields = ('client_id__last_name', 'house_id__name', 'comment')
    list_display_links = ('client_link', 'house_link')
    list_filter = (
        'rating',
        ('created_at', DateFieldListFilter),  # Правильное использование фильтра по дате
    )
    readonly_fields = ('review_id', 'created_at')
    raw_id_fields = ['client_id', 'house_id']
    date_hierarchy = 'created_at'  # Дополнительная навигация по датам
    
    @admin.display(description='Клиент')
    def client_link(self, obj):
        return f"{obj.client_id.last_name} {obj.client_id.first_name[0]}."

    @admin.display(description='Коттедж')
    def house_link(self, obj):
        return obj.house_id.name

    @admin.display(description='Комментарий')
    def short_comment(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'position', 'last_name', 'first_name', 'patronymic', 'contact_info', 'full_name')
    search_fields = ('last_name', 'first_name', 'position_id__name', 'contact_info')
    list_display_links = ('last_name', 'first_name')
    list_filter = ('position_id__name',)
    readonly_fields = ('employee_id',)
    raw_id_fields = ['position_id']
    verbose_name = _('Сотрудник')
    verbose_name_plural = _('Сотрудники')

    @admin.display(description=_('Должность'))
    def position(self, obj):
        return obj.position_id.name

    @admin.display(description=_('Полное имя'))
    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.patronymic}"

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('position_id', 'name', 'responsibilities')
    search_fields = ('name', 'responsibilities')
    list_display_links = ('name',)
    list_filter = ('name',)
    readonly_fields = ('position_id',)
    verbose_name = _('Должность')
    verbose_name_plural = _('Должности')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('get_id', 'client_link', 'house_link', 'check_in_date', 'check_out_date', 'total_cost')
    search_fields = ('client__last_name', 'house__name', 'user__username')
    list_display_links = ('get_id', 'client_link', 'house_link')  # Можно выбрать какие поля будут ссылками
    list_filter = ('house', 'check_in_date', 'check_out_date')
    readonly_fields = ('created_at',)
    raw_id_fields = ('client_id', 'house', 'user')
    verbose_name = _('Бронирование')
    verbose_name_plural = _('Бронирования')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'client', 'house', 'check_in_date', 'check_out_date')
        }),
        ('Контактная информация', {
            'fields': ('client_name', 'phone_number', 'email', 'comment')
        }),
        ('Финансы', {
            'fields': ('base_cost', 'total_cost', 'services')
        }),
    )

    @admin.display(description='ID')
    def get_id(self, obj):
        return obj.id

    @admin.display(description=_('Клиент'))
    def client_link(self, obj):
        if obj.client:
            return f"{obj.client.last_name} {obj.client.first_name[0]}."
        return "-"

    @admin.display(description=_('Коттедж'))
    def house_link(self, obj):
        return obj.house.name if obj.house else "-"

    @admin.display(description=_('Сотрудник'))
    def employee_link(self, obj):
        if obj.employee_id:
            return f"{obj.employee_id.last_name} {obj.employee_id.first_name[0]}."
        return "-"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('get_id', 'name', 'date', 'location', 'booking_link')  # Используем метод get_id вместо id
    search_fields = ('name', 'location')
    list_filter = ('date',)
    readonly_fields = ('get_id',)  # Используем метод get_id

    @admin.display(description='ID')
    def get_id(self, obj):
        return obj.event_id  # Возвращаем event_id объекта

    @admin.display(description='Бронирование')
    def booking_link(self, obj):
        if obj.booking_id:  # Используем booking_id вместо booking
            return format_html(
                '<a href="/admin/recreation/booking/{}/change/">{}</a>',
                obj.booking_id.booking_id,
                f"Бронирование #{obj.booking_id.booking_id}"
            )
        return "Общее мероприятие"

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'name', 'short_description', 'price', 'quantity', 'image_preview')
    search_fields = ('name', 'description')
    list_display_links = ('name',)
    list_filter = ('price',)
    readonly_fields = ('service_id', 'image_preview')
    verbose_name = _('Услуга')
    verbose_name_plural = _('Услуги')

    @admin.display(description=_('Описание'))
    def short_description(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    @admin.display(description=_('Изображение'))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />',
                obj.image.url
            )
        return "-"

@admin.register(BookingService)
class BookingServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'service_link', 'booking_link', 'booking_date', 'return_date')
    search_fields = ('service_id__name', 'booking_id__booking_id')  # Updated to use service_id
    list_display_links = ('service_link', 'booking_link')
    list_filter = ('booking_date', 'return_date')
    verbose_name = 'Бронирование услуги'
    verbose_name_plural = 'Бронирования услуг'

    @admin.display(description='Услуга')
    def service_link(self, obj):
        return obj.service_id.name  # Changed from obj.service to obj.service_id

    @admin.display(description='Бронирование')
    def booking_link(self, obj):
        return format_html(
            '<a href="/admin/recreation/booking/{}/change/">{}</a>',
            obj.booking_id.booking_id,
            f"Бронирование #{obj.booking_id.booking_id}"
        )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'booking_link', 'amount', 'payment_date', 'payment_method')
    search_fields = ('booking__booking_id', 'payment_method')  # Используем booking__booking_id вместо booking_id
    list_display_links = ('booking_link',)
    list_filter = ('payment_date', 'payment_method')
    readonly_fields = ('payment_id',)
    raw_id_fields = ['booking']  # Изменили booking_id на booking
    verbose_name = 'Платеж'
    verbose_name_plural = 'Платежи'

    @admin.display(description='Бронирование')
    def booking_link(self, obj):
        if obj.booking:  # Используем obj.booking вместо obj.booking_id
            return format_html(
                '<a href="/admin/recreation/booking/{}/change/">{}</a>',
                obj.booking.booking_id,
                f"Бронирование #{obj.booking.booking_id}"
            )
        return "-"
    

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    verbose_name = _('Тег')
    verbose_name_plural = _('Теги')

admin.site.register(Post, PostAdmin)