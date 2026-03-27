import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

st.set_page_config(page_title="SabroAsistencia - Dashboard", layout="wide")

st.title("🍞 SabroAsistencia - Control de Personal")

# 1. Recuperar el Calendario
fecha_seleccionada = st.date_input("Selecciona una fecha:", datetime.now())

# 2. Conexión Directa (Para evitar errores de secrets.toml)
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://scynlrjnuywjcwovnzxh.supabase.co",
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
)

# 3. Consulta a la tabla correcta: asistencia_consolidada
try:
    query = conn.table("asistencia_consolidada").select("*").eq("fecha", str(fecha_seleccionada)).execute()
    df = pd.DataFrame(query.data)

    if not df.empty:
        # Mapeo de los nombres de columna reales a los nombres de la tabla
        df_vista = df.rename(columns={
            'full_name': 'Empleado',
            'hora_entrada_real': 'Hora Entrada',
            'hora_salida_real': 'Hora Salida',
            'duracion_total': 'Jornada Total'
        })
        
        # Selección de columnas para mostrar
        columnas = ['Empleado', 'Hora Entrada', 'Hora Salida', 'Jornada Total']
        st.table(df_vista[columnas])
    else:
        st.warning(f"No se encontraron registros para el día {fecha_seleccionada.strftime('%d/%m/%Y')}")

except Exception as e:
    st.error(f"Error de conexión: {e}")
