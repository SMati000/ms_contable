# MS Contable — Instalación

## Requisitos

* Docker instalado y ejecutándose.
    * Si usa windows: [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)
* Conexión a Internet durante la instalación y las actualizaciones.

## Instalación

1. Descargar el paquete de instalación correspondiente a la versión.
2. Extraer el archivo ZIP de instalacion para Windows o Linux segun sea necesario.
3. Abrir la terminal en la carpeta `instalacion`.
4. Ejecutar el archivo `run.ps1` o `run.sh` segun corresponda
5. Seleccionar la opción **3. Instalar**.
6. Ingresar el usuario y contraseña del administrador cuando sean solicitados.

El instalador descargará automáticamente la versión indicada en el archivo `.env`, ejecutará las migraciones de la base de datos y pondrá en funcionamiento la aplicación.

En el primer inicio, el instalador genera una clave secreta aleatoria y la guarda en `.env`. Conservá ese archivo en privado: la clave no debe compartirse ni publicarse.

Una vez finalizada la instalación, acceder desde el navegador a:

```text
http://localhost:8000
```

## Uso

Ejecutar nuevamente el archivo `run.ps1` o `run.sh` segun corresponda

El menú permite:

1. Iniciar la aplicación.
2. Detener la aplicación.
3. Instalar.
4. Actualizar.
5. Desinstalar.
6. Ver el estado de la instalación.
7. Salir.

Si usa Docker Desktop en Windows, iniciar y detener el sistema puede resultar mas comodo desde su interfaz gráfica.

## Actualización

Para actualizar a una nueva versión:

1. Descargar el paquete de instalación de la nueva versión.
2. Reemplazar los archivos de instalación por los correspondientes a la nueva versión.
3. Ejecutar el archivo `run.ps1` o `run.sh` segun corresponda

4. Seleccionar **4. Actualizar**.

Antes de ejecutar las migraciones, el sistema realiza automáticamente un backup de la base de datos.

Se conservan hasta dos backups:

```text
data/
├── db.sqlite3
├── db.sqlite3.1.bak
└── db.sqlite3.2.bak
```

La actualización no elimina los datos existentes de la aplicación.

## Datos y logs

Los datos persistentes se almacenan en el directorio `data`:

```text
data/
└── db.sqlite3
```

Los logs se almacenan en:

```text
logs/
└── app.log
```

Estos directorios permanecen al actualizar o desinstalar la aplicación.

**No eliminar ni modificar manualmente `data/db.sqlite3`.**

## Desinstalación

Ejecutar el archivo `run.ps1` o `run.sh` segun corresponda

y seleccionar **5. Desinstalar**.

La desinstalación elimina los containers de Docker, pero conserva:

* La base de datos.
* Los backups de la base de datos.
* Los logs.

Esto permite reinstalar posteriormente la aplicación sin perder los datos.

## Solución de problemas

### Docker no está disponible

Si el instalador indica que Docker no está disponible:

1. Verificar que Docker esté instalado.
2. Si esta en Windows, asegurese de tener Docker Desktop abierto.
3. Esperar hasta que indique que Docker está funcionando.

### La aplicación no inicia

Ejecutar el archivo `run.ps1` o `run.sh` segun corresponda

y seleccionar **6. Ver estado**.

### El puerto 8000 está ocupado

Modificar el valor de `PORT` en `.env`:

```env
PORT=8001
```

Luego iniciar nuevamente la aplicación y acceder a:

```text
http://localhost:8001
```

## Soporte

Reportar problemas [acá](https://github.com/SMati000/ms_contable/issues). Incluir:

* Versión de la aplicación.
* Sistema operativo.
* Versión de Docker.
* Mensaje de error mostrado.
* Salida de **6. Ver estado**.
* Logs relevantes de la aplicación.
