# infsnmp documentation

[![Build status](https://secure.travis-ci.org/aleasoluciones/infsnmp.svg?branch=master)](https://secure.travis-ci.org/aleasoluciones/infsnmp)


Wrapper for pysnmp library.

## How to setup the development environment
`dev/setup_venv.sh`

## How to run the tests
`./integration_tests.sh`

## snmp daemon emulation

Integration tests starts a container with [snmpsim](http://snmplabs.com/snmpsim/) daemon, that has been configured with custom data to simuate some Huawei OLTs behaviour.

starting snmpsim manually without container:
```
${VIRTUAL_ENV}/bin/python ${VIRTUAL_ENV}/bin/snmpsimd.py --v2c-arch --agent-port=1161 --device-dir=simulated_data/ --validate-device-data --force-index-rebuild

```

Requesting an OID
```
snmpwalk -v2c -c cm-0015cf2093d7 127.0.0.1:1161 1.3.6.1.2.1.10.127.1.1
```

this should work and could the starting point to understand and play with this module.

Visit snmpsim [README](https://github.com/aleasoluciones/infsnmp3/blob/master/integration_tests/snmpsim/README) for further information
