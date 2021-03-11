from mamba import description, context, it
from expects import expect, be_a

from infsnmp import factory, clients, types, traps


A_TRAP_HANDLER = 'a_trap_handler'


with description('SNMP Factory'):
    with context('when snmp client creation'):
        with it('get an instance of PySnmpClient'):
            expect(factory.snmp_client()).to(be_a(clients.PySnmpClient))

    with context('when snmp types creation'):
        with it('get an instance of PySnmpTypes'):
            expect(factory.snmp_types()).to(be_a(types.PySnmpTypes))

    with context('when snmp trap dispatcher creation'):
        with it('get an instance of PySnmpTrapDispatcher'):
            expect(factory.snmp_trap_dispatcher(A_TRAP_HANDLER)).to(be_a(traps.PySnmpTrapDispatcher))
