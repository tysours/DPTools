from dptools import __version__

install_requires = [
    'numpy',
    'matplotlib',
    'seaborn'
]


python_requires = ">=3.6"

setup(name='dptools',
      version=__version__,
      description='CLI toolkit for working with deepmd-kit',
      url='https://github.com/tysours/DPTools',
      maintainer='Ty Sours',
      maintainer_email='tsours@ucdavis.edu',
      license='MIT',
      packages=find_packages(),
      python_requires=python_requires,
      install_requires=install_requires,
      extras_require=extras_require,
      package_data=package_data,
      entry_points={'console_scripts': ['ase=ase.cli.main:main',
                                        'ase-db=ase.cli.main:old',
                                        'ase-gui=ase.cli.main:old',
                                        'ase-run=ase.cli.main:old',
                                        'ase-info=ase.cli.main:old',
                                        'ase-build=ase.cli.main:old']},
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: Chemistry'])

