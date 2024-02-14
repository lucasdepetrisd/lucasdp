"""
Inicializa la configuración de registro (logging) para Prefect en un script.

Este módulo proporciona funciones para configurar la configuración de registro
(logging) para Prefect, incluyendo la configuración de un TimedRotatingFileHandler
para la rotación de archivos de registro y la aplicación de un formato personalizado
para los mensajes de registro.

Para funcionar correctamente el archivo de configuración de logging debe estar correctamente seteado en 

Funciones:
    - obtener_nombre_script: Devuelve el nombre del script que realiza la llamada.
    - inicializar_logger_prefect: Inicializa el registro para Prefect, incluyendo
                                  la configuración de manejadores de archivos y formateadores.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler

from prefect import runtime
from prefect import logging as prefect_logging
from prefect.logging.formatters import PrefectFormatter


class RemoveSpecificLogs(logging.Filter):
    def filter(self, record):
        # Agrega otras cadenas que deseas filtrar
        # strings_to_exclude = ['Created task run', 'Created flow run', 'Executing', 'Finished in state Completed']
        strings_to_exclude = ['Created task run',
                              'Created flow run', 'Executing']

        # Devuelve False si alguno de los records tiene el string en el mensaje
        return not any(exclude_str in record.msg for exclude_str in strings_to_exclude)

def namer(name):
    return name.replace(".log", "") + ".log"

class PrefectLogger(object):
    """
    Clase para manejar el registro de logs para Prefect.

    Atributos:
        DEFAULT_LOG_PATH (str): Ruta predeterminada para los logs.
        DEFAULT_WHEN (str): Tipo de intervalo para la rotación del archivo (por defecto, 'W0' para semanal).
        DEFAULT_INTERVAL (int): Intervalo entre rotaciones en semanas.
        DEFAULT_BACKUP_COUNT (int): Número de archivos de log de respaldo a retener.

    Métodos:
        __init__(self, scriptname, log_path: str = None):
            Inicializa la instancia de PrefectLogger.

        _initialize_logger(self):
            Inicializa el logger con los parámetros configurados.

        obtener_logger_prefect(self):
            Obtiene el logger de Prefect.

        cambiar_rotfile_handler_params(self, log_path: str = None, 
                                        when: str = DEFAULT_WHEN, 
                                        interval: int = DEFAULT_INTERVAL, 
                                        backup_count: int = DEFAULT_BACKUP_COUNT):
            Cambia los parámetros del manejador de archivos rotativos.

    """

    DEFAULT_LOG_PATH = ""
    DEFAULT_WHEN = 'W0' # Rota el archivo semanalmente los lunes.
    DEFAULT_INTERVAL = 1
    DEFAULT_BACKUP_COUNT = 12
    DEFAULT_FORMATTER = PrefectFormatter(
        format="%(asctime)s | %(levelname)-7s | %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        flow_run_fmt="%(asctime)s | %(levelname)-7s | Flow %(flow_name)r - %(message)s",
        task_run_fmt="%(asctime)s | %(levelname)-7s | Task %(task_name)r - %(message)s"
    )

    def __init__(self, script_path: str, log_path: str = None):
        self.script_path = script_path
        self.script_dir = os.path.dirname(self.script_path)
        self.script_name = os.path.splitext(os.path.basename(script_path))[0]
        self.DEFAULT_LOG_PATH = os.path.join(self.script_dir, 'logs', self.script_name)
        self._log_path = log_path or self.DEFAULT_LOG_PATH

        self._when = self.DEFAULT_WHEN
        self._interval = self.DEFAULT_INTERVAL
        self._backup_count = self.DEFAULT_BACKUP_COUNT
        self.handler = None
        self._logger_prefect = None
        self._run_name = ""

    def _initialize_logger(self):
        if self._log_path is None:
            self._log_path = self.DEFAULT_LOG_PATH

        if not os.path.isdir(os.path.dirname(self._log_path)):
            prefect_logger_aux = prefect_logging.get_run_logger()

            dirs_superiores = os.path.abspath(
                os.path.join(self.DEFAULT_LOG_PATH, "../../../.."))
            path_relativo = os.path.join(
                "~", os.path.relpath(self.script_name, dirs_superiores))

            prefect_logger_aux.info(
                "No se encontro el directorio. Creandolo en la carpeta del script: %s", path_relativo)
            os.mkdir(os.path.dirname(self._log_path))

        self.handler = TimedRotatingFileHandler(
            filename=self._log_path,
            when=self._when,
            interval=self._interval,
            backupCount=self._backup_count
        )

        self.handler.namer = namer

        self.handler.setFormatter(self.DEFAULT_FORMATTER)

        root_logger = logging.getLogger()
        prefect_logger = prefect_logging.get_run_logger()

        # En caso que se ejecute desde la UI o API por un deployment tiene otro logger de prefect por lo que saldran duplicados
        # Para solucionarlo solo configuramos el logger prefect si se ejecuta de manera manual.
        if runtime.deployment.name is None:
        # Check si el handler ya esta presente en prefect_logger.logger.handlers
            prefect_rotfile_handler_present = any(isinstance(
                h, type(self.handler)) for h in prefect_logger.logger.handlers)

            if prefect_rotfile_handler_present:
                # Reemplazar handler existente por el nuevo self.handler
                for i, h in enumerate(prefect_logger.logger.handlers):
                    if isinstance(h, type(self.handler)):
                        prefect_logger.logger.handlers[i] = self.handler
                        break
            else:
                # Añadir handler si no esta
                prefect_logger.logger.addHandler(self.handler)

        # Check si el handler ya esta presente en root_logger.handlers
        root_rotfile_handler_present = any(isinstance(
            h, type(self.handler)) for h in root_logger.handlers)

        if root_rotfile_handler_present:
            # Reemplazar handler existente por el nuevo self.handler
            for i, h in enumerate(root_logger.handlers):
                if isinstance(h, type(self.handler)):
                    root_logger.handlers[i] = self.handler
                    break
        else:
            # Añadir handler si no esta
            root_logger.addHandler(self.handler)

        return prefect_logger

    def obtener_logger_prefect(self):
        """
        Obtiene el logger de Prefect.

        Retorna:
            prefect_logger: Instancia del logger de Prefect.
        """
        # Obtengo el valor del flujo o tarea desde el que se llama la función
        actual_run_name = runtime.task_run.name or runtime.flow_run.name

        if actual_run_name:
            # Si es la primera vez que se llama desde ese flujo o tarea inicializo el logger
            if not self._run_name or self._run_name != actual_run_name:
                self._run_name = actual_run_name
                self._logger_prefect = self._initialize_logger()

        return self._logger_prefect

    def cambiar_rotfile_handler_params(self, log_path: str = DEFAULT_LOG_PATH,
                                       when: str = DEFAULT_WHEN,
                                       interval: int = DEFAULT_INTERVAL,
                                       backup_count: int = DEFAULT_BACKUP_COUNT):
        """
        Cambia los parámetros del manejador de archivos rotativos.

        Parámetros:
            log_path (str): Ruta personalizada para los logs. Si es None, se utiliza DEFAULT_LOG_PATH.
            when (str): Tipo de intervalo para la rotación del archivo.
            interval (int): Intervalo entre rotaciones en semanas.
            backup_count (int): Número de archivos de log de respaldo a retener.

        Retorna:
            prefect_logger: Instancia actualizada del logger de Prefect.
        """
        if not os.path.exists(log_path):
            if self._logger_prefect:
                self._logger_prefect.warning("""Error al cambiar el directorio de salida. No se reconoce el directorio %s.
                                              Se utilizara el predeterminado: %s""", log_path, self.DEFAULT_LOG_PATH)
            else:
                print(f"""Error al cambiar el directorio de salida. No se reconoce el directorio {log_path}.
                      Se utilizara el predeterminado: {self.DEFAULT_LOG_PATH}""")
            self._log_path = self.DEFAULT_LOG_PATH
        else:
            self._log_path = log_path

        self._when = when or self.DEFAULT_WHEN
        self._interval = interval or self.DEFAULT_INTERVAL
        self._backup_count = backup_count or self.DEFAULT_BACKUP_COUNT

        # Reinicializar el logger con los nuevos parámetros
        self._logger_prefect = self._initialize_logger()

        return self._logger_prefect


def obtener_path_script(file_path):
    file_path = os.path.abspath(file_path)
    return file_path
