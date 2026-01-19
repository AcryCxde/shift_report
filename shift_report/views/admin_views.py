"""
Views для администрирования системы.

FR-030: Импорт справочников
FR-031: Экспорт данных
FR-032: Управление справочниками
"""

from datetime import timedelta

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from shift_report.decorators import AdminRequiredMixin
from shift_report.models import (DeviationGroup, DeviationReason, Employee,
                                 Product, Sector, Shift, Workplace, Workshop)
from shift_report.services.import_export import ImportExportService


class AdminDashboardView(AdminRequiredMixin, View):
    """
    Главная панель администрирования.
    """

    template_name = 'shift_report/admin/dashboard.html'

    def get(self, request):
        # Статистика по справочникам
        stats = {
            'workshops': Workshop.objects.count(),
            'sectors': Sector.objects.count(),
            'workplaces': Workplace.objects.count(),
            'products': Product.objects.count(),
            'shifts': Shift.objects.count(),
            'deviation_groups': DeviationGroup.objects.count(),
            'deviation_reasons': DeviationReason.objects.count(),
            'employees': Employee.objects.count(),
            'employees_active': Employee.objects.filter(is_active=True).count(),
        }

        return render(request, self.template_name, {
            'stats': stats,
        })


class ImportView(AdminRequiredMixin, View):
    """
    Импорт данных из CSV.
    """

    template_name = 'shift_report/admin/import.html'

    IMPORT_MODELS = [
        ('workshops', 'Цеха'),
        ('sectors', 'Участки'),
        ('workplaces', 'Рабочие места'),
        ('products', 'Продукция'),
        ('shifts', 'Смены'),
        ('deviation_groups', 'Группы причин'),
        ('deviation_reasons', 'Причины отклонений'),
        ('employees', 'Сотрудники'),
    ]

    def get(self, request):
        return render(request, self.template_name, {
            'import_models': self.IMPORT_MODELS,
        })

    def post(self, request):
        model_name = request.POST.get('model_name')
        csv_file = request.FILES.get('csv_file')
        update_existing = request.POST.get('update_existing') == 'on'

        if not model_name or not csv_file:
            messages.error(request, 'Выберите тип данных и файл')
            return redirect('shift_admin:import')

        try:
            content = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                csv_file.seek(0)
                content = csv_file.read().decode('cp1251')
            except Exception:
                messages.error(request, 'Не удалось прочитать файл. Проверьте кодировку (UTF-8 или Windows-1251)')
                return redirect('shift_admin:import')

        service = ImportExportService()
        result = service.import_from_csv(model_name, content, update_existing)

        if result['created'] or result['updated']:
            messages.success(
                request,
                f'Импорт завершён. Создано: {result["created"]}, обновлено: {result["updated"]}'
            )

        if result['errors']:
            for error in result['errors'][:5]:
                messages.warning(request, error)
            if len(result['errors']) > 5:
                messages.warning(request, f'... и ещё {len(result["errors"]) - 5} ошибок')

        return redirect('shift_admin:import')


