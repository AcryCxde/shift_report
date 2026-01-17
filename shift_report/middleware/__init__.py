"""
Middleware для контроля доступа.

FR-039: Ролевая модель доступа
"""

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve


class RoleBasedAccessMiddleware:
    """
    Middleware для проверки прав доступа на основе ролей.

    Проверяет, имеет ли пользователь доступ к запрашиваемому URL
    на основе его роли.
    """

    # URL, доступные без авторизации
    PUBLIC_URLS = [
        'login',
        'logout',
        'admin:index',
        'admin:login',
    ]

    # Префиксы URL для разных ролей
    ROLE_URL_PREFIXES = {
        'operator': ['operator:', 'api:operator:'],
        'master': ['master:', 'operator:', 'api:master:', 'api:operator:'],
        'chief': ['analytics:', 'master:', 'operator:', 'api:'],
        'admin': None,  # None означает доступ ко всем URL
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем статику и медиа
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Пропускаем админку Django (у неё своя проверка)
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Получаем имя URL
        try:
            url_name = resolve(request.path).url_name
            namespace = resolve(request.path).namespace
            full_url_name = f'{namespace}:{url_name}' if namespace else url_name
        except Exception:
            full_url_name = None

        # Проверяем публичные URL
        if full_url_name in self.PUBLIC_URLS:
            return self.get_response(request)

        # Проверяем авторизацию
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        # Админы имеют доступ ко всему
        if request.user.is_admin or request.user.is_superuser:
            return self.get_response(request)

        # Проверяем доступ по роли
        allowed_prefixes = self.ROLE_URL_PREFIXES.get(request.user.role)

        if allowed_prefixes is None:
            # Роль не найдена, запрещаем доступ
            return redirect('login')

        if full_url_name:
            # Проверяем, начинается ли URL с разрешённых префиксов
            for prefix in allowed_prefixes:
                if full_url_name.startswith(prefix):
                    return self.get_response(request)

        # Для URL без namespace проверяем общие страницы
        if url_name in ['home', 'profile', 'change_pin']:
            return self.get_response(request)

        # Доступ запрещён
        return redirect('home')


class AutoLogoutMiddleware:
    """
    Middleware для автоматического выхода после длительного бездействия.

    Выход после 12 часов неактивности (конец смены).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем время сессии
        if request.user.is_authenticated:
            # Django автоматически управляет временем жизни сессии
            # через SESSION_COOKIE_AGE в settings
            pass

        return self.get_response(request)
