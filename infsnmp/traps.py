# -*- coding: utf-8 -*-

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from infsnmp import types
from infcommon import clock, logger, AttributesComparison

class PySnmpTrap(AttributesComparison):

    def __init__(self, timestamp, source_address, trap_oid, values):
        self.timestamp = timestamp
        self.source_address = source_address
        self.device_id = None
        self.trap_oid = trap_oid
        self.values = values


class PySnmpTrapDispatcher(object):
    SNMP_TRAP_OID = '1.3.6.1.6.3.1.1.4.1.0'

    def __init__(self, trap_handler, address, port, clock=clock.Clock()):
        self.trap_handler = trap_handler
        self.address = address
        self.port = port
        self.clock = clock

    def is_snmp_trap_oid(self, oid):
        return oid.prettyPrint() == self.SNMP_TRAP_OID

    def run(self):
        transport_dispatcher = AsynsockDispatcher()
        transport_dispatcher.registerRecvCbFun(self._callback)
        transport_dispatcher.registerTransport(udp.domainName,
            udp.UdpSocketTransport().openServerMode((self.address, self.port)))
        transport_dispatcher.jobStarted(1)

        try:
            transport_dispatcher.runDispatcher()
        except:
            transport_dispatcher.closeDispatcher()
            raise

    def _callback(self, transport_dispatcher, transport_domain, transport_address, whole_msg):
        try:
            while whole_msg:
                msg_version = int(api.decodeMessageVersion(whole_msg))
                if msg_version not in api.protoModules:
                    logger.error('Unsupported SNMP version {} {}'.format(msg_version, transport_address[0]))
                    return

                proto_module = api.protoModules[msg_version]

                request_msg, whole_msg = decoder.decode(whole_msg, asn1Spec=proto_module.Message(),)
                request_pdu = proto_module.apiMessage.getPDU(request_msg)
                if transport_address[0] == '0.0.0.0':
                    logger.info('Broadcast snmptrap ignored')
                    return
                if request_pdu.isSameTypeWith(proto_module.TrapPDU()):
                    self._extract_and_process_trap(proto_module, request_pdu, transport_address)
        except Exception as exc:
            logger.critical('Error snmptrap: {}  {}'.format(exc, exc.__class__.__name__))


    def _extract_and_process_trap(self, proto_module, request_pdu, transport_address):
            trap_oid = None
            values = {}
            try:
                for oid, val in proto_module.apiPDU.getVarBindList(request_pdu):
                    if self.is_snmp_trap_oid(oid):
                        trap_oid = self._extract_value(val).value()
                    else:
                        values[str(oid)] = self._extract_value(val)
                self.trap_handler.trap(
                    PySnmpTrap(
                            timestamp=self.clock.utctimestampnow(),
                            source_address=transport_address[0],
                            trap_oid=trap_oid,
                            values=values)
                )
            except TypeError:
                logger.error('Error processing RequestPDU transport_address:{} request_pdu:{}'.format(transport_address, request_pdu), exc_info=True)


    def _extract_value(self, val):
        return types.PySnmpValue(val.getComponent().getComponent().getComponent())
