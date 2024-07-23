"""
Módulo para establecer una conexión a una base de datos SQL Server.
Utiliza Prefect para el manejo de logs y keyring para la obtención de contraseñas.
"""

import pyodbc
import keyring as kr
from prefect import task

from consulterscommons.log_tools.prefect_log_config import PrefectLogger

logger_global = PrefectLogger(__file__)


@task(retries=2, retry_delay_seconds=5)
def connect_sql_server(server: str, database: str, username: str, password: str = None) -> (pyodbc.Connection | str):
    """
    Inicializa una conexión a la base de datos SQL Server.

    Args:
        server (str): El nombre del servidor SQL Server.
        database (str): El nombre de la base de datos.
        username (str): El nombre de usuario para la conexión.
        password (str, optional): La contraseña para la conexión. Si no se proporciona, se buscará en el Credential Manager. Defaults to None.

    Returns:
        pyodbc.Connection: La conexión a la base de datos SQL Server si se establece correctamente.
        str: Un mensaje de error si no se pudo establecer la conexión.

    Raises:
        kr.errors.KeyringError: Se produce si no se encuentran las credenciales en el Credential Manager.
        pyodb.Error: Se produce si hay un error al conectar a la base de datos.
    """

    logger = logger_global.obtener_logger_prefect()

    if password is None:
        credencial = kr.get_credential(server, username)
        if credencial:
            username = credencial.username
            password = credencial.password
            logger.info("Se obtuvieron las credenciales para %s", username)
        else:
            error_msg = f"No se encontraron credenciales para {username} en el Credential Manager"
            logger.warning(error_msg)
            raise kr.errors.KeyringError(error_msg)

    try:
        # Conexión a SQL Server
        conecc_sql = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
        logger.info("Conectado exitosamente a SQL Server")

    except pyodbc.Error as connect_err:
        error_msg = f"Error al conectar a la base de datos: {str(connect_err)}"
        logger.error(error_msg)
        raise
    except Exception as generic_err:  # pylint: disable=broad-except
        error_msg = f"Error inesperado: {str(generic_err)}"
        logger.error(error_msg)
        raise

    return conecc_sql
