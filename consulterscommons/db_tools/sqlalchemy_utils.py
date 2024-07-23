"""
Módulo para establecer una conexión a una base de datos SQL Server con SQLAlchemy.
Además reune funciones comunes para la manipulación de datos.

Utiliza Prefect para el manejo de logs y keyring para la obtención de contraseñas.
"""

import keyring as kr
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy import MetaData
import pandas as pd
from prefect import task

from consulterscommons.log_tools.prefect_log_config import PrefectLogger

logger_global = PrefectLogger(__file__)


@task(retries=2, retry_delay_seconds=5)
def get_sqlalchemy_engine(server: str, database: str, username: str, password: str = None) -> sqlalchemy.engine.base.Engine:
    """
    Inicializa una conexión a la base de datos SQL Server utilizando SQLAlchemy.

    Args:
        server (str): El nombre del servidor SQL Server.
        database (str): El nombre de la base de datos.
        username (str): El nombre de usuario para la conexión.
        password (str, opcional): La contraseña para la conexión. Si no se proporciona, se buscará en el Credential Manager. Por defecto es None.

    Returns:
        sqlalchemy.engine.base.Engine: El motor SQLAlchemy si la conexión se establece correctamente.
        str: Un mensaje de error si no se pudo establecer la conexión.

    Raises:
        kr.errors.KeyringError: Se produce si no se encuentran las credenciales en el Credential Manager.
        SQLAlchemyError: Se produce si hay un error al conectar a la base de datos.
    """

    logger = logger_global.obtener_logger_prefect()

    if password is None:
        credencial = kr.get_credential(server, username)
        if credencial:
            username = credencial.username
            password = credencial.password
            logger.info("Credentials obtained for %s", username)
        else:
            error_msg = f"Credentials not found for {username} in the Credential Manager"
            logger.warning(error_msg)
            raise kr.errors.KeyringError(error_msg)

    try:
        # Create SQLAlchemy engine
        connection_string = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )

        connection_url = sqlalchemy.URL.create(
            "mssql+pyodbc",
            query={"odbc_connect": connection_string}
        )

        engine = create_engine(connection_url)

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Conectado exitosamente a SQL Server con SQLAlchemy.")

    except sqlalchemy.exc.SQLAlchemyError as connect_err:
        error_msg = f"Error al conectar a la base de datos: {str(connect_err)}"
        logger.error(error_msg)
        raise
    except Exception as generic_err:
        error_msg = f"Error inesperado: {str(generic_err)}"
        logger.error(error_msg)
        raise

    return engine


def check_if_table_exists(engine: sqlalchemy.engine.base.Engine, table_name: str, schema: str) -> bool:
    inspector = inspect(engine)
    return inspector.has_table(table_name, schema=schema)


@task
def get_columns_to_add(df: pd.DataFrame, engine: sqlalchemy.engine.base.Engine, table_name: str, schema: str) -> dict:
    """
    Obtiene las columnas faltantes a agregar a una tabla en la base de datos si no existen en el esquema actual.

    Args:
        df (pandas.DataFrame): El DataFrame que contiene los datos.
        engine (sqlalchemy.engine.base.Engine): El motor SQLAlchemy para la conexión a la base de datos.
        table_name (str): El nombre de la tabla.
        schema (str): El nombre del esquema de la tabla.

    Returns:
        dict: Un diccionario que contiene las columnas a agregar como claves y sus tipos de datos como valores.

    Raises:
        sqlalchemy.exc.NoSuchTableError: Se produce si la tabla no se encuentra en la base de datos.
    """

    logger = logger_global.obtener_logger_prefect()

    # Refleja el esquema de la base de datos existente
    metadata = MetaData()
    metadata.reflect(engine)
    table_name_with_schema = f'{schema}.{table_name}'

    # Obtiene información de la tabla utilizando Inspector
    inspector = inspect(engine)

    if check_if_table_exists(engine, table_name, schema) is False:
        logger.warning("No se encontró la tabla '%s' en la base de datos. No se pueden agregar columnas.", table_name_with_schema)
        return {}

    existing_columns = inspector.get_columns(table_name, schema=schema)
    existing_column_names = [col['name'] for col in existing_columns]

    # Determina las columnas a agregar basándose en las columnas del DataFrame
    columns_to_add = {}
    for column in df.columns:
        if column not in existing_column_names:
            # Determina el tipo de columna basándose en los tipos de datos del DataFrame
            if pd.api.types.is_integer_dtype(df[column]):
                column_type = 'INTEGER'
            elif pd.api.types.is_float_dtype(df[column]):
                column_type = 'FLOAT'
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                column_type = 'DATETIME'
            else:
                column_type = 'NVARCHAR(MAX)'  # Por defecto, se asume tipo String

            columns_to_add[column] = column_type

    return columns_to_add


