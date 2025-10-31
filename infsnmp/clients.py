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

    def __init__(self):
        self.snmp_engine = SnmpEngine()
        self.context_data = ContextData()

    def get(self, host, community, oids, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        async def _async_get():
            try:
                object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids]

                err_indication, err_status, err_index, var_binds = await get_cmd(
                    self.snmp_engine,
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    self.context_data,
                    *object_types
                )

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
            finally:
                gc.collect()

        return self._run_coroutine(_async_get())

    def walk(self, host, community, str_oid, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        async def _async_walk():
            try:
                result = []

                async for (err_indication, err_status, err_index, var_binds) in walk_cmd(
                    self.snmp_engine,
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    self.context_data,
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

                return tuple(result)
            except socket.error as exc:
                raise exceptions.SNMPSocketError(exc)
            finally:
                gc.collect()

        return self._run_coroutine(_async_walk())

    def bulk_walk(self, host, community, str_oid, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, non_repeaters=0, max_repetitions=50):
        async def _async_bulk_walk():
            try:
                result = []

                async for (err_indication, err_status, err_index, var_binds) in bulk_walk_cmd(
                    self.snmp_engine,
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    self.context_data,
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

                return tuple(result)
            except socket.error as exc:
                raise exceptions.SNMPSocketError(exc)
            finally:
                gc.collect()

        return self._run_coroutine(_async_bulk_walk())

    def set(self, host, community, snmp_values, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
        async def _async_set():
            try:
                object_types = [ObjectType(ObjectIdentity(oid), self._to_pysnmp_value(value))
                               for oid, value in snmp_values]

                err_indication, err_status, err_index, _ = await set_cmd(
                    self.snmp_engine,
                    CommunityData(community),
                    await UdpTransportTarget.create((host, port), timeout=timeout, retries=retries),
                    self.context_data,
                    *object_types
                )

                if err_indication:
                    raise exceptions.SNMPLevelError(msg="SNMP error %s - %s" % (host, err_indication))
                if err_status:
                    raise exceptions.SNMPLevelError(msg="SNMP PDU-level error %s status %s at %s" % (host, err_status, err_index))

            except socket.error as exc:
                raise exceptions.SNMPSocketError(exc)
            finally:
                gc.collect()

        return self._run_coroutine(_async_set())

    def __is_suboid(self, suboid, initial_oid):
        return suboid[0:len(initial_oid) + 1] == (initial_oid + '.')

    def _to_pysnmp_value(self, value):
        """Convert primitive values to pysnmp objects if needed."""
        # If it's already a pysnmp object, return as is
        if hasattr(value, 'getTagSet'):
            return value

        # Convert primitive types to pysnmp objects
        if isinstance(value, bytes):
            return rfc1902.OctetString(value)
        if isinstance(value, int):
            return rfc1902.Integer(value)
        if isinstance(value, str):
            return rfc1902.OctetString(value)
        # Try to use it as is, let pysnmp handle it
        return value

    def _run_coroutine(self, coro):
        """
        Executes a coroutine handling different event loop scenarios.

        This method properly handles:
        - No event loop exists: creates a new one with asyncio.run()
        - Event loop exists but not running: uses run_until_complete()
        - Event loop is running (e.g., Tornado, FastAPI): uses nest_asyncio as fallback

        Args:
            coro: A coroutine to execute

        Returns:
            The result of the coroutine execution
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(coro)

        if loop.is_running():
            # Event loop is already running (e.g., Tornado, FastAPI)
            # We need nest_asyncio to allow nested event loops
            nest_asyncio.apply()
            return asyncio.run(coro)
        # Event loop exists but is not running
        return loop.run_until_complete(coro)
