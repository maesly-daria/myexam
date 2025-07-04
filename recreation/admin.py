from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export import fields, resources
from import_export.admin import ExportMixin
from weasyprint import CSS, HTML

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import (
    Booking,
    BookingService,
    Client,
    CustomUser,
    DZexam,
    Employee,
    Event,
    Facility,
    House,
    Payment,
    Position,
    Post,
    PostTag,
    Review,
    Service,
    Tag,
)

admin.site.site_header = _('Администрирование базы отдыха "FurTree"')
admin.site.site_title = _("База отдыха")
admin.site.index_title = _("Управление базой отдыха")


class BaseExportAdmin(ExportMixin, admin.ModelAdmin):
    def get_export_formats(self):
        return [CustomXLSXFormat]

    def get_export_filename(self, request, queryset, file_format):
        model_name = self.model._meta.verbose_name_plural
        return f"{model_name}_export_{timezone.now().strftime('%Y-%m-%d')}.xlsx"


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        "id",
        "username",
        "last_name",
        "patronymic",
        "email",
        "phone",
        "is_staff",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "phone", "last_name")
    ordering = ("last_name", "username")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Персональная информация",
            {"fields": ("last_name", "patronymic", "email", "phone")},
        ),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Важные даты",
            {"fields": ("last_login", "date_joined"), "classes": ("collapse",)},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "last_name",
                    "username",
                    "patronymic",
                    "email",
                    "phone",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    search_fields = ("last_name", "username", "patronymic", "email", "phone")
    ordering = ("last_name", "username")


admin.site.register(CustomUser, CustomUserAdmin)


class PostTagInline(admin.TabularInline):
    model = PostTag
    extra = 1
    verbose_name = _("Тег")
    verbose_name_plural = _("Теги")


class PostResource(resources.ModelResource):
    class Meta:
        model = Post
        fields = ("id", "title", "author__username", "status", "publish")
        export_order = ("id", "title", "author__username", "status", "publish")

    def get_export_queryset(self, request):
        """Кастомизация queryset для экспорта"""
        qs = super().get_export_queryset(request)
        return qs.filter(is_active=True).select_related("employee_id")

    def dehydrate_status(self, obj):
        """Кастомизация отображения статуса"""
        return "Активен" if obj.is_active else "Неактивен"

    def get_export_filename(self, request, queryset, file_format):
        """Кастомизация имени файла"""
        return f"houses_export_{timezone.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"


@admin.register(Post)
class PostAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = PostResource
    list_display = [
        "title",
        "slug",
        "author",
        "publish",
        "status",
        "custom_method",
        "image_preview",
    ]
    list_filter = ("status", "created", "publish", "author")
    search_fields = ("title", "body", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["status", "publish"]
    inlines = [PostTagInline]
    list_display_links = ("title", "slug")
    readonly_fields = ("created", "updated", "image_preview")
    verbose_name = _("Пост")
    verbose_name_plural = _("Посты")

    @admin.display(description=_("Пользовательский метод"))
    def custom_method(self, obj):
        return _("Пользовательское значение для {}").format(obj.title)

    @admin.display(description=_("Изображение"))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />', obj.image.url
            )
        return "-"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "print_post/<int:id>/",
                self.admin_site.admin_view(self.print_post),
                name="print_post",
            ),
        ]
        return custom_urls + urls

    def print_post(self, request, id):
        post = Post.objects.get(id=id)
        if post.image:
            post.image_url = request.build_absolute_uri(post.image.url)

        html = render_to_string("post_print.html", {"post": post})
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"filename=post_{post.id}.pdf"
        css = CSS(
            string="""
            @page { size: A4; margin: 1cm; }
            img { max-width: 100%; height: auto; }
        """
        )
        HTML(string=html).write_pdf(response, stylesheets=[css])
        return response

    def print_post_action(self, request, queryset):
        if queryset.count() == 1:
            post = queryset.first()
            return self.print_post(request, post.id)
        else:
            self.message_user(
                request, _("Пожалуйста, выберите только одну публикацию для печати.")
            )

    print_post_action.short_description = _("Генерация PDF документа")
    actions = [print_post_action]


class ClientResource(resources.ModelResource):
    full_name = fields.Field(column_name="ФИО")
    phone = fields.Field(column_name="Телефон", attribute="phone_number")
    email = fields.Field(column_name="Email")
    document_status = fields.Field(column_name="Документ")

    class Meta:
        model = Client
        fields = ("full_name", "phone_number", "email", "document")
        export_order = ("full_name", "phone", "email", "document_status")
        encoding = "utf-8-sig"

    def dehydrate_full_name(self, client):
        return (
            f"{client.last_name} {client.first_name} {client.patronymic or ''}".strip()
        )

    def dehydrate_email(self, client):
        return client.email or "Не указан"

    def dehydrate_document_status(self, client):
        if client.document:
            return "Прикреплен"
        return "Отсутствует"


