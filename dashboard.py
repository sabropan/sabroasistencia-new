import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN Y ESTILO UI
st.set_page_config(page_title="Sabroasistencia", layout="wide", page_icon="🍞")

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; } 
    .stApp { background-color: #FDF8F3; }
    
    [data-testid="stDataFrame"] td, [data-testid="stTable"] td {
        font-size: 24px !important; 
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    [data-testid="stDataFrame"] th {
        font-size: 18px !important;
        background-color: #D9832E !important;
        color: white !important;
    }

    .metric-card { 
        background-color: white; padding: 10px; border-radius: 12px; 
        border-left: 8px solid #D9832E; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-card h4 { margin: 0; color: #666; font-size: 1rem; }
    .metric-card h2 { margin: 0; color: #D9832E; font-size: 2rem; font-weight: bold; }
    
    div[data-testid="stDateInput"] label { display: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN REFORZADA A SUPABASE
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception:
    conn = st.connection(
        "supabase",
        type=SupabaseConnection,
        url=st.secrets["connections"]["supabase"]["url"],
        key=st.secrets["connections"]["supabase"]["key"]
    )

# --- ESTRUCTURA DE PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📺 Monitor", "📅 Asignar Horarios", "📸 Capturar Fotos", "📊 Reportes y Auditoría"])

# --- TAB 1: MONITOR ---
with tab1:
    col_t, col_cal, col_m1, col_m2, col_m3 = st.columns([1.2, 1, 1, 1, 1])
    
    with col_t:
        st.subheader("🍞 CONTROL DE ASISTENCIA")

    with col_cal:
        hoy_col = (datetime.utcnow() - timedelta(hours=5)).date()
        fecha_consulta = st.date_input("Seleccionar Fecha", hoy_col)

    try:
        query = conn.table("daily_attendance_summary").select("*").execute()
        df_raw = pd.DataFrame(query.data)

        if not df_raw.empty:
            df_raw['fecha_dia'] = pd.to_datetime(df_raw['fecha_dia']).dt.date
            df_hoy = df_raw[df_raw['fecha_dia'] == fecha_consulta].copy()

            with col_m1: st.markdown(f'<div class="metric-card"><h4>Personal</h4><h2>{len(df_hoy)}</h2></div>', unsafe_allow_html=True)
            with col_m2: st.markdown(f'<div class="metric-card"><h4>Tardanzas</h4><h2>{len(df_hoy[df_hoy["tardanza"] == "SÍ"])}</h2></div>', unsafe_allow_html=True)
            en_p = len(df_hoy[df_hoy["salida_real"] == "--"])
            with col_m3: st.markdown(f'<div class="metric-card"><h4>En Planta</h4><h2>{en_p}</h2></div>', unsafe_allow_html=True)

            if not df_hoy.empty:
                url_base = "https://scynlrjnuywjcwovnzxh.supabase.co/storage/v1/object/public/empleados/"
                df_hoy['foto_v'] = df_hoy['biometric_id'].apply(lambda x: f"{url_base}{str(x).zfill(8)}.jpg")

                st.dataframe(
                    df_hoy[['foto_v', 'persona', 'entrada_real', 'salida_real', 'tiempo_total', 'tardanza']],
                    column_config={
                        "foto_v": st.column_config.ImageColumn("", width="small"),
                        "persona": "Empleado",
                        "entrada_real": "Hora Entrada",
                        "salida_real": "Hora Salida",
                        "tiempo_total": "⏱️ Jornada",
                        "tardanza": "¿Llegó Tarde?"
                    },
                    use_container_width=True, hide_index=True
                )
            else:
                st.warning(f"No hay horarios programados para el día {fecha_consulta.strftime('%d/%m/%Y')}")
    except Exception as e:
        st.error(f"Error en Monitor: {e}")

# --- TAB 2: GESTIÓN DE HORARIOS (CON PERSISTENCIA) ---
with tab2:
    st.header("📅 Planificador de Turnos Semanales")
    lunes_actual = hoy_col - timedelta(days=hoy_col.weekday())
    fecha_semana = st.date_input("Semana iniciando el lunes:", lunes_actual, key="fecha_selector")
    
    res_e = conn.table("employees").select("biometric_id, full_name").execute()
    df_emp = pd.DataFrame(res_e.data)
    
    if not df_emp.empty:
        dias_sem = [fecha_semana + timedelta(days=i) for i in range(7)]
        nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        cols_nombres = [f"{nombres_dias[i]} {dias_sem[i].strftime('%d/%m')}" for i, d in enumerate(dias_sem)]
        
        # Cargar o inicializar datos en el estado de la sesión
        session_key = f"df_horarios_{fecha_semana}"
        if session_key not in st.session_state:
            res_h = conn.table("employee_schedules_daily")\
                .select("biometric_id, fecha, entrada_programada, salida_programada")\
                .gte("fecha", dias_sem[0].isoformat())\
                .lte("fecha", dias_sem[6].isoformat()).execute()
            df_existente = pd.DataFrame(res_h.data)

            grid_data = []
            for _, e in df_emp.iterrows():
                fila = {"ID": e['biometric_id'], "Empleado": e['full_name']}
                for i, col_name in enumerate(cols_nombres):
                    fecha_str = dias_sem[i].isoformat()
                    match = df_existente[(df_existente['biometric_id'] == e['biometric_id']) & (df_existente['fecha'] == fecha_str)]
                    if not match.empty:
                        fila[col_name] = f"{str(match.iloc[0]['entrada_programada'])[:5]} - {str(match.iloc[0]['salida_programada'])[:5]}"
                    else:
                        fila[col_name] = "06:00 - 14:00"
                grid_data.append(fila)
            st.session_state[session_key] = pd.DataFrame(grid_data)

        st.info("💡 Instrucciones: Edite las celdas y presione 'Guardar Cambios en la Nube'.")
        df_editor = st.data_editor(st.session_state[session_key], hide_index=True, use_container_width=True, key=f"ed_{fecha_semana}")
        
        if st.button("🚀 GUARDAR CAMBIOS EN LA NUBE"):
            registros = []
            for _, r in df_editor.iterrows():
                for i, col_name in enumerate(cols_nombres):
                    val = r[col_name]
                    if "-" in val:
                        try:
                            ent, sal = val.split("-")
                            registros.append({
                                "biometric_id": r["ID"],
                                "fecha": dias_sem[i].isoformat(),
                                "entrada_programada": ent.strip(),
                                "salida_programada": sal.strip()
                            })
                        except: pass
            
            if registros:
                conn.table("employee_schedules_daily").upsert(registros).execute()
                st.session_state[session_key] = df_editor
                st.success("✅ ¡Horarios sincronizados con la base de datos!")
                st.balloons()

# --- TAB 3: CAPTURAR FOTOS ---
with tab3:
    st.header("📸 Registro Fotográfico")
    res_f = conn.table("employees").select("biometric_id, full_name").execute()
    df_f = pd.DataFrame(res_f.data)
    if not df_f.empty:
        sel = st.selectbox("Empleado:", [f"{r['biometric_id']} - {r['full_name']}" for _, r in df_f.iterrows()])
        cam = st.camera_input("Tomar Foto")
        if cam:
            b_id = sel.split(" - ")[0].zfill(8)
            conn.client.storage.from_("empleados").upload(path=f"{b_id}.jpg", file=cam.getvalue(), file_options={"content-type":"image/jpeg","upsert":"true"})
            st.success(f"Foto guardada para {b_id}")

# --- TAB 4: AUDITORÍA ---
with tab4:
    st.header("📊 Reportes y Auditoría")
    c1, c2 = st.columns(2)
    with c1: f_i = st.date_input("Desde", hoy_col - timedelta(days=15))
    with c2: f_f = st.date_input("Hasta", hoy_col)
    
    if st.button("🔍 Generar Reporte"):
        res_r = conn.table("daily_attendance_summary").select("*").gte("fecha_dia", f_i).lte("fecha_dia", f_f).execute()
        df_r = pd.DataFrame(res_r.data)
        if not df_r.empty:
            st.subheader("Resumen de Tardanzas")
            resumen = df_r.groupby("persona").agg({"tardanza": lambda x: (x == "SÍ").sum()}).rename(columns={"tardanza": "Total Tardanzas"})
            st.dataframe(resumen, use_container_width=True)
            
            st.subheader("Detalle Diario")
            st.dataframe(df_r[['fecha_dia', 'persona', 'entrada_real', 'salida_real', 'tardanza']], use_container_width=True)
