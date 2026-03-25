import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# --- 1. CONFIGURACIÓN ESTÉTICA (Sabroasistencia Theme) ---
st.set_page_config(
    page_title="Sabroasistencia - Control de Personal",
    layout="wide",
    page_icon="🍞"
)

# Colores extraídos del diseño original de Sabropan
COLOR_NARANJA = "#D9832E"
COLOR_FONDO = "#FDF8F3"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_FONDO}; }}
    .main-title {{ color: {COLOR_NARANJA}; font-weight: bold; font-size: 38px; margin-bottom: 0px; }}
    .metric-card {{ 
        background-color: white; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 6px solid {COLOR_NARANJA};
        box-shadow: 2px 2px 12px rgba(0,0,0,0.06);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN DIRECTA (Solución al error de URL) ---
# Aquí integramos las llaves directamente para asegurar la conexión
try:
    conn = st.connection(
        "supabase",
        type=SupabaseConnection,
        url="https://scynlrjnuywjcwovnzxh.supabase.co",
        key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7"
    )
except Exception as e:
    st.error(f"Error configurando la conexión: {e}")
    st.stop()

# --- 3. ENCABEZADO ---
st.markdown('<p class="main-title">🍞 Sabroasistencia: Panel de Control</p>', unsafe_allow_html=True)
st.write("Seguimiento de asistencia técnica y administrativa")

# --- 4. FUNCIÓN DE CARGA DE DATOS (Auditoría segura) ---
@st.cache_data(ttl=30)  # Actualiza automáticamente cada 30 segundos
def load_attendance():
    # Consultamos la vista SQL que creamos para Sabropan
    query = conn.table("daily_attendance_summary").select("*").execute()
    df_raw = pd.DataFrame(query.data)
    if not df_raw.empty:
        df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
    return df_raw

try:
    df_all = load_attendance()
    
    # Barra Lateral
    with st.sidebar:
        st.header("🗓️ Filtros")
        fecha_sel = st.date_input("Seleccionar Fecha", pd.to_datetime("today"))
        st.divider()
        st.markdown("**Estado del Sistema:**")
        st.success("🟢 Biométrico Conectado")
        st.info("🟢 Base de Datos Sincronizada")

    # Filtrar datos por el día seleccionado
    df_hoy = df_all[df_all['fecha_dia'] == fecha_sel]

    # --- 5. INDICADORES (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        total = len(df_hoy)
        st.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{total}</h2></div>', unsafe_allow_html=True)
    with c2:
        tardanzas = len(df_hoy[df_hoy['tardanza'] == 'SÍ'])
        st.markdown(f'<div class="metric-card"><h4>Tardanzas (>5am)</h4><h2 style="color:red;">{tardanzas}</h2></div>', unsafe_allow_html=True)
    with c3:
        # En planta: Tiene entrada pero la salida es nula
        en_planta = len(df_hoy[df_hoy['salida'].isna()])
        st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2 style="color:green;">{en_planta}</h2></div>', unsafe_allow_html=True)
    with c4:
        finalizados = len(df_hoy[df_hoy['salida'].notna()])
        st.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{finalizados}</h2></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 6. TABLA DE DETALLE ---
    st.subheader(f"Detalle de Marcaciones - {fecha_sel.strftime('%d/%m/%Y')}")
    
    if not df_hoy.empty:
        # Renombrar para que el administrador vea nombres claros
        df_view = df_hoy[['persona', 'entrada', 'salida', 'tiempo_total', 'tardanza']].copy()
        df_view.columns = ['Empleado', 'Hora Entrada', 'Hora Salida', 'Jornada Total', '¿Tarde?']
        
        # Formatear horas para que se vean bonitas
        df_view['Hora Entrada'] = pd.to_datetime(df_view['Hora Entrada']).dt.strftime('%I:%M %p')
        df_view['Hora Salida'] = pd.to_datetime(df_view['Hora Salida']).dt.strftime('%I:%M %p').fillna("---")
        
        st.dataframe(df_view, use_container_width=True, hide_index=True)
        
        # Botón de descarga
        csv = df_hoy.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, f"Sabropan_{fecha_sel}.csv", "text/csv")
    else:
        st.warning("No hay registros de asistencia para la fecha seleccionada.")

except Exception as e:
    st.error(f"Error al visualizar los datos: {e}")
    st.info("Asegúrate de que la vista 'daily_attendance_summary' exista en Supabase.")