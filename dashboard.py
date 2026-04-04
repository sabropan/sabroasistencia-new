import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime

st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

# Estética institucional
st.markdown("""
    <style>
    .stApp { background-color: #FDF8F3; }
    .metric-card { 
        background-color: white; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Conexión a Supabase con credenciales integradas
conn = st.connection("supabase", type=SupabaseConnection, 
    url="https://scynlrjnuywjcwovnzxh.supabase.co", 
    key="sb_publishable_ws3IEWLtGf3sVgit7c18Uw_n-eMzmA7")

st.title("🍞 Sabroasistencia: Panel de Control")

# --- NAVEGACIÓN POR PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Monitor de Asistencia", "📅 Carga Ágil de Horarios"])

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
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-card"><h4>Registrados</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            
            # Ajuste de nombres de columnas según tu DB actual
            en_planta = len(df_hoy[df_hoy["salida"].isna()]) if "salida" in df_hoy.columns else 0
            turnos_fin = len(df_hoy[df_hoy["salida"].notna()]) if "salida" in df_hoy.columns else 0
            
            c3.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_planta}</h2></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{turnos_fin}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            if not df_hoy.empty:
                df_view = df_hoy.copy()
                
                # Formateo de columnas existentes
                cols_presentes = df_view.columns.tolist()
                
                if 'entrada' in cols_presentes:
                    df_view['entrada'] = pd.to_datetime(df_view['entrada']).dt.strftime('%I:%M %p')
                if 'salida' in cols_presentes:
                    df_view['salida'] = pd.to_datetime(df_view['salida']).dt.strftime('%I:%M %p').fillna("--")
                if 'hora_esperada' in cols_presentes:
                    df_view['hora_esperada'] = pd.to_datetime(df_view['hora_esperada']).dt.strftime('%I:%M %p').fillna("--")
                else:
                    df_view['hora_esperada'] = "No asignada"

                # Selección dinámica de columnas para evitar errores si aún no se crea la tabla de horarios
                cols_finales = ['persona', 'entrada', 'hora_esperada', 'tardanza', 'salida', 'tiempo_total']
                cols_disponibles = [c for c in cols_finales if c in df_view.columns]
                
                st.dataframe(df_view[cols_disponibles], use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay registros para el {fecha_sel.strftime('%d/%m/%Y')}")
        else:
            st.warning("No se encontraron datos en la base de datos.")

    except Exception as e:
        st.error(f"Error de visualización: {e}")

with tab2:
    st.header("Carga Semanal de Horarios")
    st.write("Sube el Excel con `BIOMETRIC_ID` y los días (LUNES, MARTES, etc.) para actualizar el comparador.")
    
    archivo_horarios = st.file_uploader("Seleccionar Excel (.xlsx)", type=["xlsx"])
    
    if archivo_horarios:
        try:
            df_upload = pd.read_excel(archivo_horarios)
            columnas_requeridas = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            
            if all(col in df_upload.columns for col in columnas_requeridas):
                st.write("Vista previa de carga:")
                st.dataframe(df_upload[columnas_requeridas].head(), use_container_width=True)
                
                if st.button("🚀 Confirmar y Actualizar en la Nube"):
                    data_to_upsert = df_upload[columnas_requeridas].to_dict(orient='records')
                    conn.table("employee_schedules").upsert(data_to_upsert).execute()
                    st.success("✅ Horarios actualizados.")
            else:
                st.error(f"Faltan columnas requeridas: {columnas_requeridas}")
        except Exception as e:
            st.error(f"Error al procesar: {e}")

    st.info("💡 Asegúrate de que las horas en el Excel estén en formato 24h (ej: 05:00 o 14:00).")
