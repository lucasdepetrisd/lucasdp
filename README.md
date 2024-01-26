# Paquete electracommons
Conjunto de scripts comunes a los proyectos de Electra

Este paquete proporciona scripts comunes que se pueden reutilizar en varios proyectos. Incluye funcionalidades para configuración de registros (logging). 
<!-- y gestión de correos electrónicos. -->

## Estructura del Proyecto

electracommons/  
├── init.py  
├── log_config.py  
├── emails_handler.py
├── sql_handler.py

## Uso

### Configuración de Registros (logging)

```python
from prefect import flow, task

from electracommons.log_config import PrefectLogger

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

## TODO

* Agregar modulo de configuración de emails.
* Probar y mejorar manejador de scripts SQL.

<!-- ### Configuración de Correos

```python
# Uso del módulo de gestión de correos electrónicos
from commonscripts import emails_manager

emails_manager.send_email(recipient='destinatario@example.com', subject='Asunto', body='Cuerpo del correo')
``` -->
