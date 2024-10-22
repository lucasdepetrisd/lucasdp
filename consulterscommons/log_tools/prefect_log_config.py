"""
Inicializa la configuración de registro (logging) para Prefect en un script.

Este módulo proporciona funciones para configurar la configuración de registro
(logging) para Prefect, incluyendo la configuración de un TimedRotatingFileHandler
para la rotación de archivos de registro y la aplicación de un formato personalizado
para los mensajes de registro.

Para funcionar correctamente el archivo de configuración de logging debe estar correctamente seteado en la configuración de Prefect.
Chequear la documentación del repositorio prefect-test para más información.

Funciones:
    - obtener_nombre_script: Devuelve el nombre del script que realiza la llamada.
    - inicializar_logger_prefect: Inicializa el registro para Prefect, incluyendo la configuración de manejadores de archivos y formateadores.
"""

import os
import logging

from prefect import runtime
from prefect import logging as prefect_logging
from prefect.logging.formatters import PrefectFormatter

# from consulterscommons.log_tools.parallel_log_rotator import ParallelTimedRotatingFileHandler

class PrefectLogger(object):
    """
    Clase para manejar el registro de logs para Prefect.

    Parámetros:
    - script_path (str): Ruta del script que llama a la clase.
    - log_path (str): Ruta personalizada para los logs.
    - when (str): Tipo de intervalo para la rotación del archivo.
    - interval (int): Intervalo entre rotaciones en semanas.
    - backup_count (int): Número de archivos de log de respaldo a retener.
    - encoding (str): Codificación de caracteres para el archivo de log.

    Atributos:
    - DEFAULT_LOG_PATH (str): Ruta predeterminada para los logs.
    - DEFAULT_WHEN (str): Tipo de intervalo para la rotación del archivo (por defecto, 'W0' para semanal).
    - DEFAULT_INTERVAL (int): Intervalo entre rotaciones en semanas.
    - DEFAULT_BACKUP_COUNT (int): Número de archivos de log de respaldo a retener.
    - DEFAULT_FORMATTER (PrefectFormatter): Formateador predeterminado para los mensajes de log.

    Métodos
    
    - __init__(self, scriptname, log_path: str = None):
        - Inicializa la instancia de PrefectLogger.
    
    - _initialize_logger(self):
        - Inicializa el logger con los parámetros configurados.
    
    - obtener_logger_prefect(self):
        - Obtiene el logger de Prefect.
    
    - cambiar_rotfile_handler_params(self, log_path: str = None, when: str = DEFAULT_WHEN, interval: int = DEFAULT_INTERVAL, backup_count: int = DEFAULT_BACKUP_COUNT):
        - Cambia los parámetros del manejador de archivos rotativos.

    """

    DEFAULT_LOG_PATH = ""
    DEFAULT_WHEN = 'D'
    DEFAULT_INTERVAL = 30
    DEFAULT_BACKUP_COUNT = 12
    DEFAULT_FORMATTER = PrefectFormatter(
        format="%(asctime)s | %(levelname)-7s | %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        flow_run_fmt="%(asctime)s | %(levelname)-7s | Flow %(flow_name)r - %(message)s",
        task_run_fmt="%(asctime)s | %(levelname)-7s | Task %(task_name)r - %(message)s"
    )
    DEFAULT_ENCODING = 'utf-8'

    def __init__(self, script_path: str,
                log_path: str = None,
                when: str = DEFAULT_WHEN,
                interval: int = DEFAULT_INTERVAL,
                backup_count: int = DEFAULT_BACKUP_COUNT,
                encoding: str = DEFAULT_ENCODING
                ):

        self.script_path = script_path
        self.script_dir = os.path.dirname(self.script_path)
        self.script_name = os.path.splitext(os.path.basename(script_path))[0]
        self.DEFAULT_LOG_PATH = os.path.join(
            self.script_dir, 'logs', (self.script_name + '.log'))
        self._log_path = log_path or self.DEFAULT_LOG_PATH

        self._when = when or self.DEFAULT_WHEN
        self._interval = interval or self.DEFAULT_INTERVAL
        self._backup_count = backup_count or self.DEFAULT_BACKUP_COUNT
        self._encoding = encoding or self.DEFAULT_ENCODING

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

        self.handler = logging.handlers.TimedRotatingFileHandler(
            filename=self._log_path,
            when=self._when,
            interval=self._interval,
            backupCount=self._backup_count,
            encoding=self._encoding,
        )

        self.handler.namer = lambda name: name.replace(".log", "") + ".log"

        self.handler.setFormatter(self.DEFAULT_FORMATTER)

        root_logger = logging.getLogger()
        prefect_logger = prefect_logging.get_run_logger()

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

        # En caso que se ejecute desde la UI o API por un deployment tiene otro logger de prefect por lo que saldran duplicados
        # Para solucionarlo solo configuramos el logger prefect si se ejecuta de manera manual.
        # if runtime.deployment.name is None:
        if runtime.deployment.name is None:
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
        else:
            raise ValueError("No se pudo obtener el nombre del flujo o tarea. Verifique que se esta intentando obtener el logger desde un flujo o tarea de Prefect.")

    def cambiar_rotfile_handler_params(self, log_path: str = DEFAULT_LOG_PATH,
                                    when: str = DEFAULT_WHEN,
                                    interval: int = DEFAULT_INTERVAL,
                                    backup_count: int = DEFAULT_BACKUP_COUNT,
                                    encoding: str = DEFAULT_ENCODING):
        """
        Cambia los parámetros del manejador de archivos rotativos.

        Parámetros:
            log_path (str): Ruta personalizada para los logs. Si es None, se utiliza DEFAULT_LOG_PATH.
            when (str): Tipo de intervalo para la rotación del archivo.
            interval (int): Intervalo entre rotaciones en semanas.
            backup_count (int): Número de archivos de log de respaldo a retener.
            encoding (str): Codificación de caracteres para el archivo de log.

        Retorna:
            prefect_logger: Instancia actualizada del logger de Prefect.
        """

        if log_path not in (self.DEFAULT_LOG_PATH, '', None):
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
        self._encoding = encoding or self.DEFAULT_ENCODING

        # Reinicializar el logger con los nuevos parámetros
        self._logger_prefect = self._initialize_logger()

        return self._logger_prefect


