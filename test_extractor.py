#!/usr/bin/env python3
"""
Simple test script for code_extractor.py
Tests extraction using the valgrind.log file
"""

import sys
sys.path.insert(0, '/home/claude')

from valgrind_parser import parse_valgrind_report
from code_extractor import extract_call_stack, format_for_ai

def main():
    # Parse the valgrind log
    log_file = 'test_valgrind.log'
    print(f"📖 Parsing {log_file}...")

    try:
        with open(log_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File {log_file} not found. Run Valgrind first:")
        print("   valgrind --leak-check=full ./push_swap 3 2 1 > test_valgrind.log 2>&1")
        return

    result = parse_valgrind_report(content)

    # Check if there are leaks
    if not result['has_leaks']:
        print("✅ No memory leaks detected!")
        return

    leaks = result['leaks']
    print(f"✅ Found {len(leaks)} leak(s)\n")

    if not leaks:
        print("❌ No leak details found")
        return

    # Take the first leak
    leak = leaks[0]
    print(f"🔍 Testing with leak:")
    print(f"   Type: {leak['type']}")
    print(f"   Size: {leak['bytes']} bytes in {leak['blocks']} block(s)")
    print(f"   Location: {leak['file']}:{leak['line']} in {leak['function']}\n")

    # Extract code from backtrace
    if 'backtrace' in leak and leak['backtrace']:
        print("📚 Extracting code from call stack...")
        extracted = extract_call_stack(leak['backtrace'])

        if extracted:
            print(f"✅ Successfully extracted {len(extracted)} functions\n")

            # Format for AI
            formatted = format_for_ai(extracted)
            print("=" * 60)
            print(formatted)
            print("=" * 60)
        else:
            print("⚠️  No code could be extracted (files might not exist or are system files)")
    else:
        print("⚠️  No backtrace found in this leak")

if __name__ == "__main__":
    main()
