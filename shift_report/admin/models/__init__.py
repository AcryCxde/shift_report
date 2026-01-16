from .deviation import DeviationGroupAdmin, DeviationReasonAdmin
from .employee import EmployeeAdmin
from .product import ProductAdmin
from .sector import SectorAdmin
from .shift import ShiftAdmin
from .workplace import WorkplaceAdmin
from .workshop import WorkshopAdmin

__all__ = [
    'WorkshopAdmin',
    'SectorAdmin',
    'WorkplaceAdmin',
    'ProductAdmin',
    'ShiftAdmin',
    'DeviationGroupAdmin',
    'DeviationReasonAdmin',
    'EmployeeAdmin',
]