@task
def add_columns_to_table(columns_to_add: dict, engine: sqlalchemy.engine.base.Engine, table_name: str, schema: str) -> None:
    """
    Agrega las columnas faltantes a una tabla en la base de datos.

    Args:
        columns_to_add (dict): Un diccionario que contiene las columnas a agregar como claves y sus tipos de datos como valores.
        engine (sqlalchemy.engine.base.Engine): El motor SQLAlchemy para la conexión a la base de datos.
        table_name (str): El nombre de la tabla.
        schema (str): El nombre del esquema de la tabla.

    Raises:
        sqlalchemy.exc.NoSuchTableError: Se produce si la tabla no se encuentra en la base de datos.
    """

    logger = logger_global.obtener_logger_prefect()

    table_name_with_schema = f'{schema}.{table_name}'

    # Agrega las columnas faltantes a la tabla
    if columns_to_add:
        for column_name, column_type in columns_to_add.items():
            with engine.connect() as connection:
                # Construye la consulta SQL para agregar la columna
                sql_query = text(f"ALTER TABLE {table_name_with_schema} ADD {column_name} {column_type}")
                connection.execute(sql_query)
                connection.commit()

            logger.info("Se agregó la columna '%s' de tipo '%s' a la tabla '%s'", column_name, column_type, table_name_with_schema)
    else:
        logger.info("No es necesario agregar columnas.")


@task
def get_only_new_rows(df_new: pd.DataFrame, engine: sqlalchemy.engine.base.Engine, table_name: str, table_schema: str, columns_to_compare: list[str]):
    """
    Compara los datos de un DataFrame con los datos actuales en una tabla en el Data Warehouse y devuelve solo las filas nuevas.

    Args:
    - engine: Objeto SQLAlchemy Engine que representa la conexión a la base de datos.
    - df_new: DataFrame que contiene los datos nuevos a comparar.
    - table_name: Nombre de la tabla en el Data Warehouse.
    - table_schema: Esquema de la tabla en el Data Warehouse.
    - columns_to_compare: Lista de columnas a utilizar para la comparación.

    Returns:
    DataFrame que contiene solo las filas nuevas encontradas en df_new en comparación con los datos actuales en la tabla del Data Warehouse.
    """

    # Validaciónes de tipos de datos
    if not isinstance(df_new, pd.DataFrame):
        raise TypeError("df_new debe ser un DataFrame de pandas.")

    if not isinstance(engine, sqlalchemy.engine.base.Engine):
        raise TypeError("engine debe ser un objeto SQLAlchemy Engine.")

    if not isinstance(table_name, str):
        raise TypeError("table_name debe ser un string.")

    if not isinstance(table_schema, str):
        raise TypeError("table_schema debe ser un string.")

    if not isinstance(columns_to_compare, list):
        if isinstance(columns_to_compare, pd.Index):
            columns_to_compare = columns_to_compare.tolist()
        else:
            raise TypeError("columns_to_compare debe ser una lista de strings.")

    columns_df_new = df_new.columns.tolist()

    if not all(col in columns_df_new for col in columns_to_compare):
        raise ValueError("Las columnas a comparar deben estar presentes en el DataFrame df_new.")

    columns_str = ', '.join(columns_to_compare)

    # Paso 1: Obtener los datos actuales de la tabla en el DW
    query = f"""
    SELECT {columns_str}
    FROM {table_schema}.{table_name}
    """
    df_existing = pd.read_sql_query(query, engine)

    # Paso 2: Comparar los datos de df_new con los datos actuales en el DW
    df_merge = pd.merge(df_new, df_existing, on=columns_to_compare, how='left', indicator=True)
    df_only_new = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge'])

    return df_only_new
