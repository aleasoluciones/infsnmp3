from mamba import description, context, it, before
from expects import expect, equal, have_length, contain, raise_error, be_false

from pysnmp.proto import rfc1902

from infsnmp import types, clients, exceptions


READ_ONLY_COMMUNITY = 'c4-temperatures'
READ_WRITE_COMMUNITY = 'set'
INVALID_COMMUNITY = 'a_community'
SNMP_HOST = '127.0.0.1'
SNMP_PORT = 1161


def snmp_integer(value):
    return types.PySnmpValue(types.PySnmpTypes().integer(value))


def snmp_octect_string(value):
    return types.PySnmpValue(types.PySnmpTypes().octect_string(value))


with description('SNMP Client') as self:
    with before.each:
        self.snmp_client = clients.PySnmpClient()

    with context('FEATURE: snmpget'):
        with context('happy path'):
            with it('returns the values'):
                oid1 = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.10'
                oid2 = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.11'

                result = self.snmp_client.get(SNMP_HOST,
                                              READ_ONLY_COMMUNITY,
                                              [oid1, oid2],
                                              port=SNMP_PORT)

                expect(result).to(equal([
                    (oid1, snmp_integer(999)),
                    (oid2, snmp_integer(31))
                ]))

        with context('having an invalid community'):
            with it('raises an exception after a timeout'):
                oid = '1.1'

                def _snmpget_with_invalid_community():
                    self.snmp_client.get(SNMP_HOST,
                                         INVALID_COMMUNITY,
                                         [oid],
                                         port=SNMP_PORT)

                expect(_snmpget_with_invalid_community).to(raise_error(exceptions.SNMPExceptionError))

        with context('having an unknown oid'):
            with it('returns no value'):
                unknown_oid = '1.2'

                result = self.snmp_client.get(SNMP_HOST,
                                              READ_ONLY_COMMUNITY,
                                              [unknown_oid],
                                              port=SNMP_PORT)

                value = result[0][1]
                expect(value.exists()).to(be_false)

    with context('FEATURE: snmpwalk'):
        with context('happy path'):
            with it('returns the descendant values'):
                oid = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29'
                oid1 = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.10'
                oid2 = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.11'

                result = self.snmp_client.walk(SNMP_HOST,
                                               READ_ONLY_COMMUNITY,
                                               oid,
                                               port=SNMP_PORT)

                expect(result).to(have_length(31))
                expect(result).to(contain((oid1, snmp_integer(999))))
                expect(result).to(contain((oid2, snmp_integer(31))))

        with context('having an unknown oid'):
            with it('returns no value'):
                unknown_oid = '1.2'

                result = self.snmp_client.walk(SNMP_HOST,
                                               READ_ONLY_COMMUNITY,
                                               unknown_oid,
                                               port=SNMP_PORT)

                expect(result).to(have_length(0))

    with context('FEATURE: snmpbulkwalk'):
        with it('returns the descendant values'):
            oid = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29'
            oid1 = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.10'
            oid2 = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.11'

            result = self.snmp_client.bulk_walk(SNMP_HOST,
                                                READ_ONLY_COMMUNITY,
                                                oid,
                                                port=SNMP_PORT)

            expect(result).to(have_length(31))
            expect(result).to(contain((oid1, snmp_integer(999))))
            expect(result).to(contain((oid2, snmp_integer(31))))

    with context('FEATURE: snmpset'):
        with context('happy path'):
            with it('sets the values'):
                oid_1 = '1.3.6.1.2.1.1.1.0'
                oid_2 = '1.3.6.1.2.1.1.3.0'
                value_1 = snmp_octect_string('a_value').value()
                value_2 = snmp_integer(22).value()
                snmp_values = ((oid_1, value_1), (oid_2, value_2),)

                self.snmp_client.set(SNMP_HOST,
                                     READ_WRITE_COMMUNITY,
                                     snmp_values,
                                     port=SNMP_PORT)

                result = self.snmp_client.get(SNMP_HOST,
                                              READ_WRITE_COMMUNITY,
                                              [oid_1, oid_2],
                                              port=SNMP_PORT)

                expect(result).to(equal([
                    (oid_1, types.PySnmpValue(value_1)),
                    (oid_2, types.PySnmpValue(value_2))
                ]))

        with context('having an invalid community'):
            with it('raises an exception after a timeout'):
                oid_1 = '1.3.6.1.2.1.1.1.0'
                value_1 = rfc1902.OctetString('hola')
                snmp_values = ((oid_1, value_1),)

                def _snmpget_with_invalid_community():
                    self.snmp_client.set(SNMP_HOST,
                                         INVALID_COMMUNITY,
                                         snmp_values,
                                         port=SNMP_PORT)

                expect(_snmpget_with_invalid_community).to(raise_error(exceptions.SNMPExceptionError))
