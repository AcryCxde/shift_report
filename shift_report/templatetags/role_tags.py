"""
Template tags для проверки ролей пользователей.
"""

from django import template

register = template.Library()


@register.filter
def has_role(user, role):
    """
    Проверка роли пользователя.

    Использование:
        {% if user|has_role:"operator" %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    return user.role == role


@register.filter
def has_any_role(user, roles):
    """
    Проверка любой из ролей.

    Использование:
        {% if user|has_any_role:"operator,master" %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    role_list = [r.strip() for r in roles.split(',')]
    return user.role in role_list


@register.simple_tag
def user_can_access(user, *roles):
    """
    Проверка доступа пользователя.

    Использование:
        {% user_can_access user "operator" "master" as can_access %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_admin or user.is_superuser:
        return True

    return user.role in roles
