import os
import shutil
import pytest
import pandas as pd

@pytest.fixture(scope="session", autouse=True)
def ensure_superstore_sales_exists():
    """Session fixture to ensure that superstore_sales.csv exists in the project root."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(root_dir, "superstore_sales.csv")
    source_path = os.path.join(root_dir, "data", "superstore_sales.csv")
    
    copied = False
    if not os.path.exists(target_path) and os.path.exists(source_path):
        shutil.copy(source_path, target_path)
        copied = True
        
    yield
    
    if copied and os.path.exists(target_path):
        try:
            os.remove(target_path)
        except OSError:
            pass

@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    import streamlit as st
    try:
        st.cache_data.clear()
    except Exception:
        pass
    yield
    try:
        st.cache_data.clear()
    except Exception:
        pass