@admin.register(Client)
class ClientAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("last_name", "first_name", "phone_number", "email", "document_link")
    search_fields = ["last_name", "first_name", "patronymic", "phone_number", "email"]
    list_filter = ("last_name",)
    raw_id_fields = ["user"]
    list_per_page = 50

    def document_status(self, obj):
        return "✓" if obj.document else "✗"

    document_status.short_description = "Документ"

    @admin.display(description="Документ")
    def document_link(self, obj):
        if obj.document:
            return format_html('<a href="{}">📄</a>', obj.document.url)
        return "—"


# Убедимся, что XLSX формат доступен
try:
    from import_export.formats.base_formats import XLSX

    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False


class CustomXLSXFormat(XLSX):
    def get_content_type(self):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8-sig"


class HouseResource(resources.ModelResource):
    name = fields.Field(column_name="Название", attribute="name")
    price = fields.Field(column_name="Цена за ночь (руб)")
    capacity = fields.Field(
        column_name="Вместимость", attribute="capacity"  # Теперь точно берем из модели
    )
    location = fields.Field(column_name="Местоположение")
    address_specified = fields.Field(column_name="Адрес указан")
    manager = fields.Field(column_name="Менеджер")

    class Meta:
        model = House
        fields = (
            "name",
            "price",
            "capacity",
            "location",
            "address_specified",
            "manager",
        )
        export_order = (
            "name",
            "price",
            "capacity",
            "location",
            "address_specified",
            "manager",
        )
        skip_unchanged = True
        report_skipped = False
        encoding = "utf-8-sig"

    def dehydrate_price(self, house):
        return f"{house.price_per_night} ₽"

    def dehydrate_address_specified(self, house):
        return "Да" if house.location else "Нет"

    def dehydrate_manager(self, house):
        if house.employee_id:
            return f"{house.employee_id.last_name} {house.employee_id.first_name}"
        return "Не назначен"

    def dehydrate_location(self, house):
        if house.location:
            return f"Свердловская область, {house.location.split(',')[-1].strip()}"
        return ""

    def before_export(self, queryset, *args, **kwargs):
        return queryset.select_related("employee_id")


