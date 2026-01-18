"""
Формы для создания и управления бланками ПА.

FR-007: Автоматическая генерация бланков
FR-010: Шаблоны бланков
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from shift_report.models import (PABlank, PATemplate, Product, Sector, Shift,
                                 Workplace)
from shift_report.models.pa_blank import PABlankType


class BlankCreateForm(forms.Form):
    """
    Форма создания нового бланка ПА.
    """

    workplace = forms.ModelChoiceField(
        label='Рабочее место',
        queryset=Workplace.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
        }),
        empty_label='Выберите рабочее место...',
    )

    date = forms.DateField(
        label='Дата',
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg',
            'type': 'date',
        }),
        initial=timezone.localdate,
    )

    shift = forms.ModelChoiceField(
        label='Смена',
        queryset=Shift.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
        }),
        empty_label='Выберите смену...',
    )

    product = forms.ModelChoiceField(
        label='Продукция',
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
        }),
        empty_label='Выберите продукцию...',
    )

    planned_quantity = forms.IntegerField(
        label='Плановое количество на смену',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Введите план...',
        }),
    )

    blank_type = forms.ChoiceField(
        label='Тип бланка',
        choices=[('auto', 'Определить автоматически')] + list(PABlankType.choices),
        initial='auto',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
        }),
    )

    notes = forms.CharField(
        label='Примечания',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Дополнительная информация...',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Фильтруем рабочие места по доступу пользователя
        if user.sector:
            self.fields['workplace'].queryset = Workplace.objects.filter(
                sector=user.sector,
                is_active=True,
            )
        elif user.workshop:
            self.fields['workplace'].queryset = Workplace.objects.filter(
                sector__workshop=user.workshop,
                is_active=True,
            )

    def clean(self):
        cleaned_data = super().clean()
        workplace = cleaned_data.get('workplace')
        date = cleaned_data.get('date')
        shift = cleaned_data.get('shift')

        if workplace and date and shift:
            # Проверяем уникальность
            if PABlank.objects.filter(
                workplace=workplace,
                date=date,
                shift=shift,
            ).exists():
                raise ValidationError(
                    'Бланк для этого рабочего места, даты и смены уже существует.'
                )

        return cleaned_data


class BlankBulkCreateForm(forms.Form):
    """
    Форма массового создания бланков.
    """

    sector = forms.ModelChoiceField(
        label='Участок',
        queryset=Sector.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
        }),
        empty_label='Выберите участок...',
    )

    date_from = forms.DateField(
        label='Дата с',
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg',
            'type': 'date',
        }),
        initial=timezone.localdate,
    )

    date_to = forms.DateField(
        label='Дата по',
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg',
            'type': 'date',
        }),
        initial=timezone.localdate,
    )

    shifts = forms.ModelMultipleChoiceField(
        label='Смены',
        queryset=Shift.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        }),
    )

    use_templates = forms.BooleanField(
        label='Использовать шаблоны',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text='Если включено, бланки будут созданы на основе активных шаблонов',
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Фильтруем участки по доступу
        if user.sector:
            self.fields['sector'].queryset = Sector.objects.filter(
                pk=user.sector.pk,
                is_active=True,
            )
            self.fields['sector'].initial = user.sector
        elif user.workshop:
            self.fields['sector'].queryset = Sector.objects.filter(
                workshop=user.workshop,
                is_active=True,
            )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError('Дата "с" не может быть позже даты "по".')

            # Ограничиваем период
            delta = (date_to - date_from).days
            if delta > 30:
                raise ValidationError('Максимальный период — 30 дней.')

        return cleaned_data


class TemplateCreateForm(forms.ModelForm):
    """
    Форма создания шаблона бланка.
    """

    class Meta:
        model = PATemplate
        fields = [
            'name',
            'workplace',
            'product',
            'shift',
            'blank_type',
            'planned_quantity',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Название шаблона...',
            }),
            'workplace': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'product': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'shift': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'blank_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'planned_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
            }),
            'monday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tuesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wednesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'thursday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'friday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Фильтруем по доступу
        if user.sector:
            self.fields['workplace'].queryset = Workplace.objects.filter(
                sector=user.sector,
                is_active=True,
            )
        elif user.workshop:
            self.fields['workplace'].queryset = Workplace.objects.filter(
                sector__workshop=user.workshop,
                is_active=True,
            )


class BlankEditForm(forms.ModelForm):
    """
    Форма редактирования бланка.
    """

    class Meta:
        model = PABlank
        fields = ['planned_quantity', 'status', 'notes']
        widgets = {
            'planned_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }
