# Email config — opciones evaluadas (decisión pendiente)

> **Estado:** 📋 Decisión pendiente — opciones documentadas para futura implementación.
> **Fecha del mapeo:** 2026-05-21.
> **Branch al que aplica:** TBD (se decide cuando se implemente).
> **Decisión bloqueante:** depende del proveedor de email del cliente final. Gmail → habilita Combo 3. Otro proveedor → Combo 2 es más viable.

Este documento captura el análisis completo del espacio de soluciones para que el envío de email sea **configurable por el usuario final** (no por el developer). No es un plan de implementación inmediata — es la **base de decisión** para cuando llegue el momento de implementar.

---

## 1. Problema actual

El sistema de envío de email hoy usa una cuenta hardcodeada del developer:

- [Hoteles/Core/controller.py:156, 266](../../Hoteles/Core/controller.py) — lee `GMTP_KEY` con `os.getenv()`.
- [Hoteles/Core/controller.py:277-308](../../Hoteles/Core/controller.py) — `enviar_correo()` conecta a `smtp.gmail.com:587` con TLS.
- [Hoteles/UI/views/modal_email.py:17-18](../../Hoteles/UI/views/modal_email.py) — `REMITENTE` y `DESTINATARIO` hardcodeados con el email del developer (`gerlucero1997@gmail.com`).
- [Hoteles/UI/views/modal_email.py:594](../../Hoteles/UI/views/modal_email.py) — `enviar_email_multiperiodo(hotel, resultado, remitente, destinatario, texto_override)` usa `self.REMITENTE` fijo.
- El `.env` define `GMTP_KEY` y `GROQ_API_KEY` (no hay `SMTP_USER` ni `EMAIL_TO`).

**Distribuir el `.exe` = distribuir las credenciales del developer.** Cada cliente final manda desde la cuenta de Germán. Si el cliente quiere mandar desde su cuenta, hoy no puede.

---

## 2. Las 3 dimensiones del problema

Decidir sobre email tiene 3 ejes **ortogonales**: una decisión en uno no determina las otras.

- **Dimensión 1 — Mecanismo de envío:** ¿cómo se manda físicamente el email? (SMTP propio, OAuth2, servicio transaccional, `mailto:`).
- **Dimensión 2 — Storage de credenciales:** ¿dónde se guarda el password/API key/refresh token? (`.env`, `config.json` plano, `keyring` del OS, encriptación custom).
- **Dimensión 3 — Datos configurables:** ¿qué del email puede tocar el usuario? (remitente, destinatario, asunto, firma, plantilla, etc.).

Este documento se concentra en **Dimensión 1**. Las otras dos quedan implícitas dentro de cada combo.

---

## 3. Mecanismos de envío evaluados

### Tabla comparativa

| Opción | Descripción corta | Pro | Contra |
|--------|-------------------|-----|--------|
| **A. SMTP propio del usuario** | Usuario carga servidor, puerto, usuario, password/App Password | Universal (cualquier proveedor). No depende de terceros. | Setup intimidante. App Passwords en Gmail son un dolor y están en lenta extinción. |
| **B. OAuth2 (Gmail/Outlook)** | Botón "Iniciar sesión con Google/Microsoft", token guardado en `keyring` | UX top post-setup. Es el camino que Google empuja activamente. | Setup en Google Cloud Console (15-20 min). Cartel "no verificada" primera vez. |
| **C. Servicio transaccional** (SendGrid, Resend, Mailgun, Postmark, Brevo, Amazon SES) | Cliente crea cuenta gratis, verifica su email, copia API key | Setup más fácil que SMTP. Free tiers ~100 mails/día. Mejor entregabilidad. | Depende de un tercero. Header "via sendgrid.net" visible si se inspeccionan detalles. |
| **D. `mailto:`** | App abre el cliente de email del SO con todo pre-rellenado | Cero config. Cero credenciales. Usa el cliente que el usuario ya tiene. | Usuario clickea "Enviar" manual. Límite ~2000 chars de URL en Windows. Sin adjuntos. |

