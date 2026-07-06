# Bot de publicación automática en Instagram — Confitería

Publica 4 posts por día en Instagram (desayuno, almuerzo, merienda y cena) con imágenes
de tus productos, editadas
automáticamente con tu nombre/logo. Todo con herramientas gratuitas.

## Flujo

```
Drive: originales/  →  [Pillow: agrega marca de agua]  →  Drive: editadas/ (para revisar)
                                                                 ↓
                                              VOS: arrastrás a mano la que apruebes
                                                                 ↓
                                                        Drive: aprobadas/
                                                                 ↓
                                        [Graph API: publica la MÁS RECIENTE de aprobadas]
                                                                 ↓
                                                        Drive: publicadas/
```

El bot **nunca publica una imagen que no hayas movido vos a `aprobadas`**. Ese
movimiento manual en Drive es el paso de aprobación. Cuando hay varias imágenes
esperando en `aprobadas`, en cada corrida se publica siempre la última que agregaste
(orden: de la más nueva a la más vieja).

Corre 4 veces al día vía GitHub Actions (gratis, hasta 2000 min/mes en repos privados,
ilimitado en repos públicos).

---

## 1. Preparar Instagram + Facebook

1. Convertí tu cuenta de Instagram a **cuenta profesional** (Configuración → Cuenta → Cambiar
   a cuenta profesional → Empresa).
2. Creá o usá una **página de Facebook** y vinculala a tu Instagram (Configuración de
   Instagram → Cuentas vinculadas → Facebook).

## 2. Crear la app en Meta for Developers

1. Andá a https://developers.facebook.com/apps y creá una app tipo **"Empresa"**.
2. Agregá el producto **Instagram Graph API**.
3. En **Herramientas → Explorador de la API Graph**, generá un token de usuario con estos
   permisos: `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`.
4. Con ese token, hacé esta consulta para obtener tu `IG_USER_ID`:
   ```
   GET /me/accounts
   GET /{page_id}?fields=instagram_business_account
   ```
5. **Token de larga duración**: los tokens de usuario duran ~1-2h. Cambialo por uno de
   larga duración (60 días):
   ```
   GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}
   ```
   Nota: a los 60 días hay que renovarlo. Como es gratis y no hay forma de hacerlo
   "permanente" sin costo, poné un recordatorio en el calendario o automatizá la renovación
   más adelante si querés.

Guardá: `IG_USER_ID` y `IG_ACCESS_TOKEN`.

## 3. Google Drive con cuenta de servicio

1. Creá un proyecto en https://console.cloud.google.com
2. Habilitá la **Google Drive API** (APIs y servicios → Habilitar APIs).
3. Creá una **cuenta de servicio** (IAM y administración → Cuentas de servicio → Crear).
4. Generá una clave en formato **JSON** y descargala.
5. **Importante**: la cuenta de servicio tiene su propio "usuario" de Drive. Compartí las
   4 carpetas (`originales`, `editadas`, `aprobadas`, `publicadas`) con el email de la
   cuenta de servicio (algo como `nombre@proyecto.iam.gserviceaccount.com`), con permiso
   de Editor.
6. Anotá el **ID de cada carpeta** (es la parte final de la URL cuando la abrís en Drive:
   `https://drive.google.com/drive/folders/ESTE_ES_EL_ID`).

## 4. Subir el proyecto a GitHub

1. Creá un repositorio (puede ser público o privado; **si es privado**, el hosting temporal
   de imágenes vía `raw.githubusercontent.com` no va a funcionar sin token — ver nota abajo).
