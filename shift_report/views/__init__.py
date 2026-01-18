from .auth import ChangePINView, HomeView, LoginView, LogoutView, ProfileView
from .operator import (BlankDetailView, OperatorDashboardView, QuickInputView,
                       ReasonSearchView, RecordInputView)

__all__ = [
    # Auth
    'HomeView',
    'LoginView',
    'LogoutView',
    'ChangePINView',
    'ProfileView',
    # Operator
    'OperatorDashboardView',
    'BlankDetailView',
    'RecordInputView',
    'QuickInputView',
    'ReasonSearchView',
]