### Detalle de cada opción

#### Opción A — SMTP propio

El usuario carga sus credenciales SMTP. La app se conecta como cliente SMTP y manda en su nombre.

**Lo que debe configurar el usuario (sin presets):**

| Campo | Ejemplo | Cómo lo saca |
|-------|---------|--------------|
| Servidor SMTP | `smtp.gmail.com` | Googleando |
| Puerto | `587` | Googleando |
| Seguridad | `STARTTLS` | Googleando |
| Usuario | `juan@gmail.com` | Su email |
| Contraseña / App Password | `abcd efgh ijkl mnop` | Generándola (el gran dolor) |
| Email "From" | `juan@gmail.com` | Normalmente igual al usuario |
| Nombre "From" | `Juan Pérez` | Lo que quiere mostrar |

**Con presets por proveedor**, el usuario solo carga email + password + nombre. Tabla de presets que la app conoce:

| Proveedor | Servidor | Puerto | Seguridad | Nota |
|-----------|----------|--------|-----------|------|
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | STARTTLS | Requiere App Password (link a tutorial) |
| Outlook / Hotmail / Office 365 | `smtp-mail.outlook.com` | 587 | STARTTLS | Requiere App Password si tiene 2FA |
| Yahoo Mail | `smtp.mail.yahoo.com` | 587 | STARTTLS | Requiere App Password |
| iCloud Mail | `smtp.mail.me.com` | 587 | STARTTLS | Requiere App-Specific Password |
| Servidor propio / Otro | (manual) | (manual) | (dropdown) | Usuario llena todo |

**El verdadero dolor**: para los 4 proveedores principales, si el usuario tiene 2FA activado (la norma hoy), **no puede usar su contraseña normal** — tiene que generar una App Password específica. Proceso típico en Gmail:

1. Ir a `myaccount.google.com/security`.
2. Verificar que tenga 2FA activado.
3. Buscar "App Passwords" (Google la esconde a propósito).
4. Generar contraseña → Google muestra 16 caracteres, **la copia se borra al cerrar la ventana**.
5. Pegarla en la app.

**10-15 minutos para un no-técnico la primera vez**, propenso a errores.

#### Opción B — OAuth2 con Google (o Microsoft)

La app NUNCA ve la contraseña del usuario. Lo redirige al sitio de Google, el usuario se loguea ahí, Google le da a la app un **token** con permisos limitados (scope `gmail.send`) y revocable.

**Diferencia con App Password:**

| App Password | OAuth2 |
|--------------|--------|
| La app guarda tu password de 16 chars | La app guarda un refresh token |
| Sin scopes (full SMTP + IMAP) | Scope específico (solo `gmail.send`) |
| No expira hasta borrarse manualmente | Access token vive 1h, refresh token revocable |
| No revocable individualmente | Cada app tiene su token revocable por separado |
| Indistinguible de un ataque | Auditado por Google como uso autorizado |

**Esfuerzo de código:**

- Librería oficial: `google-auth-oauthlib`.
- Flow: botón → abre navegador → autoriza → servidor local efímero (`localhost:8080`) captura el `code` → token + refresh token.
- Storage del refresh token en `keyring`. Access tokens viven 1h y se renuevan transparentemente.
- Para mandar: `smtplib` con mecanismo `XOAUTH2`, o la Gmail API REST.

#### Opción C — Servicios transaccionales

Servicios externos que se especializan en entregar emails en nombre de alguien. **No son la cuenta de email del usuario** — son intermediarios.

**Cómo funciona el "from" — 2 modos:**

- **Single Sender Verification:** el usuario agrega su email personal (ej. `juan@gmail.com`) en el panel del servicio, recibe un email de confirmación, lo confirma. A partir de ahí la API puede mandar con `From: juan@gmail.com`. Header "via sendgrid.net" aparece si el destinatario busca detalles. **Setup 3-5 min, gratis.**
- **Domain Authentication:** si el cliente tiene dominio propio (ej. `hotelxyz.com.ar`), agrega registros DNS (SPF, DKIM, DMARC). Mejor entregabilidad, sin "via". Pero requiere dominio + saber DNS — la mayoría de los clientes no tienen.

