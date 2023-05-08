from setuptools import setup, find_packages

setup(name='infsnmp',
      version='0.0.1',
      author='Bifer Team',
      description='snmp library',
      platforms='Linux',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'specs', 'regression_specs', 'integration_specs']),
      install_requires=['pysnmp-mibs==0.1.4',
                        'pysnmp-pyasn1==1.1.2',
                        'pysnmp-pysmi==1.1.10',
                        'pysnmplib==5.0.21',
                        'pyasn1==0.4.8',
                        'infcommon'],
      dependency_links=['git+https://github.com/aleasoluciones/infcommon3.git#egg=infcommon'],
      scripts=[])
