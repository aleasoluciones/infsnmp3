from mamba import description, context, it
from expects import expect, equal, be_a

import os
import binascii

import pysnmp
from pysnmp.proto import rfc1902
from pyasn1.type import univ

from infsnmp.types import PySnmpValue, PySnmpTypes


with description('SNMP Values'):
    with context('when type is Integer'):
        with it('checks value and type'):
            snmp_data = rfc1902.Integer(5)

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal(5))
            expect(snmp_value.type_text()).to(equal('Integer'))

    with context('when type is Integer32'):
        with it('checks value and type'):
            snmp_data = rfc1902.Integer32(5)

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal(5))
            expect(snmp_value.type_text()).to(equal('Integer32'))

    with context('when type is Counter64'):
        with it('checks value and type'):
            snmp_data = rfc1902.Counter64(42)

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal(42))
            expect(snmp_value.type_text()).to(equal('Counter64'))

    with context('when type is OctetString'):
        with it('checks value and type'):
            snmp_data = rfc1902.OctetString(b'HG8110')

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal(b'HG8110'))
            expect(snmp_value.type_text()).to(equal('OctetString'))

        with context('having hexadecimal characters'):
            with it('checks decoded value'):
                snmp_data = rfc1902.OctetString(b'HWTC\xe5\x8f"\t')

                snmp_value = PySnmpValue(snmp_data)

                expect(snmp_value.to_hex_string()).to(equal('48575443e58f2209'))

        with context('having padding characters'):
            with it('checks sanetized value'):
                snmp_data = rfc1902.OctetString(b'\x00HG8110')

                snmp_value = PySnmpValue(snmp_data)

                expect(snmp_value.value()).to(equal(b'\x00HG8110'))
                expect(snmp_value.sanetized_value()).to(equal(b'HG8110'))

        with context('having a timestamp'):
            with context('having an hex string with time and date'):
                with it('returns a timestamp value'):
                    # See https://docs.python.org/3/library/struct.html for more details
                    # Useful when datetime is encoded as OctetString
                    # With binascii.unhexlify we separate each byte, and the we map with struct.unpack
                    # Example for 07e4011b04173a002b0000
                    #                 -------------------------------
                    # Hex:            07E4 01 1B 04 17 3A 00 2B 00 00
                    # Size:              h  b  b  b  b  b  b  c  b  b
                    # Dec:            2020 01 27 04 23 58 00  + 00 00
                    #                 -------------------------------
                    # Dec to datetime:    Jan 27 2020 23:58:00 +00:00
                    # Datetime to timestamp (in seconds):  1580169480

                    os.environ['TZ'] = 'UTC'
                    data = binascii.unhexlify(b'07e4011b04173a002b0000')
                    snmp_data = rfc1902.OctetString(data)

                    snmp_value = PySnmpValue(snmp_data)

                    expect(snmp_value.to_timestamp()).to(equal(1580099038.0))

    with context('when type is IpAddress'):
        with it('checks value and type'):
            snmp_data = rfc1902.IpAddress('127.0.0.1')

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal('127.0.0.1'))
            expect(snmp_value.type_text()).to(equal('IpAddress'))

    with context('when type is Gauge32'):
        with it('checks value and type'):
            snmp_data = rfc1902.Gauge32(42)

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal(42))
            expect(snmp_value.type_text()).to(equal('Gauge32'))

    with context('when type is ObjectIdentifier'):
        with it('checks value and type'):
            snmp_data = univ.ObjectIdentifier('1.1')

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal('1.1'))
            expect(snmp_value.type_text()).to(equal('ObjectIdentifier'))

    with context('when type is not recognized'):
        with it('value is None'):
            snmp_data = rfc1902.TimeTicks(42)

            snmp_value = PySnmpValue(snmp_data)

            expect(snmp_value.value()).to(equal(None))


with description('SNMP Types'):
    with context('when type is Integer'):
        with it('checks that value is an instance of Integer'):
            snmp_value = PySnmpTypes().integer(5)

            expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.Integer))

    with context('when type is Integer32'):
        with it('checks that value is an instance of Integer32'):
            snmp_value = PySnmpTypes().integer32(5)

            expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.Integer32))

    with context('when type is OctetString'):
        with it('checks that value is an instance of OctetString'):
            snmp_value = PySnmpTypes().octect_string('HG8110')

            expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.OctetString))

        with context('having utf8 chars'):
            with it('checks that value is an instance of OctetString'):
                snmp_value = PySnmpTypes().octect_string_utf8(u'Habitación 237')

                expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.OctetString))

        with context('having an hex string'):
            with it('checks that value is an instance of OctetString'):
                snmp_value = PySnmpTypes().octect_string_from_hex_string(b'48575443e58f2209')

                expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.OctetString))
                expect(snmp_value._value).to(equal(b'HWTC\xe5\x8f"\t'))

    with context('when type is IPAddress'):
        with it('checks that value is an instance of IpAddress'):
            snmp_value = PySnmpTypes().ipaddress_string('127.0.0.1')

            expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.IpAddress))

    with context('when type is Counter64'):
        with it('checks that value is an instance of Counter64'):
            snmp_value = PySnmpTypes().counter64(42)

            expect(snmp_value).to(be_a(pysnmp.proto.rfc1902.Counter64))
