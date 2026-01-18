"""
Views для создания и управления бланками ПА.

FR-007: Автоматическая генерация бланков
FR-008: Выбор типа бланка
FR-010: Шаблоны бланков
"""

from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from shift_report.decorators import MasterRequiredMixin
from shift_report.forms import (BlankBulkCreateForm, BlankCreateForm,
                                BlankEditForm, TemplateCreateForm)
from shift_report.models import PABlank, PATemplate, Product, Shift, Workplace
from shift_report.services import BlankGeneratorService


class BlankListView(MasterRequiredMixin, View):
    """
    Список бланков ПА.
    """

    template_name = 'shift_report/blanks/list.html'

    def get(self, request):
        user = request.user

        # Фильтры
        date_str = request.GET.get('date')
        if date_str:
            try:
                from datetime import datetime
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = timezone.localdate()
        else:
            selected_date = timezone.localdate()

        status = request.GET.get('status', '')
        workplace_id = request.GET.get('workplace', '')

        # Базовый queryset
        blanks = PABlank.objects.select_related(
            'workplace',
            'workplace__sector',
            'product',
            'shift',
            'created_by',
        ).order_by('-date', 'shift__number', 'workplace__number')

        # Фильтр по доступу
        if user.sector:
            blanks = blanks.filter(workplace__sector=user.sector)
        elif user.workshop:
            blanks = blanks.filter(workplace__sector__workshop=user.workshop)

        # Фильтр по дате
        blanks = blanks.filter(date=selected_date)

        # Фильтр по статусу
        if status:
            blanks = blanks.filter(status=status)

        # Фильтр по РМ
        if workplace_id:
            blanks = blanks.filter(workplace_id=workplace_id)

        # Рабочие места для фильтра
        workplaces = Workplace.objects.filter(is_active=True)
        if user.sector:
            workplaces = workplaces.filter(sector=user.sector)
        elif user.workshop:
            workplaces = workplaces.filter(sector__workshop=user.workshop)

        # Статистика
        stats = {
            'total': blanks.count(),
            'draft': blanks.filter(status='draft').count(),
            'active': blanks.filter(status='active').count(),
            'completed': blanks.filter(status='completed').count(),
        }

        return render(request, self.template_name, {
            'blanks': blanks,
            'selected_date': selected_date,
            'selected_status': status,
            'selected_workplace': workplace_id,
            'workplaces': workplaces,
            'stats': stats,
        })


class BlankCreateView(MasterRequiredMixin, View):
    """
    Создание нового бланка ПА.
    """

    template_name = 'shift_report/blanks/create.html'

    def get(self, request):
        form = BlankCreateForm(user=request.user)

        # Получаем данные для подсказок
        products = Product.objects.filter(is_active=True).values('id', 'name', 'article', 'takt_time')
        shifts = [
            {
                'id': s.id,
                'name': s.name,
                'working_time_minutes': s.working_time_minutes
            }
            for s in Shift.objects.filter(is_active=True)
        ]

        return render(request, self.template_name, {
            'form': form,
            'products_data': list(products),
            'shifts_data': list(shifts),
        })

    def post(self, request):
        form = BlankCreateForm(user=request.user, data=request.POST)

        if form.is_valid():
            service = BlankGeneratorService()

            blank_type = form.cleaned_data['blank_type']
            if blank_type == 'auto':
                blank_type = None

            try:
                blank = service.create_blank(
                    workplace=form.cleaned_data['workplace'],
                    date=form.cleaned_data['date'],
                    shift=form.cleaned_data['shift'],
                    product=form.cleaned_data['product'],
                    planned_quantity=form.cleaned_data['planned_quantity'],
                    blank_type=blank_type,
                    notes=form.cleaned_data.get('notes', ''),
                    created_by=request.user,
                )

                messages.success(
                    request,
                    f'Бланк успешно создан: {blank.workplace.name} на {blank.date}'
                )
                return redirect('blanks:detail', blank_id=blank.pk)

            except ValueError as e:
                messages.error(request, str(e))

        return render(request, self.template_name, {
            'form': form,
        })


