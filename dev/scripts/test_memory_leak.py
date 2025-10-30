#!/usr/bin/env python3
"""
Memory leak reproduction test for infsnmp3 library.

This script simulates production scenario where an event loop is already running
(like in Tornado or FastAPI applications) and executes multiple SNMP operations
to demonstrate the memory leak .

Usage:
    python test_memory_leak.py

Requirements:
    - snmpd running on localhost:1161 (running dependencies is ok)
    - infsnmp3 library installed
"""

import asyncio
import gc
import tracemalloc
import sys
from infsnmp.clients import PySnmpClient


async def simulate_production_leak(iterations=1000, host='127.0.0.1', port=1161):
    """
    Simulates production scenario with event loop running.

    Args:
        iterations: Number of SNMP operations to perform
        host: SNMP host to query
        port: SNMP port
    """
    print("=" * 80)
    print("MEMORY LEAK REPRODUCTION TEST")
    print("=" * 80)
    print(f"\nSimulating production scenario (event loop running)")
    print(f"Will execute {iterations} SNMP get operations")
    print(f"Target: {host}:{port}")
    print("\nMonitoring memory growth...\n")

    # Start memory tracking
    tracemalloc.start()

    client = PySnmpClient()

    # Take initial snapshot
    snapshot1 = tracemalloc.take_snapshot()
    initial_current, initial_peak = tracemalloc.get_traced_memory()

    print(f"Initial memory: {initial_current / 1024 / 1024:.2f} MB")
    print("-" * 80)

    # Simulate production load - many SNMP requests
    for i in range(iterations):
        try:
            # This will trigger the problematic code path:
            # - _run_coroutine() detects running loop
            # - Calls asyncio.run() which creates NEW loop
            # - Creates SnmpEngine() without cleanup
            result = client.get(
                host,
                'public',
                ['1.3.6.1.2.1.1.1.0'],  # sysDescr OID
                port=port
            )

            # Report every 100 iterations
            if (i + 1) % 100 == 0:
                gc.collect()  # Force garbage collection like the code does
                snapshot2 = tracemalloc.take_snapshot()
                current, peak = tracemalloc.get_traced_memory()

                # Calculate growth
                growth_mb = (current - initial_current) / 1024 / 1024
                growth_percent = ((current - initial_current) / initial_current * 100) if initial_current > 0 else 0

                print(f"Iteration {i + 1:4d}: "
                      f"Current: {current / 1024 / 1024:7.2f} MB | "
                      f"Peak: {peak / 1024 / 1024:7.2f} MB | "
                      f"Growth: +{growth_mb:6.2f} MB ({growth_percent:+6.1f}%)")

                # Show top memory allocations every 500 iterations
                if (i + 1) % 500 == 0:
                    print("\n  Top 5 memory allocations since start:")
                    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
                    for stat in top_stats[:5]:
                        print(f"    {stat}")
                    print()

        except Exception as e:
            print(f"\n⚠️  Error at iteration {i + 1}: {e}")
            print(f"    Make sure snmpd is running on {host}:{port}")
            print(f"    You can change host/port in the script if needed")
            break

    # Final report
    print("-" * 80)
    gc.collect()
    final_current, final_peak = tracemalloc.get_traced_memory()
    total_growth = (final_current - initial_current) / 1024 / 1024
    growth_per_op = (total_growth / iterations * 1024) if iterations > 0 else 0

    # Calculate growth rate (MB per 100 operations for normalization)
    growth_per_100 = (total_growth / iterations * 100) if iterations > 0 else 0

    print(f"\nFINAL RESULTS:")
    print(f"  Initial memory: {initial_current / 1024 / 1024:.2f} MB")
    print(f"  Final memory:   {final_current / 1024 / 1024:.2f} MB")
    print(f"  Peak memory:    {final_peak / 1024 / 1024:.2f} MB")
    print(f"  Total growth:   +{total_growth:.2f} MB")
    print(f"  Growth per op:  +{growth_per_op:.2f} KB")
    print(f"  Growth per 100 ops: +{growth_per_100:.2f} MB")

    # Verdict based on absolute growth (normalized per 100 operations)
    # These thresholds are based on actual testing after the fix
    print(f"\nVERDICT:")
    if growth_per_100 > 50:  # More than 50 MB per 100 operations
        print(f"🔴 CRITICAL MEMORY LEAK!")
        print(f"   Growing +{growth_per_100:.2f} MB per 100 operations")
        print(f"   This indicates a severe memory leak that needs immediate attention")
    elif growth_per_100 > 10:  # More than 10 MB per 100 operations
        print(f"🟡 WARNING: Possible memory leak")
        print(f"   Growing +{growth_per_100:.2f} MB per 100 operations")
        print(f"   This is higher than expected, investigate potential leaks")
    elif growth_per_100 > 5:  # More than 5 MB per 100 operations
        print(f"🟢 ACCEPTABLE: Minor memory growth")
        print(f"   Growing +{growth_per_100:.2f} MB per 100 operations")
        print(f"   Within acceptable range for Python with GC")
    else:  # Less than 5 MB per 100 operations
        print(f"🟢 EXCELLENT: Memory stable!")
        print(f"   Growing only +{growth_per_100:.2f} MB per 100 operations")
        print(f"   Memory usage is optimal, no significant leak detected")

    print("\n" + "=" * 80)

    tracemalloc.stop()


def main():
    """Main entry point"""
    # Configuration
    ITERATIONS = 1000
    HOST = '127.0.0.1'
    PORT = 1161

    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        try:
            ITERATIONS = int(sys.argv[1])
        except ValueError:
            print(f"Invalid iterations: {sys.argv[1]}, using default {ITERATIONS}")

    if len(sys.argv) > 2:
        HOST = sys.argv[2]

    if len(sys.argv) > 3:
        try:
            PORT = int(sys.argv[3])
        except ValueError:
            print(f"Invalid port: {sys.argv[3]}, using default {PORT}")

    # Create event loop and run it (simulates Tornado/FastAPI production environment)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(simulate_production_leak(ITERATIONS, HOST, PORT))
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        loop.close()


if __name__ == '__main__':
    main()