**Servicios candidatos:**

| Servicio | Free tier | Notas |
|----------|-----------|-------|
| **SendGrid** | 100 mails/día (legacy free) | Más maduro, owned by Twilio. UI compleja. |
| **Resend** | 100 mails/día, 3000/mes | Modern, API limpia, devs-friendly. ⭐ Recomendado. |
| **Mailgun** | 100 mails/día (3 meses), después $35/mes | Caro post-trial. |
| **Postmark** | 100/mes free trial | Excelente entregabilidad transaccional. |
| **Brevo** (ex Sendinblue) | 300/día | Más orientado a marketing. |
| **Amazon SES** | 62.000/mes desde EC2 | Más barato pero setup AWS = pesadilla para no-técnicos. |

#### Opción D — `mailto:`

La app abre el cliente de email default del SO con todo pre-rellenado vía URL `mailto:`. El usuario solo clickea "Enviar".

**Snippet técnico:**

```python
import webbrowser
from urllib.parse import quote

url = f"mailto:{destinatario}?subject={quote(subject)}&body={quote(body)}"
webbrowser.open(url)
```

**Limitaciones técnicas reales:**

- Windows: límite ~2000 caracteres URL. La tabla ASCII multi-período puede superarlo y se trunca silenciosamente.
- Caracteres especiales (tildes, ñ, saltos de línea) quedan escapados feos en algunos clientes.
- Sin adjuntos (limitación del protocolo).
- Algunos clientes (Outlook web) ignoran `body=` y solo respetan `subject=`.

**Mitigación posible:** mandar resumen corto en el body, tabla completa al portapapeles con mensaje "ya copié la tabla, pegala con Ctrl+V". Feo pero funcional.

---

## 4. Profundización — por qué Google empuja OAuth2 y limita App Passwords

Es contraintuitivo: ¿no es Google el que ofrece App Passwords? ¿Por qué las está matando? Es exactamente la mira del problema.

### Por qué Google odia las App Passwords — 5 razones

1. **Si la app guarda mal el password, se filtra la cuenta entera.** Una App Password tiene acceso completo a SMTP/IMAP. Si un dev mete el archivo de config en git por accidente (le pasó a miles), cualquiera lee tus mails y manda en tu nombre. Con OAuth, lo peor que pasa es que se filtra un token revocable.

2. **No se pueden revocar individualmente.** Si configuraste 5 apps con App Passwords y querés sacarle permiso a una sola, no podés saber cuál es cuál. Solo podés borrar TODAS y regenerar. Con OAuth, cada app tiene su token revocable desde myaccount.google.com.

3. **No expiran.** Una App Password vive para siempre hasta que la borres manualmente. Un access token de OAuth dura 1 hora, un refresh token se puede invalidar centralmente.

4. **No tienen scopes.** La App Password puede mandar mails Y leer tu inbox Y borrar mensajes. Es full access. OAuth te permite pedir solo `gmail.send` sin tocar el resto.

5. **Indistinguibles de un ataque.** Cuando una app loguea con tu password real (o App Password), Google ve "alguien con la contraseña hizo login desde IP X" y no sabe si sos vos o un atacante. Con OAuth, ve "la app autorizada Y usó el token Z desde IP X" y puede aplicar políticas más finas.

### Cronología real

- **2014:** Google introduce App Passwords como parche temporal al activar 2FA masivamente. Outlook desktop, Thunderbird, etc. no sabían 2FA y se rompían.
- **2022:** deprecan "Less Secure App Access" (login con password real sin 2FA). App Passwords sobreviven.
- **2024-2025:** empiezan a **no permitir generar App Passwords nuevas** en ciertas cuentas (Workspace empresariales primero, gradualmente personales).
- **Roadmap:** Google ha indicado que App Passwords eventualmente desaparecen del todo.

