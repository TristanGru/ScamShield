import sys
import os

# Add pi/ to path so modules like config, db, detection can be imported directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pi"))
