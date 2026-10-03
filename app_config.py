from __future__ import annotations

import os


def setting(name: str, default: str = "") -> str:
    environment_value = os.environ.get(name)
    if environment_value is not None:
        return environment_value.strip()
    try:
        import streamlit as st

        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, RuntimeError):
        return default
