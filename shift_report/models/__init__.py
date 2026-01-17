from .deviation import DeviationGroup, DeviationReason
from .deviation_entry import DeviationEntry
from .employee import Employee, EmployeeRole
from .pa_blank import PABlank, PABlankStatus, PABlankType
from .pa_record import PARecord
from .pa_template import PATemplate
from .product import Product
from .sector import Sector
from .shift import Shift
from .taken_measure import MeasureType, TakenMeasure
from .workplace import Workplace
from .workshop import Workshop

__all__ = [
    # Справочники
    'Workshop',
    'Sector',
    'Workplace',
    'Product',
    'Shift',
    'DeviationGroup',
    'DeviationReason',
    'Employee',
    'EmployeeRole',
    # Бланки ПА
    'PABlank',
    'PABlankType',
    'PABlankStatus',
    'PARecord',
    'PATemplate',
    # Отклонения и меры
    'DeviationEntry',
    'TakenMeasure',
    'MeasureType',
]
