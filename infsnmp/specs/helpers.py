from pysnmp.proto import api
from pysnmp.smi import builder, view, rfc1902 as rfc1902_smi

PROTO_MODULE = api.PROTOCOL_MODULES[api.SNMP_VERSION_2C]

def build_request_pdu(str_oid):
    request_pdu = PROTO_MODULE.GetRequestPDU()
    PROTO_MODULE.apiPDU.set_defaults(request_pdu)
    PROTO_MODULE.apiPDU.set_varbinds(
        request_pdu, ((str_oid, PROTO_MODULE.Null('')),
                        )
    )
    return request_pdu

def first_oid_from_request_pdu(request_pdu):
    for varbind in PROTO_MODULE.apiPDU.get_varbind_list(request_pdu):
        return varbind[0]

def build_oid_object_from(str_oid):
    request_pdu = build_request_pdu(str_oid)
    an_oid = first_oid_from_request_pdu(request_pdu)
    return an_oid

def build_snmp_data_object_identity(str_oid):
    mib_builder = builder.MibBuilder()
    mib_view = view.MibViewController(mib_builder)
    snmp_data = rfc1902_smi.ObjectIdentity(str_oid)
    snmp_data.resolveWithMib(mib_view)
    return snmp_data
