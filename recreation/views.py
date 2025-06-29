import logging
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
# from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    BookingForm,
    ClientForm,
    ClientRegistrationForm,
    CustomAuthenticationForm,
    CustomUserCreationForm,
    EmailPhoneAuthForm,
    HouseFilter,
    HouseForm,
    PostForm,
    ReviewForm,
    UserProfileForm,
)
from .models import Booking, Client, DZexam, House, Post, Review, Service, Tag

logger = logging.getLogger(__name__)


# Главная страница
def home(request):
    rating_stats = Review.objects.aggregate(
        global_avg=Avg("rating"), total=Count("review_id")
    )
    try:
        # 1. Получаем активные коттеджи с их рейтингами
        houses = House.objects.filter(is_active=True).order_by("name")
        cottages_data = []

        for house in houses:
            # Получаем средний рейтинг и количество отзывов для каждого коттеджа
            avg_rating = house.review_set.aggregate(Avg("rating"))["rating__avg"] or 0
            review_count = house.review_set.count()

            cottages_data.append(
                {
                    "obj": house,
                    "image_url": house.get_image_url,  # Используем свойство без вызова ()
                    "avg_rating": avg_rating,
                    "review_count": review_count,
                }
            )

        # 2. Получаем последние отзывы
        reviews = Review.objects.select_related("client_id", "house_id").order_by(
            "-created_at"
        )[:5]

        # 3. Получаем последние посты
        latest_posts = Post.objects.filter(status="published").order_by("-publish")[:3]

        # 4. Получаем активные услуги
        services = Service.objects.filter(is_active=True).order_by("type", "name")[:9]

        return render(
            request,
            "home.html",
            {
                "cottages": cottages_data,
                "guest_range": range(1, 21),
                "reviews": reviews,
                "latest_posts": latest_posts,
                "services": services,
                "STATIC_URL": settings.STATIC_URL,
                "debug": settings.DEBUG,
                "global_avg_rating": rating_stats["global_avg"] or 0,
                "global_total_reviews": rating_stats["total"],
            },
        )

    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        return render(
            request,
            "home.html",
            {
                "cottages": [],
                "guest_range": range(1, 21),
                "reviews": [],
                "latest_posts": [],
                "services": [],
                "debug": settings.DEBUG,
            },
        )


@require_GET
def service_data(request, pk):
    service = get_object_or_404(Service, pk=pk)

    # Получаем URL изображения
    if service.image and hasattr(service.image, "url"):
        image_url = service.image.url
    else:
        # Проверяем наличие изображения в static/images/
        image_name = f"service-{pk}.jpg"
        static_path = os.path.join("images", image_name)
        full_static_path = os.path.join(settings.STATIC_ROOT, static_path)

        if os.path.exists(full_static_path):
            image_url = os.path.join(settings.STATIC_URL, static_path)
        else:
            # Используем общее изображение "no-image.jpg" если специфичное не найдено
            image_url = os.path.join(settings.STATIC_URL, "images/no-image.jpg")

    response_data = {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "price": str(service.price),
        "type": service.get_type_display(),
        "image_url": image_url,
        "icon": service.get_icon(),
    }

    return JsonResponse(response_data)


# Личный кабинет
@login_required
def account_view(request):
    try:
        client = request.user.client_profile
    except Client.DoesNotExist:
        client = Client.objects.create(
            user=request.user,
            last_name=request.user.last_name or "",
            first_name=request.user.username or "",
            patronymic=request.user.patronymic or "",
            email=request.user.email,
            phone_number=request.user.phone or "",
        )

    if request.method == "POST" and "logout" in request.POST:
        logout(request)
        return redirect("home")

        form = ClientForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            # Обработка удаления документа
            if (
                "document-clear" in request.POST
                and request.POST["document-clear"] == "on"
            ):
                client.document.delete(save=False)

            form.save()
            messages.success(request, "Профиль успешно обновлен")
            return redirect("account")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = ClientForm(instance=client)

    return render(request, "account.html", {"form": form, "client": client})