@admin.register(House)
class HouseAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "price_per_night",
        "capacity",
        "location_short",
        "get_address_specified",
        "get_manager",
        "status_badge",
        "image_preview",
    )
    list_filter = ("is_active", "employee_id", "price_per_night", "capacity")
    search_fields = ("name", "location", "description")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("employee_id",)
    ordering = ["name"]
    list_per_page = 30
    readonly_fields = ("image_preview",)
    list_editable = (
        "price_per_night",
        "capacity",
    )  # Добавляем возможность быстрого редактирования

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("name", "slug", "employee_id", "is_active")},
        ),
        ("Характеристики", {"fields": ("location", "capacity", "price_per_night")}),
        (
            "Медиа и описание",
            {
                "fields": ("image", "image_preview", "description", "amenities"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_export_formats(self):
        if XLSX_AVAILABLE:
            return [CustomXLSXFormat]
        return super().get_export_formats()

    def get_address_specified(self, obj):
        return "Да" if obj.location else "Нет"

    get_address_specified.short_description = "Адрес указан"

    def get_manager(self, obj):
        if obj.employee_id:
            return f"{obj.employee_id.last_name} {obj.employee_id.first_name}"
        return "Не назначен"

    get_manager.short_description = "Менеджер"

    def get_export_filename(self, request, queryset, file_format):
        return f"houses_export_{timezone.now().strftime('%Y-%m-%d')}.xlsx"

    @admin.display(description="Цена")
    def price_display(self, obj):
        return f"{obj.price_per_night} ₽"

    @admin.display(description="Местоположение")
    def location_short(self, obj):
        return obj.location[:50] + "..." if len(obj.location) > 50 else obj.location

    @admin.display(description="Статус")
    def status_badge(self, obj):
        color = "green" if obj.is_active else "red"
        text = "Активен" if obj.is_active else "Неактивен"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, text
        )

    @admin.display(description="Изображение")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />', obj.image.url
            )
        return "-"


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("facility_id", "house_link", "name", "description", "status")
    search_fields = ("name", "description")
    list_display_links = ("name",)
    list_filter = ("status",)
    readonly_fields = ("facility_id",)
    raw_id_fields = ["house_id"]
    verbose_name = _("Удобство")
    verbose_name_plural = _("Удобства")

    @admin.display(description=_("Коттедж"))
    def house_link(self, obj):
        return format_html(
            '<a href="/admin/recreation/house/{}/change/">{}</a>',
            obj.house_id.house_id,
            obj.house_id.name,
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "review_id",
        "client_link",
        "house_link",
        "rating",
        "short_comment",
        "created_at",
    )
    search_fields = ("client_id__last_name", "house_id__name", "comment")
    list_display_links = ("client_link", "house_link")
    list_filter = (
        "rating",
        ("created_at", DateFieldListFilter),
    )
    readonly_fields = ("review_id", "created_at")
    raw_id_fields = ["client_id", "house_id"]
    date_hierarchy = "created_at"

    @admin.display(description="Клиент")
    def client_link(self, obj):
        if obj.client_id:
            first_initial = (
                obj.client_id.first_name[0] if obj.client_id.first_name else ""
            )
            return f"{obj.client_id.last_name} {first_initial}."
        return "-"

    @admin.display(description="Коттедж")
    def house_link(self, obj):
        return obj.house_id.name if obj.house_id else "-"

    @admin.display(description="Комментарий")
    def short_comment(self, obj):
        if obj.comment:
            return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
        return "-"


class EmployeeResource(resources.ModelResource):
    full_name = fields.Field(column_name="ФИО")
    position = fields.Field(column_name="Должность")
    contacts = fields.Field(column_name="Контакты")
    hire_date = fields.Field(column_name="Дата приема")

    class Meta:
        model = Employee
        fields = ("full_name", "position", "contacts", "hire_date")
        export_order = ("full_name", "position", "contacts", "hire_date")
        encoding = "utf-8-sig"

    def dehydrate_full_name(self, employee):
        return f"{employee.last_name} {employee.first_name} {employee.patronymic or ''}".strip()

    def dehydrate_position(self, employee):
        return str(employee.position_id) if employee.position_id else "Не указана"

    def dehydrate_contacts(self, employee):
        contact_parts = []
        if employee.phone:
            contact_parts.append(f"тел: {employee.phone}")
        if employee.email:
            contact_parts.append(f"email: {employee.email}")
        return ", ".join(contact_parts) or "Не указаны"

    def dehydrate_hire_date(self, employee):
        return (
            employee.hire_date.strftime("%d.%m.%Y")
            if employee.hire_date
            else "Не указана"
        )


@admin.register(Employee)
class EmployeeAdmin(BaseExportAdmin, admin.ModelAdmin):
    resource_class = EmployeeResource
    list_display = ("get_full_name", "get_position", "get_contacts", "get_hire_date")
    list_filter = ("position_id",)
    search_fields = ("last_name", "first_name", "phone", "email", "position_id__name")

    def get_full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.patronymic or ''}".strip()

    get_full_name.short_description = "ФИО"

    def get_position(self, obj):
        return str(obj.position_id) if obj.position_id else "-"

    get_position.short_description = "Должность"

    def get_contacts(self, obj):
        contacts = []
        if obj.phone:
            contacts.append(obj.phone)
        if obj.email:
            contacts.append(obj.email)
        return " | ".join(contacts) or obj.contact_info or "Не указаны"

    get_contacts.short_description = "Контакты"

    def get_hire_date(self, obj):
        return obj.hire_date.strftime("%d.%m.%Y") if obj.hire_date else "-"

    get_hire_date.short_description = "Дата приема"


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("position_id", "name", "responsibilities")
    search_fields = ("name", "responsibilities")
    list_display_links = ("name",)
    list_filter = ("name",)
    readonly_fields = ("position_id",)
    verbose_name = _("Должность")
    verbose_name_plural = _("Должности")


class BookingServiceInline(admin.TabularInline):
    model = BookingService
    extra = 1
    raw_id_fields = ["service_id"]


