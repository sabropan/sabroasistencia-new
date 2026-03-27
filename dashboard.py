import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="SabroAsistencia", layout="wide")

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://scynlrjnuywjcwovnzxh.supabase.co",
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
)

st.title("🍞 SabroAsistencia")

# Consultamos la vista que procesa los logs automágicamente
try:
    # Traemos los datos de la vista consolidada que ya tienes creada
    query = conn.table("asistencia_consolidada").select("*").execute()
    df = pd.DataFrame(query.data)

    if not df.empty:
        st.dataframe(df)
    else:
        st.warning("No hay registros procesados aún.")
except Exception as e:
    st.error(f"Error de visualización: {e}")
