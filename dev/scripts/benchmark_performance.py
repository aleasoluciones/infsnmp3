#!/usr/bin/env python3
"""
Simple performance benchmark for infsnmp3 library.

Measures execution time of SNMP GET operations to compare performance
between different versions.

Usage:
    python benchmark_performance.py [iterations] [host] [port]

    iterations: Number of SNMP GET operations (default: 100)
    host: SNMP host to query (default: 127.0.0.1)
    port: SNMP port (default: 1161)

Example:
    python benchmark_performance.py 100 127.0.0.1 1161

Requirements:
    - snmpd running on target host:port (start with dev/start_infsnmp3_dependencies.sh)
    - infsnmp3 library installed
"""

import sys
import time
from statistics import mean, median, stdev
from infsnmp.clients import PySnmpClient


def main():
    """Main entry point."""
    # Configuration
    ITERATIONS = 100
    HOST = '127.0.0.1'
    PORT = 1161

    # Parse command line arguments
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

    print("=" * 80)
    print("SNMP GET PERFORMANCE BENCHMARK")
    print("=" * 80)
    print(f"\nTarget: {HOST}:{PORT}")
    print(f"Operations: {ITERATIONS} SNMP GET requests")
    print(f"OID: 1.3.6.1.2.1.1.1.0 (sysDescr)")
    print("\n" + "-" * 80)

    client = PySnmpClient()
    timings = []

    # Warm-up request (first request is always slower)
    try:
        print("Performing warm-up request...")
        client.get(HOST, 'public', ['1.3.6.1.2.1.1.1.0'], port=PORT)
        print("✓ Warm-up complete\n")
    except Exception as e:
        print(f"\n⚠️  Error during warm-up: {e}")
        print(f"   Make sure snmpd is running on {HOST}:{PORT}")
        print(f"   Start dependencies with: dev/start_infsnmp3_dependencies.sh")
        sys.exit(1)

    # Benchmark
    print("Running benchmark...")
    overall_start = time.perf_counter()

    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            result = client.get(
                HOST,
                'public',
                ['1.3.6.1.2.1.1.1.0'],
                port=PORT
            )
            end = time.perf_counter()

            elapsed_ms = (end - start) * 1000
            timings.append(elapsed_ms)

            # Progress indicator every 10 operations
            if (i + 1) % 10 == 0:
                avg_so_far = mean(timings)
                print(f"Progress: {i + 1:3d}/{ITERATIONS} ops | "
                      f"Avg: {avg_so_far:6.2f} ms/op | "
                      f"Last: {elapsed_ms:6.2f} ms")

        except Exception as e:
            print(f"\n⚠️  Error at iteration {i + 1}: {e}")
            sys.exit(1)

    overall_end = time.perf_counter()
    total_time = overall_end - overall_start

    # Calculate statistics
    avg_time = mean(timings)
    med_time = median(timings)
    min_time = min(timings)
    max_time = max(timings)
    std_time = stdev(timings) if len(timings) > 1 else 0
    ops_per_sec = ITERATIONS / total_time if total_time > 0 else 0

    # Print results
    print("\n" + "-" * 80)
    print("RESULTS:")
    print("-" * 80)
    print(f"Total time:        {total_time:8.3f} seconds")
    print(f"Operations:        {ITERATIONS:8d}")
    print(f"Throughput:        {ops_per_sec:8.2f} ops/sec")
    print(f"\nPer-operation timing:")
    print(f"  Average:         {avg_time:8.2f} ms")
    print(f"  Median:          {med_time:8.2f} ms")
    print(f"  Min:             {min_time:8.2f} ms")
    print(f"  Max:             {max_time:8.2f} ms")
    print(f"  Std deviation:   {std_time:8.2f} ms")

    # Performance verdict
    print(f"\nPERFORMANCE ASSESSMENT:")
    if avg_time < 10:
        print(f"🟢 EXCELLENT: {avg_time:.2f} ms/op - Very fast")
    elif avg_time < 25:
        print(f"🟢 GOOD: {avg_time:.2f} ms/op - Acceptable performance")
    elif avg_time < 50:
        print(f"🟡 MODERATE: {avg_time:.2f} ms/op - Slower than expected")
    else:
        print(f"🔴 SLOW: {avg_time:.2f} ms/op - Performance issue detected")

    print("\n" + "=" * 80)
    print("\nTo compare with another version:")
    print("1. Note the 'Average' and 'Throughput' values above")
    print("2. Switch to the other version (git checkout, change virtualenv, etc.)")
    print("3. Run this script again with the same parameters")
    print("4. Compare the results manually")
    print("=" * 80)


if __name__ == '__main__':
    main()
