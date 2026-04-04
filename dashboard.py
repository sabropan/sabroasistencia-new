import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. CONFIGURACIÓN E IMAGEN INSTITUCIONAL
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

# CSS Avanzado para diseño responsivo y tarjetas elegantes
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    
    /* Tarjetas de métricas */
    .metric-card { 
        background-color: white; 
        padding: 15px; 
        border-radius: 12px; 
        border-left: 6px solid #D9832E; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        text-align: center;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 0.9rem; }
    .metric-card h2 { margin: 5px 0; color: #D9832E; font-size: 1.8rem; }

    /* Ajustes para Celular */
    @media (max-width: 640px) {
        .metric-card { padding: 10px; }
        .metric-card h2 { font-size: 1.4rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 2px !important; }
        .stTabs [data-baseweb="tab"] { padding: 8px !important; font-size: 0.8rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A SUPABASE
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabropan: Gestión de Asistencia")

# 3. NAVEGACIÓN POR PESTAÑAS
tab1, tab2, tab3 = st.tabs(["📊 Monitor", "📅 Carga Horarios", "📸 Registrar Fotos"])

# --- PESTAÑA 1: MONITOR DE ASISTENCIA ---
with tab1:
    with st.sidebar:
        fecha_sel = st.date_input("Fecha de auditoría:", datetime.now())

    try:
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel].copy()

            # Métricas superiores
            c1, c2, c3, c4 = st.columns([1,1,1,1])
            with c1: st.markdown(f'<div class="metric-card"><h4>Registros</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            
            en_planta = len(df_hoy[df_hoy["salida"].isna()]) if "salida" in df_hoy.columns else 0
            turnos_fin = len(df_hoy[df_hoy["salida"].notna()]) if "salida" in df_hoy.columns else 0
            
            with c3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_planta}</h2></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{turnos_fin}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            if not df_hoy.empty:
                # Construir URL de fotos (Bucket 'empleados')
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                df_hoy['foto'] = df_hoy['bio_id'].apply(lambda x: f"{url_base}{x}.jpg")

                # Formatear horas para visualización
                for col in ['entrada', 'salida', 'hora_esperada']:
                    if col in df_hoy.columns:
                        df_hoy[col] = pd.to_datetime(df_hoy[col]).dt.strftime('%I:%M %p').fillna("--")

                # Mostrar tabla con miniatura de fotos
                cols_mostrar = ['foto', 'persona', 'entrada', 'hora_esperada', 'tardanza', 'salida']
                st.dataframe(
                    df_hoy[cols_mostrar],
                    column_config={
                        "foto": st.column_config.ImageColumn("Foto", width="small"),
                        "persona": "Empleado",
                        "entrada": "Entrada",
                        "hora_esperada": "H. Programada",
                        "tardanza": "¿Tarde?",
                        "salida": "Salida"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Sin registros para esta fecha.")
    except Exception as e:
        st.error(f"Error en monitor: {e}")

# --- PESTAÑA 2: CARGA ÁGIL DE HORARIOS ---
with tab2:
    st.header("Actualizar Horarios Semanales")
    archivo_horarios = st.file_uploader("Subir Excel de Horarios", type=["xlsx"])
    
    if archivo_horarios:
        try:
            df_upload = pd.read_excel(archivo_horarios)
            columnas_req = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            
            if all(col in df_upload.columns for col in columnas_req):
                st.dataframe(df_upload.head(), use_container_width=True)
                
                if st.button("🚀 Guardar Horarios en la Nube"):
                    df_to_save = df_upload[columnas_req].copy()
                    df_to_save.columns = [c.lower() for c in df_to_save.columns]
                    
                    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
                    for d in dias:
                        df_to_save[d] = df_to_save[d].apply(lambda x: x.strftime('%H:%M:%S') if hasattr(x, 'strftime') else str(x))
                    
                    conn.table("employee_schedules").upsert(df_to_save.to_dict(orient='records')).execute()
                    st.success("✅ Horarios actualizados correctamente.")
            else:
                st.error("El Excel no coincide con el formato requerido.")
        except Exception as e:
            st.error(f"Error al procesar: {e}")

# --- PESTAÑA 3: REGISTRO DE FOTOS ---
with tab3:
    st.header("📸 Captura de Foto de Empleado")
    st.write("Selecciona un empleado y tómale la foto directamente.")
    
    try:
        # Obtenemos lista de empleados de la tabla maestra
        # Nota: Ajustar nombre de tabla si es diferente a 'employees'
        query_emp = conn.table("employees").select("biometric_id, full_name").execute()
        df_emp = pd.DataFrame(query_emp.data)
        
        if not df_emp.empty:
            lista = {f"{r['biometric_id']} - {r['full_name']}": r['biometric_id'] for _, r in df_emp.iterrows()}
            seleccion = st.selectbox("Empleado a fotografiar:", options=list(lista.keys()))
            id_per = lista[seleccion]
            
            foto_cap = st.camera_input("Capturar foto")
            
            if foto_cap:
                with st.spinner("Subiendo imagen..."):
                    img_bytes = foto_cap.getvalue()
                    nombre_archivo = f"{id_per}.jpg"
                    
                    # Subir al bucket 'empleados'
                    storage = conn.client.storage.from_("empleados")
                    storage.upload(
                        path=nombre_archivo,
                        file=img_bytes,
                        file_options={"content-type": "image/jpeg", "x-upsert": "true"}
                    )
                    st.success(f"✅ Foto de ID {id_per} actualizada.")
                    st.balloons()
        else:
            st.warning("No hay empleados en la tabla 'employees' para vincular fotos.")
    except Exception as e:
        st.error(f"Error en cámara: {e}")
