"""
Views для аутентификации.

FR-014: Авторизация оператора (упрощённая)
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views import View

from shift_report.forms import PINChangeForm, PINLoginForm


class HomeView(View):
    """
    Главная страница с перенаправлением по ролям.
    """

    template_name = 'shift_report/home.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        user = request.user

        # Маршрутизация по ролям (FR-002)
        if user.is_superuser or user.is_admin:
            # Администратор → панель администрирования
            return redirect('shift_admin:dashboard')

        elif user.is_chief:
            # Начальник цеха → мониторинг
            return redirect('master:monitoring')

        elif user.is_master:
            # Мастер → мониторинг своего участка
            return redirect('master:monitoring')

        elif user.is_operator:
            # Оператор → панель внесения данных
            return redirect('operator:dashboard')

        else:
            # Неопределённая роль → отображаем главную страницу
            return render(request, self.template_name, {
                'user': user
            })


class LoginView(View):
    """
    Страница входа по табельному номеру и PIN-коду.

    GET: Отображение формы входа
    POST: Обработка входа
    """

    template_name = 'shift_report/auth/login.html'

    def get(self, request):
        # Если пользователь уже авторизован, перенаправляем
        if request.user.is_authenticated:
            return redirect('home')

        form = PINLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PINLoginForm(request.POST)

        if form.is_valid():
            personnel_number = form.cleaned_data['personnel_number']
            pin = form.cleaned_data['pin']
            remember_me = form.cleaned_data['remember_me']

            user = authenticate(
                request,
                personnel_number=personnel_number,
                pin=pin
            )

            if user is not None:
                login(request, user)

                # Настройка времени жизни сессии
                if remember_me:
                    # 12 часов (конец смены)
                    request.session.set_expiry(
                        getattr(settings, 'SESSION_COOKIE_AGE', 43200)
                    )
                else:
                    # Сессия до закрытия браузера
                    request.session.set_expiry(0)

                messages.success(
                    request,
                    f'Добро пожаловать, {user.get_short_name()}!'
                )

                # Перенаправление
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                # ИСПРАВЛЕНО: Перенаправление по ролям
                if user.is_superuser or user.is_admin:
                    return redirect('shift_admin:dashboard')
                elif user.is_chief:
                    return redirect('master:monitoring')
                elif user.is_master:
                    return redirect('master:monitoring')
                elif user.is_operator:
                    return redirect('operator:dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(
                    request,
                    'Неверный табельный номер или PIN-код'
                )

        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """
    Выход из системы.
    """

    def get(self, request):
        return self.post(request)

    def post(self, request):
        logout(request)
        messages.info(request, 'Вы вышли из системы')
        return redirect('login')


class ChangePINView(View):
    """
    Страница смены PIN-кода.
    """

    template_name = 'shift_report/auth/change_pin.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        form = PINChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        form = PINChangeForm(user=request.user, data=request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'PIN-код успешно изменён')
            return redirect('home')

        return render(request, self.template_name, {'form': form})


class ProfileView(View):
    """
    Страница профиля пользователя.
    """

    template_name = 'shift_report/auth/profile.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        return render(request, self.template_name, {
            'user': request.user
        })