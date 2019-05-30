from pysnmp.proto import api

PROTO_MODULE = api.protoModules[api.protoVersion2c]

def build_request_pdu(str_oid):
    request_pdu = PROTO_MODULE.GetRequestPDU()
    PROTO_MODULE.apiPDU.setDefaults(request_pdu)
    PROTO_MODULE.apiPDU.setVarBinds(
        request_pdu, ((str_oid, PROTO_MODULE.Null('')),
                        )
    )
    return request_pdu

def first_oid_from_request_pdu(request_pdu):
    for oid, val in PROTO_MODULE.apiPDU.getVarBindList(request_pdu):
        return oid

def build_oid_object_from(str_oid):
    request_pdu = build_request_pdu(str_oid)
    an_oid = first_oid_from_request_pdu(request_pdu)
    return an_oid
