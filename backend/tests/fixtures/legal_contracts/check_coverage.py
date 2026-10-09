"""Reproduce B's scoped line coverage, including discovery/import execution, without dependencies."""
import trace
import unittest


def run():
    suite = unittest.TestSuite(unittest.defaultTestLoader.discover("tests", pattern=pattern) for pattern in (
        "test_legal_scope_contracts*.py", "test_legal_scope_summaries*.py", "test_legal_scope_assistant*.py"))
    return unittest.TextTestRunner(verbosity=1).run(suite)


if __name__ == "__main__":
    tracer = trace.Trace(count=True, trace=False, ignoredirs=["/usr/local/lib/python3.11"])
    result = tracer.runfunc(run)
    tracer.results().write_results(show_missing=True, summary=True, coverdir="/tmp/legal-b-coverage")
    raise SystemExit(not result.wasSuccessful())
