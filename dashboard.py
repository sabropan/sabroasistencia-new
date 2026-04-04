import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. Configuración de página (Layout Wide es vital para móviles)
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

# 2. CSS Inteligente (Responsive)
# He ajustado el metric-card para que sea más compacto en móviles
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    
    /* Tarjeta de métrica optimizada */
    .metric-card { 
        background-color: white; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #D9832E; 
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        text-align: center;
    }
    
    .metric-card h4 { 
        margin: 0; color: #555; font-size: 0.9rem; 
    }
    
    .metric-card h2 { 
        margin: 5px 0 0 0; color: #D9832E; font-size: 1.8rem; 
    }

    /* Ajustes específicos para pantallas pequeñas (Celulares) */
    @media (max-width: 640px) {
        .metric-card {
            padding: 10px;
            margin-bottom: 8px;
        }
        .metric-card h2 {
            font-size: 1.5rem;
        }
        /* Elimina el espacio excesivo en las pestañas en móvil */
        .stTabs [data-baseweb="tab-list"] {
            gap: 5px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Conexión a Supabase
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabropan: Asistencia")

# Pestañas
tab1, tab2 = st.tabs(["📊 Monitor", "📅 Horarios"])

with tab1:
    with st.sidebar:
        fecha_sel = st.date_input("Consultar fecha:", datetime.now())

    try:
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel]

            # --- MÉTRICAS RESPONSIVE ---
            # En PC se ven 4 columnas, en Móvil se apilan automáticamente de forma elegante
            c1, c2, c3, c4 = st.columns([1,1,1,1])
            
            with c1: st.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            
            en_planta = len(df_hoy[df_hoy["salida"].isna()]) if "salida" in df_hoy.columns else 0
            turnos_fin = len(df_hoy[df_hoy["salida"].notna()]) if "salida" in df_hoy.columns else 0
            
            with c3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_planta}</h2></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{turnos_fin}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            if not df_hoy.empty:
                df_view = df_hoy.copy()
                # Formateo de horas
                if 'entrada' in df_view.columns:
                    df_view['entrada'] = pd.to_datetime(df_view['entrada']).dt.strftime('%I:%M %p')
                if 'salida' in df_view.columns:
                    df_view['salida'] = pd.to_datetime(df_view['salida']).dt.strftime('%I:%M %p').fillna("--")
                if 'hora_esperada' in df_view.columns:
                    df_view['hora_esperada'] = pd.to_datetime(df_view['hora_esperada']).dt.strftime('%I:%M %p').fillna("Sin horario")

                # Columnas finales
                cols_finales = ['persona', 'entrada', 'hora_esperada', 'tardanza', 'salida', 'tiempo_total', 'tiempo_adicional']
                cols_disponibles = [c for c in cols_finales if c in df_view.columns]
                
                # use_container_width=True es la clave para que la tabla sea responsive
                st.dataframe(df_view[cols_disponibles], use_container_width=True, hide_index=True)
            else:
                st.info("No hay registros para hoy.")
        else:
            st.warning("Base de datos vacía.")

    except Exception as e:
        st.error(f"Error: {e}")

with tab2:
    st.header("Carga de Horarios")
    archivo = st.file_uploader("Subir Excel", type=["xlsx"])
    
    if archivo:
        try:
            df_upload = pd.read_excel(archivo)
            columnas_req = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            
            if all(col in df_upload.columns for col in columnas_req):
                st.dataframe(df_upload.head(), use_container_width=True)
                if st.button("🚀 Actualizar Horarios"):
                    df_to_save = df_upload[columnas_req].copy()
                    df_to_save.columns = [c.lower() for c in df_to_save.columns]
                    
                    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
                    for d in dias:
                        df_to_save[d] = df_to_save[d].apply(lambda x: x.strftime('%H:%M:%S') if hasattr(x, 'strftime') else str(x))
                    
                    conn.table("employee_schedules").upsert(df_to_save.to_dict(orient='records')).execute()
                    st.success("✅ Horarios cargados.")
            else:
                st.error("Formato de Excel incorrecto.")
        except Exception as e:
            st.error(f"Error: {e}")