def obtener_path_script(file_path):
    file_path = os.path.abspath(file_path)
    return file_path


class RemoveSpecificLogs(logging.Filter):
    """
    NO ES PARA USO DIRECTO EN EL CÓDIGO.
    Este filtro está diseñado para ser utilizado por Prefect en su archivo de configuración de loggers YAML.

    Filtro personalizado para excluir registros específicos en los registros de registro.
    Este filtro se utiliza para excluir registros que contienen ciertas cadenas en el mensaje.
    Se proporciona una lista de cadenas a excluir y el filtro devolverá False si alguno de los registros tiene una de esas cadenas en el mensaje.

    Atributos:
        - strings_to_exclude (list): Lista de cadenas a excluir en los registros.
    Métodos:
        - filter(record): Método para filtrar los registros de registro.
    """
    def filter(self, record):
        # Agrega otras cadenas que deseas filtrar
        # strings_to_exclude = ['Created task run', 'Created flow run', 'Executing', 'Finished in state Completed']
        strings_to_exclude = ['Submitted task run', 'Created task run', 'Finished in state Completed',
                            'Created flow run', 'Executing']

        # Devuelve False si alguno de los records tiene el string en el mensaje
        return not any(exclude_str in record.msg for exclude_str in strings_to_exclude)


class RemoveUnicodeErrorLogs(logging.Filter):
    """
    NO ES PARA USO DIRECTO EN EL CÓDIGO.
    Este filtro está diseñado para ser utilizado por Prefect en su archivo de configuración de loggers YAML.

    Filtro personalizado para excluir el log de error Unicode que es una falsa alarma y debe ser ignorado.

    Atributos:
        - strings_to_exclude (list): Lista de cadenas a excluir en los registros.
    Métodos:
        - filter(record): Método para filtrar los registros de registro.
    """
    def filter(self, record):
        # Agrega otras cadenas que deseas filtrar
        # strings_to_exclude = ['Created task run', 'Created flow run', 'Executing', 'Finished in state Completed']
        strings_to_exclude = ["UnicodeDecodeError: 'utf-8' codec can't decode byte"]

        # Devuelve False si alguno de los records tiene el string en el mensaje
        return not any(exclude_str in record.msg for exclude_str in strings_to_exclude)