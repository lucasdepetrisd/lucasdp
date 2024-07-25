# Paquete consulterscommons
Conjunto de scripts comunes a los proyectos de consulters

Este paquete proporciona scripts comunes que se pueden reutilizar en varios proyectos. Incluye funcionalidades para configuración de registros (logging) y conexión a base de datos. 
<!-- y gestión de correos electrónicos. -->

## Estructura del Proyecto

consulterscommons/  
├── init.py  

## Uso

### Configuración de Registros (logging)

```python
from prefect import flow, task

from consulterscommons.log_tools import PrefectLogger

logger_global = PrefectLogger(__file__)

@task
def mi_tarea(mensaje_tarea: str = ""):
    logger = logger_global.obtener_logger_prefect()
    logger.info("Iniciando tarea...")
    logger.info("Hola %s desde la tarea", mensaje_tarea)
    
    # Cambio el archivo de salida
    logger = logger_global.cambiar_rotfile_handler_params(r"C:\src\logeo\logs\hola.log")
    logger.info("Tarea finalizada...")

@flow
def mi_flujo(mensaje_flujo: str = ""):
    logger = logger_global.obtener_logger_prefect()
    logger.info("Hola %s desde el flujo", mensaje_flujo)
    mi_tarea(mensaje_flujo)

if __name__ == '__main__':
    mi_flujo()
```

## ¿Como colaborar en el proyecto?
### 1. Clonar el repositorio

```bash
git clone https://github.com/Technological-Consulters/consulterscommons.git
cd consulterscommons
```

### 2. Crear una rama nueva
```bash
git checkout -b nombre_de_tu_rama
```

### 3. Realizar mejoras y hacer un commit
```bash
git add .
git commit -m "Descripción clara de las mejoras realizadas"
```

### 4. Subir los cambios
```bash
git push origin nombre_de_tu_rama
```

### 5. Crear un Pull Request (PR)
Desde GitHub creá un pull request.

Podes seguir la sig. guía: [Como crear un pull request | GitHub](https://docs.github.com/es/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request#creating-the-pull-request)

### 6. Incorporación de cambios
Luego de que un admin del repositorio acepte el PR este usuario deberá cambiar la versión del archivo consulterscommons/__init__.py
Al cambiar la versión y hacer un commit en la rama principal se considerará como una nueva versión del repositorio y podra ser instalada utilizando el comando:

```bash
pip install git+https://github.com/Technological-Consulters/consulterscommons.git
```

Finalmente se puede borrar la rama mergeada para limpiar el repositorio.

## TODO

- [ ] Actualizar documentacion de nuevos modulos en este README

- [ ] Probar y mejorar manejador de scripts SQL.
    - [ ] Agregar ejemplo funcional
- [ ] Agregar modulo de configuración de emails.

<!-- ### Configuración de Correos

```python
# Uso del módulo de gestión de correos electrónicos
from commonscripts import emails_manager

emails_manager.send_email(recipient='destinatario@example.com', subject='Asunto', body='Cuerpo del correo')
``` -->
