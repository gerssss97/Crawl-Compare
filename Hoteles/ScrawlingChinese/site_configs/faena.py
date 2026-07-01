class FaenaConfig:
    NOMBRE_HOTEL = "Faena Buenos Aires"
    BASE_URL = "https://all.accor.com/booking/en/accor/hotel/B8G3"
    CSS_SELECTOR = ".hotel-accommodations"
    WAIT_FOR = "css:.hotel-accommodations-offers__item-title"
    PAGE_TIMEOUT_MS = 30000

    DOM_NOMBRE_HAB_SEL = ".hotel-accommodations-offers__item-title"
    DOM_PRECIO_SEL = ".offer-price--alternative .offer-price__amount"
    DOM_TAXES_SEL = ".stay-details__formatted-tax-type"

    LLM_INSTRUCTION = (
        "Extract all hotel rooms available on this Faena Buenos Aires / Accor page. "
        "For each room extract: name, details, and all available rates "
        "(title, description, nightly price in USD)."
    )

    # Firefox bypasea el TLS fingerprinting de api.accor.com.
    # Crawl4AI 0.4.x tiene Firefox roto; se usa Playwright directo en HotelScraper.
    # LLMParser no es compatible con el path Firefox — siempre usar DOM.
    BROWSER_TYPE = "firefox"
    DEFAULT_PARSER = "dom"
    HEADLESS = True
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) "
        "Gecko/20100101 Firefox/138.0"
    )

    def build_params(self, fecha_ingreso: str, fecha_egreso: str, **kwargs) -> dict:
        """
        Accor usa el parámetro 'compositions' para la ocupación.
        Formato: "{adultos}" o "{adultos}-{edad1}-{edad2}-..."
        Ej: "2" = 2 adultos solos, "2-16-2" = 2 adultos + niño 16 + niño 2.
        Si se pasan 'edades_ninos' (lista), se usan las edades reales.
        """
        adultos = kwargs.get("adultos", 2)
        edades_ninos = kwargs.get("edades_ninos") or []
        compositions = str(adultos)
        for edad in edades_ninos:
            compositions += f"-{edad}"

        return {
            "checkin": fecha_ingreso,
            "currency": "USD",
            "partya": 1,
            "viewtype": "roomrate",
            "resultViewType": "mda",
            "dateIn": fecha_ingreso,
            "dateOut": fecha_egreso,
            "compositions": compositions,
        }

    def get_extra_browser_args(self) -> list:
        return []

    def extraer_precio_web(self, hab_web, nombre_excel: str) -> float:
        """Retorna el precio total (base + impuestos) para una habitación.

        Args:
            hab_web: Instancia de HabitacionWeb con precio y impuestos.
            nombre_excel: Nombre de la habitación en Excel (no usado en Faena).

        Returns:
            Precio total (base + impuestos).
        """
        return hab_web.precio_total()
