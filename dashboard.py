import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO RESPONSIVO
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    
    /* Tarjetas de métricas optimizadas */
    .metric-card { 
        background-color: white; 
        padding: 15px; 
        border-radius: 12px; 
        border-left: 6px solid #D9832E; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        text-align: center;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 0.85rem; text-transform: uppercase; }
    .metric-card h2 { margin: 5px 0; color: #D9832E; font-size: 1.8rem; font-weight: bold; }

    /* Ajustes para pantallas de celular */
    @media (max-width: 640px) {
        .metric-card { padding: 10px; margin-bottom: 5px; }
        .metric-card h2 { font-size: 1.4rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 2px !important; }
        .stTabs [data-baseweb="tab"] { padding: 8px !important; font-size: 0.75rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A LA BASE DE DATOS
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabropan: Panel de Asistencia")

# 3. PESTAÑAS DE NAVEGACIÓN
tab1, tab2, tab3 = st.tabs(["📊 Monitor", "📅 Horarios", "📸 Fotos"])

# --- TAB 1: MONITOR (ACTUALIZACIÓN QUIRÚRGICA) ---
with tab1:
    with st.sidebar:
        fecha_sel = st.date_input("Día a consultar:", datetime.now())

    try:
        # Consulta a la vista de asistencia
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel].copy()

            # Métricas Superiores
            c1, c2, c3, c4 = st.columns([1,1,1,1])
            with c1: st.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            
            en_planta = len(df_hoy[df_hoy["salida"].isna()]) if "salida" in df_hoy.columns else 0
            turnos_fin = len(df_hoy[df_hoy["salida"].notna()]) if "salida" in df_hoy.columns else 0
            
            with c3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_planta}</h2></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><h4>Finalizados</h4><h2>{turnos_fin}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            if not df_hoy.empty:
                # INTEGRACIÓN DE FOTOS DEL BUCKET
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                # Creamos la URL basada en el bio_id. Si no hay foto, Streamlit mostrará un icono por defecto.
                df_hoy['foto_url'] = df_hoy['bio_id'].apply(lambda x: f"{url_base}{str(x)}.jpg")

                # Formatear horas para lectura humana (12h AM/PM)
                for col in ['entrada', 'salida', 'hora_esperada']:
                    if col in df_hoy.columns:
                        df_hoy[col] = pd.to_datetime(df_hoy[col]).dt.strftime('%I:%M %p').replace("NaT", "--")

                # Renderizado de la tabla con miniaturas
                cols_finales = ['foto_url', 'persona', 'entrada', 'hora_esperada', 'tardanza', 'salida']
                st.dataframe(
                    df_hoy[cols_finales],
                    column_config={
                        "foto_url": st.column_config.ImageColumn("Foto", width="small"),
                        "persona": "Empleado",
                        "entrada": "Entrada",
                        "hora_esperada": "Horario",
                        "tardanza": "¿Tarde?",
                        "salida": "Salida"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"No se encontraron marcas para el {fecha_sel.strftime('%d/%m/%Y')}")
    except Exception as e:
        st.error(f"Error al cargar el monitor: {e}")

# --- TAB 2: CARGA DE HORARIOS ---
with tab2:
    st.header("Carga Semanal de Horarios")
    archivo_h = st.file_uploader("Archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo_h:
        try:
            df_up = pd.read_excel(archivo_h)
            columnas_req = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            
            if all(col in df_up.columns for col in columnas_req):
                st.write("Vista previa de carga:")
                st.dataframe(df_up.head(), use_container_width=True)
                
                if st.button("🚀 Confirmar y Subir Horarios"):
                    # Normalizar para SQL
                    df_save = df_up[columnas_req].copy()
                    df_save.columns = [c.lower() for c in df_save.columns]
                    
                    # Convertir tiempos a string para evitar error JSON
                    for d in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']:
                        df_save[d] = df_save[d].apply(lambda x: x.strftime('%H:%M:%S') if hasattr(x, 'strftime') else str(x))
                    
                    conn.table("employee_schedules").upsert(df_save.to_dict(orient='records')).execute()
                    st.success("✅ Horarios actualizados en la base de datos.")
            else:
                st.error(f"El Excel debe tener exactamente estas columnas: {columnas_req}")
        except Exception as e:
            st.error(f"Error procesando Excel: {e}")

# --- TAB 3: REGISTRO FOTOGRÁFICO ---
with tab3:
    st.header("📸 Captura de Foto Institucional")
    try:
        # Obtener lista de empleados para vincular la foto
        query_e = conn.table("employees").select("biometric_id, full_name").execute()
        df_e = pd.DataFrame(query_e.data)
        
        if not df_e.empty:
            dict_e = {f"{r['biometric_id']} - {r['full_name']}": r['biometric_id'] for _, r in df_e.iterrows()}
            emp_sel = st.selectbox("Seleccione Empleado:", options=list(dict_e.keys()))
            id_final = dict_e[emp_sel]
            
            foto_data
