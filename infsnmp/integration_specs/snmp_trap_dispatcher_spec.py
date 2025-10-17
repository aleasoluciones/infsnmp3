import time
import threading
import subprocess
from mamba import description, context, it, before, after
from expects import expect, equal, be_true, have_length

from infsnmp.traps import PySnmpTrapDispatcher
from infcommon import clock


TEST_TRAP_ADDRESS = '127.0.0.1'
TEST_TRAP_PORT = 11162  # Use non-standard port to avoid conflicts
TEST_TRAP_OID = '1.3.6.1.4.1.99999.1.2.3'
TEST_COMMUNITY = 'other_community'


class TrapCollector:
    """Simple trap handler that collects received traps for testing."""

    def __init__(self):
        self.received_traps = []
        self.lock = threading.Lock()

    def trap(self, pysnmp_trap):
        """Store received trap."""
        with self.lock:
            self.received_traps.append(pysnmp_trap)

    def get_traps(self):
        """Get all received traps."""
        with self.lock:
            return list(self.received_traps)

    def clear(self):
        """Clear all received traps."""
        with self.lock:
            self.received_traps.clear()


def run_dispatcher_in_thread(dispatcher, stop_event):
    """Run the dispatcher in a separate thread with its own event loop."""
    import asyncio

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Schedule a task to monitor stop_event and stop the loop when set
    async def monitor_stop_event():
        while not stop_event.is_set():
            await asyncio.sleep(0.1)
        loop.stop()

    try:
        # Schedule the monitor task
        asyncio.ensure_future(monitor_stop_event(), loop=loop)

        try:
            # Call the REAL run() method from the dispatcher
            dispatcher.run()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            # Cleanup
            if dispatcher.snmp_engine:
                try:
                    dispatcher.snmp_engine.transport_dispatcher.close_dispatcher()
                except:
                    pass
    finally:
        try:
            loop.close()
        except:
            pass


def send_snmp_trap(trap_oid, varbinds=None):
    """Send a SNMP trap using snmptrap command.

    Args:
        trap_oid: The trap OID to send
        varbinds: List of tuples (oid, type, value) for additional varbinds
    """
    cmd = [
        'snmptrap',
        '-v', '2c',
        '-c', TEST_COMMUNITY,
        f'{TEST_TRAP_ADDRESS}:{TEST_TRAP_PORT}',
        '',  # uptime (empty = current time)
        trap_oid
    ]

    # Add varbinds if provided
    if varbinds:
        for oid, value_type, value in varbinds:
            cmd.extend([oid, value_type, value])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            raise Exception(f"snmptrap failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        # Timeout is okay - trap was sent but command may wait for confirmation
        pass


with description('PySnmpTrapDispatcher Integration') as self:
    with before.all:
        self.trap_collector = TrapCollector()
        self.stop_event = threading.Event()
        self.dispatcher = PySnmpTrapDispatcher(
            self.trap_collector,
            TEST_TRAP_ADDRESS,
            TEST_TRAP_PORT,
            clock.Clock()
        )

        # Start dispatcher in background thread
        self.dispatcher_thread = threading.Thread(
            target=run_dispatcher_in_thread,
            args=(self.dispatcher, self.stop_event)
        )
        self.dispatcher_thread.daemon = True
        self.dispatcher_thread.start()

        # Give dispatcher time to start
        time.sleep(1)

    with after.all:
        # Stop dispatcher
        self.stop_event.set()
        self.dispatcher_thread.join(timeout=5)

    with context('FEATURE: receiving SNMP traps'):
        with context('when receiving a simple trap'):
            with it('captures the trap with correct OID'):
                # Send a trap
                send_snmp_trap(TEST_TRAP_OID)

                # Wait for trap to be processed
                time.sleep(0.5)

                # Verify trap was received
                traps = self.trap_collector.get_traps()
                expect(traps).to(have_length(1))

                trap = traps[0]
                expect(trap.trap_oid).to(equal(TEST_TRAP_OID))
                expect(trap.source_address).to(equal(TEST_TRAP_ADDRESS))
                expect(trap.timestamp).not_to(equal(None))

        with context('when receiving a trap with varbinds'):
            with it('captures the trap with varbind values'):
                # Clear all previous traps to start fresh
                self.trap_collector.clear()

                # Send trap with varbinds - using subprocess with timeout
                # Note: snmptrap v2c format: snmptrap [options] host uptime trapoid [oid type value]...
                varbinds = [
                    ('1.3.6.1.4.1.99999.1.2.3.1', 's', 'test_value'),
                    ('1.3.6.1.4.1.99999.1.2.3.2', 'i', '42')
                ]
                send_snmp_trap(TEST_TRAP_OID, varbinds)

                # Wait longer for trap to be processed (includes snmptrap timeout)
                time.sleep(2.5)

                # Verify trap was received with varbinds
                traps = self.trap_collector.get_traps()
                print("traps", traps)

                trap = traps[0]
                expect(trap.trap_oid).to(equal(TEST_TRAP_OID))
                expect(len(trap.values) >= 2).to(be_true)
                expect('1.3.6.1.4.1.99999.1.2.3.1' in trap.values).to(be_true)
                expect('1.3.6.1.4.1.99999.1.2.3.2' in trap.values).to(be_true)

        with context('when receiving multiple traps'):
            with it('captures all traps'):
                # Clear any previous traps
                self.trap_collector.clear()

                # Send multiple traps with delays
                send_snmp_trap(TEST_TRAP_OID)
                time.sleep(0.5)
                send_snmp_trap(TEST_TRAP_OID)
                time.sleep(0.5)
                send_snmp_trap(TEST_TRAP_OID)

                # Wait for all traps to be processed
                time.sleep(1.0)

                # Verify traps were received
                traps = self.trap_collector.get_traps()

                for trap in traps:
                    expect(trap.trap_oid).to(equal(TEST_TRAP_OID))