class ExportView(AdminRequiredMixin, View):
    """
    Экспорт данных в CSV.
    """

    template_name = 'shift_report/admin/export.html'

    EXPORT_MODELS = [
        ('workshops', 'Цеха'),
        ('sectors', 'Участки'),
        ('workplaces', 'Рабочие места'),
        ('products', 'Продукция'),
        ('shifts', 'Смены'),
        ('deviation_groups', 'Группы причин'),
        ('deviation_reasons', 'Причины отклонений'),
        ('employees', 'Сотрудники'),
    ]

    def get(self, request):
        return render(request, self.template_name, {
            'export_models': self.EXPORT_MODELS,
            'today': timezone.localdate(),
        })

    def post(self, request):
        export_type = request.POST.get('export_type')

        service = ImportExportService()

        if export_type in dict(self.EXPORT_MODELS):
            # Экспорт справочника
            content = service.export_to_csv(export_type)
            filename = f'{export_type}_{timezone.localdate().isoformat()}.csv'

        elif export_type == 'blanks_report':
            # Экспорт отчёта по бланкам
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')

            if date_from and date_to:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            else:
                date_to = timezone.localdate()
                date_from = date_to - timedelta(days=30)

            content = service.export_blanks_report(date_from, date_to)
            filename = f'blanks_report_{date_from.isoformat()}_{date_to.isoformat()}.csv'

        elif export_type == 'deviations_report':
            # Экспорт отчёта по отклонениям
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')

            if date_from and date_to:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            else:
                date_to = timezone.localdate()
                date_from = date_to - timedelta(days=30)

            content = service.export_deviations_report(date_from, date_to)
            filename = f'deviations_report_{date_from.isoformat()}_{date_to.isoformat()}.csv'

        else:
            messages.error(request, 'Неизвестный тип экспорта')
            return redirect('shift_admin:export')

        response = HttpResponse(content, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # BOM для корректного открытия в Excel
        response.write('\ufeff')
        response.write(content)

        return response


class DirectoryListView(AdminRequiredMixin, View):
    """
    Просмотр справочников.
    """

    template_name = 'shift_report/admin/directory_list.html'

    def get(self, request, directory_type):
        data = []
        title = ''

        if directory_type == 'workshops':
            title = 'Цеха'
            data = Workshop.objects.all().order_by('number')
        elif directory_type == 'sectors':
            title = 'Участки'
            data = Sector.objects.select_related('workshop').order_by('workshop__number', 'number')
        elif directory_type == 'workplaces':
            title = 'Рабочие места'
            data = Workplace.objects.select_related('sector', 'sector__workshop').order_by(
                'sector__workshop__number', 'sector__number', 'number'
            )
        elif directory_type == 'products':
            title = 'Продукция'
            data = Product.objects.all().order_by('article')
        elif directory_type == 'shifts':
            title = 'Смены'
            data = Shift.objects.all().order_by('number')
        elif directory_type == 'deviation_groups':
            title = 'Группы причин отклонений'
            data = DeviationGroup.objects.all().order_by('order')
        elif directory_type == 'deviation_reasons':
            title = 'Причины отклонений'
            data = DeviationReason.objects.select_related('group').order_by('group__order', 'code')
        elif directory_type == 'employees':
            title = 'Сотрудники'
            data = Employee.objects.select_related(
                'workshop', 'sector', 'workplace'
            ).order_by('personnel_number')
        else:
            messages.error(request, 'Неизвестный справочник')
            return redirect('shift_admin:dashboard')

        return render(request, self.template_name, {
            'directory_type': directory_type,
            'title': title,
            'data': data,
        })


class TemplateDownloadView(AdminRequiredMixin, View):
    """
    Скачивание шаблонов CSV для импорта.
    """

    TEMPLATES = {
        'workshops': 'number,name,description,is_active\n1,Цех №1,Описание цеха,true',
        'sectors': 'number,name,workshop_number,description,is_active\n1,Участок №1,1,Описание участка,true',
        'workplaces': 'number,name,sector_number,workshop_number,equipment_type,passport_capacity,achieved_capacity,'
                      'description,is_active\n1,Рабочее место №1,1,1,Станок,10.0,9.5,Описание,true',
        'products': 'article,name,takt_time,is_active\nPROD001,Изделие №1,120,true',
        'shifts': 'number,name,start_time,end_time,break_minutes,is_active\n1,Первая смена,08:00,20:00,60,true',
        'deviation_groups': 'code,name,color,order\nORG,Организационные,#ffc107,1',
        'deviation_reasons': 'code,name,group_code,is_active\nORG-01,Отсутствие материала,ORG,true',
        'employees': 'personnel_number,first_name,last_name,middle_name,role,workshop_number,sector_number,'
                     'workplace_number,pin,is_active\n100001,Иван,Иванов,Иванович,operator,1,1,1,1234,true',
    }

    def get(self, request, template_name):
        if template_name not in self.TEMPLATES:
            messages.error(request, 'Шаблон не найден')
            return redirect('shift_admin:import')

        content = self.TEMPLATES[template_name]
        response = HttpResponse(content, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="template_{template_name}.csv"'

        return response
