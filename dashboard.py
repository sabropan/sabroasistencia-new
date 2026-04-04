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

# Conexión a Supabase
conn = st.connection("supabase", type=SupabaseConnection)

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
            c3.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{len(df_hoy[df_hoy["salida_real"].isna()])}</h2></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><h4>Turnos Fin</h4><h2>{len(df_hoy[df_hoy["salida_real"].notna()])}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            if not df_hoy.empty:
                # Limpieza de visualización
                df_view = df_hoy.copy()
                
                # Formato de horas para el usuario
                for col in ['entrada_real', 'salida_real', 'hora_esperada']:
                    df_view[col] = pd.to_datetime(df_view[col]).dt.strftime('%I:%M %p').fillna("--")
                
                # Columnas finales a mostrar
                cols_mostrar = ['persona', 'entrada_real', 'hora_esperada', 'tardanza', 'salida_real', 'tiempo_total_real', 'tiempo_adicional']
                df_final = df_view[cols_mostrar]
                df_final.columns = ['Empleado', 'Entrada Real', 'H. Esperada', '¿Tarde?', 'Salida', 'Jornada', 'Extra (H)']

                st.dataframe(df_final, use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay registros para el {fecha_sel.strftime('%d/%m/%Y')}")
        else:
            st.warning("No se encontraron datos en la base de datos.")

    except Exception as e:
        st.error(f"Error de conexión o de vista: {e}")

with tab2:
    st.header("Carga Semanal de Horarios")
    st.write("Sube el archivo Excel con los IDs biométricos y las horas de entrada para actualizar el comparador.")
    
    archivo_horarios = st.file_uploader("Seleccionar Excel (.xlsx)", type=["xlsx"])
    
    if archivo_horarios:
        try:
            df_upload = pd.read_excel(archivo_horarios)
            
            # Validamos columnas mínimas
            columnas_requeridas = ['BIOMETRIC_ID', 'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO']
            if all(col in df_upload.columns for col in columnas_requeridas):
                st.write("Vista previa de los datos a cargar:")
                st.dataframe(df_upload[columnas_requeridas].head(), use_container_width=True)
                
                if st.button("🚀 Confirmar y Actualizar en la Nube"):
                    # Preparamos los datos para Supabase (Upsert por biometric_id)
                    data_to_upsert = df_upload[columnas_requeridas].to_dict(orient='records')
                    
                    # Ejecutamos la carga
                    res = conn.table("employee_schedules").upsert(data_to_upsert).execute()
                    
                    st.success("✅ ¡Horarios actualizados correctamente! El monitor ya reflejará las nuevas tardanzas.")
            else:
                st.error(f"El archivo no tiene el formato correcto. Debe incluir las columnas: {', '.join(columnas_requeridas)}")
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

    st.write("---")
    st.info("💡 **Instrucciones:** El Excel debe tener el ID del biométrico y la hora de entrada en formato 24h (ej: 05:00 o 14:30). El sistema calculará las extras automáticamente basándose en una jornada de 8 horas.")
