from mamba import describe, context, it, before
from expects import expect, equal
from doublex import Spy
from unittest.mock import patch, MagicMock

from infcommon import clock
from infsnmp.traps import PySnmpTrapDispatcher
from infsnmp.specs import helpers

with describe('PySnmpTrapDispatcher Spec') as self:
    with context('FEATURE: is snmp trap OID'):
        with before.each:
            trap_hander = Spy()
            address = '0.0.0.0'
            port = 162
            myclock = Spy(clock.Clock())
            self.pysnmp_trap_dispatcher = PySnmpTrapDispatcher(trap_hander, address, port, myclock)

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

    with context('FEATURE: run method'):
        with before.each:
            self.trap_handler = Spy()
            self.address = '0.0.0.0'
            self.port = 162
            self.clock = Spy(clock.Clock())
            self.pysnmp_trap_dispatcher = PySnmpTrapDispatcher(
                self.trap_handler,
                self.address,
                self.port,
                self.clock
            )

        with context('when starting the trap dispatcher'):
            with it('configures listener using existing SNMP engine'):
                with patch('infsnmp.traps.config') as mock_config, \
                     patch('infsnmp.traps.ntfrcv') as mock_ntfrcv, \
                     patch('infsnmp.traps.udp') as mock_udp, \
                     patch('asyncio.get_event_loop') as mock_get_loop:

                    # Setup mocks
                    mock_transport = MagicMock()
                    mock_udp.UdpAsyncioTransport.return_value.open_server_mode.return_value = mock_transport

                    mock_loop = MagicMock()
                    mock_get_loop.return_value = mock_loop

                    # Mock the snmp_engine observer that was created in __init__
                    self.pysnmp_trap_dispatcher.snmp_engine.observer = MagicMock()
                    self.pysnmp_trap_dispatcher.snmp_engine.observer.register_observer = MagicMock()

                    # Execute
                    try:
                        self.pysnmp_trap_dispatcher.run()
                    except KeyboardInterrupt:
                        pass

                    # Verify observer was registered for community rewriting
                    self.pysnmp_trap_dispatcher.snmp_engine.observer.register_observer.assert_called_once()
                    call_args = self.pysnmp_trap_dispatcher.snmp_engine.observer.register_observer.call_args
                    expect(call_args[1]['cbCtx']).to(equal('public'))

                    # Verify UDP transport was configured
                    mock_config.add_transport.assert_called_once_with(
                        self.pysnmp_trap_dispatcher.snmp_engine,
                        mock_udp.DOMAIN_NAME,
                        mock_transport
                    )

                    # Verify v1 system was configured with 'public' community
                    mock_config.add_v1_system.assert_called_once_with(
                        self.pysnmp_trap_dispatcher.snmp_engine,
                        'my-area',
                        'public'
                    )

                    # Verify notification receiver was created with callback
                    mock_ntfrcv.NotificationReceiver.assert_called_once()

                    # Verify event loop was started
                    mock_loop.run_forever.assert_called_once()

