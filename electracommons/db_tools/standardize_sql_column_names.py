"""
Módulo para estandarizar los nombres de las columnas de una tabla SQL.
"""

import re
import string
import unicodedata

def standardize_sql_column_names(original_col_names: list, remove_punct: bool = True):
    """
    Estandariza los nombres de las columnas eliminando la puntuación, normalizando los caracteres unicode,
    convirtiéndolos a mayúsculas, reemplazando los espacios por guiones bajos y eliminando guiones bajos consecutivos.

    Args:
        original_col_names (list): Una lista de nombres de columnas originales.
        remove_punct (bool, opcional): Bandera para indicar si se debe eliminar la puntuación. Por defecto es True. Ejemplo: 'Producción' -> 'PRODUCCION'

    Returns:
        list: Una lista de nombres de columnas estandarizados.
    
    Ejemplo:
    ```python
        original_col_names = ['Ramón', '''Ho?a sóy
                               u=a c/lumn4''', 'CoLuMN~W1th!-Spé&ciál-Cháractérs   ', '''Ánother-Çolumn
                               ''', 'Yét_Another-Çolumn']
        standardized_col_names = standardise_column_names(original_col_names)
        print(standardized_col_names)
        # Salida: ['RAMON', 'HOYA_SOY_U_A_C_LUMN4', 'COLUMN_W1TH_SPECIAL_CHARACTERS', 'ANOTHER_COLUMN', 'YET_ANOTHER_COLUMN']
    ```
    """

    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    standardized_col_names = []

    for c in original_col_names:
        c_mod = c.replace('\n', '').strip()
        c_mod = ''.join(char for char in unicodedata.normalize('NFKD', c_mod) if not unicodedata.combining(char))
        c_mod = c_mod.upper()

        if remove_punct:
            c_mod = c_mod.translate(translator)

        c_mod = '_'.join(c_mod.split(' '))

        if c_mod[-1] == '_':
            c_mod = c_mod[:-1]

        c_mod = re.sub(r'\_+', '_', c_mod)
        standardized_col_names.append(c_mod)

    return standardized_col_names

if __name__ == '__main__':
    pass
    # Casos de prueba
    # original_col_names = ['Ramón', '''Ho?a sóy
    #                        u=a c/lumn4''', 'CoLuMN~W1th!-Spé&ciál-Cháractérs   ', '''Ánother-Çolumn
    #                        ''', 'Yét_Another-Çolumn']
    # standardized_col_names = standardise_column_names(original_col_names)
    # print(standardized_col_names)
