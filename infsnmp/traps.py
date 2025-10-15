import asyncio
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import ntfrcv

from infcommon import clock, logger, AttributesComparison

from infsnmp import types


class PySnmpTrap(AttributesComparison):

    def __init__(self, timestamp, source_address, trap_oid, values):
        self.timestamp = timestamp
        self.source_address = source_address
        self.device_id = None
        self.trap_oid = trap_oid
        self.values = values


class PySnmpTrapDispatcher:
    SNMP_TRAP_OID = '1.3.6.1.6.3.1.1.4.1.0'

    def __init__(self, trap_handler, address, port, clock=clock.Clock()):
        self.trap_handler = trap_handler
        self.address = address
        self.port = port
        self.clock = clock
        self.snmp_engine = None

    def is_snmp_trap_oid(self, oid):
        return str(oid) == self.SNMP_TRAP_OID

    def _community_rewrite_observer(self, snmpEngine, execpoint, variables, cbCtx):
        """Observer that rewrites any incoming community string to 'public'.
        This allows accepting traps with any community string (similar to pysnmp 4.x behavior)."""
        if 'communityName' in variables:
            variables['communityName'] = variables['communityName'].clone(cbCtx)

    def run(self):
        self.snmp_engine = engine.SnmpEngine()

        # Register observer to accept any community string by rewriting to 'public'
        # This emulates the 'disableAuthorization' behavior
        self.snmp_engine.observer.register_observer(
            self._community_rewrite_observer,
            'rfc2576.processIncomingMsg:writable',
            cbCtx='public'
        )

        # Configure UDP transport
        config.add_transport(
            self.snmp_engine,
            udp.DOMAIN_NAME,
            udp.UdpAsyncioTransport().open_server_mode((self.address, self.port))
        )

        # Only need to configure 'public' since all community strings are rewritten to it
        config.add_v1_system(self.snmp_engine, 'my-area', 'public')

        # Register notification receiver with callback
        ntfrcv.NotificationReceiver(self.snmp_engine, self._callback)

        logger.info(f'SNMP trap dispatcher listening on {self.address}:{self.port}')

        try:
            asyncio.get_event_loop().run_forever()
        except Exception as exc:
            self.snmp_engine.transport_dispatcher.close_dispatcher()
            raise exc

    def _callback(self, snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
        """Callback invoked when a trap/inform is received."""
        try:
            # Get transport information (source address)
            try:
                transportDomain, transportAddress = snmpEngine.message_dispatcher.get_transport_info(stateReference)
                source_address = transportAddress[0] if transportAddress else 'unknown'
            except Exception as e:
                logger.warning(f'Could not get transport info: {e}')
                source_address = 'unknown'

            # Ignore broadcast traps
            if source_address == '0.0.0.0':
                logger.info('Broadcast snmptrap ignored')
                return

            # Extract trap OID and values
            trap_oid = None
            values = {}

            for oid, val in varBinds:
                oid_str = str(oid)
                if self.is_snmp_trap_oid(oid):
                    # This is the trap OID
                    trap_oid = str(val)
                else:
                    # This is a varbind
                    values[oid_str] = types.PySnmpValue(val)

            # Call the trap handler
            self.trap_handler.trap(
                PySnmpTrap(
                    timestamp=self.clock.utctimestampnow(),
                    source_address=source_address,
                    trap_oid=trap_oid,
                    values=values
                )
            )

        except Exception as exc:
            logger.critical('Error processing snmptrap: {} {}'.format(exc, exc.__class__.__name__), exc_info=True)
