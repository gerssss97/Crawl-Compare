"""Modal de advertencia para gaps (cobertura parcial de periodos)."""

import tkinter as tk
from tkinter import scrolledtext


class ModalAdvertenciaGaps(tk.Toplevel):
    """Modal que advierte sobre gaps antes de ejecutar comparación.

    Este modal se muestra cuando hay periodos sin cobertura de precio en el
    Excel para el rango de fechas solicitado. Permite al usuario:
    - Ver claramente qué rangos NO tienen cobertura
    - Decidir si continuar de todas formas (comparar solo periodos cubiertos)
    - Cancelar la comparación

    Atributos:
        gap_analysis: GapAnalysis con información de gaps detectados
        callback: Función que recibe (bool) indicando si usuario confirmó
    """

    def __init__(self, parent, gap_analysis, callback):
        """Inicializa el modal de advertencia.

        Args:
            parent: Widget padre (ventana principal)
            gap_analysis: GapAnalysis con gaps detectados
            callback: Función que recibe (True=continuar, False=cancelar)
        """
        super().__init__(parent)
        self.gap_analysis = gap_analysis
        self.callback = callback

        # Configuración de ventana
        self.title("Advertencia: Cobertura Parcial")
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # Modal bloqueante

        self._setup_ui()

        # Centrar respecto al parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        """Construye la interfaz del modal."""
        # Header amarillo con ícono de advertencia
        header_frame = tk.Frame(self, bg='#FFF3CD', height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="⚠️  ADVERTENCIA: Cobertura Parcial de Precios",
            font=('Arial', 12, 'bold'),
            bg='#FFF3CD',
            fg='#856404',
            anchor='center'
        ).place(relx=0.5, rely=0.5, anchor='center')

        # Contenido principal
        content_frame = tk.Frame(self, padx=25, pady=20)
        content_frame.pack(fill='both', expand=True)

        # Mensaje explicativo
        tk.Label(
            content_frame,
            text="No hay periodos Excel para los siguientes rangos:",
            font=('Arial', 10),
            justify='left',
            anchor='w'
        ).pack(fill='x', pady=(0, 12))

        # Caja de texto con gaps (scrollable)
        gaps_container = tk.Frame(content_frame)
        gaps_container.pack(fill='both', expand=True, pady=(0, 15))

        gaps_text = scrolledtext.ScrolledText(
            gaps_container,
            height=8,
            font=('Courier New', 9),
            bg='#F5F5F5',
            fg='#D32F2F',
            relief=tk.SOLID,
            borderwidth=1,
            wrap='word',
            padx=10,
            pady=10
        )
        gaps_text.pack(fill='both', expand=True)

        # Insertar descripción de gaps
        descripcion = self.gap_analysis.get_gap_description()
        gaps_text.insert('1.0', descripcion)
        gaps_text.config(state='disabled')  # Solo lectura

        # Mensaje informativo
        tk.Label(
            content_frame,
            text="Se comparará solamente en los periodos con cobertura disponible.",
            font=('Arial', 9),
            fg='#666',
            justify='left',
            anchor='w',
            wraplength=450
        ).pack(fill='x')

        # Frame de botones
        button_frame = tk.Frame(self, padx=20, pady=15)
        button_frame.pack(fill='x', side='bottom')

        # Botón Continuar
        btn_continuar = tk.Button(
            button_frame,
            text="Continuar de Todas Formas",
            command=lambda: self._close(True),
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=10,
            cursor='hand2',
            relief=tk.RAISED,
            borderwidth=2
        )
        btn_continuar.pack(side='left', padx=(0, 10))

        # Hover effect para botón continuar
        def on_enter_continuar(e):
            btn_continuar.config(bg='#1976D2')

        def on_leave_continuar(e):
            btn_continuar.config(bg='#2196F3')

        btn_continuar.bind('<Enter>', on_enter_continuar)
        btn_continuar.bind('<Leave>', on_leave_continuar)

        # Botón Cancelar
        btn_cancelar = tk.Button(
            button_frame,
            text="Cancelar",
            command=lambda: self._close(False),
            bg='#757575',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=10,
            cursor='hand2',
            relief=tk.RAISED,
            borderwidth=2
        )
        btn_cancelar.pack(side='left')

        # Hover effect para botón cancelar
        def on_enter_cancelar(e):
            btn_cancelar.config(bg='#616161')

        def on_leave_cancelar(e):
            btn_cancelar.config(bg='#757575')

        btn_cancelar.bind('<Enter>', on_enter_cancelar)
        btn_cancelar.bind('<Leave>', on_leave_cancelar)

        # Bind tecla Escape para cancelar
        self.bind('<Escape>', lambda e: self._close(False))

    def _close(self, confirmo):
        """Cierra el modal y ejecuta callback.

        Args:
            confirmo: True si usuario confirmó continuar, False si canceló
        """
        self.callback(confirmo)
        self.destroy()
