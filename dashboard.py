import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, timedelta

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

# --- TAB 1: MONITOR (CORRECCIÓN FINAL DE HORA COLOMBIA) ---
with tab1:
    with st.sidebar:
        # Fecha actual en Colombia para el selector
        fecha_hoy_col = (datetime.utcnow() - timedelta(hours=5)).date()
        fecha_sel = st.date_input("Día a consultar:", fecha_hoy_col)

    try:
        # Consultamos la vista
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel].copy()

            if not df_hoy.empty:
                # A. URL de Fotos (Formato 8 dígitos)
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                df_hoy['foto_v'] = df_hoy['biometric_id'].apply(
                    lambda x: f"{url_base}{str(x).zfill(8)}.jpg" if pd.notnull(x) else None
                )

                # B. Métricas
                c1, c2, c3, c4 = st.columns([1,1,1,1])
                with c1: st.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
                
                en_p = len(df_hoy[df_hoy["salida"].isna()]) if "salida" in df_hoy.columns else 0
                with c3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_p}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="metric-card"><h4>Finalizados</h4><h2>{len(df_hoy) - en_p}</h2></div>', unsafe_allow_html=True)

                # C. Formateo de Horas (Eliminando rastro de zona horaria para evitar desfases)
                for col in ['entrada', 'salida']:
                    if col in df_hoy.columns:
                        # tz_localize(None) es el secreto para que no se mueva la hora de Bogotá
                        df_hoy[col] = pd.to_datetime(df_hoy[col]).dt.tz_localize(None).dt.strftime('%I:%M %p').replace("NaT", "--")

                # D. Tabla Principal
                st.dataframe(
                    df_hoy[['foto_v', 'persona', 'entrada', 'tardanza', 'salida']],
                    column_config={
                        "foto_v": st.column_config.ImageColumn("Foto", width="small"),
                        "persona": "Empleado",
                        "entrada": "Entrada",
                        "tardanza": "¿Tarde?",
                        "salida": "Salida"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"No hay registros para el día {fecha_sel.strftime('%d/%m/%Y')}")
    except Exception as e:
        st.error(f"Error en monitor: {e}")

# --- TAB 2: HORARIOS ---
with tab2:
    st.header("Actualizar Horarios (Excel)")
    archivo_h = st.file_uploader("Subir archivo .xlsx", type=["xlsx"])
    if archivo_h:
        try:
            df_up = pd.read_excel(archivo_h)
            if 'BIOMETRIC_ID' in df_up.columns:
                if st.button("🚀 Guardar Horarios"):
                    df_save = df_up.copy()
                    df_save.columns = [c.lower() for c in df_save.columns]
                    conn.table("employee_schedules").upsert(df_save.to_dict(orient='records')).execute()
                    st.success("✅ Horarios actualizados en Supabase.")
        except Exception as e:
            st.error(f"Error al procesar Excel: {e}")

# --- TAB 3: REGISTRO DE FOTOS ---
with tab3:
    st.header("📸 Captura de Foto Institucional")
    try:
        res_e = conn.table("employees").select("biometric_id, full_name").execute()
        df_e = pd.DataFrame(res_e.data)
        
        if not df_e.empty:
            lista_e = {f"{r['biometric_id']} - {r['full_name']}": r['biometric_id'] for _, r in df_e.iterrows()}
            seleccion = st.selectbox("Seleccione Empleado:", options=list(lista_e.keys()))
            id_final = lista_e[seleccion]
            
            foto_input = st.camera_input(f"Tomar foto para ID: {id_final}")
            
            if foto_input:
                with st.spinner("Subiendo al servidor..."):
                    nombre_archivo = f"{str(id_final).zfill(8)}.jpg"
                    storage = conn.client.storage.from_("empleados")
                    storage.upload(
                        path=nombre_archivo,
                        file=foto_input.getvalue(),
                        file_options={"content-type": "image/jpeg", "upsert": "true"}
                    )
                    st.success(f"✅ Foto de {seleccion} guardada.")
                    st.balloons()
    except Exception as e:
        st.error(f"Error en cámara: {e}")
