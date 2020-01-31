# infsnmp documentation

[![Build status](https://secure.travis-ci.org/aleasoluciones/infsnmp3.svg?branch=master)](https://secure.travis-ci.org/aleasoluciones/infsnmp3)


Wrapper for [PySNMP](http://snmplabs.com/pysnmp/index.html) library.

## How to setup the development environment

- Create a virtual environment with [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) using Python 3.7+:

```sh
mkvirtualenv infsnmp -p $(which python3.7)
```

- Install the dependencies:

```sh
dev/setup_venv.sh
```

## How to run the tests

```sh
./all_tests.sh
```

The integration tests need to be thrown against something "real", so a container executing the [SNMP Simulator Tool](http://snmplabs.com/snmpsim/) (snmpsim) will be built and run to simulate it. It has been loaded with custom data. The container will be stopped and removed after running the tests.

## Example: request an OID

In the following examples we'll execute a *snmpwalk* using both the command line and the library. But first we have to manually build and run the previous container simulating a device with snmp so we can ask for OIDs.

```sh
docker-compose -f dev/infsnmp3_devdocker/docker-compose.yml up -d
```

### Using the command line

```sh
snmpwalk -v2c -c cm-0015cf2093d7 127.0.0.1:1161 1.3.6.1.2.1
```

### Using the library

```python
from infsnmp import clients as infsnmp_clients

snmp_client = infsnmp_clients.PySnmpClient()

host = '127.0.0.1'
community = 'cm-0015cf2093d7'
root_oid = '1.3.6.1.2.1'
port = '1161'

results = snmp_client.bulk_walk(host=host, port=port, community=community, str_oid=root_oid)

for result in results:
    # Each result is a tuple of two elements
    oid = result[0]
    data = result[1].value()
    print(f'{oid} --- {data}')

```