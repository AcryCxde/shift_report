"""
Views для панели мониторинга мастера.

FR-019: Панель мониторинга для мастеров
FR-020: Карточки рабочих мест с real-time статусом
FR-021: Детализация по часам
FR-025: Фиксация принятых мер
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from shift_report.decorators import MasterRequiredMixin
from shift_report.models import (DeviationEntry, PABlank, Sector, TakenMeasure,
                                 Workplace)


class MasterMonitoringView(MasterRequiredMixin, View):
    """
    Главная панель мониторинга мастера.

    Отображает карточки всех рабочих мест участка с текущим статусом.
    FR-019, FR-020
    """

    template_name = 'shift_report/master/monitoring.html'

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Определяем участок для мониторинга
        if user.sector:
            sector = user.sector
        elif user.workshop:
            # Начальник цеха видит все участки
            sectors = Sector.objects.filter(
                workshop=user.workshop,
                is_active=True
            )
            sector = None
        else:
            sector = None
            sectors = Sector.objects.none()

        # Получаем бланки на сегодня
        blanks_qs = PABlank.objects.filter(
            date=today,
            status__in=['draft', 'active'],
        ).select_related(
            'workplace',
            'workplace__sector',
            'product',
            'shift',
        ).prefetch_related(
            'records',
        )

        if sector:
            blanks_qs = blanks_qs.filter(workplace__sector=sector)
            sectors = [sector]  # noqa: F841
        elif user.workshop:
            blanks_qs = blanks_qs.filter(workplace__sector__workshop=user.workshop)

        blanks = blanks_qs.order_by('workplace__sector__number', 'workplace__number')

        # Группируем по участкам
        sectors_data = {}
        total_plan = 0
        total_fact = 0
        total_deviation = 0

        for blank in blanks:
            sector_id = blank.workplace.sector_id
            if sector_id not in sectors_data:
                sectors_data[sector_id] = {
                    'sector': blank.workplace.sector,
                    'blanks': [],
                    'total_plan': 0,
                    'total_fact': 0,
                    'total_deviation': 0,
                }
            sectors_data[sector_id]['blanks'].append(blank)
            sectors_data[sector_id]['total_plan'] += blank.total_plan or 0
            sectors_data[sector_id]['total_fact'] += blank.total_fact or 0
            sectors_data[sector_id]['total_deviation'] += blank.total_deviation or 0

            # Суммируем общие итоги
            total_plan += blank.total_plan or 0
            total_fact += blank.total_fact or 0
            total_deviation += blank.total_deviation or 0

        # Рассчитываем процент выполнения для каждого участка
        for data in sectors_data.values():
            if data['total_plan'] > 0:
                data['completion'] = round(data['total_fact'] / data['total_plan'] * 100, 1)
            else:
                data['completion'] = 0

        # Статистика по отклонениям
        deviations_today = DeviationEntry.objects.filter(
            record__blank__date=today,
        )
        if sector:
            deviations_today = deviations_today.filter(
                record__blank__workplace__sector=sector
            )
        elif user.workshop:
            deviations_today = deviations_today.filter(
                record__blank__workplace__sector__workshop=user.workshop
            )

        deviations_stats = deviations_today.values(
            'reason__group__name',
            'reason__group__color',
        ).annotate(
            count=Count('id'),
            total_duration=Sum('duration_minutes'),
        ).order_by('-count')[:5]

        return render(request, self.template_name, {
            'sectors_data': sectors_data,
            'total_plan': total_plan,
            'total_fact': total_fact,
            'total_deviation': total_deviation,
            'today': today,
            'deviations_stats': deviations_stats,
            'current_sector': sector,
        })


class WorkplaceDetailView(MasterRequiredMixin, View):
    """
    Детальный просмотр рабочего места.

    Показывает все бланки РМ за выбранную дату с почасовой детализацией.
    FR-021
    """

    template_name = 'shift_report/master/workplace_detail.html'

    def get(self, request, workplace_id):
        workplace = get_object_or_404(
            Workplace.objects.select_related('sector', 'sector__workshop'),
            pk=workplace_id
        )

        # Проверяем доступ
        if not self._can_access_workplace(request.user, workplace):
            messages.error(request, 'У вас нет доступа к этому рабочему месту')
            return redirect('master:monitoring')

        date_str = request.GET.get('date')
        if date_str:
            try:
                from datetime import datetime
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = timezone.localdate()
        else:
            selected_date = timezone.localdate()

        # Получаем бланки за выбранную дату
        blanks = PABlank.objects.filter(
            workplace=workplace,
            date=selected_date,
        ).select_related(
            'product',
            'shift',
            'created_by',
        ).prefetch_related(
            'records',
            'records__deviations',
            'records__deviations__reason',
            'records__deviations__reason__group',
            'records__deviations__measures',
        ).order_by('shift__number')

        # Определяем текущий час
        now = timezone.localtime()
        current_hour = now.hour

        return render(request, self.template_name, {
            'workplace': workplace,
            'blanks': blanks,
            'selected_date': selected_date,
            'current_hour': current_hour,
        })

    def _can_access_workplace(self, user, workplace):
        """Проверка доступа к рабочему месту"""
        if user.is_admin or user.is_superuser:
            return True
        if user.is_chief:
            return workplace.sector.workshop == user.workshop
        if user.is_master:
            return workplace.sector == user.sector
        return False


class BlankMonitorView(MasterRequiredMixin, View):
    """
    Мониторинг конкретного бланка.

    Детальная информация о бланке с возможностью фиксации мер.
    """

    template_name = 'shift_report/master/blank_monitor.html'

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
        if not self._can_access_blank(request.user, blank):
            messages.error(request, 'У вас нет доступа к этому бланку')
            return redirect('master:monitoring')

        records = blank.records.select_related(
            'filled_by'
        ).prefetch_related(
            'deviations',
            'deviations__reason',
            'deviations__reason__group',
            'deviations__responsible',
            'deviations__measures',
            'deviations__measures__created_by',
        ).order_by('hour_number')

        # Текущий час
        now = timezone.localtime()
        current_hour = None
        for record in records:
            if record.start_time <= now.time() <= record.end_time:
                current_hour = record.hour_number
                break

        # Статистика отклонений
        deviations = DeviationEntry.objects.filter(
            record__blank=blank
        ).select_related(
            'reason',
            'reason__group',
        )

        deviations_by_group = {}
        for dev in deviations:
            group_name = dev.reason.group.name
            if group_name not in deviations_by_group:
                deviations_by_group[group_name] = {
                    'color': dev.reason.group.color,
                    'count': 0,
                    'duration': 0,
                }
            deviations_by_group[group_name]['count'] += 1
            deviations_by_group[group_name]['duration'] += dev.duration_minutes or 0

        return render(request, self.template_name, {
            'blank': blank,
            'records': records,
            'current_hour': current_hour,
            'deviations_by_group': deviations_by_group,
        })

    def _can_access_blank(self, user, blank):
        """Проверка доступа к бланку"""
        if user.is_admin or user.is_superuser:
            return True
        if user.is_chief:
            return blank.workplace.sector.workshop == user.workshop
        if user.is_master:
            return blank.workplace.sector == user.sector
        return False


class AddMeasureView(MasterRequiredMixin, View):
    """
    Добавление принятой меры к отклонению.

    FR-025: Фиксация принятых мер
    """

    template_name = 'shift_report/master/add_measure.html'

    def get(self, request, deviation_id):
        deviation = get_object_or_404(
            DeviationEntry.objects.select_related(
                'record',
                'record__blank',
                'record__blank__workplace',
                'reason',
                'reason__group',
            ),
            pk=deviation_id
        )

        # Проверяем доступ
        blank = deviation.record.blank
        if not self._can_access_blank(request.user, blank):
            messages.error(request, 'У вас нет доступа')
            return redirect('master:monitoring')

        # Существующие меры
        existing_measures = deviation.measures.select_related('created_by').all()

        # Типы мер
        from shift_report.models.taken_measure import MeasureType
        measure_types = MeasureType.choices

        return render(request, self.template_name, {
            'deviation': deviation,
            'existing_measures': existing_measures,
            'measure_types': measure_types,
        })

    def post(self, request, deviation_id):
        deviation = get_object_or_404(
            DeviationEntry.objects.select_related(
                'record',
                'record__blank',
            ),
            pk=deviation_id
        )

        blank = deviation.record.blank
        if not self._can_access_blank(request.user, blank):
            messages.error(request, 'У вас нет доступа')
            return redirect('master:monitoring')

        measure_type = request.POST.get('measure_type')
        description = request.POST.get('description', '').strip()
        is_resolved = request.POST.get('is_resolved') == 'on'

        if not measure_type or not description:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('master:add_measure', deviation_id=deviation_id)

        with transaction.atomic():
            measure = TakenMeasure.objects.create(  # noqa: F841
                deviation_entry=deviation,
                measure_type=measure_type,
                description=description,
                resolved_at=timezone.now() if is_resolved else None,
                created_by=request.user,
            )

        messages.success(request, 'Мера добавлена')
        return redirect('master:blank_monitor', blank_id=blank.pk)

    def _can_access_blank(self, user, blank):
        if user.is_admin or user.is_superuser:
            return True
        if user.is_chief:
            return blank.workplace.sector.workshop == user.workshop
        if user.is_master:
            return blank.workplace.sector == user.sector
        return False


class MonitoringAPIView(MasterRequiredMixin, View):
    """
    API для обновления данных мониторинга в реальном времени.

    Возвращает JSON с текущим состоянием бланков.
    """

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Фильтруем бланки по доступу пользователя
        blanks_qs = PABlank.objects.filter(
            date=today,
            status__in=['draft', 'active'],
        ).select_related(
            'workplace',
            'product',
        )

        if user.sector:
            blanks_qs = blanks_qs.filter(workplace__sector=user.sector)
        elif user.workshop:
            blanks_qs = blanks_qs.filter(workplace__sector__workshop=user.workshop)

        data = []
        for blank in blanks_qs:
            data.append({
                'id': blank.pk,
                'workplace_id': blank.workplace_id,
                'workplace_name': blank.workplace.name,
                'product_name': blank.product.name,
                'total_plan': blank.total_plan,
                'total_fact': blank.total_fact,
                'total_deviation': blank.total_deviation,
                'completion': float(blank.current_completion_percentage),  # ИЗМЕНЕНО: используем current_completion_percentage
                'status': blank.status,
            })

        return JsonResponse({'blanks': data})


class BlankStatusAPIView(MasterRequiredMixin, View):
    """
    API для получения статуса конкретного бланка.
    """

    def get(self, request, blank_id):
        blank = get_object_or_404(PABlank, pk=blank_id)

        records_data = []
        for record in blank.records.all().order_by('hour_number'):
            records_data.append({
                'hour_number': record.hour_number,
                'planned_quantity': record.planned_quantity,
                'actual_quantity': record.actual_quantity,
                'deviation': record.deviation,
                'is_filled': record.is_filled,
                'cumulative_plan': record.cumulative_plan,
                'cumulative_fact': record.cumulative_fact,
                'cumulative_deviation': record.cumulative_deviation,
            })

        return JsonResponse({
            'blank': {
                'id': blank.pk,
                'total_plan': blank.total_plan,
                'total_fact': blank.total_fact,
                'total_deviation': blank.total_deviation,
                'completion': float(blank.current_completion_percentage),  # ИЗМЕНЕНО: используем current_completion_percentage
                'status': blank.status,
            },
            'records': records_data,
        })