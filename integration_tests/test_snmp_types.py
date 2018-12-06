# -*- coding: utf-8 -*-

import unittest
import os
from hamcrest import *

import datetime
import pysnmp
from pysnmp.proto import rfc1902
from pyasn1.type import univ

from infcommon import clock
from infsnmp import types

class PySnmpValuesTest(unittest.TestCase):

    def test_integer(self):
        snmp_value = rfc1902.Integer(5)
        assert_that(types.PySnmpValue(snmp_value).value(), is_(5))
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('Integer'))

    def test_integer_32(self):
        snmp_value = rfc1902.Integer32(5)
        assert_that(types.PySnmpValue(snmp_value).value(), is_(5))
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('Integer32'))

    def test_counter_64(self):
        snmp_value = rfc1902.Counter64(42)
        assert_that(types.PySnmpValue(snmp_value).value(), is_(42))
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('Counter64'))

    def test_octect_string(self):
        snmp_value = rfc1902.OctetString('HG8110')
        assert_that(types.PySnmpValue(snmp_value).value(), is_('HG8110'))
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('OctetString'))

    def test_ipaddress_string(self):
        snmp_value = rfc1902.IpAddress('127.0.0.1')
        assert_that(types.PySnmpValue(
            snmp_value).value(), is_('127.0.0.1'))
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('IpAddress'))

    def test_timestamp(self):
        # '07dd011c0c292c002b0100' -> '2013-01-28 12:41:44' -> timstamp 1359373304.0
        os.environ['TZ'] = 'UTC'
        snmp_value = rfc1902.OctetString('07dd011c0c292c002b0100'.decode('hex'))

        assert_that(types.PySnmpValue(snmp_value).to_timestamp(), is_(1359376904.0))
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('OctetString'))

    def test_gauge32(self):
        snmp_value = rfc1902.Gauge32(42)
        assert_that(types.PySnmpValue(snmp_value).value(), 42)
        assert_that(types.PySnmpValue(snmp_value).type_text(), is_('Gauge32'))

    def test_unknown_type_returns_none(self):
        no_converted_value = rfc1902.TimeTicks(42)
        assert_that(types.PySnmpValue(no_converted_value).value(), none())

    def test_convert_octect_with_hexadecimal_to_string_with_hexadecimal(self):
        snmp_value = rfc1902.OctetString('HWTC\xe5\x8f"\t')
        assert_that(types.PySnmpValue(
            snmp_value).to_hex_string(), is_('48575443e58f2209'))

    def test_convert_object_identifier_string_oid(self):
        snmp_value = univ.ObjectIdentifier('1.1')
        assert_that(types.PySnmpValue(snmp_value).value(), is_('1.1'))


class PySnmpTypesTest(unittest.TestCase):

    def setUp(self):
        self.types = types.PySnmpTypes()

    def test_integer(self):
        snmp_value = self.types.integer(5)
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.Integer))

    def test_integer_32(self):
        snmp_value = self.types.integer32(5)
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.Integer32))

    def test_octect_string(self):
        snmp_value = self.types.octect_string('HG8110')
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.OctetString))

    def test_octect_string_utf8(self):
        snmp_value = self.types.octect_string_utf8(u'Habitación 237')
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.OctetString))

    def test_ipaddress_string(self):
        snmp_value = self.types.ipaddress_string('127.0.0.1')
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.IpAddress))

    def test_octect_string_from_hex_string(self):
        snmp_value = self.types.octect_string_from_hex_string(
            '48575443e58f2209')
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.OctetString))
        assert_that(snmp_value._value, is_('HWTC\xe5\x8f"\t'))

    def test_counter_64(self):
        snmp_value = self.types.counter64(42)
        assert_that(snmp_value, instance_of(pysnmp.proto.rfc1902.Counter64))
