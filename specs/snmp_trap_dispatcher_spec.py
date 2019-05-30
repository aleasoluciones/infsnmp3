from mamba import describe, context, it, before
from expects import expect, equal
from doublex import Spy

from infsnmp.traps import PySnmpTrapDispatcher
from specs import helpers

with describe('PySnmpTrapDispatcher Spec'):
    with context('FEATURE: is snmp trap OID'):
        with before.each:
            trap_hander = Spy()
            address = Spy()
            port = Spy()
            clock = Spy()
            self.pysnmp_trap_dispatcher = PySnmpTrapDispatcher(trap_hander, address, port, clock)

        with context('having a trap oid'):
            with it('returs true'):
                an_str_oid = '1.3.6.1.6.3.1.1.4.1.0'
                an_oid = helpers.build_oid_object_from(an_str_oid)

                is_snmp_trap_oid = self.pysnmp_trap_dispatcher.is_snmp_trap_oid(an_oid)

                expect(is_snmp_trap_oid).to(equal(True))

        with context('having a NON trap oid'):
            with it('returs false'):
                an_str_oid = '1.2.3.4.5.6.7'
                an_oid = helpers.build_oid_object_from(an_str_oid)

                is_snmp_trap_oid = self.pysnmp_trap_dispatcher.is_snmp_trap_oid(an_oid)

                expect(is_snmp_trap_oid).to(equal(False))

