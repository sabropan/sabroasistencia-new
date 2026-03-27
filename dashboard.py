import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# --- 1. ESTÉTICA ORIGINAL SABROPAN ---
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

COLOR_NARANJA = "#D9832E"
COLOR_FONDO = "#FDF8F3"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; }}
    .main-title {{ color: {COLOR_NARANJA}; font-weight: bold; font-size: 30px; }}
    .metric-card {{ 
        background-color: white; padding: 15px; border-radius: 10px; 
        border-left: 5px solid {COLOR_NARANJA}; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN ---
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://scynlrjnuywjcwovnzxh.supabase.co",
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
)

st.markdown('<p class="main-title">🍞 Sabroasistencia - Control de Personal</p>', unsafe_allow_html=True)

# --- 3. FILTRO DE FECHA ---
fecha_sel = st.date_input("Consultar fecha:", datetime.now())
fecha_str = fecha_sel.strftime('%Y-%m-%d')

# --- 4. LÓGICA DE DATOS ---
try:
    # Consultamos la vista maestra del reporte
    data = conn.table("daily_attendance_summary").select("*").eq("fecha", fecha_str).execute()
    df = pd.DataFrame(data.data)

    if not df.empty:
        # Indicadores Superiores (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><b>Registrados</b><br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
        with col2:
            tardanzas = len(df[pd.to_datetime(df['hora_entrada_real']).dt.time > datetime.strptime("05:05", "%H:%M").time()])
            st.markdown(f'<div class="metric-card"><b>Tardanzas</b><br><h2>{tardanzas}</h2></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><b>En Planta</b><br><h2>{len(df[df["hora_salida_real"].isna()])}</h2></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><b>Turnos OK</b><br><h2>{len(df[df["hora_salida_real"].notna()])}</h2></div>', unsafe_allow_html=True)

        st.write("### Detalle de Asistencia")
        # Limpieza de nombres de columna para el usuario
        df_show = df.rename(columns={
            'full_name': 'Empleado',
            'hora_entrada_real': 'Entrada',
            'hora_salida_real': 'Salida',
            'duracion_total': 'Jornada'
        })
        
        # Formato de hora 12h
        for col in ['Entrada', 'Salida']:
            df_show[col] = pd.to_datetime(df_show[col]).dt.strftime('%I:%M %p').replace("NaT", "---")
            
        st.table(df_show[['Empleado', 'Entrada', 'Salida', 'Jornada']])
    else:
        st.info(f"Sin registros para el {fecha_sel.strftime('%d/%m/%Y')}")

except Exception as e:
    st.error("Sincronizando con base de datos...")
