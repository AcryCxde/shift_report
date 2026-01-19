"""
Views для аналитики и отчётов.

FR-026: Дашборды и аналитика
FR-027: Анализ отклонений по категориям
FR-028: Сравнительный анализ
FR-029: Drill-down анализ
"""

from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from shift_report.decorators import ChiefRequiredMixin, MasterRequiredMixin
from shift_report.services.analytics import AnalyticsService


class DashboardView(MasterRequiredMixin, View):
    """
    Главный дашборд аналитики.
    FR-026
    """

    template_name = 'shift_report/analytics/dashboard.html'

    def get(self, request):
        user = request.user

        # Параметры фильтрации
        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')

        today = timezone.localdate()

        if date_from_str:
            try:
                from datetime import datetime
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                date_from = today - timedelta(days=7)
        else:
            date_from = today - timedelta(days=7)

        if date_to_str:
            try:
                from datetime import datetime
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                date_to = today
        else:
            date_to = today

        # Определяем область видимости
        workshop = None
        sector = None

        if user.sector:
            sector = user.sector
        elif user.workshop:
            workshop = user.workshop

        # Получаем данные
        service = AnalyticsService()

        summary = service.get_dashboard_summary(date_from, date_to, workshop, sector)
        daily_dynamics = service.get_daily_dynamics(date_from, date_to, workshop, sector)
        deviations_by_category = service.get_deviations_by_category(date_from, date_to, workshop, sector)
        top_deviations = service.get_top_deviations(date_from, date_to, workshop, sector, limit=5)

        return render(request, self.template_name, {
            'date_from': date_from,
            'date_to': date_to,
            'summary': summary,
            'daily_dynamics': daily_dynamics,
            'deviations_by_category': deviations_by_category,
            'top_deviations': top_deviations,
            'current_sector': sector,
            'current_workshop': workshop,
        })


class DeviationsAnalysisView(MasterRequiredMixin, View):
    """
    Детальный анализ отклонений.
    FR-027
    """

    template_name = 'shift_report/analytics/deviations.html'

    def get(self, request):
        user = request.user

        # Параметры
        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')

        today = timezone.localdate()
        date_from = self._parse_date(date_from_str, today - timedelta(days=30))
        date_to = self._parse_date(date_to_str, today)

        workshop = user.workshop if not user.sector else None
        sector = user.sector

        service = AnalyticsService()

        deviations_by_category = service.get_deviations_by_category(date_from, date_to, workshop, sector)
        top_deviations = service.get_top_deviations(date_from, date_to, workshop, sector, limit=15)
        pareto = service.get_pareto_analysis(date_from, date_to, workshop, sector)

        return render(request, self.template_name, {
            'date_from': date_from,
            'date_to': date_to,
            'deviations_by_category': deviations_by_category,
            'top_deviations': top_deviations,
            'pareto': pareto,
        })

    def _parse_date(self, date_str, default):
        if date_str:
            try:
                from datetime import datetime
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        return default


class ComparisonView(MasterRequiredMixin, View):
    """
    Сравнительный анализ.
    FR-028
    """

    template_name = 'shift_report/analytics/comparison.html'

    def get(self, request):
        user = request.user

        # Параметры
        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')
        compare_by = request.GET.get('compare_by', 'workplace')

        today = timezone.localdate()
        date_from = self._parse_date(date_from_str, today - timedelta(days=30))
        date_to = self._parse_date(date_to_str, today)

        workshop = user.workshop if not user.sector else None
        sector = user.sector

        service = AnalyticsService()

        if compare_by == 'shift':
            comparison_data = service.get_shift_comparison(date_from, date_to, workshop, sector)
        else:
            comparison_data = service.get_workplace_comparison(date_from, date_to, workshop, sector)

        hourly_pattern = service.get_hourly_pattern(date_from, date_to, workshop, sector)

        return render(request, self.template_name, {
            'date_from': date_from,
            'date_to': date_to,
            'compare_by': compare_by,
            'comparison_data': comparison_data,
            'hourly_pattern': hourly_pattern,
        })

    def _parse_date(self, date_str, default):
        if date_str:
            try:
                from datetime import datetime
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        return default


class ReportsView(ChiefRequiredMixin, View):
    """
    Генерация отчётов.
    """

    template_name = 'shift_report/analytics/reports.html'

    def get(self, request):
        return render(request, self.template_name, {
            'today': timezone.localdate(),
        })


class DashboardAPIView(MasterRequiredMixin, View):
    """
    API для данных дашборда.
    """

    def get(self, request):
        user = request.user

        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')

        today = timezone.localdate()
        date_from = self._parse_date(date_from_str, today - timedelta(days=7))
        date_to = self._parse_date(date_to_str, today)

        workshop = user.workshop if not user.sector else None
        sector = user.sector

        service = AnalyticsService()

        return JsonResponse({
            'summary': service.get_dashboard_summary(date_from, date_to, workshop, sector),
            'daily_dynamics': service.get_daily_dynamics(date_from, date_to, workshop, sector),
            'deviations_by_category': service.get_deviations_by_category(date_from, date_to, workshop, sector),
        })

    def _parse_date(self, date_str, default):
        if date_str:
            try:
                from datetime import datetime
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        return default


class ChartDataAPIView(MasterRequiredMixin, View):
    """
    API для данных графиков.
    """

    def get(self, request, chart_type):
        user = request.user

        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')

        today = timezone.localdate()
        date_from = self._parse_date(date_from_str, today - timedelta(days=30))
        date_to = self._parse_date(date_to_str, today)

        workshop = user.workshop if not user.sector else None
        sector = user.sector

        service = AnalyticsService()

        if chart_type == 'daily':
            data = service.get_daily_dynamics(date_from, date_to, workshop, sector)
        elif chart_type == 'deviations':
            data = service.get_deviations_by_category(date_from, date_to, workshop, sector)
        elif chart_type == 'hourly':
            data = service.get_hourly_pattern(date_from, date_to, workshop, sector)
        elif chart_type == 'workplace':
            data = service.get_workplace_comparison(date_from, date_to, workshop, sector)
        elif chart_type == 'pareto':
            data = service.get_pareto_analysis(date_from, date_to, workshop, sector)
        else:
            return JsonResponse({'error': 'Unknown chart type'}, status=400)

        return JsonResponse({'data': data})

    def _parse_date(self, date_str, default):
        if date_str:
            try:
                from datetime import datetime
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        return default
