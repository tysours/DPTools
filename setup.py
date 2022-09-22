from dptools import __version__
from setuptools import setup
from pathlib import Path

version = __version__

HERE = Path(__file__).parent

README = (HERE / "README.md").read_text()

install_requires = (HERE / 'requirements.txt').read_text().splitlines()

python_requires = '>=3.6' # lots of f-string usage

packages = ['dptools', 'dptools.simulate', 'dptools.cli', 'dptools.train']
package_data = {'dptools': ['simulate/parameter_sets.yaml', 'train/in.json']}

setup(name='dpmdtools', # dptools taken on PyPI :(
      version=version,
      description='DPTools: CLI toolkit and python library for working with deepmd-kit.',
      long_description=README,
      long_description_content_type='text/markdown',
      url='https://github.com/tysours/DPTools',
      maintainer='Ty Sours',
      maintainer_email='tsours@ucdavis.edu',
      license='MIT',
      packages=packages,
      python_requires=python_requires,
      install_requires=install_requires,
      #extras_require=extras_require,
      package_data=package_data,
      entry_points={'console_scripts': ['dptools=dptools.cli:main']},
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: Chemistry'],
      project_urls={
          'Documentation': 'http://dptools.readthedocs.io/',
          'Source': 'https://github.com/tysours/DPTools',
          'Tracker': 'https://github.com/tysours/DPTools/issues',
          },
      )
