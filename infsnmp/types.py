import datetime
import struct
import binascii

from pysnmp.proto import rfc1902, rfc1905
from pysnmp.smi import rfc1902 as rfc1902_smi

from infcommon import clock


class PySnmpValue:
    _CONVERSIONS = {
        'OctetString': lambda self, value: value.asOctets(),
        'IpAddress': lambda self, value: self.snmp_value.prettyPrint(),
        'Integer': lambda self, value: int(self.snmp_value.prettyPrint()),
        'Integer32': lambda self, value: int(self.snmp_value.prettyPrint()),
        'Counter32': lambda self, value: int(self.snmp_value.prettyPrint()),
        'Counter64': lambda self, value: int(self.snmp_value.prettyPrint()),
        'Gauge32': lambda self, value: int(self.snmp_value.prettyPrint()),
        'DisplayString': lambda self, value: self.snmp_value.prettyPrint(),
        'ObjectIdentifier': lambda self, value: self.snmp_value.prettyPrint(),
        'ObjectIdentity': lambda self, value: str(self.snmp_value),
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
        return self._CONVERSIONS.get(self.snmp_value.__class__.__name__, lambda self, value: None)(self, self.snmp_value)

    def to_hex_string(self):
        return self.value().hex()

    def to_timestamp(self):
        byte_data = self.value()
        if len(byte_data) == 11:
            interpreted_datetime = struct.unpack('>hbbbbbbcbb', byte_data)
            interpreted_datetime_naive = interpreted_datetime[:7]
        if len(byte_data) == 8:
            interpreted_datetime = struct.unpack('>hbbbbbb', byte_data)
            interpreted_datetime_naive = interpreted_datetime
        return clock.Clock.timestamp(datetime.datetime(*interpreted_datetime_naive))

    def sanetized_value(self):
        return self.value().replace(chr(0).encode('utf-8'), b'')

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.snmp_value == other.snmp_value)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if isinstance(self.snmp_value, rfc1902_smi.ObjectIdentity):
            return str(self.snmp_value)
        return self.snmp_value.prettyPrint()

    def __repr__(self):
        return self.__str__()


class PySnmpTypes:
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
        return rfc1902.OctetString(binascii.unhexlify(value))

    def counter64(self, value):
        return rfc1902.Counter64(value)


class FakeSnmpValue:
    def __init__(self, snmp_value):
        self.snmp_value = snmp_value

    def exists(self):
        if isinstance(self.snmp_value, rfc1905.NoSuchInstance):
            return False
        if isinstance(self.snmp_value, rfc1905.NoSuchObject):
            return False
        return True

    def has_value(self, value):
        return value == self.value()

    def value(self):
        return self.snmp_value

    def to_hex_string(self):
        return self.snmp_value.hex()

    def to_timestamp(self):
        return self.snmp_value

    def sanetized_value(self):
        return str(self.value()).replace(chr(0), '')

    def __repr__(self):
        return "FakeSnmpValue %s" % self.snmp_value


class FakeSanitizedSnmpValue(FakeSnmpValue):
    def sanetized_value(self):
        return self.value().replace(chr(0).encode('utf-8'), b'')
