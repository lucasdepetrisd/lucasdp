from setuptools import setup, find_packages

from electracommons import __version__

# extra_tests = [
#     'tests'
# ]

# extra_dev = [
#     *extra_tests
# ]

setup(
    name='electracommons',
    version=__version__,

    author='Lucas Depetris',
    author_email='lucasdepetris14@gmail.com',
    description='Módulos comunes de los proyectos de Electra',

    # packages=['electracommons'],
    packages=find_packages(), # Busca automáticamente los paquetes en la carpeta actual
    install_requires=[
        'keyring',
        'pandas'
        'prefect',
        'sqlalchemy',
    ], # Dependencias de terceros
    # extras_require={
    #     'dev': extra_dev,
    # } # Dependencias opcionales
)