### Implicancias HOY para este proyecto

- Cliente con **Workspace empresarial** → probablemente ya no puede generar App Passwords (depende del admin).
- Cliente con **@gmail.com personal** → todavía puede, pero la opción está cada vez más escondida en la UI.
- Si Google corta App Passwords en 2027, una app basada en Opción A para Gmail deja de funcionar y obligaría a migrar.

> **Google no quiere que las apps tengan tu contraseña (ni siquiera una "alternativa"). Quiere que tengan tokens limitados, revocables y auditables (OAuth2). App Passwords son un compromiso histórico que están en lenta extinción.**

---

## 5. Profundización — OAuth2 con Google: ¿cuán costoso es?

Distinguir entre "registrar la app" (gratis, 15-20 min) y "certificar la app" (caro, **no aplica a este caso**).

### Lo que SÍ hay que hacer (gratis)

1. **Crear proyecto en Google Cloud Console** (console.cloud.google.com). 5 min, formulario web, gratis. Cualquier cuenta Google sirve.
2. **Habilitar la API "Gmail API"** desde el panel del proyecto. 1 click.
3. **Configurar OAuth consent screen**: nombre de la app, email de soporte, scopes que vas a usar (solo `gmail.send`). 5-10 min de formulario.
4. **Crear credenciales OAuth Client ID** tipo "Desktop app". Te genera `client_id` y `client_secret`. Descargás como JSON.
5. **Embeber esos credenciales en la app** (legítimo para desktop apps — no son secretos verdaderos en este modelo).

**Total: 15-20 minutos**, sin tarjeta de crédito, sin dominio, sin cuenta empresarial.

### Lo que NO hay que hacer (la parte cara)

**Verificación de la app** (Google la llama "App Verification", Microsoft "Publisher Verification"). Esto SÍ es complejo: política de privacidad publicada, demostración del scope, a veces auditoría por un tercero (~$15.000 USD), tiempos largos.

**¿Tu app necesita verificación?** **No**, mientras se mantenga en **"External + unverified"**:

- En "Testing" de Google: hasta 100 usuarios, **refresh tokens duran solo 7 días** (hay que reauth). **No sirve para producción.**
- En "External unverified": la pantalla de consentimiento muestra cartel grande **"Google no ha verificado esta aplicación"** con un "Show advanced" → "Go to (unsafe)". Suena feo pero **funciona** y los refresh tokens NO caducan a los 7 días. **Para 1 cliente conocido al que le avisás, totalmente viable.**

### Esfuerzo real de código

