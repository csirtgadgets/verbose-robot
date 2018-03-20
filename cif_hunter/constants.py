import os

ENABLED = os.getenv('CIF_HUNTER_ADVANCED', False)
if ENABLED == '1':
    ENABLED = True
