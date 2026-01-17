"""
Формы аутентификации.

FR-014: Упрощённая авторизация оператора
"""

from django import forms
from django.core.exceptions import ValidationError


class PINLoginForm(forms.Form):
    """
    Форма входа по табельному номеру и PIN-коду.

    Большие поля и кнопки для удобства работы на планшете.
    """

    personnel_number = forms.CharField(
        label='Табельный номер',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Введите табельный номер',
            'autofocus': True,
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'username',
        })
    )

    pin = forms.CharField(
        label='PIN-код',
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '••••',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'current-password',
        })
    )

    remember_me = forms.BooleanField(
        label='Запомнить меня на этом устройстве',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def clean_personnel_number(self):
        """Валидация табельного номера"""
        personnel_number = self.cleaned_data.get('personnel_number', '').strip()

        if not personnel_number:
            raise ValidationError('Введите табельный номер')

        if not personnel_number.isdigit():
            raise ValidationError('Табельный номер должен содержать только цифры')

        return personnel_number

    def clean_pin(self):
        """Валидация PIN-кода"""
        pin = self.cleaned_data.get('pin', '').strip()

        if not pin:
            raise ValidationError('Введите PIN-код')

        if not pin.isdigit():
            raise ValidationError('PIN-код должен содержать только цифры')

        if len(pin) < 4 or len(pin) > 6:
            raise ValidationError('PIN-код должен содержать от 4 до 6 цифр')

        return pin


class PINChangeForm(forms.Form):
    """
    Форма смены PIN-кода.
    """

    current_pin = forms.CharField(
        label='Текущий PIN-код',
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '••••',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
        })
    )

    new_pin = forms.CharField(
        label='Новый PIN-код',
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '••••',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
        })
    )

    confirm_pin = forms.CharField(
        label='Подтвердите новый PIN-код',
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '••••',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_pin(self):
        """Проверка текущего PIN-кода"""
        current_pin = self.cleaned_data.get('current_pin', '').strip()

        if not self.user.check_pin(current_pin):
            raise ValidationError('Неверный текущий PIN-код')

        return current_pin

    def clean_new_pin(self):
        """Валидация нового PIN-кода"""
        new_pin = self.cleaned_data.get('new_pin', '').strip()

        if not new_pin.isdigit():
            raise ValidationError('PIN-код должен содержать только цифры')

        if len(new_pin) < 4 or len(new_pin) > 6:
            raise ValidationError('PIN-код должен содержать от 4 до 6 цифр')

        return new_pin

    def clean(self):
        """Проверка совпадения нового PIN-кода"""
        cleaned_data = super().clean()
        new_pin = cleaned_data.get('new_pin')
        confirm_pin = cleaned_data.get('confirm_pin')

        if new_pin and confirm_pin and new_pin != confirm_pin:
            raise ValidationError('PIN-коды не совпадают')

        return cleaned_data

    def save(self):
        """Сохранение нового PIN-кода"""
        self.user.set_pin(self.cleaned_data['new_pin'])
        self.user.save(update_fields=['pin_hash'])
        return self.user