class BlankBulkCreateView(MasterRequiredMixin, View):
    """
    Массовое создание бланков.
    """

    template_name = 'shift_report/blanks/bulk_create.html'

    def get(self, request):
        form = BlankBulkCreateForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BlankBulkCreateForm(user=request.user, data=request.POST)

        if form.is_valid():
            sector = form.cleaned_data['sector']
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            shifts = form.cleaned_data['shifts']
            use_templates = form.cleaned_data['use_templates']

            service = BlankGeneratorService()  # noqa: F841
            created_count = 0
            skipped_count = 0
            errors = []

            # Получаем рабочие места участка
            workplaces = Workplace.objects.filter(
                sector=sector,
                is_active=True,
            )

            # Получаем шаблоны
            templates = {}
            if use_templates:
                for template in PATemplate.objects.filter(
                    workplace__sector=sector,
                    is_active=True,
                ).select_related('workplace', 'product', 'shift'):
                    key = (template.workplace_id, template.shift_id)
                    templates[key] = template

            # Создаём бланки
            current_date = date_from
            while current_date <= date_to:
                weekday = current_date.weekday()

                for shift in shifts:
                    for workplace in workplaces:
                        # Проверяем, есть ли уже бланк
                        if PABlank.objects.filter(
                            workplace=workplace,
                            date=current_date,
                            shift=shift,
                        ).exists():
                            skipped_count += 1
                            continue

                        # Ищем шаблон
                        template = templates.get((workplace.pk, shift.pk))

                        if template:
                            # Проверяем день недели
                            if not template.is_applicable_for_weekday(weekday):
                                continue

                            try:
                                blank = template.create_blank(  # noqa: F841
                                    date=current_date,
                                    shift=shift,
                                    created_by=request.user,
                                )
                                created_count += 1
                            except Exception as e:
                                errors.append(f'{workplace.name}: {str(e)}')

                        elif not use_templates:
                            # Без шаблонов нужно указать продукцию и план
                            # Пропускаем
                            pass

                current_date += timedelta(days=1)

            # Результат
            if created_count > 0:
                messages.success(
                    request,
                    f'Создано бланков: {created_count}'
                )
            if skipped_count > 0:
                messages.info(
                    request,
                    f'Пропущено (уже существуют): {skipped_count}'
                )
            if errors:
                messages.warning(
                    request,
                    f'Ошибки: {len(errors)}. {"; ".join(errors[:3])}'
                )

            return redirect('blanks:list')

        return render(request, self.template_name, {'form': form})


class BlankDetailView(MasterRequiredMixin, View):
    """
    Детальный просмотр и редактирование бланка.
    """

    template_name = 'shift_report/blanks/detail.html'

    def get(self, request, blank_id):
        blank = get_object_or_404(
            PABlank.objects.select_related(
                'workplace',
                'workplace__sector',
                'workplace__sector__workshop',
                'product',
                'shift',
                'created_by',
            ),
            pk=blank_id
        )

        # Проверяем доступ
        if not self._can_access(request.user, blank):
            messages.error(request, 'У вас нет доступа к этому бланку')
            return redirect('blanks:list')

        records = blank.records.select_related(
            'filled_by'
        ).prefetch_related(
            'deviations',
            'deviations__reason',
        ).order_by('hour_number')

        form = BlankEditForm(instance=blank)

        return render(request, self.template_name, {
            'blank': blank,
            'records': records,
            'form': form,
        })

    def post(self, request, blank_id):
        blank = get_object_or_404(PABlank, pk=blank_id)

        if not self._can_access(request.user, blank):
            messages.error(request, 'У вас нет доступа к этому бланку')
            return redirect('blanks:list')

        form = BlankEditForm(instance=blank, data=request.POST)

        if form.is_valid():
            with transaction.atomic():
                old_quantity = blank.planned_quantity
                blank = form.save()

                # Пересчитываем записи при изменении плана
                if blank.planned_quantity != old_quantity:
                    service = BlankGeneratorService()
                    service.recalculate_blank(blank)

            messages.success(request, 'Бланк обновлён')
            return redirect('blanks:detail', blank_id=blank.pk)

        records = blank.records.all().order_by('hour_number')

        return render(request, self.template_name, {
            'blank': blank,
            'records': records,
            'form': form,
        })

    def _can_access(self, user, blank):
        if user.is_admin or user.is_superuser:
            return True
        if user.is_chief:
            return blank.workplace.sector.workshop == user.workshop
        if user.is_master:
            return blank.workplace.sector == user.sector
        return False


class BlankDeleteView(MasterRequiredMixin, View):
    """
    Удаление бланка.
    """

    def post(self, request, blank_id):
        blank = get_object_or_404(PABlank, pk=blank_id)

        # Проверяем возможность удаления
        if blank.status == 'completed':
            messages.error(request, 'Нельзя удалить завершённый бланк')
            return redirect('blanks:detail', blank_id=blank_id)

        if blank.records.filter(is_filled=True).exists():
            messages.error(request, 'Нельзя удалить бланк с заполненными записями')
            return redirect('blanks:detail', blank_id=blank_id)

        blank_info = f'{blank.workplace.name} на {blank.date}'
        blank.delete()

        messages.success(request, f'Бланк удалён: {blank_info}')
        return redirect('blanks:list')


