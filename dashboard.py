import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO AGRESIVO DE DISEÑO
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

st.markdown("""
    <style>
    /* 1. Eliminar espacio superior */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stApp { background-color: #FDF8F3; }
    
    /* 2. Tamaño de letra duplicado para la tabla */
    [data-testid="stTable"] td, [data-testid="stDataFrame"] td {
        font-size: 24px !important; 
        font-weight: 500 !important;
    }
    [data-testid="stTable"] th, [data-testid="stDataFrame"] th {
        font-size: 18px !important;
    }

    /* 3. Cards de métricas */
    .metric-card { 
        background-color: white; padding: 10px; border-radius: 12px; 
        border-left: 6px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 1rem; }
    .metric-card h2 { margin: 0; color: #D9832E; font-size: 2rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A SUPABASE
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

# Título más compacto
st.title("🍞 Sabropan: Monitor")

# 3. PESTAÑAS
tab1, tab2, tab3 = st.tabs(["📊 Monitor", "📅 Horarios", "📸 Fotos"])

with tab1:
    with st.sidebar:
        fecha_hoy_col = (datetime.utcnow() - timedelta(hours=5)).date()
        fecha_sel = st.date_input("Día:", fecha_hoy_col)

    try:
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel].copy()

            if not df_hoy.empty:
                # URL de Fotos
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                df_hoy['foto_v'] = df_hoy['biometric_id'].apply(
                    lambda x: f"{url_base}{str(x).zfill(8)}.jpg" if pd.notnull(x) else None
                )

                # Métricas
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="metric-card"><h4>Personal</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
                
                # Tabla Principal - Solo las columnas necesarias para evitar la columna vacía
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
                st.info("No hay registros.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- TAB 2 y 3 (Se mantienen igual pero con el estilo nuevo) ---
with tab2:
    st.header("Horarios")
    archivo_h = st.file_uploader("Subir Excel", type=["xlsx"])
    if archivo_h:
        try:
            df_up = pd.read_excel(archivo_h)
            if st.button("🚀 Guardar"):
                df_save = df_up.copy()
                df_save.columns = [c.lower() for c in df_save.columns]
                conn.table("employee_schedules").upsert(df_save.to_dict(orient='records')).execute()
                st.success("Actualizado.")
        except Exception as e: st.error(f"Error: {e}")

with tab3:
    st.header("📸 Fotos")
    try:
        res_e = conn.table("employees").select("biometric_id, full_name").execute()
        df_e = pd.DataFrame(res_e.data)
        if not df_e.empty:
            lista_e = {f"{r['biometric_id']} - {r['full_name']}": r['biometric_id'] for _, r in df_e.iterrows()}
            seleccion = st.selectbox("Empleado:", options=list(lista_e.keys()))
            id_final = lista_e[seleccion]
            foto_input = st.camera_input(f"Foto ID: {id_final}")
            if foto_input:
                nombre_archivo = f"{str(id_final).zfill(8)}.jpg"
                conn.client.storage.from_("empleados").upload(
                    path=nombre_archivo, file=foto_input.getvalue(),
                    file_options={"content-type": "image/jpeg", "upsert": "true"}
                )
                st.success("Foto guardada.")
    except Exception as e: st.error(f"Error: {e}")
