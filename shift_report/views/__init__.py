from .analytics import (ChartDataAPIView, ComparisonView, DashboardAPIView,
                        DashboardView, DeviationsAnalysisView, ReportsView)
from .auth import ChangePINView, HomeView, LoginView, LogoutView, ProfileView
from .blanks import (BlankBulkCreateView, BlankCreateView, BlankDeleteView,
                     BlankDetailView, BlankListView, CalculatePlanAPIView,
                     TemplateCreateView, TemplateDeleteView, TemplateEditView,
                     TemplateListView, WorkplaceAPIView)
from .master import (AddMeasureView, BlankMonitorView, BlankStatusAPIView,
                     MasterMonitoringView, MonitoringAPIView,
                     WorkplaceDetailView)
from .operator import BlankDetailView as OperatorBlankDetailView
from .operator import (OperatorDashboardView, QuickInputView, ReasonSearchView,
                       RecordInputView)

__all__ = [
    # Auth
    'HomeView',
    'LoginView',
    'LogoutView',
    'ChangePINView',
    'ProfileView',
    # Operator
    'OperatorDashboardView',
    'OperatorBlankDetailView',
    'RecordInputView',
    'QuickInputView',
    'ReasonSearchView',
    # Master
    'MasterMonitoringView',
    'WorkplaceDetailView',
    'BlankMonitorView',
    'AddMeasureView',
    'MonitoringAPIView',
    'BlankStatusAPIView',
    # Blanks
    'BlankListView',
    'BlankCreateView',
    'BlankBulkCreateView',
    'BlankDetailView',
    'BlankDeleteView',
    'TemplateListView',
    'TemplateCreateView',
    'TemplateEditView',
    'TemplateDeleteView',
    'WorkplaceAPIView',
    'CalculatePlanAPIView',

    # Analytics
    'DashboardView',
    'DeviationsAnalysisView',
    'ComparisonView',
    'ReportsView',
    'DashboardAPIView',
    'ChartDataAPIView',
]
