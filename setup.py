from setuptools import setup, find_packages
from cbpi import __version__
import platform

# read the contents of your README file
from os import popen

localsystem = platform.system()
raspberrypi=False
if localsystem == "Linux":
    command="cat /proc/cpuinfo | grep Raspberry"
    model=popen(command).read()
    if len(model) != 0:
        raspberrypi=True


setup(name='cbpi',
      version=__version__,
      description='CraftBeerPi',
      author='Manuel Fritsch',
      author_email='manuel@craftbeerpi.com',
      url='http://web.craftbeerpi.com',
      packages=find_packages(),
      include_package_data=True,
      package_data={
        # If any package contains *.txt or *.rst files, include them:
      '': ['*.txt', '*.rst', '*.yaml'],
      'cbpi': ['*','*.txt', '*.rst', '*.yaml']},

      python_requires='>=3.9',

      install_requires=[
          "aiohttp>=3.9.0,<4.0.0",
          "aiohttp-auth==0.1.1",
          "aiohttp-route-decorator==0.1.4",
          "aiohttp-security==0.4.0",
          "aiohttp-session>=2.12.0,<3.0.0",
          "aiohttp-swagger==1.0.16",
          "aiojobs==1.0.0",
          "aiosqlite>=0.19.0,<1.0.0",
          "cryptography>=41.0.0,<43.0.0",
          "requests>=2.31.0,<3.0.0",
          "voluptuous>=0.13.0,<0.14.0",
          "pyfiglet==0.8.post1",
          'click>=8.1.0,<9.0.0',
          'shortuuid>=1.0.8,<2.0.0',
          'tabulate>=0.9.0,<1.0.0',
          'asyncio-mqtt>=0.16.0,<1.0.0',
          # 'PyInquirer==1.0.3',  # Removed - not compatible with Python 3.13, using standard input() instead
          'colorama>=0.4.6,<1.0.0',
          'psutil>=5.9.0,<6.0.0',
          # 'cbpi5ui',  # Referência original do PyPI (comentada para usar GitHub)
          'cbpi5ui @ git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@main',  # Instalação do repositório GitHub
          'importlib_metadata>=6.0.0,<8.0.0',
          'numpy>=2.1.0,<3.0.0',
          'pandas>=2.0.0,<3.0.0',
          'setuptools>=70.0.0'] + (
          ['RPi.GPIO==0.7.1'] if raspberrypi else [] ),

        dependency_links=[
        'https://testpypi.python.org/pypi',
        
        ],
      entry_points = {
        "console_scripts": [
            "cbpi=cbpi.cli:main",
        ]
    }
)
