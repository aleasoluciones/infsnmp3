#!/usr/bin/env python3
"""
Object tracking test to identify leaked Python objects in infsnmp3.

This script performs detailed tracking of Python objects to identify what
is not being garbage collected properly. It specifically looks for:
- SnmpEngine objects that should be cleaned up but aren't
- Event loop objects accumulating
- Other pysnmp-related objects leaking
- Reference counts preventing garbage collection

Usage:
    python test_object_tracking.py

Requirements:
    - snmpd running on localhost:1161 (running dependencies is ok)
    - infsnmp3 library installed
"""

import asyncio
import gc
import sys
import tracemalloc
from collections import defaultdict
from infsnmp.clients import PySnmpClient


def count_objects_by_type():
    """
    Count all Python objects grouped by type.

    Returns:
        dict: Mapping of type name to count
    """
    type_counts = defaultdict(int)
    for obj in gc.get_objects():
        type_name = type(obj).__name__
        type_counts[type_name] += 1
    return type_counts


def find_snmp_objects():
    """
    Find all pysnmp-related objects in memory.

    Returns:
        dict: Mapping of object type to list of objects
    """
    snmp_objects = defaultdict(list)
    keywords = [
        'SnmpEngine', 'UdpTransportTarget', 'CommunityData',
        'CommandGenerator', 'UdpSocketTransport', 'AsyncioDispatcher',
        'getCmd', 'nextCmd', 'bulkCmd', 'setCmd'
    ]

    for obj in gc.get_objects():
        type_name = type(obj).__name__
        # Check if this is a pysnmp object
        for keyword in keywords:
            if keyword.lower() in type_name.lower():
                snmp_objects[type_name].append(obj)
                break

        # Also check module name
        module = getattr(type(obj), '__module__', '')
        if 'pysnmp' in module or 'pyasn1' in module:
            snmp_objects[type_name].append(obj)

    return snmp_objects


