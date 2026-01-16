from django.contrib import admin

from shift_report.models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'personnel_number',
        'get_full_name',
        'role',
        'workplace',
        'sector',
        'workshop',
        'is_active',
    )
    list_filter = ('is_active', 'role', 'workshop', 'sector')
    search_fields = (
        'personnel_number',
        'first_name',
        'last_name',
        'middle_name',
    )
    ordering = ('last_name', 'first_name')

    fieldsets = (
        ('Идентификация', {
            'fields': ('personnel_number',)
        }),
        ('ФИО', {
            'fields': ('last_name', 'first_name', 'middle_name')
        }),
        ('Роль и подразделение', {
            'fields': ('role', 'workshop', 'sector', 'workplace'),
            'description': (
                'Операторы привязываются к рабочему месту, '
                'мастера — к участку, начальники — к цеху'
            )
        }),
        ('Статус', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('last_login', 'date_joined')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'personnel_number',
                'last_name',
                'first_name',
                'middle_name',
                'role',
                'workshop',
                'sector',
                'workplace',
            ),
        }),
        ('PIN-код', {
            'classes': ('wide',),
            'fields': ('pin',),
            'description': 'PIN-код для входа в систему (4-6 цифр)'
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Добавляем поле для ввода PIN при создании
        if obj is None and 'pin' not in form.base_fields:
            from django import forms
            form.base_fields['pin'] = forms.CharField(
                label='PIN-код',
                widget=forms.PasswordInput,
                required=True,
                help_text='4-6 цифр'
            )
        return form

    def save_model(self, request, obj, form, change):
        if not change and 'pin' in form.cleaned_data:
            obj.set_pin(form.cleaned_data['pin'])
        super().save_model(request, obj, form, change)

    @admin.display(description='ФИО')
    def get_full_name(self, obj):
        return obj.get_full_name()
