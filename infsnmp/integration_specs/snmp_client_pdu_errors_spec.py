import socket
import threading

from mamba import description, context, it, before, after
from expects import expect, equal, be_a

from pyasn1.codec.ber import decoder, encoder
from pysnmp.proto import api

from infsnmp import types, clients, exceptions


SNMP_HOST = '127.0.0.1'
A_COMMUNITY = 'a_community'
AN_OID = '1.3.6.1.4.1.2011.6.128.1.1.2.43.1.3'
AN_INSTANCE_OID = AN_OID + '.0'
VENDOR_ERROR_STATUS = 6859601
GEN_ERR = 5
NO_SUCH_NAME = 2


class ErrorStatusAgent:
    def __init__(self):
        self.error_status = VENDOR_ERROR_STATUS
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((SNMP_HOST, 0))
        self.port = self._socket.getsockname()[1]
        threading.Thread(target=self._serve, daemon=True).start()

    def stop(self):
        self._socket.close()

    def _serve(self):
        protocol = api.PROTOCOL_MODULES[api.SNMP_VERSION_2C]
        while True:
            try:
                data, address = self._socket.recvfrom(65535)
            except OSError:
                return
            request, _ = decoder.decode(data, asn1Spec=protocol.Message())
            response = protocol.apiMessage.get_response(request)
            response_pdu = protocol.apiMessage.get_pdu(response)
            protocol.apiPDU.set_varbinds(response_pdu, protocol.apiPDU.get_varbinds(protocol.apiMessage.get_pdu(request)))
            protocol.apiPDU.set_error_status(response_pdu, self.error_status)
            protocol.apiPDU.set_error_index(response_pdu, 1)
            self._socket.sendto(encoder.encode(response), address)


def error_raised_by(callback):
    try:
        callback()
    except Exception as exc:
        return exc
    return None


with description('SNMP Client PDU-level errors') as self:
    with before.all:
        self.agent = ErrorStatusAgent()

    with after.all:
        self.agent.stop()

    with before.each:
        self.snmp_client = clients.PySnmpClient()
        self.agent.error_status = VENDOR_ERROR_STATUS
        self.expected_message = 'SNMPLevelError SNMP PDU-level error 127.0.0.1 status 6859601 at 1'

    with context('when the agent answers with a vendor specific error status'):
        with context('FEATURE: snmpget'):
            with it('raises an SNMPLevelError with the numeric status'):
                error = error_raised_by(lambda: self.snmp_client.get(SNMP_HOST, A_COMMUNITY, [AN_INSTANCE_OID], port=self.agent.port))

                expect(error).to(be_a(exceptions.SNMPLevelError))
                expect(str(error)).to(equal(self.expected_message))

        with context('FEATURE: snmpset'):
            with it('raises an SNMPLevelError with the numeric status'):
                values = [(AN_INSTANCE_OID, types.PySnmpTypes().integer(1))]

                error = error_raised_by(lambda: self.snmp_client.set(SNMP_HOST, A_COMMUNITY, values, port=self.agent.port))

                expect(error).to(be_a(exceptions.SNMPLevelError))
                expect(str(error)).to(equal(self.expected_message))

        with context('FEATURE: snmpbulkwalk'):
            with it('raises an SNMPLevelError with the numeric status'):
                error = error_raised_by(lambda: self.snmp_client.bulk_walk(SNMP_HOST, A_COMMUNITY, AN_OID, port=self.agent.port))

                expect(error).to(be_a(exceptions.SNMPLevelError))
                expect(str(error)).to(equal(self.expected_message))

        with context('FEATURE: snmpwalk'):
            with it('raises an SNMPLevelError with the numeric status'):
                error = error_raised_by(lambda: self.snmp_client.walk(SNMP_HOST, A_COMMUNITY, AN_OID, port=self.agent.port))

                expect(error).to(be_a(exceptions.SNMPLevelError))
                expect(str(error)).to(equal(self.expected_message))

    with context('when the agent answers with a standard error status'):
        with context('FEATURE: snmpwalk'):
            with it('raises an SNMPLevelError with the status name'):
                self.agent.error_status = GEN_ERR

                error = error_raised_by(lambda: self.snmp_client.walk(SNMP_HOST, A_COMMUNITY, AN_OID, port=self.agent.port))

                expect(error).to(be_a(exceptions.SNMPLevelError))
                expect(str(error)).to(equal('SNMPLevelError SNMP PDU-level error 127.0.0.1 status genErr at 1'))

    with context('when the agent answers with noSuchName'):
        with context('FEATURE: snmpwalk'):
            with it('returns no value'):
                self.agent.error_status = NO_SUCH_NAME

                result = self.snmp_client.walk(SNMP_HOST, A_COMMUNITY, AN_OID, port=self.agent.port)

                expect(result).to(equal(()))
