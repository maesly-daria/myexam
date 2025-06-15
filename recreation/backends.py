from django.contrib.auth.backends import ModelBackend

from .models import CustomUser, models


class EmailPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Пробуем найти по email или телефону
            user = CustomUser.objects.get(
                models.Q(email=username) | models.Q(phone=username)
            )
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None
