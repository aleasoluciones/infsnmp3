# -*- coding: utf-8 -*-

import datetime
import struct
from pysnmp.proto import rfc1902, rfc1905
from pyasn1.type import univ
from infcommon import clock


class PySnmpValue(object):
    _CONVERSIONS = {
        rfc1902.OctetString: lambda self, value: value,
        rfc1902.IpAddress: lambda self, value: self.snmp_value.prettyOut(value),
        rfc1902.Integer: lambda self, value: value,
        rfc1902.Integer32: lambda self, value: value,
        rfc1902.Counter32: lambda self, value: value,
        rfc1902.Counter64: lambda self, value: value,
        rfc1902.Gauge32: lambda self, value: int(self.snmp_value.prettyOut(value)),
        univ.ObjectIdentifier: lambda self, value: self.snmp_value.prettyOut(value),
    }

    def __init__(self, snmp_value):
        self.snmp_value = snmp_value

    def exists(self):
        if isinstance(self.snmp_value, rfc1905.NoSuchInstance):
            return False
        if isinstance(self.snmp_value, rfc1905.NoSuchObject):
            return False
        return True


    def is_valid(self):
        return not isinstance(self.snmp_value, rfc1905.EndOfMibView)

    def type_text(self):
        return self.snmp_value.__class__.__name__

    def has_value(self, value):
        return value == self.value()

    def value(self):
        return self._CONVERSIONS.get(self.snmp_value.__class__, lambda self, value: None)(self, self.snmp_value._value)

    def to_hex_string(self):
        return self.value().encode('hex')

    def to_timestamp(self):
        return clock.Clock.timestamp(datetime.datetime(*struct.unpack('>hbbbbbbcbb', self.value())[:7]))

    def sanetized_value(self):
        return self.value().replace(chr(0), '')

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.snmp_value == other.snmp_value)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.snmp_value.prettyPrint()

    def __repr__(self):
        return self.__str__()


class PySnmpTypes(object):

    def integer(self, value):
        return rfc1902.Integer(value)

    def integer32(self, value):
        return rfc1902.Integer32(value)

    def octect_string(self, value):
        return rfc1902.OctetString(value)

    def octect_string_utf8(self, value):
        return rfc1902.OctetString(value.encode('utf-8'))

    def ipaddress_string(self, value):
        return rfc1902.IpAddress(value)

    def octect_string_from_hex_string(self, value):
        return rfc1902.OctetString(value.decode('hex'))

    def counter64(self, value):
        return rfc1902.Counter64(value)


class FakeSnmpValue(object):

    def __init__(self, snmp_value):
        self.snmp_value = snmp_value

    def has_value(self, value):
        return value == self.value()

    def value(self):
        return self.snmp_value

    def to_hex_string(self):
        return self.snmp_value

    def to_timestamp(self):
        return self.snmp_value

    def sanetized_value(self):
        return str(self.value()).replace(chr(0), '')

    def __repr__(self):
        return "FakeSnmpValue %s" % self.snmp_value
