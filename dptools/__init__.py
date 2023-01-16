import os
__version__ = '1.1.1'

# suppress annoying tensorflow warnings
os.environ["KMP_WARNINGS"] = "0"
os.environ["KMP_BLOCKTIME"] = "0"
