import os
import sys


def result_stream():
    """Keep FastRPC diagnostics on stderr, including native exit messages."""
    output = os.fdopen(os.dup(sys.stdout.fileno()), "w", encoding="utf-8")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    return output
