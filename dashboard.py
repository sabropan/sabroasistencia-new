import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN Y ESTILO UI (DISEÑO MAXIMIZADO)
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

st.markdown("""
    <style>
    /* Pegar contenido al borde superior */
    .block-container { padding-top: 0rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    header { visibility: hidden; } /* Oculta el menú superior de Streamlit */
    
    .stApp { background-color: #FDF8F3; }
    
    /* Tamaño de letra duplicado para los datos de la tabla */
    [data-testid="stDataFrame"] td, [data-testid="stTable"] td {
        font-size: 26px !important; 
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    /* Estilo para los encabezados de la tabla */
    [data-testid="stDataFrame"] th {
        font-size: 18px !important;
        background-color: #D9832E !important;
        color: white !important;
    }

    /* Cards de métricas más compactas y visibles */
    .metric-card { 
        background-color: white; padding: 10px; border-radius: 12px; 
        border-left: 8px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center; margin-top: -10px;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 1.1rem; }
    .metric-card h2 { margin: 0; color: #D9832E; font-size: 2.2rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A SUPABASE
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

# 3. CUERPO DEL DASHBOARD
# Usamos columnas para el título y métricas en una sola fila muy alta
col_t, col_m1, col_m2, col_m3 = st.columns([1.5, 1, 1, 1])

with col_t:
    st.title("🍞 MONITOR")

try:
    # Traemos los datos de la vista que ya tiene la hora corregida como texto
    query = conn.table("daily_attendance_summary").select("*").execute()
    df_raw = pd.DataFrame(query.data)

    if not df_raw.empty:
        # Fecha de hoy en Colombia para el filtro
        hoy_col = (datetime.utcnow() - timedelta(hours=5)).date()
        df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
        df_hoy = df_raw[df_raw['fecha_dia'] == hoy_col].copy()

        # Render de Métricas en el encabezado
        with col_m1: st.markdown(f'<div class="metric-card"><h4>Personal</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
        with col_m2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
        en_p = len(df_hoy[df_hoy["salida"] == "--"])
        with col_m3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_p}</h2></div>', unsafe_allow_html=True)

        if not df_hoy.empty:
            # URL de Fotos
            url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
            df_hoy['foto_v'] = df_hoy['biometric_id'].apply(
                lambda x: f"{url_base}{str(x).zfill(8)}.jpg" if pd.notnull(x) else None
            )

            # TABLA PRINCIPAL - Selección exacta de columnas para evitar la columna vacía
            st.dataframe(
                df_hoy[['foto_v', 'persona', 'entrada', 'salida', 'tiempo_total', 'tardanza']],
                column_config={
                    "foto_v": st.column_config.ImageColumn("", width="small"),
                    "persona": "Empleado",
                    "entrada": "Entrada",
                    "salida": "Salida",
                    "tiempo_total": "⏱️ Tiempo",
                    "tardanza": "¿Tarde?"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay registros hoy.")

except Exception as e:
    st.error(f"Error: {e}")

# --- SECCIÓN INFERIOR PARA GESTIÓN (Pestañas discretas) ---
st.write("---")
tab_h, tab_f = st.tabs(["📅 Cargar Horarios", "📸 Capturar Fotos"])

with tab_h:
    archivo = st.file_uploader("Subir Excel", type=["xlsx"])
    if archivo:
        df_up = pd.read_excel(archivo)
        if st.button("🚀 Guardar"):
            df_up.columns = [c.lower() for c in df_up.columns]
            conn.table("employee_schedules").upsert(df_up.to_dict(orient='records')).execute()
            st.success("Guardado.")

with tab_f:
    res_e = conn.table("employees").select("biometric_id, full_name").execute()
    df_e = pd.DataFrame(res_e.data)
    if not df_e.empty:
        lista_e = {f"{r['biometric_id']} - {r['full_name']}": r['biometric_id'] for _, r in df_e.iterrows()}
        seleccion = st.selectbox("Empleado:", options=list(lista_e.keys()))
        foto_input = st.camera_input("Capturar")
        if foto_input:
            nombre = f"{str(lista_e[seleccion]).zfill(8)}.jpg"
            conn.client.storage.from_("empleados").upload(path=nombre, file=foto_input.getvalue(), file_options={"content-type":"image/jpeg","upsert":"true"})
            st.success("Foto guardada.")
