#!/usr/bin/env python3
"""
Profile SNMP GET operations to identify performance bottlenecks.

Usage:
    python profile_performance.py [iterations]

Example:
    python profile_performance.py 50
"""

import cProfile
import pstats
import sys
from io import StringIO
from infsnmp.clients import PySnmpClient


def profile_snmp_gets(iterations=50):
    """Profile multiple SNMP GET operations."""
    client = PySnmpClient()
    host = '127.0.0.1'
    port = 1161
    oid = '1.3.6.1.2.1.1.1.0'

    # Warm-up
    client.get(host, 'public', [oid], port=port)

    # Profile the operations
    for _ in range(iterations):
        client.get(host, 'public', [oid], port=port)


def main():
    iterations = 50

    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
        except ValueError:
            print(f"Invalid iterations: {sys.argv[1]}, using default {iterations}")

    print("=" * 80)
    print(f"PROFILING {iterations} SNMP GET OPERATIONS")
    print("=" * 80)
    print("\nRunning profiler...\n")

    # Profile the code
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        profile_snmp_gets(iterations)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure snmpd is running: dev/start_infsnmp3_dependencies.sh")
        sys.exit(1)

    profiler.disable()

    # Print results
    print("\n" + "=" * 80)
    print("TOP 30 TIME-CONSUMING FUNCTIONS")
    print("=" * 80)

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(30)

    print(stream.getvalue())

    print("\n" + "=" * 80)
    print("TOP 30 BY TOTAL TIME (including subcalls)")
    print("=" * 80)

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats('tottime')
    stats.print_stats(30)

    print(stream.getvalue())

    # Save to file for detailed analysis
    output_file = 'profile_results.prof'
    stats.dump_stats(output_file)
    print(f"\n✓ Full profile saved to: {output_file}")
    print(f"\nTo visualize with snakeviz:")
    print(f"  pip install snakeviz")
    print(f"  snakeviz {output_file}")
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