async def track_snmp_operations(iterations=50, host='127.0.0.1', port=1161):
    """
    Track object creation/destruction during SNMP operations.

    Args:
        iterations: Number of SNMP operations to perform
        host: SNMP host to query
        port: SNMP port
    """
    print("=" * 80)
    print("OBJECT TRACKING TEST")
    print("=" * 80)
    print(f"\nTracking object lifecycle during {iterations} SNMP operations")
    print(f"Target: {host}:{port}")
    print("\nThis test runs in Scenario 3 (event loop running - production mode)")
    print("=" * 80)

    client = PySnmpClient()

    # Baseline: Count objects before any operations
    print("\n[BASELINE] Counting objects before SNMP operations...")
    gc.collect()
    gc.collect()  # Double collect to ensure cleanup
    gc.collect()

    before_count = len(gc.get_objects())
    before_types = count_objects_by_type()
    before_snmp = find_snmp_objects()

    print(f"  Total objects: {before_count:,}")
    print(f"  SNMP-related object types: {len(before_snmp)}")

    # Perform SNMP operations
    print(f"\n[OPERATIONS] Executing {iterations} SNMP operations...")

    for i in range(iterations):
        try:
            result = client.get(host, 'public', ['1.3.6.1.2.1.1.1.0'], port=port)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{iterations}")

        except Exception as e:
            print(f"\n⚠️  Error at iteration {i + 1}: {e}")
            print(f"    Make sure snmpd is running on {host}:{port}")
            break

    # Force garbage collection multiple times
    print("\n[CLEANUP] Forcing garbage collection...")
    collected = []
    for i in range(3):
        collected.append(gc.collect())
        print(f"  GC pass {i + 1}: collected {collected[-1]} objects")

    # Count objects after operations
    print("\n[ANALYSIS] Analyzing remaining objects...")
    after_count = len(gc.get_objects())
    after_types = count_objects_by_type()
    after_snmp = find_snmp_objects()

    leaked_objects = after_count - before_count
    leaked_percent = (leaked_objects / before_count * 100) if before_count > 0 else 0

    print(f"  Total objects: {after_count:,}")
    print(f"  SNMP-related object types: {len(after_snmp)}")
    print(f"  Leaked objects: {leaked_objects:,} ({leaked_percent:+.1f}%)")

    # Analyze type differences
    print("\n[LEAKED TYPES] Top 10 object types that leaked:")
    type_differences = {}
    for type_name in set(after_types.keys()) | set(before_types.keys()):
        diff = after_types[type_name] - before_types[type_name]
        if diff > 0:
            type_differences[type_name] = diff

    sorted_diffs = sorted(type_differences.items(), key=lambda x: x[1], reverse=True)
    for i, (type_name, count) in enumerate(sorted_diffs[:10], 1):
        print(f"  {i:2d}. {type_name:30s}: +{count:5d} objects")

    # Analyze SNMP-specific objects
    print("\n[SNMP OBJECTS] SNMP-related objects analysis:")

    if not after_snmp:
        print("  ✓ No SNMP objects remaining (good!)")
    else:
        print(f"  ⚠️  Found {sum(len(objs) for objs in after_snmp.values())} SNMP-related objects:")

        for type_name, objs in sorted(after_snmp.items(), key=lambda x: len(x[1]), reverse=True):
            before_snmp_count = len(before_snmp.get(type_name, []))
            leaked_snmp_count = len(objs) - before_snmp_count

            if leaked_snmp_count > 0:
                print(f"    - {type_name:30s}: {leaked_snmp_count:3d} leaked")

                # Show reference count for first leaked object
                if objs and leaked_snmp_count > 0:
                    first_leaked_idx = before_snmp_count
                    if first_leaked_idx < len(objs):
                        obj = objs[first_leaked_idx]
                        ref_count = sys.getrefcount(obj) - 1  # -1 for temporary reference in getrefcount
                        print(f"      (ref count: {ref_count})")

    # Find objects with high reference counts (potential circular references)
    print("\n[REFERENCE ANALYSIS] Looking for circular references...")
    high_refs = []

    for type_name, objs in after_snmp.items():
        before_snmp_count = len(before_snmp.get(type_name, []))
        for i, obj in enumerate(objs):
            if i >= before_snmp_count:  # Only check leaked objects
                ref_count = sys.getrefcount(obj) - 1
                if ref_count > 10:  # Arbitrary threshold
                    high_refs.append((type_name, obj, ref_count))

    if high_refs:
        print(f"  ⚠️  Found {len(high_refs)} objects with >10 references (possible circular refs):")
        for type_name, obj, ref_count in sorted(high_refs, key=lambda x: x[2], reverse=True)[:5]:
            print(f"    - {type_name:30s}: {ref_count} references")
    else:
        print("  ✓ No objects with excessive references found")

    # Memory statistics
    print("\n[MEMORY] Memory statistics:")
    current, peak = tracemalloc.get_traced_memory()
    print(f"  Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"  Peak memory:    {peak / 1024 / 1024:.2f} MB")

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT:")
    print("=" * 80)

    # Adjusted thresholds based on actual testing with fix applied
    objects_per_op = leaked_objects / iterations

    if leaked_objects > iterations * 100:  # More than 100 objects per operation
        print("🔴 CRITICAL MEMORY LEAK DETECTED!")
        print(f"   Leaked {leaked_objects:,} objects after {iterations} operations")
        print(f"   ({objects_per_op:.1f} objects per operation)")
        print(f"   Memory grew to {current / 1024 / 1024:.2f} MB")
    elif leaked_objects > iterations * 50:  # More than 50 objects per operation
        print("🟡 WARNING: Possible memory leak detected")
        print(f"   Leaked {leaked_objects:,} objects after {iterations} operations")
        print(f"   ({objects_per_op:.1f} objects per operation)")
        print(f"   Memory grew to {current / 1024 / 1024:.2f} MB")
    elif leaked_objects > iterations * 20:  # More than 20 objects per operation
        print("🟢 ACCEPTABLE: Minor object accumulation")
        print(f"   Leaked {leaked_objects:,} objects after {iterations} operations")
        print(f"   ({objects_per_op:.1f} objects per operation)")
        print(f"   Memory grew to {current / 1024 / 1024:.2f} MB")
        print(f"   This is within normal range for Python with GC")
    else:
        print("🟢 EXCELLENT: Object count within optimal range")
        print(f"   Only {leaked_objects:,} objects leaked after {iterations} operations")
        print(f"   ({objects_per_op:.1f} objects per operation)")
        print(f"   Memory grew to {current / 1024 / 1024:.2f} MB")

    if after_snmp:
        snmp_leaked = sum(
            len(objs) - len(before_snmp.get(type_name, []))
            for type_name, objs in after_snmp.items()
        )
        if snmp_leaked > iterations:  # More than 1 per operation
            print(f"\n⚠️  {snmp_leaked} SNMP-related objects were not cleaned up!")
            print("   This indicates SnmpEngine resources are leaking.")
        elif snmp_leaked > 0:
            print(f"\n✅ Only {snmp_leaked} residual SNMP objects (likely from test framework)")
            print("   This is acceptable for a test run.")

    print("=" * 80 + "\n")


def main():
    """Main entry point"""
    # Configuration
    ITERATIONS = 50
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

    # Start memory tracking
    tracemalloc.start()

    # Create event loop and run it (simulates production environment)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(track_snmp_operations(ITERATIONS, HOST, PORT))
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        loop.close()
        tracemalloc.stop()


if __name__ == '__main__':
    main()
