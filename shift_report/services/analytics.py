"""
Сервис аналитики и отчётов.

FR-026: Дашборды и аналитика
FR-027: Анализ отклонений по категориям
FR-028: Сравнительный анализ
"""
from datetime import date
from typing import Any

from django.db.models import Avg, Count, Sum

from shift_report.models import (DeviationEntry, PABlank, PARecord, Sector,
                                 Workshop)


class AnalyticsService:
    """
    Сервис для расчёта аналитических показателей.
    """

    def get_dashboard_summary(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> dict[str, Any]:
        """
        Сводная статистика для дашборда.
        """
        blanks = PABlank.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        )

        if sector:
            blanks = blanks.filter(workplace__sector=sector)
        elif workshop:
            blanks = blanks.filter(workplace__sector__workshop=workshop)

        # Агрегируем данные
        totals = blanks.aggregate(
            total_plan=Sum('total_plan'),
            total_fact=Sum('total_fact'),
            total_deviation=Sum('total_deviation'),
            total_downtime=Sum('total_downtime'),
            blanks_count=Count('id'),
        )

        # Процент выполнения
        total_plan = totals['total_plan'] or 0
        total_fact = totals['total_fact'] or 0

        if total_plan > 0:
            completion_percentage = round(total_fact / total_plan * 100, 1)
        else:
            completion_percentage = 0

        # Считаем бланки по статусам
        status_counts = blanks.values('status').annotate(
            count=Count('id')
        )
        statuses = {item['status']: item['count'] for item in status_counts}

        # Количество отклонений
        deviations_count = DeviationEntry.objects.filter(
            record__blank__in=blanks
        ).count()

        return {
            'total_plan': total_plan,
            'total_fact': total_fact,
            'total_deviation': totals['total_deviation'] or 0,
            'total_downtime': totals['total_downtime'] or 0,
            'completion_percentage': completion_percentage,
            'blanks_count': totals['blanks_count'] or 0,
            'deviations_count': deviations_count,
            'statuses': statuses,
        }

    def get_daily_dynamics(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> list[dict]:
        """
        Динамика по дням для графика.
        """
        blanks = PABlank.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        )

        if sector:
            blanks = blanks.filter(workplace__sector=sector)
        elif workshop:
            blanks = blanks.filter(workplace__sector__workshop=workshop)

        daily_data = blanks.values('date').annotate(
            plan=Sum('total_plan'),
            fact=Sum('total_fact'),
            deviation=Sum('total_deviation'),
            blanks=Count('id'),
        ).order_by('date')

        result = []
        for item in daily_data:
            plan = item['plan'] or 0
            fact = item['fact'] or 0
            completion = round(fact / plan * 100, 1) if plan > 0 else 0

            result.append({
                'date': item['date'].isoformat(),
                'date_display': item['date'].strftime('%d.%m'),
                'plan': plan,
                'fact': fact,
                'deviation': item['deviation'] or 0,
                'completion': completion,
                'blanks': item['blanks'],
            })

        return result

    def get_deviations_by_category(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> list[dict]:
        """
        Анализ отклонений по категориям (группам причин).
        FR-027
        """
        deviations = DeviationEntry.objects.filter(
            record__blank__date__gte=date_from,
            record__blank__date__lte=date_to,
        ).select_related('reason__group')

        if sector:
            deviations = deviations.filter(
                record__blank__workplace__sector=sector
            )
        elif workshop:
            deviations = deviations.filter(
                record__blank__workplace__sector__workshop=workshop
            )

        by_group = deviations.values(
            'reason__group__name',
            'reason__group__color',
            'reason__group__code',
        ).annotate(
            count=Count('id'),
            total_duration=Sum('duration_minutes'),
        ).order_by('-count')

        result = []
        total_count = sum(item['count'] for item in by_group)

        for item in by_group:
            percentage = round(item['count'] / total_count * 100, 1) if total_count > 0 else 0
            result.append({
                'group_name': item['reason__group__name'],
                'group_code': item['reason__group__code'],
                'group_color': item['reason__group__color'],
                'count': item['count'],
                'duration': item['total_duration'] or 0,
                'percentage': percentage,
            })

        return result

    def get_top_deviations(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Топ причин отклонений.
        """
        deviations = DeviationEntry.objects.filter(
            record__blank__date__gte=date_from,
            record__blank__date__lte=date_to,
        ).select_related('reason', 'reason__group')

        if sector:
            deviations = deviations.filter(
                record__blank__workplace__sector=sector
            )
        elif workshop:
            deviations = deviations.filter(
                record__blank__workplace__sector__workshop=workshop
            )

        top_reasons = deviations.values(
            'reason__name',
            'reason__code',
            'reason__group__name',
            'reason__group__color',
        ).annotate(
            count=Count('id'),
            total_duration=Sum('duration_minutes'),
        ).order_by('-count')[:limit]

        return [
            {
                'reason_name': item['reason__name'],
                'reason_code': item['reason__code'],
                'group_name': item['reason__group__name'],
                'group_color': item['reason__group__color'],
                'count': item['count'],
                'duration': item['total_duration'] or 0,
            }
            for item in top_reasons
        ]

    def get_workplace_comparison(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> list[dict]:
        """
        Сравнительный анализ по рабочим местам.
        FR-028
        """
        blanks = PABlank.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        )

        if sector:
            blanks = blanks.filter(workplace__sector=sector)
        elif workshop:
            blanks = blanks.filter(workplace__sector__workshop=workshop)

        workplace_data = blanks.values(
            'workplace__id',
            'workplace__name',
            'workplace__sector__name',
        ).annotate(
            total_plan=Sum('total_plan'),
            total_fact=Sum('total_fact'),
            total_deviation=Sum('total_deviation'),
            total_downtime=Sum('total_downtime'),
            blanks_count=Count('id'),
        ).order_by('-total_fact')

        result = []
        for item in workplace_data:
            plan = item['total_plan'] or 0
            fact = item['total_fact'] or 0
            completion = round(fact / plan * 100, 1) if plan > 0 else 0

            result.append({
                'workplace_id': item['workplace__id'],
                'workplace_name': item['workplace__name'],
                'sector_name': item['workplace__sector__name'],
                'total_plan': plan,
                'total_fact': fact,
                'total_deviation': item['total_deviation'] or 0,
                'total_downtime': item['total_downtime'] or 0,
                'completion': completion,
                'blanks_count': item['blanks_count'],
            })

        return result

    def get_shift_comparison(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> list[dict]:
        """
        Сравнительный анализ по сменам.
        """
        blanks = PABlank.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        )

        if sector:
            blanks = blanks.filter(workplace__sector=sector)
        elif workshop:
            blanks = blanks.filter(workplace__sector__workshop=workshop)

        shift_data = blanks.values(
            'shift__name',
            'shift__number',
        ).annotate(
            total_plan=Sum('total_plan'),
            total_fact=Sum('total_fact'),
            total_deviation=Sum('total_deviation'),
            blanks_count=Count('id'),
        ).order_by('shift__number')

        result = []
        for item in shift_data:
            plan = item['total_plan'] or 0
            fact = item['total_fact'] or 0
            completion = round(fact / plan * 100, 1) if plan > 0 else 0

            result.append({
                'shift_name': item['shift__name'],
                'shift_number': item['shift__number'],
                'total_plan': plan,
                'total_fact': fact,
                'total_deviation': item['total_deviation'] or 0,
                'completion': completion,
                'blanks_count': item['blanks_count'],
            })

        return result

    def get_hourly_pattern(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> list[dict]:
        """
        Почасовой паттерн выполнения плана.
        """
        records = PARecord.objects.filter(
            blank__date__gte=date_from,
            blank__date__lte=date_to,
            is_filled=True,
        )

        if sector:
            records = records.filter(blank__workplace__sector=sector)
        elif workshop:
            records = records.filter(blank__workplace__sector__workshop=workshop)

        hourly_data = records.values('hour_number').annotate(
            avg_plan=Avg('planned_quantity'),
            avg_fact=Avg('actual_quantity'),
            total_plan=Sum('planned_quantity'),
            total_fact=Sum('actual_quantity'),
            records_count=Count('id'),
        ).order_by('hour_number')

        result = []
        for item in hourly_data:
            avg_plan = float(item['avg_plan'] or 0)
            avg_fact = float(item['avg_fact'] or 0)
            completion = round(avg_fact / avg_plan * 100, 1) if avg_plan > 0 else 0

            result.append({
                'hour': item['hour_number'],
                'avg_plan': round(avg_plan, 1),
                'avg_fact': round(avg_fact, 1),
                'completion': completion,
                'records_count': item['records_count'],
            })

        return result

    def get_pareto_analysis(
        self,
        date_from: 'date',
        date_to: 'date',
        workshop: Workshop = None,
        sector: Sector = None,
    ) -> dict:
        """
        Анализ Парето для причин отклонений.
        """
        top_reasons = self.get_top_deviations(
            date_from, date_to, workshop, sector, limit=20
        )

        total_duration = sum(r['duration'] for r in top_reasons)
        cumulative = 0
        pareto_data = []

        for reason in top_reasons:
            cumulative += reason['duration']
            percentage = round(reason['duration'] / total_duration * 100, 1) if total_duration > 0 else 0
            cumulative_percentage = round(cumulative / total_duration * 100, 1) if total_duration > 0 else 0

            pareto_data.append({
                **reason,
                'percentage': percentage,
                'cumulative_percentage': cumulative_percentage,
            })

        return {
            'data': pareto_data,
            'total_duration': total_duration,
        }