- Librería oficial: [`google-auth-oauthlib`](https://googleapis.dev/python/google-auth-oauthlib/latest/).
- Flow estándar:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=8080)  # abre navegador, captura code
# creds.refresh_token → guardar en keyring
```

- Para mandar: `smtplib` con mecanismo `XOAUTH2`, o más limpio, la Gmail API REST con `users.messages.send`.

### Lo verdaderamente molesto

- **Formularios confusos** en OAuth consent screen (te piden "dominio autorizado" que para desktop app es irrelevante pero hay que rellenar).
- **Cartel "no verificada" la primera vez asusta** a clientes no-técnicos. Hay que avisarle "ignoralo, hacé click en Show advanced".
- **Refresh tokens pueden fallar** si el usuario revoca permisos desde su cuenta. La app tiene que manejar el caso con "tu sesión expiró, volvé a loguear".

---

## 6. Profundización — Servicios transaccionales: cómo funciona el "from"

Hay un malentendido común: estos servicios **no son tu cuenta de email**. Son intermediarios profesionales que entregan emails en nombre de alguien.

### Flujo concreto con Resend o SendGrid

1. **Cliente se registra** en resend.com / sendgrid.com (free tier). Solo necesita email + password.
2. **Genera API key** desde su panel (1 click, copy/paste).
3. **Verifica un email "from"**: ver los 2 modos detallados arriba.
4. La pega en la app.
5. La app llama a la API REST del servicio con header `Authorization: Bearer <api_key>` y body con `from`, `to`, `subject`, `text`.

### Pro real vs SMTP propio

- **Setup mucho más fácil**: una API key vs todo el lío de App Password de Gmail (2FA + settings + token de 16 chars).
- **No tiene los problemas de Google bloqueando App Passwords**.
- **Mejor entregabilidad** que SMTP propio mal configurado.
- **Logs accesibles**: el cliente puede ver desde el panel si los mails se entregaron, rebotaron, etc.
- **API keys scope-limited**: solo "mandar emails", no acceso al inbox.

### Contra real

- **El cliente tiene que crear UNA CUENTA MÁS** (en SendGrid/Resend). Para "una app que comparo precios y mando un mail", muchos prefieren usar su Gmail directo. Es fricción.
- **Si SendGrid sube precios o cierra el free tier**, la app deja de funcionar (o migrás a otro servicio, tocando código).
- **"via sendgrid.net"** queda raro si el cliente es muy puntilloso.

---

## 7. Combo 2: D + C (mailto: + servicio transaccional) ⭐

Dos vías de envío que el usuario elige según el contexto.

- **mailto: (D)** para el caso "lo mando rápido desde mi Outlook desktop sin configurar nada".
- **Servicio transaccional (C)** para "lo mando automático sin abrir el cliente".

### Setup que requiere el cliente (una sola vez)

1. Crear cuenta gratis en Resend o SendGrid (~3 min).
2. Verificar su email personal (recibe un mail con link).
3. Generar una API key desde el panel.
4. Pegar la API key en la app (`Config → Email`).
5. Click "Probar envío" → la app manda un email de prueba al propio remitente.

### Implementación en código

- **Nueva dependencia**: SDK del servicio elegido (`resend` o `sendgrid`). Ambos son `pip install` simples sin compilación.
- **`ConfigService`** guarda:
  - `email_provider: "resend"` (o `"sendgrid"`, o `"mailto"`).
  - `email_api_key: <en keyring>`.
  - `email_from: <email verificado>`.
  - `email_from_name: <opcional>`.
  - `email_destinatario_default: <opcional>`.
  - `email_firma: <opcional>`.
- **Modal de Email config**: dropdown "Modo de envío" → opciones `[mailto:, Resend, SendGrid]`. Si elige uno de los servicios, aparecen los campos correspondientes.
- **Modal de envío** (cuando el usuario quiere mandar el email de discrepancia): radio "Cómo mandar: [Automático (Resend) / Abrir mi cliente (mailto:)]" pre-seleccionado según preferencia configurada.
- **Refactor**: reemplazar `enviar_correo()` en [Core/controller.py](../../Hoteles/Core/controller.py) por una **factory** `obtener_sender(config) → Sender` que devuelve `ResendSender`, `SendGridSender`, o `MailtoSender`. Cada uno implementa la misma interfaz `enviar(remitente, destinatario, asunto, cuerpo) → bool`.

### Pro

- D no requiere ninguna config — el usuario lo puede usar el día uno.
- C tiene setup más simple que SMTP propio (una API key vs el quilombo de App Passwords).
- Si Google/Microsoft cambian políticas, los servicios transaccionales no se ven afectados.
- API keys de servicios transaccionales son scope-limited a "mandar emails".
- Mejor entregabilidad que SMTP propio mal configurado.

### Contra

- Dependés del servicio externo (Resend/SendGrid).
- Cliente tiene que crear cuenta en un servicio que probablemente no conoce.
- Header "via sendgrid.net" / "via resend.dev" visible si el destinatario inspecciona detalles.
- Si el cliente cambia de proveedor de email en el futuro, tiene que re-verificar el nuevo email en el panel del servicio (no es transparente).

### Cuándo elegir Combo 2

- Cliente **NO usa Gmail** ni Outlook (descarta B).
- Cliente tiene varios proveedores de email distintos (querés universalidad).
- No querés meterte con Google Cloud / Azure.
- Aceptás depender de un servicio externo a cambio de simplicidad de código.

---

## 8. Combo 3: D + B (mailto: + OAuth2 Gmail) ⭐

Dos vías de envío.

- **mailto: (D)** para "lo mando rápido sin tocar nada".
- **OAuth2 Gmail (B)** para "lo mando automático con UX premium".

### Setup que requiere el developer (una vez en la vida de la app)

1. Crear proyecto en Google Cloud Console (5 min).
2. Habilitar Gmail API (1 click).
3. Configurar OAuth consent screen (10 min, formulario web).
4. Crear OAuth Client ID tipo "Desktop app" (3 min).
5. Descargar JSON con `client_id` y `client_secret`. Embeberlos en la app.

### Setup que requiere el cliente (una sola vez)

1. Abrir Config → Email → click "Iniciar sesión con Google".
2. Se abre el navegador en la URL de auth de Google.
3. **Primera vez**: ve cartel "Google no ha verificado esta aplicación" → "Show advanced" → "Go to (unsafe)". Hay que avisarle: "ignoralo, la app es para uso interno".
4. Login con su cuenta Gmail.
5. Acepta los permisos (solo "Enviar emails en tu nombre" — scope `gmail.send`).
6. La app captura el token, lo guarda. **Listo para siempre** (modulo refresh de token, transparente).

### Implementación en código

- **Nueva dependencia**: `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`. Todos `pip install` simples.
- **`ConfigService`** guarda:
  - `email_provider: "gmail_oauth"` (o `"mailto"`).
  - `email_user: <gmail>`.
  - `gmail_refresh_token: <en keyring>`.
  - `email_from_name: <opcional>`.
  - `email_destinatario_default: <opcional>`.
  - `email_firma: <opcional>`.
- **Modal de Email config**: botón "Iniciar sesión con Google" → ejecuta `InstalledAppFlow.run_local_server(port=8080)`.
- **En el envío**: cargar credentials desde refresh token, refrescar access token si expiró (la librería lo hace sola), llamar a Gmail API REST `users.messages.send` con el mensaje base64-encoded.
- **Misma factory pattern que Combo 2**: `MailtoSender` + `GmailOAuthSender`.

### Pro

- UX post-setup inicial **es la mejor de todas**. El cliente clickea "login" una vez y nunca más toca nada.
- Es el camino que Google **empuja activamente** — no se va a romper a futuro.
- Tokens revocables individualmente desde la cuenta Google del cliente.
- Scope limitado a `gmail.send` — la app NO puede leer ni borrar mails.
- Sin "via" en headers — el destinatario ve el email normal del cliente, sin marcas raras.
- Cliente no necesita generar App Passwords ni saber qué es SMTP.

### Contra

- **SOLO sirve para Gmail.** Si el cliente migra a Outlook, hay que re-implementar con Microsoft Graph API (Azure) — duplicar trabajo.
- Cartel "app no verificada" la primera vez asusta a clientes no-técnicos.
- Setup inicial tuyo en Google Cloud (15-20 min, una vez en la vida de la app).
- Si el cliente revoca permisos desde myaccount.google.com (improbable pero posible), el refresh token muere y hay que re-loguear.
- Más código que Combo 2 (flow de OAuth + refresh handling + manejo de tokens vencidos).

### Cuándo elegir Combo 3

- Cliente **usa Gmail** (cuenta personal o Workspace).
- Querés UX premium y estás dispuesto a invertir más en setup inicial.
- No querés depender de servicios transaccionales externos.
- Estás cómodo gestionando 1 proyecto en Google Cloud Console (mantenimiento mínimo).

---

## 9. Comparativa final Combo 2 vs Combo 3

| Criterio | Combo 2 (D + C) | Combo 3 (D + B) |
|----------|-----------------|-----------------|
| Setup inicial tuyo (developer) | Nada (pip install) | 15-20 min en Google Cloud |
| Setup inicial del cliente | Crear cuenta en Resend + verificar email + API key | Click "login con Google" una vez |
| Universalidad | Funciona con cualquier email del cliente | Solo Gmail |
| Dependencia externa | Sí (Resend/SendGrid) | No (Google es el proveedor del cliente igual) |
| UX recurrente | Bueno | Excelente (transparente) |
| Headers limpios | No ("via resend.dev") | Sí |
| Permisos solicitados | Solo "mandar email" (API key scoped) | Solo "gmail.send" |
| Resistencia futura | Buena | Excelente |
| Complejidad de código | Baja (SDK simple) | Media (OAuth flow + refresh) |

---

## 10. Decisión pendiente — qué hace falta para elegir

Antes de implementar, responder:

1. **¿Qué proveedor de email usa el cliente final?** — **Bloqueante para elegir Combo.**
2. ¿El cliente tiene 2FA activado en su cuenta? (Si es Gmail Workspace, casi seguro sí.)
3. ¿El developer quiere mantener proyecto en Google Cloud Console activo? (Combo 3 requiere check anual de OAuth consent screen.)
4. ¿Hay tolerancia a depender de un servicio externo? (Combo 2 vive o muere con Resend.)
5. ¿Aceptaríamos la UX de doble vía (mailto: + servicio) o el cliente espera "mandar email" = un solo botón?

---

## 11. Decisiones tomadas en la conversación

- ✅ **mailto: (D)** queda como **fallback siempre disponible** (cero config, vía rápida).
- ✅ La segunda vía la decide el cliente final según su proveedor: Combo 2 si no usa Gmail, Combo 3 si sí.
- ❌ NO se va por Combo 1 (D + SMTP propio con presets). Razón: App Passwords están en lenta extinción + setup intimidante.
- ❌ NO se va por OAuth2 con Microsoft. Razón: si el cliente no usa Outlook, sería duplicar trabajo.
- ✅ Storage de credenciales: `keyring` del OS para los secretos, `config.json` ([Core/services/config_service.py](../../Hoteles/Core/services/config_service.py)) para el resto.
- ✅ Datos configurables en la primera versión: remitente, destinatario por defecto, firma personalizada. NO: plantilla de asunto, Reply-To, HTML.

---

## 12. Próximos pasos cuando se decida implementar

1. Confirmar con el cliente final qué proveedor de email usa.
2. Elegir Combo 2 o Combo 3 en base a esa info.
3. Crear plan de implementación detallado (otro documento, no este).
4. Implementar en este orden:
   1. Extender `ConfigService` con las claves nuevas (`email_provider`, `email_user`, `email_from_name`, `email_destinatario_default`, `email_firma`).
   2. Sumar dependencia de `keyring` (común a ambos combos).
   3. Refactorizar `enviar_correo()` en [Core/controller.py](../../Hoteles/Core/controller.py) a una factory de senders (`obtener_sender(config) → Sender`).
   4. Implementar `MailtoSender` (común a ambos combos).
   5. Implementar el sender específico del combo elegido (`ResendSender` o `GmailOAuthSender`).
   6. Modificar [UI/views/modal_email.py](../../Hoteles/UI/views/modal_email.py) para que use el sender configurado.
   7. Activar el contenido de la pestaña "Email" en [UI/views/config_modal.py](../../Hoteles/UI/views/config_modal.py) (hoy es placeholder).
   8. Botón "Probar conexión" en la pestaña Email del modal.

---

## 13. Referencias

- [Google Cloud Console - OAuth setup docs](https://developers.google.com/identity/protocols/oauth2)
- [Resend docs](https://resend.com/docs)
- [SendGrid Python SDK](https://github.com/sendgrid/sendgrid-python)
- [google-auth-oauthlib](https://googleapis.dev/python/google-auth-oauthlib/latest/)
- [Python `keyring` library](https://pypi.org/project/keyring/)
- [Gmail API users.messages.send](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send)
- Conversación de diseño en este chat (fecha 2026-05-21).