@admin.register(Booking)
class BookingAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        "booking_id",
        "get_client",
        "get_house",
        "check_in_date",
        "check_out_date",
        "get_nights",
        "total_cost",
    )
    list_filter = ("house", "check_in_date", "check_out_date")
    date_hierarchy = "created_at"
    raw_id_fields = ("client_id", "house", "user")
    list_select_related = True
    readonly_fields = ("get_nights_readonly",)

    @admin.display(description="Ночи")
    def get_nights_readonly(self, obj):
        return self.get_nights(obj)

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("client_id", "house", "user", "client_name")},
        ),
        (
            "Даты бронирования",
            {"fields": ("check_in_date", "check_out_date", "guests")},
        ),
        (
            "Контактные данные",
            {"fields": ("phone_number", "email"), "classes": ("collapse",)},
        ),
        ("Финансы", {"fields": ("base_cost", "total_cost", "services")}),
        ("Дополнительно", {"fields": ("comment",), "classes": ("collapse",)}),
    )

    @admin.display(description="Клиент")
    def get_client(self, obj):
        if obj.client_id:
            return f"{obj.client_id.last_name} {obj.client_id.first_name[0]}."
        return obj.client_name or "-"

    @admin.display(description="Ночи")
    def get_nights(self, obj):
        if obj.check_in_date and obj.check_out_date:
            return (obj.check_out_date - obj.check_in_date).days
        return "-"

    @admin.display(description="Коттедж")
    def get_house(self, obj):
        if obj.house:
            return format_html(
                '<a href="/admin/recreation/house/{}/change/">{}</a>',
                obj.house.house_id,
                obj.house.name,
            )
        return "-"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "name", "date", "location", "booking_link")
    search_fields = ("name", "location")
    list_filter = ("date",)
    readonly_fields = ("event_id",)
    raw_id_fields = ("booking_id",)
    verbose_name = _("Мероприятие")
    verbose_name_plural = _("Мероприятия")

    @admin.display(description="Бронирование")
    def booking_link(self, obj):
        if obj.booking_id:  # Используем booking_id вместо booking
            return format_html(
                '<a href="/admin/recreation/booking/{}/change/">{}</a>',
                obj.booking_id.booking_id,
                f"Бронирование #{obj.booking_id.booking_id}",
            )
        return "-"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "service_id",
        "name",
        "short_description",
        "price",
        "quantity",
        "image_preview",
    )
    search_fields = ("name", "description")
    list_display_links = ("name",)
    list_filter = ("price",)
    readonly_fields = ("service_id", "image_preview")
    verbose_name = _("Услуга")
    verbose_name_plural = _("Услуги")

    @admin.display(description=_("Описание"))
    def short_description(self, obj):
        return (
            obj.description[:50] + "..."
            if len(obj.description) > 50
            else obj.description
        )

    @admin.display(description=_("Изображение"))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />', obj.image.url
            )
        return "-"


@admin.register(BookingService)
class BookingServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "service_link", "booking_link", "booking_date", "return_date")
    search_fields = ("service_id__name", "booking_id__booking_id")
    list_display_links = ("service_link", "booking_link")
    list_filter = ("booking_date", "return_date")
    raw_id_fields = ("service_id", "booking_id")  # Используем _id суффикс
    verbose_name = "Бронирование услуги"
    verbose_name_plural = "Бронирования услуг"

    @admin.display(description="Услуга")
    def service_link(self, obj):
        if obj.service_id:  # Используем service_id вместо service
            return format_html(
                '<a href="/admin/recreation/service/{}/change/">{}</a>',
                obj.service_id.service_id,
                obj.service_id.name,
            )
        return "-"

    @admin.display(description="Бронирование")
    def booking_link(self, obj):
        if obj.booking_id:  # Используем booking_id вместо booking
            return format_html(
                '<a href="/admin/recreation/booking/{}/change/">{}</a>',
                obj.booking_id.booking_id,
                f"Бронирование #{obj.booking_id.booking_id}",
            )
        return "-"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_id",
        "booking_link",
        "amount",
        "payment_date",
        "payment_method",
    )
    search_fields = ("booking__booking_id", "payment_method")
    list_display_links = ("booking_link",)
    list_filter = ("payment_date", "payment_method")
    readonly_fields = ("payment_id",)
    raw_id_fields = ["booking"]
    verbose_name = _("Платеж")
    verbose_name_plural = _("Платежи")

    @admin.display(description="Бронирование")
    def booking_link(self, obj):
        if obj.booking:
            return format_html(
                '<a href="/admin/recreation/booking/{}/change/">{}</a>',
                obj.booking.booking_id,
                f"Бронирование #{obj.booking.booking_id}",
            )
        return "-"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)
    verbose_name = _("Тег")
    verbose_name_plural = _("Теги")


@admin.register(DZexam)
class DZexamAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "exam_date", "is_public")
    search_fields = ("title", "users__email")
    list_filter = ("is_public", "created_at")
    filter_horizontal = ("users",)
    date_hierarchy = "exam_date"

    @admin.display(description="Изображение")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />', obj.image.url
            )
        return "-"
