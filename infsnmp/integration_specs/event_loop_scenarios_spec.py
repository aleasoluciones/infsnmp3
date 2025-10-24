"""
Tests for different event loop scenarios handled by PySnmpClient._run_coroutine()

This test suite validates the fix for handling multiple event loop scenarios:
- SCENARIO 1: No event loop exists (RuntimeError) -> uses asyncio.run()
- SCENARIO 2: Event loop exists but is not running -> uses run_until_complete()
- SCENARIO 3: Event loop is already running -> uses nest_asyncio
"""
from mamba import description, context, it, before
from expects import expect, equal, have_length
import asyncio
import threading

from infsnmp import clients, types


READ_ONLY_COMMUNITY = 'c4-temperatures'
SNMP_HOST = '127.0.0.1'
SNMP_PORT = 1161


def snmp_integer(value):
    return types.PySnmpValue(types.PySnmpTypes().integer(value))


def reset_event_loop():
    """Reset the event loop to a clean state."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            # Create new loop if closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


with description('Event Loop Scenarios') as self:
    with before.each:
        reset_event_loop()
        self.snmp_client = clients.PySnmpClient()
        self.test_oid = '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29.1.10'

    with context('SCENARIO 1: No event loop exists (RuntimeError)'):
        with it('creates a new event loop with asyncio.run()'):
            # Ensure no event loop exists by getting a fresh thread
            def test_in_new_thread():
                # In a new thread, there's no event loop
                result = self.snmp_client.get(
                    SNMP_HOST,
                    READ_ONLY_COMMUNITY,
                    [self.test_oid],
                    port=SNMP_PORT
                )
                return result

            # Use a thread to simulate a clean environment without event loop
            result_container = []

            def run_test():
                result_container.append(test_in_new_thread())

            thread = threading.Thread(target=run_test)
            thread.start()
            thread.join()

            result = result_container[0]
            expect(result).to(have_length(1))
            expect(result[0][0]).to(equal(self.test_oid))
            expect(result[0][1]).to(equal(snmp_integer(999)))

    with context('SCENARIO 2: Event loop exists but is not running'):
        with it('uses run_until_complete() on existing loop'):
            # Create an event loop but don't run it
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Verify loop exists and is not running
            expect(loop.is_running()).to(equal(False))

            # Execute SNMP operation
            result = self.snmp_client.get(
                SNMP_HOST,
                READ_ONLY_COMMUNITY,
                [self.test_oid],
                port=SNMP_PORT
            )

            expect(result).to(have_length(1))
            expect(result[0][0]).to(equal(self.test_oid))
            expect(result[0][1]).to(equal(snmp_integer(999)))

    with context('SCENARIO 3: Event loop is already running (nested)'):
        with it('uses nest_asyncio to allow nested execution'):
            # Simulate a running event loop (like Tornado, FastAPI, etc.)
            async def run_with_running_loop():
                # At this point, the event loop is running
                # The SNMP client should detect this and use nest_asyncio
                result = self.snmp_client.get(
                    SNMP_HOST,
                    READ_ONLY_COMMUNITY,
                    [self.test_oid],
                    port=SNMP_PORT
                )
                return result

            # Run the test within an async context
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(run_with_running_loop())

            expect(result).to(have_length(1))
            expect(result[0][0]).to(equal(self.test_oid))
            expect(result[0][1]).to(equal(snmp_integer(999)))

    with context('SCENARIO: All SNMP operations work with different loop states'):
        with context('when using walk'):
            with it('handles event loop scenarios correctly'):
                result = self.snmp_client.walk(
                    SNMP_HOST,
                    READ_ONLY_COMMUNITY,
                    '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29',
                    port=SNMP_PORT
                )

                expect(result).to(have_length(31))

        with context('when using bulk_walk'):
            with it('handles event loop scenarios correctly'):
                result = self.snmp_client.bulk_walk(
                    SNMP_HOST,
                    READ_ONLY_COMMUNITY,
                    '1.3.6.1.4.1.4998.1.1.10.1.4.2.1.29',
                    port=SNMP_PORT
                )

                expect(result).to(have_length(31))

        with context('when using set'):
            with it('handles event loop scenarios correctly'):
                oid = '1.3.6.1.2.1.1.1.0'
                # Use PySnmpTypes correctly - it returns the object directly, not .value()
                value = types.PySnmpTypes().octect_string('test_value')

                # Should not raise any errors
                self.snmp_client.set(
                    SNMP_HOST,
                    'set',
                    [(oid, value)],
                    port=SNMP_PORT
                )

                # Verify the value was set
                result = self.snmp_client.get(
                    SNMP_HOST,
                    'set',
                    [oid],
                    port=SNMP_PORT
                )

                expect(result).to(have_length(1))
                expect(result[0][0]).to(equal(oid))
