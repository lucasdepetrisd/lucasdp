from setuptools import setup, find_packages

from lucasdp import __version__


# extra_tests = [
#     'tests'
# ]

# extra_dev = [
#     *extra_tests
# ]

setup(
    name='lucasdp',
    version=__version__,

    author='Lucas Depetris',
    author_email='lucasdepetris14@gmail.com',
    description='Modulos comunes para proyectos de datos',

    # packages=['lucasdp'],
    packages=find_packages(), # Busca automáticamente los paquetes en la carpeta actual
    # Dependencias de terceros
    install_requires=[
        'keyring',
        'pandas',
        'prefect',
        'sqlalchemy',
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    # extras_require={
    #     'dev': extra_dev,
    # } # Dependencias opcionales
)