def account(request):
    if not request.user.is_authenticated:
        return redirect("login")

    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related("house_id")
        .prefetch_related("services")
    )

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        client_form = ClientForm(request.POST, instance=request.user.client_profile)

        if form.is_valid() and client_form.is_valid():
            form.save()
            client_form.save()
            messages.success(request, "Профиль успешно обновлен")
            return redirect("account")
    else:
        form = UserProfileForm(instance=request.user)
        client_form = ClientForm(instance=request.user.client_profile)

    # Добавляем текущую дату в контекст для отображения статуса бронирований
    context = {
        "form": form,
        "client_form": client_form,
        "bookings": bookings,
        "now": timezone.now().date(),
    }

    return render(request, "account.html", context)


# def post_detail(request, slug, id=None):
# Посты
def post_detail(request, slug):
    post = get_object_or_404(Post, slug__iexact=slug)
    return render(request, "blog/post_detail.html", {"post": post})


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # Для сохранения тегов
            messages.success(request, "Пост успешно создан")
            return redirect("post_detail", id=post.id)
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})


@login_required
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect("post_detail", slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, "blog/post_form.html", {"form": form})


# @login_required
# def post_delete(request, pk):
#     post = get_object_or_404(Post, pk=pk)
#     if request.method == "POST":
#         post.delete()
#         return redirect("post_list")
#     return render(request, "blog/post_confirm_delete.html", {"post": post})


def post_list(request):
    # Получаем все опубликованные посты с авторами и тегами
    posts = (
        Post.objects.filter(status="published")
        .select_related("author")
        .prefetch_related("tags")
    )

    # Получаем параметры фильтрации из GET-запроса
    search_query = request.GET.get("search", "")
    tag_query = request.GET.get("tag", "")
    order_by = request.GET.get("order_by", "-publish")

    # Применяем фильтры
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | Q(body__icontains=search_query)
        )

    if tag_query:
        posts = posts.filter(tags__name=tag_query)

    # Применяем сортировку
    posts = posts.order_by(order_by).distinct()

    # Получаем все теги с количеством постов для фильтра
    all_tags = Tag.objects.annotate(num_posts=Count("posts")).filter(num_posts__gt=0)

    # Пагинация
    paginator = Paginator(posts, 5)
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Подготавливаем контекст для шаблона
    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "tag_query": tag_query,
        "order_by": order_by,
        "all_tags": all_tags,
    }

    return render(request, "blog/post_list.html", context)


# def post_detail(request, slug):
#     post = get_object_or_404(Post, slug=slug)
#     return render(
#         request,
#         "blog/post_detail.html",
#         {
#             "post": post,
#             "user": request.user,  # Убедитесь, что user передается в контекст
#         },
#     )


@login_required
def delete_old_posts(request):
    if request.method == "POST":
        old_posts = Post.objects.filter(
            publish__lt=timezone.now() - timedelta(days=365)
        )
        deleted_count = old_posts.delete()[0]
        messages.success(request, f"Удалено {deleted_count} старых постов")
        return redirect("post_list")
    return render(request, "blog/confirm_bulk_delete.html")


# Коттеджи и бронирование
def cottages(request):
    # Текущая логика (даты и гости)
    check_in = request.GET.get("check_in", "")
    check_out = request.GET.get("check_out", "")
    guests = int(request.GET.get("guests", 2))

    # Фильтрация по гостям (сохраняем вашу проверку)
    houses = House.objects.filter(capacity__gte=guests)

    # Добавляем фильтрацию через django_filters (цена, название и т.д.)
    house_filter = HouseFilter(request.GET, queryset=houses)
    filtered_houses = house_filter.qs

    # Подготовка данных для шаблона (сохраняем ваш формат)
    houses_data = []
    for house in filtered_houses:
        houses_data.append(
            {
                "obj": house,
                "image_url": house.get_image_url,  # Убраны скобки, так как это свойство
                "image_exists": house.image_exists(),
            }
        )

    return render(
        request,
        "cottages.html",
        {
            "houses_data": houses_data,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "guest_range": range(1, 21),
            "filter": house_filter,  # Передаём фильтр для формы
        },
    )


