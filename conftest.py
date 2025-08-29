# Ensure project root is on sys.path for test imports
import sys, os
ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