class TemplateListView(MasterRequiredMixin, View):
    """
    Список шаблонов бланков.
    """

    template_name = 'shift_report/blanks/templates_list.html'

    def get(self, request):
        user = request.user

        templates = PATemplate.objects.select_related(
            'workplace',
            'workplace__sector',
            'product',
            'shift',
            'created_by',
        ).order_by('workplace__sector__number', 'workplace__number', 'shift__number')

        # Фильтр по доступу
        if user.sector:
            templates = templates.filter(workplace__sector=user.sector)
        elif user.workshop:
            templates = templates.filter(workplace__sector__workshop=user.workshop)

        return render(request, self.template_name, {
            'templates': templates,
        })


class TemplateCreateView(MasterRequiredMixin, View):
    """
    Создание шаблона бланка.
    """

    template_name = 'shift_report/blanks/template_create.html'

    def get(self, request):
        form = TemplateCreateForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = TemplateCreateForm(user=request.user, data=request.POST)

        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            messages.success(request, f'Шаблон "{template.name}" создан')
            return redirect('blanks:templates')

        return render(request, self.template_name, {'form': form})


class TemplateEditView(MasterRequiredMixin, View):
    """
    Редактирование шаблона.
    """

    template_name = 'shift_report/blanks/template_edit.html'

    def get(self, request, template_id):
        template = get_object_or_404(PATemplate, pk=template_id)
        form = TemplateCreateForm(user=request.user, instance=template)
        return render(request, self.template_name, {
            'form': form,
            'template': template,
        })

    def post(self, request, template_id):
        template = get_object_or_404(PATemplate, pk=template_id)
        form = TemplateCreateForm(user=request.user, instance=template, data=request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, f'Шаблон "{template.name}" обновлён')
            return redirect('blanks:templates')

        return render(request, self.template_name, {
            'form': form,
            'template': template,
        })


class TemplateDeleteView(MasterRequiredMixin, View):
    """
    Удаление шаблона.
    """

    def post(self, request, template_id):
        template = get_object_or_404(PATemplate, pk=template_id)
        name = template.name
        template.delete()

        messages.success(request, f'Шаблон "{name}" удалён')
        return redirect('blanks:templates')


class WorkplaceAPIView(MasterRequiredMixin, View):
    """
    API для получения информации о рабочем месте.
    """

    def get(self, request, workplace_id):
        workplace = get_object_or_404(Workplace, pk=workplace_id)

        return JsonResponse({
            'id': workplace.pk,
            'name': workplace.name,
            'passport_capacity': workplace.passport_capacity,
            'achieved_capacity': workplace.achieved_capacity,
            'sector': workplace.sector.name,
        })


class CalculatePlanAPIView(MasterRequiredMixin, View):
    """
    API для расчёта планового количества.
    """

    def get(self, request):
        product_id = request.GET.get('product_id')
        shift_id = request.GET.get('shift_id')
        workplace_id = request.GET.get('workplace_id')

        if not all([product_id, shift_id]):
            return JsonResponse({'error': 'Не указаны обязательные параметры'}, status=400)

        try:
            product = Product.objects.get(pk=product_id)
            shift = Shift.objects.get(pk=shift_id)
        except (Product.DoesNotExist, Shift.DoesNotExist):
            return JsonResponse({'error': 'Продукция или смена не найдена'}, status=404)

        # Расчёт по времени такта
        if product.takt_time and product.takt_time > 0:
            working_seconds = shift.working_time_minutes * 60
            calculated_quantity = working_seconds // product.takt_time
        else:
            calculated_quantity = 0

        # Расчёт по мощности РМ
        workplace_capacity = None
        if workplace_id:
            try:
                workplace = Workplace.objects.get(pk=workplace_id)
                if workplace.passport_capacity:
                    workplace_hours = shift.working_time_minutes / 60
                    workplace_capacity = int(workplace.passport_capacity * workplace_hours)
            except Workplace.DoesNotExist:
                pass

        return JsonResponse({
            'calculated_by_takt': calculated_quantity,
            'calculated_by_capacity': workplace_capacity,
            'takt_time': product.takt_time,
            'working_minutes': shift.working_time_minutes,
        })
