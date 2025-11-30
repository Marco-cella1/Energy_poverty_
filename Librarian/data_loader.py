import streamlit as st
from Librarian.models import WorldDataset
from Librarian.config import INDICATORS

@st.cache_data
def load_world():
    """Download and cache the World Bank panel."""
    world = WorldDataset.from_api(INDICATORS, years=range(2000, 2023))
    return world