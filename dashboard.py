import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

# Estética institucional y ajustes para móvil
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    .metric-card { 
        background-color: white; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Conexión directa a Supabase
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabroasistencia: Panel de Control")

# Navegación por pestañas para mejor visualización en celular
tab1, tab2 = st.tabs(["📊 Monitor de Asistencia", "📅 Carga de Horarios"])

with tab1:
    with st.sidebar:
        fecha_sel = st.date_input("Fecha de auditoría:", datetime.now())

    try:
        # Consultamos la vista maestra
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_sel]

            # --- MÉTRICAS ---
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
                
                # Formateo de horas 12h para el usuario
                if 'entrada' in df_view.columns:
                    df_view['entrada'] = pd.to_datetime(df_view['entrada']).dt.strftime('%I:%M %p')
                if 'salida' in df_view.columns:
                    df_view['salida'] = pd.to_datetime(df_view['salida']).dt.strftime('%I:%M %p').fillna("--")
                if 'hora_esperada' in df_view.columns:
                    df_view['hora_esperada'] = pd.to_datetime(df_view['hora_esperada']).dt.strftime('%I:%M %p').fillna("No asignada")

                # Columnas finales a mostrar
                cols_finales = ['persona', 'entrada', 'hora_esperada', 'tardanza', 'salida', 'tiempo_total', 'tiempo_adicional']
                # Filtramos solo las que existan en el DataFrame para evitar errores
                cols_disponibles = [c for c in cols_finales if c in df_view.columns]
                
                st.dataframe(df_view[cols_disponibles], use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay registros para el {fecha_sel.strftime('%d/%m/%Y')}")
        else:
            st.warning("No hay datos disponibles en la base de datos.")

    except Exception as e:
        st.error(f"Error al cargar monitor: {e}")

with tab2:
    st.header("Carga Semanal de Horarios")
    st.write("Sube el Excel con `BIOMETRIC_ID` y las horas de entrada (LUNES, MARTES, etc.)")
    
    archivo_horarios = st.file_uploader("Seleccionar Excel (.xlsx)", type=["xlsx"])
    
    if archivo_horarios:
        try:
            df_upload = pd.read_excel(archivo_horarios)
            columnas_requeridas = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            
            if all(col in df_upload.columns for col in columnas_requeridas):
                st.write("Vista previa de los datos encontrados:")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                if st.button("🚀 Confirmar y Actualizar en la Nube"):
                    # Crear copia y convertir horas a texto para evitar error de JSON
                    df_to_save = df_upload[columnas_requeridas].copy()
                    
                    dias = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
                    for dia in dias:
                        # Convertimos los objetos de tiempo a string HH:MM:SS
                        df_to_save[dia] = df_to_save[dia].apply(
                            lambda x: x.strftime('%H:%M:%S') if hasattr(x, 'strftime') else str(x)
                        )
                    
                    # Subida a Supabase
                    data_to_upsert = df_to_save.to_dict(orient='records')
                    conn.table("employee_schedules").upsert(data_to_upsert).execute()
                    
                    st.success("✅ Horarios actualizados con éxito en la base de datos.")
            else:
                st.error(f"El archivo debe contener estas columnas: {columnas_requeridas}")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

    st.info("💡 Consejo: Las horas deben estar en formato 24h (ej: 05:00 o 14:00).")
