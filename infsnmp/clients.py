# -*- coding: utf-8 -*-

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import ObjectName
from pysnmp.smi.error import NoSuchObjectError
import socket
from infsnmp import types, exceptions


class PySnmpClient(object):
    AGENT_ID = 'felix_agent'
    DEFAULT_BULK_SIZE = 205
    DEFAULT_TIMEOUT = 2
    DEFAULT_RETRIES = 2
    DEFAULT_PORT = 161

    def get(self, host, community, oids, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        try:
            err_indication, err_status, err_index, var_binds = cmdgen.CommandGenerator().getCmd(
                    cmdgen.CommunityData('my-agent', community),
                    cmdgen.UdpTransportTarget((host, port), timeout=timeout, retries=retries),
                    *oids)
            if err_indication:
                    raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
            if err_status:
                    raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))
            result = []
            for oid, value in var_binds:
                oid = str(oid)
                value = types.PySnmpValue(value)
                result.append((oid, value))
            return result
        except socket.error as exc:
            raise exceptions.SNMPSocketError(exc)
        except NoSuchObjectError as exc:
            raise exceptions.InvalidOIDError()

    def walk(self, host, community, str_oid, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        cmd_oid = self.__convert_to_pysnmp_oid_format(str_oid)
        try:
            # timeout and retries are optional=> Just detect that the pysnmp fails, do not use them
            err_indication, err_status, err_index, var_binds = cmdgen.CommandGenerator().nextCmd(
                cmdgen.CommunityData('my-agent', community),
                cmdgen.UdpTransportTarget((host, port), timeout=timeout, retries=retries),
                ObjectName(cmd_oid))

            if err_indication:
                raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
            if err_status:
                raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

            result = []
            for snmp_value in var_binds:
                snmp_value = snmp_value[0]
                oid, value = self.__extract_oid_and_value_from_varbind(snmp_value)
                if self.__is_suboid(oid, str_oid) and value.is_valid():
                    result.append((oid, value))
            return tuple(result)
        except socket.error as exc:
            raise exceptions.SNMPSocketError(exc)

    def bulk_walk(self, host, community, str_oid, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, non_repeaters=0, max_repetitions=50):
        cmd_oid = self.__convert_to_pysnmp_oid_format(str_oid)
        try:
            # timeout and retries are optional=> Just detect that the pysnmp fails, do not use them
            err_indication, err_status, err_index, var_binds = cmdgen.CommandGenerator().bulkCmd(
                cmdgen.CommunityData('my-agent', community),
                cmdgen.UdpTransportTarget((host, port), timeout=timeout, retries=retries),
                non_repeaters, max_repetitions,
                ObjectName(cmd_oid))

            if err_indication:
                raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
            if err_status:
                raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

            result = []
            for snmp_value in var_binds:
                snmp_value = snmp_value[0]
                oid, value = self.__extract_oid_and_value_from_varbind(snmp_value)
                if self.__is_suboid(oid, str_oid) and value.is_valid():
                    result.append((oid, value))
            return tuple(result)
        except socket.error as exc:
            raise exceptions.SNMPSocketError(exc)

    def __convert_to_pysnmp_oid_format(self, str_oid):
        cmd_oid = map(int, str_oid.split('.'))
        return cmd_oid

    def __is_suboid(self, suboid, initial_oid):
        return suboid[0:len(initial_oid)+1] == (initial_oid + '.')

    def __extract_oid_and_value_from_varbind(self, snmp_value):
        oid = str(snmp_value[0])
        value = types.PySnmpValue(snmp_value[1])
        return oid, value

    def set(self, host, community, snmp_values, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        snmp_values = self._regenerate_snmp_types_from(snmp_values)
        try:
            err_indication, err_status, err_index, var_binds = cmdgen.CommandGenerator().setCmd(
                cmdgen.CommunityData('my-agent', community),
                cmdgen.UdpTransportTarget((host, port), timeout=timeout, retries=retries), *snmp_values)

            if err_indication:
                raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
            if err_status:
                raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

        except socket.error as exc:
            raise exceptions.SNMPSocketError(exc)

    def _regenerate_snmp_types_from(self, snmp_values):
        return [(oid, value.__class__(value)) for oid, value in snmp_values]
