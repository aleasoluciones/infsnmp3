from setuptools import setup, find_packages

setup(name='infsnmp',
      version='0.0.1',
      author='Bifer Team',
      description='snmp library',
      platforms='Linux',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'specs', 'regression_specs', 'integration_tests']),
      install_requires=['pysnmp==4.2.4',
                        'pyasn1==0.1.9',
                        'pysnmp-mibs==0.1.4',
                        'infcommon'],
      dependency_links=['git+https://github.com/aleasoluciones/infcommon3.git#egg=infcommon'],
      scripts=[])
