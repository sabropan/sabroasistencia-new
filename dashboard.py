import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    .metric-card { 
        background-color: white; padding: 15px; border-radius: 12px; 
        border-left: 6px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px; text-align: center;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 0.85rem; text-transform: uppercase; }
    .metric-card h2 { margin: 5px 0; color: #D9832E; font-size: 1.8rem; font-weight: bold; }
    @media (max-width: 640px) {
        .metric-card h2 { font-size: 1.4rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 2px !important; }
        .stTabs [data-baseweb="tab"] { padding: 8px !important; font-size: 0.75rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A SUPABASE
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabropan: Panel de Asistencia")

# 3. PESTAÑAS
tab1, tab2, tab3 = st.tabs(["📊 Monitor", "📅 Horarios", "📸 Fotos"])

# --- TAB 1: MONITOR CON FOTOS ---
with tab1:
    with st.sidebar:
        fecha_sel = st.date_input("Día a consultar:", datetime.now())

    try:
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel].copy()

            # Identificar el nombre de la columna del ID (bio_id o biometric_id)
            col_id = 'biometric_id' if 'biometric_id' in df_hoy.columns else ('bio_id' if 'bio_id' in df_hoy.columns else None)

            # Métricas
            c1, c2, c3, c4 = st.columns([1,1,1,1])
            with c1: st.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            en_p = len(df_hoy[df_hoy["salida"].isna()]) if "salida" in df_hoy.columns else 0
            with c3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_p}</h2></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><h4>Finalizados</h4><h2>{len(df_hoy) - en_p}</h2></div>', unsafe_allow_html=True)

            if not df_hoy.empty and col_id:
                # URL del Bucket público
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                df_hoy['foto_url'] = df_hoy[col_id].apply(lambda x: f"{url_base}{str(x)}.jpg")

                for col in ['entrada', 'salida', 'hora_esperada']:
                    if col in df_hoy.columns:
                        df_hoy[col] = pd.to_datetime(df_hoy[col]).dt.strftime('%I:%M %p').replace("NaT", "--")

                # Columnas a mostrar
                cols_finales = ['foto_url', 'persona', 'entrada', 'hora_esperada', 'tardanza', 'salida']
                st.dataframe(
                    df_hoy[cols_finales],
                    column_config={
                        "foto_url": st.column_config.ImageColumn("Foto", width="small"),
                        "persona": "Empleado", "entrada": "Entrada", "hora_esperada": "Horario", "tardanza": "¿Tarde?", "salida": "Salida"
                    },
                    use_container_width=True, hide_index=True
                )
            elif not col_id:
                st.error("No se encontró la columna de ID en la base de datos (biometric_id o bio_id).")
            else:
                st.info("No hay marcas para esta fecha.")
    except Exception as e:
        st.error(f"Error en monitor: {e}")

# --- TAB 2: CARGA DE HORARIOS ---
with tab2:
    st.header("Actualizar Horarios")
    archivo_h = st.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])
    if archivo_h:
        try:
            df_up = pd.read_excel(archivo_h)
            columnas_req = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            if all(col in df_up.columns for col in columnas_req):
                if st.button("🚀 Guardar Horarios"):
                    df_save = df_up[columnas_req].copy()
                    df_save.columns = [c.lower() for c in df_save.columns]
                    for d in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']:
                        df_save[d] = df_save[d].apply(lambda x: x.strftime('%H:%M:%S') if hasattr(x, 'strftime') else str(x))
                    conn.table("employee_schedules").upsert(df_save.to_dict(orient='records')).execute()
                    st.success("✅ Horarios actualizados.")
            else:
                st.error("Columnas incorrectas en el Excel.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- TAB 3: REGISTRO DE FOTOS ---
with tab3:
    st.header("📸 Capturar Foto")
    try:
        query_e = conn.table("employees").select("biometric_id, full_name").execute()
        df_e = pd.DataFrame(query_e.data)
        if not df_e.empty:
            dict_e = {f"{r['biometric_id']} - {r['full_name']}": r['biometric_id'] for _, r in df_e.iterrows()}
            emp_sel = st.selectbox("Empleado:", options=list(dict_e.keys()))
            id_final = dict_e[emp_sel]
            
            foto_data = st.camera_input(f"Foto para ID {id_final}")
            if foto_data:
                with st.spinner("Subiendo..."):
                    storage = conn.client.storage.from_("empleados")
                    # Subimos con el nombre id.jpg (ej: 4.jpg)
                    storage.upload(path=f"{id_final}.jpg", file=foto_data.getvalue(), file_options={"content-type": "image/jpeg", "x-upsert": "true"})
                    st.success("✅ Foto guardada.")
        else:
            st.warning("No hay empleados en la base de datos.")
    except Exception as e:
        st.error(f"Error en cámara: {e}")
