"""
Standalone Test Runner for Fair AI Recruitment System Aggregation Engine.
Discovers and executes all unit and integration test suites.
"""

import sys
import unittest
import time


def main():
    print("=" * 70)
    print("      FAIR AI RECRUITMENT SYSTEM — AGGREGATION ENGINE TEST SUITE")
    print("=" * 70)

    start_time = time.time()
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    duration = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Tests Run:     {result.testsRun}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Skipped:       {len(result.skipped)}")
    print(f"Time Elapsed:  {duration:.3f} seconds")
    print("=" * 70)

    if not result.wasSuccessful():
        print("\n[FAIL] SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("\n[PASS] ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()
