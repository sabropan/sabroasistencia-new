import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

# Estética institucional
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    .metric-card { 
        background-color: white; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabroasistencia: Panel de Control")

with st.sidebar:
    fecha_sel = st.date_input("Fecha de auditoría:", datetime.now())

try:
    # Consultamos la vista maestra que une empleados con logs
    query = conn.table("daily_attendance_summary").select("*").execute()
    df_raw = pd.DataFrame(query.data)

    if not df_raw.empty:
        df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
        df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel].copy()

        if not df_hoy.empty:
            # Resumen en tarjetas
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{len(df_hoy[df_hoy["salida"].isna()])}</h2></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{len(df_hoy[df_hoy["salida"].notna()])}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            # --- AJUSTE QUIRÚRGICO DE TABLA ---
            df_view = df_hoy[['persona', 'entrada', 'salida', 'tiempo_total', 'tardanza']].copy()
            df_view.columns = ['Empleado', 'Entrada', 'Salida', 'Jornada Total', '¿Tarde?']

            # Formato 12h para horas
            df_view['Entrada'] = pd.to_datetime(df_view['Entrada']).dt.strftime('%I:%M %p')
            df_view['Salida'] = pd.to_datetime(df_view['Salida']).dt.strftime('%I:%M %p').fillna("---")
            
            # Formato HH:MM para la Jornada (Elimina microsegundos)
            df_view['Jornada Total'] = df_view['Jornada Total'].astype(str).str[:5].replace(['None', 'nan', '00:00'], '---')

            st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No hay registros para el día {fecha_sel.strftime('%d/%m/%Y')}")
except Exception as e:
    st.error(f"Error: {e}")
