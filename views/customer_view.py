import streamlit as st
import pandas as pd

def customer_view(data):
    st.title("📦 Track Your Order")
    st.caption("Real-time visibility into your order and support")

    st.dataframe(data["orders"].head())
