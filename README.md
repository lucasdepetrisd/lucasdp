# Paquete electracommons
Conjunto de scripts comunes a los proyectos de Electra

Este paquete proporciona scripts comunes que se pueden reutilizar en varios proyectos. Incluye funcionalidades para configuración de registros (logging). 
<!-- y gestión de correos electrónicos. -->

## Estructura del Proyecto

electracommons/  
├── init.py  
├── log_config.py  
<!-- ├── emails_manager.py   -->

## Uso

### Configuración de Registros (logging)

```python
# Uso del módulo de configuración de registros
from commonscripts import log_config

log_config.configure_logger()
```

## TODO

* Agregar modulo de configuración de emails.

<!-- ### Configuración de Correos

```python
# Uso del módulo de gestión de correos electrónicos
from commonscripts import emails_manager

emails_manager.send_email(recipient='destinatario@example.com', subject='Asunto', body='Cuerpo del correo')
``` -->