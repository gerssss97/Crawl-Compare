"""Reusable UI components layer."""

# Legacy tkinter components
from .base_component import BaseComponent
from .date_input import DateInputWidget
from .labeled_combobox import LabeledComboBox
from .periodos_panel import PeriodosPanel
from .precio_panel import PrecioPanel
from .entrada_etiquetada import EntradaEtiquetada

# New CustomTkinter components
from .ctk_base_component import CTkBaseComponent
from .ctk_card import CTkCard
from .ctk_custom_dropdown import CTkCustomDropdown
from .ctk_labeled_combobox import CTkLabeledComboBox
from .ctk_date_input import CTkDateInput
from .ctk_labeled_entry import CTkLabeledEntry
from .ctk_precio_panel import CTkPrecioPanel
from .ctk_periodos_panel import CTkPeriodosPanel
from .ctk_progress_panel import CTkProgressPanel

__all__ = [
    # Legacy
    'BaseComponent',
    'DateInputWidget',
    'LabeledComboBox',
    'PeriodosPanel',
    'PrecioPanel',
    'EntradaEtiquetada',
    # CustomTkinter
    'CTkBaseComponent',
    'CTkCard',
    'CTkCustomDropdown',
    'CTkLabeledComboBox',
    'CTkDateInput',
    'CTkLabeledEntry',
    'CTkPrecioPanel',
    'CTkPeriodosPanel',
    'CTkProgressPanel',
]
