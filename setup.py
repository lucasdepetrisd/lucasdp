from setuptools import setup, find_packages

from consulterscommons import __version__

# extra_tests = [
#     'tests'
# ]

# extra_dev = [
#     *extra_tests
# ]

setup(
    name='consulterscommons',
    version=__version__,

    author='Lucas Depetris',
    author_email='lucasdepetris14@gmail.com',
    description='Módulos comunes de los proyectos de Consulters',

    # packages=['consulterscommons'],
    packages=find_packages(), # Busca automáticamente los paquetes en la carpeta actual
    install_requires=[
        'keyring',
        'pandas',
        'prefect',
        'sqlalchemy',
    ], # Dependencias de terceros
    # extras_require={
    #     'dev': extra_dev,
    # } # Dependencias opcionales
)
