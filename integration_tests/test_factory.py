# -*- coding: utf-8 -*-

import unittest
from doublex import *

from infsnmp import factory
from infsnmp import clients, types, traps

IRRELEVANT_TRAP_HANDLER = 'irrelevant_trap_handler'
IRRELEVANT_DIRECTORY = 'irrelevant_directory'


class SnmpFactoryTest(unittest.TestCase):

    def test_snmp_client_creation(self):
        assert_that(factory.snmp_client(), instance_of(clients.PySnmpClient))

    def test_snmp_types_creation(self):
        assert_that(factory.snmp_types(), instance_of(types.PySnmpTypes))

    def test_snmp_trap_dispatcher_creation(self):
        assert_that(factory.snmp_trap_dispatcher(IRRELEVANT_TRAP_HANDLER), instance_of(traps.PySnmpTrapDispatcher))
