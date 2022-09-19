from dptools import __version__
from setuptools import setup, find_packages

version = __version__

install_requires = [
    'ase',
    'scikit-learn', # only needed for shuffle util, maybe write own function to avoid dependency
    'python-dotenv',
    'ruamel.yaml'
]


python_requires = ">=3.6"
package_data = {'dptools': ['simulate/parameter_sets.yaml']}
#packages = find_packages(where='dptools', include=['*.py'],  # alternatively: `exclude=['additional*']`
#        ) # TODO: Figure out how to use this

packages = ['dptools', 'dptools.simulate', 'dptools.cli', 'dptools.train']

setup(name='dpmdtools',
      version=version,
      description='DPTools: CLI toolkit for working with deepmd-kit',
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
