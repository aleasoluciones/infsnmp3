# -*- coding: utf-8 -*-

import glob
import os.path

import os
from infcommon.factory import Factory
from infsnmp import (
    clients,
    types,
    oid_converter as oid_converter_module,
    traps
)

snmp_client = lambda: Factory.instance(
    'snmp_client', lambda: clients.PySnmpClient())

snmp_types = lambda: Factory.instance(
    'snmp_types', lambda: types.PySnmpTypes())


def get_mibdir():
    return os.environ.get('MIBDIR', '/etc/felix/snmp/pymibs/')


def get_mib_modules():
    return [value for value in os.environ.get('MIBMODULES', '').split(':') if value]


def modules_from_dir(directory):
    return [os.path.basename(f).split('.')[0] for f in glob.glob('%s/*.py' % directory)]


def oid_converter():
    mibdir = get_mibdir()
    return Factory.instance('oid_converter',
                            lambda: oid_converter_module.PyOIDConverter(
                            mibdir,
                            modules_from_dir(mibdir)))


def snmp_trap_dispatcher(trap_handler):
    return Factory.instance('snmp_trap_dispatcher', lambda:
            traps.PySnmpTrapDispatcher(trap_handler, address='0.0.0.0',
                port=162))
