from .deviation import DeviationGroupAdmin, DeviationReasonAdmin
from .deviation_entry import DeviationEntryAdmin
from .employee import EmployeeAdmin
from .pa_blank import PABlankAdmin
from .pa_record import PARecordAdmin
from .pa_template import PATemplateAdmin
from .product import ProductAdmin
from .sector import SectorAdmin
from .shift import ShiftAdmin
from .taken_measure import TakenMeasureAdmin
from .workplace import WorkplaceAdmin
from .workshop import WorkshopAdmin

__all__ = [
    # Справочники
    'WorkshopAdmin',
    'SectorAdmin',
    'WorkplaceAdmin',
    'ProductAdmin',
    'ShiftAdmin',
    'DeviationGroupAdmin',
    'DeviationReasonAdmin',
    'EmployeeAdmin',
    # Бланки ПА
    'PABlankAdmin',
    'PARecordAdmin',
    'PATemplateAdmin',
    # Отклонения и меры
    'DeviationEntryAdmin',
    'TakenMeasureAdmin',
]
