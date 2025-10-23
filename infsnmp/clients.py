import socket
import nest_asyncio
import asyncio
# HOTFIX due to memory leak problems with pysnmp, we have to manually garbace collect after snmp commands
import gc

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd, walk_cmd, bulk_walk_cmd, set_cmd
)
from pysnmp.proto import rfc1902
from pysnmp.smi.error import NoSuchObjectError

from infsnmp import types, exceptions


class PySnmpClient:
    AGENT_ID = 'felix_agent'
    DEFAULT_BULK_SIZE = 205
    DEFAULT_TIMEOUT = 5
    DEFAULT_RETRIES = 2
    DEFAULT_PORT = 161

    def get(self, host, community, oids, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        async def _async_get():
            try:
                object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids]

                err_indication, err_status, err_index, var_binds = await get_cmd(
                    SnmpEngine(),
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    ContextData(),
                    *object_types
                )

                gc.collect()

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
            except NoSuchObjectError:
                raise exceptions.InvalidOIDError()

        return asyncio.run(_async_get())

    def walk(self, host, community, str_oid, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        async def _async_walk():
            try:
                result = []

                async for (err_indication, err_status, err_index, var_binds) in walk_cmd(
                    SnmpEngine(),
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(str_oid)),
                    lexicographicMode=False
                ):
                    if err_indication:
                        raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
                    if err_status:
                        raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

                    for var_bind in var_binds:
                        oid = str(var_bind[0])
                        value = types.PySnmpValue(var_bind[1])
                        if self.__is_suboid(oid, str_oid) and value.is_valid():
                            result.append((oid, value))

                gc.collect()
                return tuple(result)
            except socket.error as exc:
                raise exceptions.SNMPSocketError(exc)

        return asyncio.run(_async_walk())

    def bulk_walk(self, host, community, str_oid, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, non_repeaters=0, max_repetitions=50):
        async def _async_bulk_walk():
            try:
                result = []

                async for (err_indication, err_status, err_index, var_binds) in bulk_walk_cmd(
                    SnmpEngine(),
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    ContextData(),
                    non_repeaters,
                    max_repetitions,
                    ObjectType(ObjectIdentity(str_oid)),
                    lexicographicMode=False
                ):
                    if err_indication:
                        raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
                    if err_status:
                        raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

                    for var_bind in var_binds:
                        oid = str(var_bind[0])
                        value = types.PySnmpValue(var_bind[1])
                        if self.__is_suboid(oid, str_oid) and value.is_valid():
                            result.append((oid, value))

                gc.collect()
                return tuple(result)
            except socket.error as exc:
                raise exceptions.SNMPSocketError(exc)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return asyncio.run(_async_bulk_walk())
        if loop.is_running():
            nest_asyncio.apply()
            return asyncio.run(_async_bulk_walk())
        return loop.run_until_complete(_async_bulk_walk())

    def __convert_to_pysnmp_oid_format(self, str_oid):
        cmd_oid = list(map(int, str_oid.split('.')))
        return cmd_oid

    def __is_suboid(self, suboid, initial_oid):
        return suboid[0:len(initial_oid) + 1] == (initial_oid + '.')

    def __extract_oid_and_value_from_varbind(self, snmp_value):
        oid = str(snmp_value[0])
        value = types.PySnmpValue(snmp_value[1])
        return oid, value

    def set(self, host, community, snmp_values, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        async def _async_set():
            try:
                object_types = [ObjectType(ObjectIdentity(oid), self._to_pysnmp_value(value))
                               for oid, value in snmp_values]

                err_indication, err_status, err_index, var_binds = await set_cmd(
                    SnmpEngine(),
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    ContextData(),
                    *object_types
                )

                gc.collect()

                if err_indication:
                    raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
                if err_status:
                    raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

            except socket.error as exc:
                raise exceptions.SNMPSocketError(exc)

        return asyncio.run(_async_set())

    def _to_pysnmp_value(self, value):
        """Convert primitive values to pysnmp objects if needed."""
        # If it's already a pysnmp object, return as is
        if hasattr(value, 'getTagSet'):
            return value

        # Convert primitive types to pysnmp objects
        if isinstance(value, bytes):
            return rfc1902.OctetString(value)
        elif isinstance(value, int):
            return rfc1902.Integer(value)
        elif isinstance(value, str):
            return rfc1902.OctetString(value)
        else:
            # Try to use it as is, let pysnmp handle it
            return value
