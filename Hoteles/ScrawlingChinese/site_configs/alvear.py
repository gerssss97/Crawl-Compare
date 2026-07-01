class AlvearConfig:
    NOMBRE_HOTEL = "Alvear Palace Hotel"
    BASE_URL = "https://be.synxis.com/"
    CSS_SELECTOR = ".thumb-cards_products .app_col-sm-12.app_col-md-8.app_col-lg-8"
    WAIT_FOR = "css:.thumb-cards_products"
    PAGE_TIMEOUT_MS = 30000

    # DOM selectors — pendiente: inspeccionar HTML del Alvear
    DOM_NOMBRE_HAB_SEL = None
    DOM_PRECIO_SEL = None

    LLM_INSTRUCTION = (
        "Extract all hotel rooms with: name, details, "
        "and promotions list (title, description, nightly price)"
    )

    USE_MAGIC = False  # be.synxis.com no tiene anti-bot agresivo
    DEFAULT_PARSER = "llm"

    def build_params(self, fecha_ingreso: str, fecha_egreso: str, **kwargs) -> dict:
        adultos = kwargs.get("adultos", 2)
        ninos = kwargs.get("ninos", 0)
        return {
            "adult": adultos,
            "child": ninos,
            "arrive": fecha_ingreso,
            "depart": fecha_egreso,
            "chain": 24447,
            "hotel": 6933,
            "currency": "USD",
            "level": "hotel",
            "locale": "en-US",
            "productcurrency": "USD",
            "rooms": 1,
            "src": 30,
        }

    def get_extra_browser_args(self) -> list:
        return []

    def extraer_precio_web(self, hab_web, nombre_excel: str) -> float:
        """Retorna el precio total después de aplicar filtro de breakfast.

        Args:
            hab_web: Instancia de HabitacionWeb con combos.
            nombre_excel: Nombre de la habitación en Excel (usado para decidir filtro breakfast).

        Returns:
            Precio total con filtro de breakfast aplicado.
        """
        from Core.comparador import aplicar_filtro_breakfast
        hab = aplicar_filtro_breakfast(hab_web, nombre_excel)
        return hab.precio_total()
