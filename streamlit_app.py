
import streamlit as st
import os
import sys
import importlib.util

# ------------------------------------------------------------------------------
# STREAMLIT CLOUD ENTRYPOINT
# ------------------------------------------------------------------------------
# This file is the root entrypoint for Streamlit Cloud deployment.
# It sets up the python path correctly and then imports the actual app
# from the 07_streamlit_demo directory.
# ------------------------------------------------------------------------------

# Define paths
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_DEMO_DIR = os.path.join(_REPO_ROOT, "K-12-Sales-Toolkit", "07_streamlit_demo")
_SRC_DIR = os.path.join(_REPO_ROOT, "K-12-Sales-Toolkit", "src")

# Add directories to sys.path so imports work
if _DEMO_DIR not in sys.path:
    sys.path.insert(0, _DEMO_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Import the main app module safely
# We use importlib to avoid issues with running a script inside another script
# and to preserve __file__ resolution in the target app.
spec = importlib.util.spec_from_file_location("app", os.path.join(_DEMO_DIR, "app.py"))
app_module = importlib.util.module_from_spec(spec)
app_module.__file__ = os.path.join(_DEMO_DIR, "app.py")
sys.modules["app"] = app_module
spec.loader.exec_module(app_module)