def cottage_detail(request, slug):
    cottage = get_object_or_404(House, slug=slug)

    # 1. Похожие коттеджи (те же удобства или цена в том же диапазоне)
    similar_houses = (
        House.objects.filter(
            Q(amenities__icontains=cottage.amenities.split("\n")[0])  # Первое удобство
            | Q(
                price_per_night__range=(
                    cottage.price_per_night * 0.8,
                    cottage.price_per_night * 1.2,
                )
            ),
            is_active=True,
        )
        .exclude(pk=cottage.pk)
        .distinct()[:4]
    )  # Исключаем текущий и ограничиваем 4

    # 2. Услуги, подходящие для этого коттеджа (по вместимости)
    recommended_services = Service.objects.filter(
        (Q(type="entertainment") | Q(type="relax"))
        & ~Q(price__lt=2000)
        & Q(quantity__gte=cottage.capacity * 0.5)  # Услуги для компаний такого размера
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        data = {
            "name": cottage.name,
            "capacity": cottage.capacity,
            "price_per_night": cottage.price_per_night,
            "description": cottage.description,
            "amenities": cottage.amenities,
            "image_url": cottage.get_image_url(),
        }
        return JsonResponse(data)

    amenities_list = cottage.amenities.split("\n") if cottage.amenities else []
    return render(
        request,
        "cottage_detail.html",
        {
            "cottage": cottage,
            "similar_houses": similar_houses,
            "recommended_services": recommended_services,
            "image_url": cottage.get_image_url(),
            "image_exists": cottage.image_exists(),
            "amenities_list": amenities_list,
        },
    )


def booking(request):
    house_id = request.GET.get("house")
    check_in = request.GET.get("check_in")
    check_out = request.GET.get("check_out")
    guests = request.GET.get("guests", 2)

    if not all([house_id, check_in, check_out]):
        return redirect("cottages")

    try:
        house = House.objects.get(pk=house_id)
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        nights = (check_out_date - check_in_date).days
        house_cost = house.price_per_night * nights

        if check_in_date >= check_out_date:
            messages.error(request, "Дата выезда должна быть позже даты заезда")
            return redirect("cottages")

    except (House.DoesNotExist, ValueError):
        return redirect("cottages")

    if request.method == "POST":
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    booking = form.save(commit=False)
                    # ... existing booking setup code ...

                    # Get selected services
                    selected_services = form.cleaned_data.get("services", [])
                    if selected_services:
                        service_cost = sum(s.price for s in selected_services)
                        booking.total_cost += service_cost

                    booking.save()
                    booking.services.set(selected_services)  # Set the services

                    return redirect("payment", booking_id=booking.id)
            except Exception as e:
                messages.error(request, f"Ошибка при бронировании: {str(e)}")
                logger.error(f"Booking error: {str(e)}", exc_info=True)
    else:
        form = BookingForm(user=request.user)
        selected_services = []

    return render(
        request,
        "booking.html",
        {
            "house": house,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": guests,
            "nights": nights,
            "house_cost": house_cost,
            "form": form,
            "services": Service.objects.all(),
        },
    )


@login_required
def payment(request, booking_id):
    try:
        booking = Booking.objects.select_related("house_id", "client_id").get(
            pk=booking_id
        )

        # Проверка прав доступа
        if booking.user != request.user:
            raise Http404("Бронирование не найдено")

        nights = (booking.check_out_date - booking.check_in_date).days
        services = booking.services.all()

        return render(
            request,
            "payment.html",
            {
                "booking": booking,
                "house": booking.house_id,
                "nights": nights,
                "services": services,
            },
        )

    except Booking.DoesNotExist:
        raise Http404("Бронирование не найдено")


# Для входа
class LoginView(auth_views.LoginView):
    form_class = EmailPhoneAuthForm
    template_name = "registration/login.html"


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Явно указываем бэкенд при логине
            login(request, user, backend="recreation.backends.EmailPhoneBackend")
            return redirect("account")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


def all_reviews(request):
    # reviews = Review.objects.all().select_related

    if request.method == "POST" and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.client_id = request.user.client_profile
            review.save()
            messages.success(request, "Ваш отзыв успешно добавлен!")
            return redirect("all_reviews")
    else:
        form = ReviewForm()

    reviews_list = (
        Review.objects.all()
        .select_related("client_id", "house_id")
        .order_by("-created_at")
    )
    paginator = Paginator(reviews_list, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "all_reviews.html",
        {
            "page_obj": page_obj,
            "total_reviews": reviews_list.count(),
            "form": form,
            "houses": House.objects.all(),
        },
    )


@login_required
def create_review(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.client_id = request.user.client_profile
            review.save()
            messages.success(request, "Ваш отзыв успешно добавлен!")
            return redirect("all_reviews")
    else:
        form = ReviewForm()
    return render(request, "review_form.html", {"form": form})


@login_required
def update_review(request, pk):
    review = get_object_or_404(Review, pk=pk)

    # Проверка, что пользователь может редактировать этот отзыв
    if review.client_id.user != request.user:
        return redirect("all_reviews")

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect("all_reviews")
    else:
        form = ReviewForm(instance=review)

    # Добавляем houses в контекст
    return render(
        request,
        "review_form.html",
        {"form": form, "houses": House.objects.all()},  # Добавляем список всех домов
    )


@login_required
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.client_id.user != request.user:
        return JsonResponse(
            {"status": "error", "message": "Недостаточно прав"}, status=403
        )
    review.delete()
    return JsonResponse({"status": "success"})


# def all_reviews(request):
#     reviews_list = (
#         Review.objects.all()
#         .select_related("client_id", "house_id")
#         .order_by("-created_at")
#     )
#     paginator = Paginator(reviews_list, 9)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)

#     return render(
#         request,
#         "all_reviews.html",
#         {
#             "page_obj": page_obj,
#             "total_reviews": reviews_list.count(),
#             "houses": House.objects.all(),
#         },
#     )


class HouseDetailAPI(APIView):
    def get(self, request, pk):
        house = get_object_or_404(House, pk=pk)
        data = {
            "id": house.house_id,
            "name": house.name,
            "price_per_night": house.price_per_night,
            "capacity": house.capacity,
        }
        return Response(data)


def create_client(request):
    if request.method == "POST":
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("some_view_name")
    else:
        form = ClientRegistrationForm()

    return render(request, "create_client.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page
            return redirect("some-view-name")
        else:
            # Return an error message
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")


# def post_list(request):
#     posts = Post.objects.select_related('author').prefetch_related('tags').filter(status='published')

#     # Фильтрация
#     search_query = request.GET.get('search', '')
#     if search_query:
#         posts = posts.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))

#     # Пагинация
#     paginator = Paginator(posts, 5)
#     page_number = request.GET.get('page')
#     try:
#         page_obj = paginator.page(page_number)
#     except PageNotAnInteger:
#         page_obj = paginator.page(1)
#     except EmptyPage:
#         page_obj = paginator.page(paginator.num_pages)

#     context = {
#         'page_obj': page_obj,
#         'search_query': search_query,
#     }
#     return render(request, 'blog/post_list.html', context)


@login_required
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    if request.method == "POST":
        post.delete()
        return redirect("post_list")
    return render(request, "blog/post_confirm_delete.html", {"post": post})


# def delete_old_posts(request):
#     # Удалить посты старше 1 года
#     old_posts = Post.objects.filter(publish__lt=timezone.now() - timedelta(days=365))
#     deleted_count = old_posts.delete()[0]
#     messages.success(request, f"Deleted {deleted_count} old posts")
#     return redirect("post_list")


def create_house(request):
    if request.method == "POST":
        form = HouseForm(request.POST, request.FILES)
        if form.is_valid():
            house = form.save()
            messages.success(request, "Дом успешно создан!")
            return redirect(
                "house_detail", slug=house.slug
            )  # Или другой подходящий URL
    else:
        form = HouseForm()
    return render(request, "houses/create_house.html", {"form": form})


class CustomLoginView(auth_views.LoginView):
    form_class = CustomAuthenticationForm
    template_name = "registration/login.html"


@login_required
def download_document(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    if client.user != request.user and not request.user.is_staff:
        raise PermissionDenied

    response = FileResponse(client.document.open(), as_attachment=True)
    return response


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Проверка прав ТОЛЬКО здесь, внутри функции!
    if not (request.user == post.author or request.user.is_superuser):
        raise PermissionDenied("У вас нет прав для редактирования этого поста")


def dzexam_view(request):
    exams = DZexam.objects.filter(is_public=True)
    return render(
        request,
        "dzexam.html",
        {"exams": exams, "fio": "Змеева Дарья Васильевна", "group": "Группа 231-365"},
    )


class CottagesListView(ListView):
    model = House
    template_name = "recreation/house_list.html"  # Главная страница с коттеджами
    context_object_name = "houses"

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = HouseFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs  # Возвращаем отфильтрованные данные

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset  # Передаём фильтр в шаблон
        return context


@login_required
def user_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('house')
    return render(request, 'bookings/user_bookings.html', {'bookings': bookings})