2. Subí todos estos archivos al repo.
3. Poné tu logo en `assets/logo.png` (si vas a usar `WATERMARK_MODE = "logo"`) y/o una
   tipografía `.ttf` en `assets/font.ttf` (si vas a usar modo `"text"`; podés bajar una
   gratis de https://fonts.google.com).

### Sobre el hosting temporal de imágenes

La Graph API necesita una URL pública para descargar la imagen. Este proyecto resuelve
esto subiendo la imagen a una carpeta `temp_hosting/` del propio repo y usando la URL
`raw.githubusercontent.com`. **Para que funcione sin autenticación, el repo debe ser
público.** Como las fotos son de tus productos y de todas formas van a terminar públicas
en Instagram, esto no suele ser un problema — pero tenelo en cuenta.

Alternativa si preferís repo privado: usar un servicio gratuito de hosting de imágenes
(ej. un bucket público de Cloudflare R2 o un repo público *aparte* solo para el hosting
temporal). Puedo ayudarte a adaptar el script si preferís esa opción.

## 5. Configurar secretos en GitHub

En tu repo: **Settings → Secrets and variables → Actions → New repository secret**.
Cargá:

| Secreto | Valor |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON_B64` | El JSON de la cuenta de servicio, codificado en base64 (ver comando abajo) |
| `GDRIVE_FOLDER_ORIGINALES` | ID de la carpeta `originales` |
| `GDRIVE_FOLDER_EDITADAS` | ID de la carpeta `editadas` |
| `GDRIVE_FOLDER_APROBADAS` | ID de la carpeta `aprobadas` |
| `GDRIVE_FOLDER_PUBLICADAS` | ID de la carpeta `publicadas` |
| `IG_USER_ID` | ID de tu cuenta de Instagram business |
| `IG_ACCESS_TOKEN` | Token de larga duración |

Para generar el base64 del JSON de la cuenta de servicio:
```bash
base64 -i mi-cuenta-de-servicio.json | tr -d '\n'
```
(en Windows con PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("archivo.json"))`)

## 6. Editar `config.py`

Ajustá al menos:
- `BUSINESS_NAME`
- `WATERMARK_MODE` ("text" o "logo")
- `WATERMARK_POSITION`

## 7. Probar

- Subí una foto de prueba a la carpeta `originales` en Drive.
- Andá a la pestaña **Actions** de tu repo → seleccioná el workflow → **Run workflow**
  (ejecución manual, no hace falta esperar al cron).
- Revisá los logs. Si algo falla, el error va a aparecer ahí (token vencido, permisos de
  Drive, etc.).
- Revisá la carpeta `editadas` en Drive para ver cómo quedó la marca de agua.
- Cuando estés conforme, **mové esa imagen a mano de `editadas` a `aprobadas`** en Drive
  (desde el celular o la compu). Recién ahí queda habilitada para publicarse en la
  próxima corrida del bot.

## Horarios de publicación

Se publican **4 posts por día**, cada uno con un caption acorde al momento (definidos en
`config.py`, sección `CAPTIONS`):

| Franja | Hora (Argentina) | Hora (UTC, la que usa el cron) |
|---|---|---|
| Desayuno | 08:00 | 11:00 |
| Almuerzo | 12:00 | 15:00 |
| Merienda | 15:00 | 18:00 |
| Cena | 18:00 | 21:00 |

Si tu huso horario cambia (horario de verano, etc.) o querés otros horarios, editá los
`cron` en `.github/workflows/publish.yml` — están en UTC — y actualizá también el `case`
que mapea cada cron a su franja (`POST_SLOT`), en el mismo archivo.

También podés probar una franja específica a mano desde la pestaña **Actions → Publicar
posts de Instagram → Run workflow**, eligiendo la franja en el desplegable.

## Límites a tener en cuenta (todo gratuito, pero con límites)

- Graph API: máx. 25 publicaciones por cuenta de Instagram cada 24hs (muy por encima de 3/día).
- El token de acceso de larga duración vence a los 60 días y hay que renovarlo a mano
  (o automatizar la renovación más adelante).
- GitHub Actions: gratis e ilimitado en repos públicos; en privados hay una cuota mensual
  de minutos que este proyecto no debería agotar con 3 corridas cortas por día.

## Pendientes de tu lado

- [ ] Definir nombre final de la confitería y subir el logo a `assets/logo.png`
- [ ] Elegir tipografía y colores de la marca de agua en `config.py`
- [ ] Cargar los secretos en GitHub
- [ ] Compartir las 4 carpetas de Drive con la cuenta de servicio
- [ ] Generar y renovar el token de Instagram cuando corresponda
