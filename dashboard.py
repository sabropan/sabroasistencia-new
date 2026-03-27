import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# --- 1. CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="Sabroasistencia - Control de Personal", layout="wide", page_icon="🍞")

COLOR_NARANJA = "#D9832E"
COLOR_FONDO = "#FDF8F3"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; }}
    .main-title {{ color: {COLOR_NARANJA}; font-weight: bold; font-size: 38px; }}
    .metric-card {{ 
        background-color: white; padding: 20px; border-radius: 12px; 
        border-left: 6px solid {COLOR_NARANJA}; box-shadow: 2px 2px 12px rgba(0,0,0,0.06);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN DIRECTA ---
try:
    conn = st.connection(
        "supabase",
        type=SupabaseConnection,
        url="https://scynlrjnuywjcwovnzxh.supabase.co",
        key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
    )
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.markdown('<p class="main-title">🍞 Sabroasistencia: Panel de Control</p>', unsafe_allow_html=True)

# --- 3. BARRA LATERAL Y FILTROS ---
with st.sidebar:
    st.header("🗓️ Filtros")
    # Usamos la fecha actual por defecto
    fecha_sel = st.date_input("Seleccionar Fecha", datetime.now())
    st.divider()
    st.success("🟢 Biométrico Conectado")
    st.info("🟢 Base de Datos Sincronizada")

# --- 4. CARGA Y VISUALIZACIÓN ---
try:
    # Consultamos la vista de resumen
    query = conn.table("daily_attendance_summary").select("*").execute()
    df_all = pd.DataFrame(query.data)

    if not df_all.empty:
        # Asegurar formato de fecha para filtrar
        df_all['fecha_dia'] = pd.to_datetime(df_all['fecha_dia']).dt.date
        df_hoy = df_all[df_all['fecha_dia'] == fecha_sel]

        if not df_hoy.empty:
            # INDICADORES (KPIs)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with c2:
                # Tardanza basada en el campo de la vista
                tardanzas = len(df_hoy[df_hoy['tardanza'] == 'SÍ'])
                st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2 style="color:red;">{tardanzas}</h2></div>', unsafe_allow_html=True)
            with c3:
                en_planta = len(df_hoy[df_hoy['salida'].isna()])
                st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2 style="color:green;">{en_planta}</h2></div>', unsafe_allow_html=True)
            with c4:
                finalizados = len(df_hoy[df_hoy['salida'].notna()])
                st.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{finalizados}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            st.subheader(f"Detalle de Marcaciones - {fecha_sel.strftime('%d/%m/%Y')}")

            # Ajuste de columnas según los campos reales
            df_view = df_hoy[['persona', 'entrada', 'salida', 'tiempo_total', 'tardanza']].copy()
            df_view.columns = ['Empleado', 'Hora Entrada', 'Hora Salida', 'Jornada Total', '¿Tarde?']

            # Formatear horas para la tabla
            df_view['Hora Entrada'] = pd.to_datetime(df_view['Hora Entrada']).dt.strftime('%I:%M %p')
            df_view['Hora Salida'] = pd.to_datetime(df_view['Hora Salida']).dt.strftime('%I:%M %p').fillna("---")

            st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No hay registros de asistencia para el {fecha_sel.strftime('%d/%m/%Y')}")
    else:
        st.info("La base de datos está vacía o esperando nuevos registros.")

except Exception as e:
    st.error(f"Error al visualizar los datos: {e}")
    st.info("Verifica que la vista 'daily_attendance_summary' esté activa en Supabase.")
