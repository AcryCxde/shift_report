"""
Views для интерфейса оператора.

FR-015: Интерфейс ввода данных оператором
FR-016: Выбор причины отклонения
FR-017: Подтверждение ввода данных
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from shift_report.decorators import OperatorRequiredMixin
from shift_report.models import (DeviationEntry, DeviationReason, PABlank,
                                 PARecord)


class OperatorDashboardView(OperatorRequiredMixin, View):
    """
    Главная страница оператора.

    Отображает активные бланки для рабочего места оператора.
    """

    template_name = 'shift_report/operator/dashboard.html'

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Получаем активные бланки для рабочего места оператора
        blanks = PABlank.objects.filter(
            status__in=['draft', 'active'],
            date=today,
        )

        # Фильтруем по рабочему месту оператора
        if user.workplace:
            blanks = blanks.filter(workplace=user.workplace)
        elif user.sector:
            blanks = blanks.filter(workplace__sector=user.sector)
        elif user.workshop:
            blanks = blanks.filter(workplace__sector__workshop=user.workshop)

        blanks = blanks.select_related(
            'workplace',
            'workplace__sector',
            'product',
            'shift',
        ).order_by('shift__number', 'workplace__number')

        return render(request, self.template_name, {
            'blanks': blanks,
            'today': today,
        })


class BlankDetailView(OperatorRequiredMixin, View):
    """
    Детальный просмотр бланка ПА.

    Отображает все записи бланка с возможностью ввода данных.
    """

    template_name = 'shift_report/operator/blank_detail.html'

    def get(self, request, blank_id):
        blank = get_object_or_404(
            PABlank.objects.select_related(
                'workplace',
                'workplace__sector',
                'workplace__sector__workshop',
                'product',
                'shift',
            ),
            pk=blank_id
        )

        # Проверяем доступ к бланку
        if not self._can_access_blank(request.user, blank):
            messages.error(request, 'У вас нет доступа к этому бланку')
            return redirect('operator:dashboard')

        records = blank.records.select_related(
            'filled_by'
        ).prefetch_related(
            'deviations',
            'deviations__reason',
            'deviations__reason__group',
        ).order_by('hour_number')

        # Определяем текущий час для подсветки
        now = timezone.localtime()
        current_hour = None

        for record in records:
            if record.start_time <= now.time() <= record.end_time:
                current_hour = record.hour_number
                break

        return render(request, self.template_name, {
            'blank': blank,
            'records': records,
            'current_hour': current_hour,
        })

    def _can_access_blank(self, user, blank):
        """Проверка доступа пользователя к бланку"""
        if user.is_admin or user.is_superuser:
            return True

        if user.is_chief:
            return blank.workplace.sector.workshop == user.workshop

        if user.is_master:
            return blank.workplace.sector == user.sector

        if user.is_operator:
            return blank.workplace == user.workplace

        return False


class RecordInputView(OperatorRequiredMixin, View):
    """
    Страница ввода фактических данных для записи.

    FR-015: Интерфейс ввода данных оператором
    FR-018: Удобство работы на планшете
    """

    template_name = 'shift_report/operator/record_input.html'

    def get(self, request, record_id):
        record = get_object_or_404(
            PARecord.objects.select_related(
                'blank',
                'blank__workplace',
                'blank__product',
                'blank__shift',
            ),
            pk=record_id
        )

        blank = record.blank

        # Проверяем, можно ли редактировать
        if not blank.is_editable:
            messages.warning(request, 'Бланк недоступен для редактирования')
            return redirect('operator:blank_detail', blank_id=blank.pk)

        # Получаем топ-5 частых причин + все причины
        top_reasons = DeviationReason.objects.filter(
            is_active=True
        ).order_by('-usage_count')[:5]

        all_reasons = DeviationReason.objects.filter(
            is_active=True
        ).select_related('group').order_by('group__order', 'order', 'name')

        # Существующие отклонения для этой записи
        existing_deviations = record.deviations.select_related(
            'reason', 'reason__group'
        ).all()

        return render(request, self.template_name, {
            'record': record,
            'blank': blank,
            'top_reasons': top_reasons,
            'all_reasons': all_reasons,
            'existing_deviations': existing_deviations,
        })

    def post(self, request, record_id):
        record = get_object_or_404(
            PARecord.objects.select_related('blank'),
            pk=record_id
        )

        blank = record.blank

        if not blank.is_editable:
            messages.warning(request, 'Бланк недоступен для редактирования')
            return redirect('operator:blank_detail', blank_id=blank.pk)

        try:
            actual_quantity = int(request.POST.get('actual_quantity', 0))
        except (ValueError, TypeError):
            actual_quantity = 0

        # Сохраняем данные
        with transaction.atomic():
            record.actual_quantity = actual_quantity
            record.is_filled = True
            record.filled_at = timezone.now()
            record.filled_by = request.user

            # Расчёт отклонения
            record.deviation = record.actual_quantity - record.planned_quantity

            record.save()

            # Обработка причин отклонения (если есть отклонение)
            if record.deviation < 0:
                self._process_deviations(request, record)

            # Пересчитываем накопительные показатели
            record.calculate_cumulative()

            # Пересчитываем итоги бланка
            blank.recalculate_totals()

        messages.success(
            request,
            f'Данные за {record.hour_number}-й час сохранены'
        )

        return redirect('operator:blank_detail', blank_id=blank.pk)

    def _process_deviations(self, request, record):
        """Обработка причин отклонения"""
        # Удаляем старые отклонения
        record.deviations.all().delete()

        reason_ids = request.POST.getlist('reason_ids', [])
        durations = request.POST.getlist('durations', [])
        comments = request.POST.getlist('comments', [])

        for i, reason_id in enumerate(reason_ids):
            if not reason_id:
                continue

            try:
                reason = DeviationReason.objects.get(pk=reason_id, is_active=True)
                duration = int(durations[i]) if i < len(durations) else 0
                comment = comments[i] if i < len(comments) else ''

                DeviationEntry.objects.create(
                    record=record,
                    reason=reason,
                    duration_minutes=duration,
                    comment=comment,
                    created_by=request.user,
                )
            except (DeviationReason.DoesNotExist, ValueError, IndexError):
                continue


class QuickInputView(OperatorRequiredMixin, View):
    """
    Быстрый ввод данных без отклонений.

    Для случаев, когда план выполнен или перевыполнен.
    """

    def post(self, request, record_id):
        record = get_object_or_404(
            PARecord.objects.select_related('blank'),
            pk=record_id
        )

        blank = record.blank

        if not blank.is_editable:
            return JsonResponse({
                'success': False,
                'error': 'Бланк недоступен для редактирования'
            })

        try:
            actual_quantity = int(request.POST.get('actual_quantity', 0))
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Некорректное значение'
            })

        with transaction.atomic():
            record.actual_quantity = actual_quantity
            record.is_filled = True
            record.filled_at = timezone.now()
            record.filled_by = request.user
            record.deviation = record.actual_quantity - record.planned_quantity
            record.save()

            record.calculate_cumulative()
            blank.recalculate_totals()

        return JsonResponse({
            'success': True,
            'actual_quantity': record.actual_quantity,
            'deviation': record.deviation,
            'cumulative_fact': record.cumulative_fact,
            'cumulative_deviation': record.cumulative_deviation,
            'blank_completion': float(blank.completion_percentage),
        })


class ReasonSearchView(OperatorRequiredMixin, View):
    """
    Поиск причин отклонения.

    API для автокомплита при выборе причины.
    """

    def get(self, request):
        query = request.GET.get('q', '').strip()

        reasons = DeviationReason.objects.filter(
            is_active=True
        ).select_related('group')

        if query:
            reasons = reasons.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(group__name__icontains=query)
            )

        reasons = reasons.order_by('-usage_count', 'name')[:20]

        data = [
            {
                'id': r.pk,
                'name': r.name,
                'code': r.code,
                'group': r.group.name,
                'group_color': r.group.color,
            }
            for r in reasons
        ]

        return JsonResponse({'reasons': data})
