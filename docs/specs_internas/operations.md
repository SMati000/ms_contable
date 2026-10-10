Por el momento, este proyecto no tiene CI/CD automatizado. Se documentan aca los criterios y pasos que se realizan manualmente.

# Releases

- Validar que pasan exitosamente todos los tests.

- Cambiar la version en el Proyecto (`settings.VERSION`)

- DEBUG = False

- Eliminar las migraciones intermedias que son propias de la etapa de desarrollo, pero que no fueron lanzadas para que usen los usuarios.
    - Ejecutar `python manage.py makemigrations`

- Generar imagen Docker y subirla a [Dockerhub](https://hub.docker.com/repository/docker/matiasschulz/ms_contable/tags)
    - python manage.py collectstatic
    - crear imagen:
        ```shell
        docker build -t matiasschulz/ms_contable:0.1.0 .
        docker push matiasschulz/ms_contable:0.1.0
        docker tag matiasschulz/ms_contable:0.1.0 matiasschulz/ms_contable:latest
        docker push matiasschulz/ms_contable:latest
        ```

- Generar, en el repositorio de Github, Tag con la version y Release con sus artefactos y release notes \
Artefactos:
    - Archivos minimos para instalacion/uso (formato de nombre: ms_contable-vX.Y.Z-windows.zip)
        - dir instalacion/ - cambiar .env.example por .env con la version especifica
    - Release notes
    - Codigo fuente

# Extras

### Comandos utiles de Django

```shell
python manage.py startapp {app_name}
python manage.py makemigrations
python manage.py makemigrations --empty <nombre_app>
python manage.py migrate
python manage.py migrate zero
python manage.py migrate zero --fake
python manage.py migrate 0001
python manage.py createsuperuser
python manage.py runserver
python manage.py squashmigrations {app_name} {start_migration} {end_migration}
python manage.py shell; # importlib
python manage.py test
python manage.py collectstatic
```

### Instancia aislada para pruebas

Iniciar desde la raíz del proyecto:

```shell
python -m ms_contable.run_test_instance
```

La instancia solo se inicia cuando `DEBUG = True` en `ms_contable/settings.py`. Migra `data/db_test.sqlite3` y garantiza la cuenta superusuario `test` con contraseña `test`. El login está en `http://127.0.0.1:8001/`; tras iniciar sesión, el panel se abre en `/test/`. Si ese puerto está ocupado, se puede cambiar con `MS_CONTABLE_TEST_PORT`.

Esta instancia usa una configuración Django y una base SQLite propias, por lo que los cambios que se hagan ahí no se guardan en `data/db.sqlite3`. Para cambiar las credenciales predeterminadas se pueden definir `MS_CONTABLE_TEST_USERNAME` y `MS_CONTABLE_TEST_PASSWORD`.
