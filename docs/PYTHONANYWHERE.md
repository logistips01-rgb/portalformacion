# Publicar la demo en PythonAnywhere (gratis)

Sirve para **ver y probar el portal desde cualquier móvil u ordenador** mientras se preparan los cursos. Cuando esté validado, el portal pasa a Informática (ver [INFORMATICA.md](INFORMATICA.md)) junto con lo que se haya cargado aquí.

Condiciones del plan gratuito:
- No pide tarjeta.
- La web está siempre encendida y los datos se guardan.
- La dirección será `https://TUUSUARIO.pythonanywhere.com`.
- **Hay que entrar una vez cada 3 meses** y pulsar un botón para que siga activa (avisan por correo).

Se tarda unos 15 minutos y solo se hace una vez.

---

## 1. Crear la cuenta

1. Entra en <https://www.pythonanywhere.com> y pulsa **Pricing & signup** y después **Create a Beginner account** (gratis).
2. El nombre de usuario que elijas formará la dirección web, por ejemplo `formacionaldelis` daría `formacionaldelis.pythonanywhere.com`.

## 2. Crear una llave de GitHub (para descargar el código)

El repositorio es privado, así que PythonAnywhere necesita permiso de solo lectura:

1. En GitHub: foto de perfil → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. Rellena estos campos:
   - Nombre: `pythonanywhere-formacion`.
   - Caducidad: 90 días o más.
   - **Repository access**: *Only select repositories* → `portalformacion`.
   - **Permissions** → *Contents*: **Read-only**.
3. Pulsa **Generate token** y copia la llave. Empieza por `github_pat_`.

## 3. Crear la web vacía

En PythonAnywhere:

1. Ve a la pestaña **Web** y pulsa **Add a new web app** → **Next**.
2. Elige **Manual configuration** (¡no «Django»!).
3. Elige la versión de Python **más alta** de la lista → **Next**.

## 4. Instalar el portal

En PythonAnywhere, pestaña **Consoles** → **Bash**. Pega estos comandos uno a uno.

Descarga el código. Cuando pida *Username*, pon tu usuario de GitHub; cuando pida *Password*, pega la llave del paso 2 (no se ve al pegarla, es normal):

```bash
git clone -b claude/gifted-hamilton-f6zkyz https://github.com/logistips01-rgb/portalformacion.git
```

Para que no vuelva a pedir la llave en las actualizaciones:

```bash
git -C portalformacion config credential.helper store
```

Instala:

```bash
bash portalformacion/despliegue/pythonanywhere.sh
```

Tarda un par de minutos. Al final muestra:
- la **contraseña del usuario `admin`**: apúntala;
- dos datos para el paso siguiente.

## 5. Terminar la configuración de la web

En la pestaña **Web**:

1. **Virtualenv**: pulsa *Enter path to a virtualenv* y pega la ruta que mostró el script, por ejemplo `/home/TUUSUARIO/.virtualenvs/portalformacion`.
2. **Static files**: en la primera fila escribe:
   - URL: `/static/`
   - Directory: `/home/TUUSUARIO/portalformacion/staticfiles`
3. **Force HTTPS**: actívalo.
4. Pulsa el botón verde **Reload**.

Vuelve a la consola Bash y ejecuta otra vez el instalador. Ahora detecta la web y la deja lista:

```bash
bash portalformacion/despliegue/pythonanywhere.sh
```

Abre `https://TUUSUARIO.pythonanywhere.com`.

---

## Accesos de la demo

| Quién | Usuario | Clave |
|---|---|---|
| Administración / RR. HH. | `admin` | la que mostró el instalador (también en el archivo `portalformacion/.env`) |
| Operaria de Recepción | DNI `11111111H` | PIN `123456` |
| Operario de Expediciones | DNI `22222222J` | PIN `123456` |
| Transportista externo | DNI `33333333P` | PIN `123456` |

Cambia la contraseña de `admin` desde *Gestión* → *Cambiar contraseña*.

## Actualizar cuando haya cambios

Cada vez que se suban mejoras a GitHub, en la consola Bash de PythonAnywhere:

```bash
bash portalformacion/despliegue/pythonanywhere.sh
```

Trae los cambios y recarga la web. **No borra** los cursos, preguntas ni usuarios que hayáis creado.

## Avisos

- Es una **demo**: no metáis datos personales reales de empleados (DNI, nombres) hasta que Informática lo monte en los servidores de la empresa.
- El plan gratuito permite 512 MB de archivos. Sobra para unos cuantos temarios en PDF, pero no para muchos vídeos: para los vídeos usad un enlace de SharePoint o Stream en el tema.
- Si en la pestaña **Web** aparece *«This site will be disabled on…»*, pulsa **Run until 3 months from today**.
